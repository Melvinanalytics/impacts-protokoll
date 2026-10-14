"""Read one immutable selection that Core accepts into plain nodes; refuse anything else."""
from __future__ import annotations

import hashlib
import math
import re
from collections import deque
from pathlib import Path

from impacts_protocol.io import load_yaml_strict

# Private on purpose: a bound revision must be read exactly as the validator reads it.
from impacts_protocol.validator import _validate_application

from .blocks import document


class Unreadable(ValueError):
    """Core accepts the selection, but the view cannot show it without changing its text."""


def issue_list(issues) -> list[dict]:
    return [{"code": i.code, "path": i.path, "message": i.message} for i in issues]


def check_metadata(value) -> None:
    """Refuse non-JSON sets and reused containers before a YAML graph can expand in JSON."""
    pending, seen, count = [(value, 0)], set(), 0
    while pending:
        item, depth = pending.pop()
        count += 1
        if count > 20000 or depth > 64:
            raise Unreadable("metadata exceeds the viewer's bounded JSON projection")
        if isinstance(item, float) and not math.isfinite(item):
            raise Unreadable("nonfinite YAML numbers cannot be represented in the viewer JSON model")
        if isinstance(item, (set, frozenset)):
            raise Unreadable("YAML sets cannot be represented faithfully in the viewer's JSON model")
        if isinstance(item, (dict, list)):
            if id(item) in seen:
                raise Unreadable("reused or recursive YAML alias collections cannot be expanded into the viewer's JSON model")
            seen.add(id(item))
            pending.extend((v, depth + 1) for v in (item.values() if isinstance(item, dict) else item))


def read_file(path: Path, shown: str) -> dict:
    """Read the bytes once. Metadata follows Core's frontmatter rule; body and line numbers
    split only at LF. Where the two splits disagree, refuse instead of guessing."""
    data = path.read_bytes()
    text = data.decode("utf-8-sig")
    lines = [line.removesuffix("\r") for line in text.split("\n")]
    core = text.splitlines()
    metadata, first, meta_lines = {}, 1, None
    if core and core[0].strip() == "---":
        core_close = next((i for i, line in enumerate(core[1:], 1) if line.strip() == "---"), None)
        close = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
        if core_close is None or close is None or lines[0].strip() != "---" or lines[1:close] != core[1:core_close]:
            raise Unreadable(f"{shown}: frontmatter contains a Unicode line separator; "
                             "Core and the view would read different lines")
        metadata = load_yaml_strict("\n".join(core[1:core_close])) or {}
        first, meta_lines = close + 2, ([2, close] if close >= 2 else None)  # YAML lines between the markers
    elif lines[0].strip() == "---":
        raise Unreadable(f"{shown}: Core and the view disagree where the frontmatter starts")
    check_metadata(metadata)
    title, title_line, parts = document("\n".join(lines[first - 1:]), first)
    meta_field_lines = {match.group(2): number for number, line in enumerate(lines[:first - 1], 1)
                        if (match := re.match(r"^(['\"]?)([A-Za-z_]\w*)\1\s*:", line)) and match.group(2) in metadata}
    return {"path": shown, "path_in_revision": re.sub(r"^git-tree:[0-9a-f]+/", "", shown),
            "sha256": hashlib.sha256(data).hexdigest(), "meta_lines": meta_lines,
            "meta": metadata, "meta_field_lines": meta_field_lines, "title": title,
            "title_line": title_line, "sections": parts}


def route_order(process: dict, steps: dict) -> list[str]:
    """Steps in breadth-first route order from the entry; Core guarantees reachability."""
    order, queue = [], deque([process["einstieg_ref"]])
    while queue:
        step = queue.popleft()
        if step not in order:
            order.append(step)
            queue.extend(t for t in steps[step][1]["routen"].values() if t in steps)
    return order


def read_application(root: Path, shown: str, *, check_slug: bool) -> tuple[list[dict], list[dict]]:
    """Validate an immutable Application once; return its issues, or its HP, TP and AS nodes."""
    found = []
    application = _validate_application(root, found, check_slug=check_slug)
    if application is None or found:
        return issue_list(found) or [{"code": "structure.invalid", "path": ".", "message": "Application cannot be read"}], []

    def node(folder: Path, kind: str, parent: str | None) -> dict:
        relative = folder.relative_to(root).as_posix()
        content = read_file(folder / "CONTEXT.md", f"{shown}/CONTEXT.md" if relative == "." else f"{shown}/{relative}/CONTEXT.md")
        return {"id": content["meta"]["id"], "kind": kind, "parent": parent, "children": [], **content}

    hp = node(root, "hauptprozess", None)
    nodes, parts = {hp["id"]: hp}, {}
    for step_id in route_order(application.hauptprozess, application.arbeitsschritte):
        folder = application.arbeitsschritte[step_id][0]
        if folder.parent not in parts:
            parts[folder.parent] = node(folder.parent, "teilprozess", hp["id"])
            nodes[parts[folder.parent]["id"]] = parts[folder.parent]
            hp["children"].append(parts[folder.parent]["id"])
        part_id = parts[folder.parent]["id"]
        step = nodes[step_id] = node(folder, "arbeitsschritt", part_id)
        # JavaScript reorders integer-like object keys; an ordered list keeps the file's order.
        step["routes"] = list(step["meta"]["routen"].items())
        nodes[part_id]["children"].append(step_id)
    return [], list(nodes.values())


def read_run(path: Path, shown: str) -> dict:
    run = read_file(path, shown)
    return {"id": run["meta"]["id"], "kind": "vorgang", "parent": None, "children": [], **run}
