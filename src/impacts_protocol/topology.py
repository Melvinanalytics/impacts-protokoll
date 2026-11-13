"""Workspace levels: each declares its form, and its entries follow that form's shape."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
import os
import re
import subprocess
import unicodedata
from typing import Callable, Iterable
from urllib.parse import unquote

from yaml import YAMLError

from .io import load_frontmatter_and_body
from .model import Issue

LEVEL_FORMS = ("Record Library", "Knowledge Bundle", "Context Map")
CODE_FORMS = ("Capability", "Tool", "Check")
IMPLICIT = {"hauptprozesse", "vorgaenge", "__pycache__"}
DATED = re.compile(r"\d{4}-\d{2}-\d{2}")
SCHEME = re.compile(r"[a-z][a-z0-9+.-]*:", re.IGNORECASE)
ROUTER = "CONTEXT.md"


def body_lines(body: str) -> Iterable[str]:
    """Yield visible Markdown outside comments and code, preserving indentation."""
    body = re.sub(r"<!--.*?(?:-->|$)", "", body, flags=re.DOTALL)
    fence = None
    visible = []
    for line in re.split(r"\r\n|\r|\n", body):
        marker = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            continue
        if marker:
            fence = marker[1]
            continue
        visible.append(line)
    # Inline spans can cross lines; replacing their bytes preserves column-zero rules.
    text = "\n".join(visible)
    text = re.sub(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)",
                  lambda match: re.sub(r"[^\n]", " ", match[0]), text, flags=re.DOTALL)
    yield from text.split("\n")


@dataclass
class Topology:
    root: Path
    human_pattern: str
    issues: list[Issue] = field(default_factory=list)
    forms: dict[Path, str] = field(default_factory=dict)
    held: list[dict] = field(default_factory=list)
    record_units: dict[str, list[Path]] = field(default_factory=dict)
    bundles: list[tuple[Path, str, list[Path]]] = field(default_factory=list)
    has_file: dict[Path, bool] = field(default_factory=dict)
    attempted: set[Path] = field(default_factory=set)
    listings: dict[Path, tuple[dict[str, Path], dict[str, Path]]] = field(default_factory=dict)
    ignored: set[str] = field(default_factory=set)

    def skip(self, path: Path) -> bool:
        name = path.relative_to(self.root).as_posix()
        return name in self.ignored or any(parent.as_posix() + "/" in self.ignored for parent in Path(name).parents if str(parent) != ".") or name + "/" in self.ignored

    def add(self, code: str, path: Path, message: str) -> None:
        self.issues.append(Issue(code, _safe(path.relative_to(self.root).as_posix() or "."), _safe(message)))

    def name(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def opaque(self, path: Path) -> bool:
        return self.forms.get(path) in CODE_FORMS + ("none",)


def check_topology(root: Path, human_pattern: str) -> tuple[list[Issue], tuple[dict, ...], dict[Path, str]]:
    """Return topology issues, held rows and the top-level forms of a workspace."""
    state = Topology(root, human_pattern)
    try:
        result = subprocess.run(["git", "-C", str(root), "ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z"], capture_output=True, check=True)
        state.ignored = set(result.stdout.decode("utf-8", errors="surrogateescape").rstrip("\0").split("\0"))
    except (OSError, subprocess.CalledProcessError):
        pass
    body, children = _read_level(state, root)
    _check_links(state, root, body, may_leave=True)
    for folder in _entries(state, root):
        try:
            if folder.is_dir() and folder.name not in IMPLICIT and folder not in state.attempted:
                state.add("topology.form_missing", folder, f"{folder.name}/ has no Form line; add `Form: {folder.name}/ <form> per <unit>` as a plain unindented line in the root CONTEXT.md; if it has no form, move its content to the case, record or Vorgang it serves or leave it to Git history; only a person may hold it")
        except (OSError, ValueError) as error:
            _unreadable(state, folder, error)
    for child in sorted(children):
        if not state.opaque(child):
            _visit(state, child)
    for folder, body, entries in state.bundles:
        try:
            _linked_entries(state, folder, body, entries, knowledge=True)
        except (OSError, ValueError) as error:
            _unreadable(state, folder, error)
    _scan_definitions(state, root)
    top = {path: form for path, form in state.forms.items() if path.parent == root}
    return state.issues, tuple(state.held), top


def _normal(name: str) -> str:
    return "".join("-" if unicodedata.category(char) == "Pd" else char for char in unicodedata.normalize("NFKC", name).casefold() if unicodedata.category(char) != "Cf")


def _safe(text: str) -> str:
    return "".join(repr(char)[1:-1] if unicodedata.category(char) == "Cc" else char for char in text)


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _locate(folder: Path, relative: str, state: Topology | None = None, *, aliases_ok: bool = True) -> Path | None:
    """Use cached NFC names, then aliases for spelling diagnostics; reject broken symlinks."""
    current = folder
    listings = state.listings if state is not None else {}
    for part in relative.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            current = current.parent
            continue
        try:
            if current not in listings:
                children = list(current.iterdir())
                listings[current] = ({_nfc(child.name): child for child in children}, {_normal(child.name): child for child in children})
            exact, aliases = listings[current]
            current = exact.get(_nfc(part)) or (aliases[_normal(part)] if aliases_ok else exact[_nfc(part)])
        except (KeyError, OSError, ValueError):
            return None
    return current if current.exists() else None


def _unreadable(state: Topology, entry: Path, error: Exception) -> None:
    state.add("topology.shape", entry, f"{state.name(entry)} cannot be read: {error}; restore read access")


def _has_file(state: Topology, folder: Path) -> bool:
    if folder not in state.has_file:
        state.has_file[folder] = _walk_for_file(state, folder)
    return state.has_file[folder]


def _walk_for_file(state: Topology, folder: Path) -> bool:
    found = False
    try:
        children = sorted(folder.iterdir())
    except (OSError, ValueError) as error:
        _unreadable(state, folder, error)
        return True  # Retain unreadable entries so their neighbours are still checked.
    for child in children:
        try:
            if state.skip(child) or child.name.startswith(".") or child.is_symlink():
                continue
            if child.is_file() or child.is_dir() and _has_file(state, child):
                found = True
        except (OSError, ValueError) as error:
            _unreadable(state, child, error)
            found = True
    return found


def _entries(state: Topology, folder: Path) -> list[Path]:
    entries = []
    try:
        children = sorted(folder.iterdir())
    except (OSError, ValueError) as error:
        _unreadable(state, folder, error)
        return entries
    for entry in children:
        if state.skip(entry) or entry.name.startswith(".") or entry.name == ROUTER:
            continue
        try:
            if entry.is_dir() and not entry.is_symlink() and not state.opaque(entry) and not _has_file(state, entry):
                continue
            entries.append(entry)
        except (OSError, ValueError) as error:
            _unreadable(state, entry, error)
    return entries


def _scan_definitions(state: Topology, folder: Path) -> None:
    try:
        children = sorted(folder.iterdir())
    except (OSError, ValueError) as error:
        _unreadable(state, folder, error)
        return
    for child in children:
        try:
            if state.skip(child) or child.name.startswith(".") or child.is_symlink() or not child.is_dir():
                continue
            if state.forms.get(child) in {"none", "Context Map"}:
                continue
            if child.parent == state.root and child.name in {"hauptprozesse", "vorgaenge"}:
                continue
            context = child / ROUTER
            if not state.skip(context) and context.is_file() and not context.is_symlink():
                try:
                    document, _ = load_frontmatter_and_body(context, state.root)
                except (ValueError, YAMLError, RecursionError):
                    text = context.read_text(encoding="utf-8-sig", errors="replace")
                    front = re.match(r"\A---[ \t]*\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
                    document = {"type": "hauptprozess"} if front and re.search(r"^type:[ \t]*(['\"]?)hauptprozess\1[ \t]*$", front[1], re.MULTILINE) else {}
                except OSError as error:
                    _unreadable(state, context, error)
                    document = {}
                if isinstance(document, dict) and document.get("type") == "hauptprozess":
                    state.add("topology.shape", context, "Hauptprozess definition outside hauptprozesse/; report it to the owner, whose confirming commit moves it into hauptprozesse/; a candidate goes under analyse/")
            _scan_definitions(state, child)
        except (OSError, ValueError) as error:
            _unreadable(state, child, error)


def _read_level(state: Topology, folder: Path) -> tuple[str, set[Path]]:
    """Read a level router's Form lines; return its body and declared child levels."""
    context = folder / ROUTER
    if state.skip(context):
        return "", set()
    body = ""
    try:
        if context.is_symlink() or context.exists() and not context.is_file():
            state.add("topology.shape", context, f"{state.name(context)} is not a regular file; replace it with the level's router")
        elif context.is_file():
            _, body = load_frontmatter_and_body(context, state.root)
    except (ValueError, YAMLError, OSError) as error:
        _unreadable(state, context, error)
    children: set[Path] = set()
    for line in body_lines(body):
        if line.startswith("Form:"):
            target = _declare(state, folder, context, line[len("Form:"):].strip())
            if target is not None and target != folder:
                children.add(target)
    return body, children


def _declare(state: Topology, folder: Path, context: Path, value: str) -> Path | None:
    target = folder
    whole = _token(state, value)
    path_match = None if whole[0] else re.match(r"(.+?/)\s+(.*)$", value)
    candidate = path_match[2] if path_match else value
    token, hold = _token(state, candidate)
    if folder != state.root and token is None and not re.fullmatch(r"none:[ \t]*\S.*", candidate):
        return None
    if path_match:
        name, value = path_match.groups()
        if name.count("/") != 1 or name[:-1] in {".", ".."} or "\\" in name:
            state.add("topology.form_invalid", context, f"Form path {name!r} is not one folder; write one relative folder name with a trailing slash")
            return None
        target = folder / name[:-1]
        if state.skip(target):
            return None
        try:
            matches = [child for child in folder.iterdir() if _normal(child.name) == _normal(name[:-1])]
            if matches:
                target = next((child for child in matches if _nfc(child.name) == _nfc(name[:-1])), sorted(matches)[0])
                state.attempted.add(target)
                if _nfc(target.name) != _nfc(name[:-1]):
                    state.add("topology.form_invalid", context, f"Form path {name!r} differs from on-disk {target.name + '/'!r}; use the on-disk spelling")
                    if target in state.forms:
                        return None
        except (OSError, ValueError) as error:
            _unreadable(state, folder, error)
            return None
    elif folder == state.root:
        state.add("topology.form_invalid", context, f"Root Form line {value!r} names no folder; write Form: <folder>/ <form> per <unit>")
        return None
    state.attempted.add(target)
    if folder != state.root and (token in CODE_FORMS + ("Pipeline", "none") or value.startswith("none:")):
        state.add("topology.form_invalid", context, "top-level lines live only in the root CONTEXT.md; move this line there or use the parent's form")
        return None
    label = f"{state.name(target)}/"
    if token is None:
        state.add("topology.form_invalid", context, f"Form line for {label} is not valid: {value!r}; write a form with its unit, `Capability`, `Tool` or `Check` alone, or a held row with reason and decided by human:<id>")
        return None
    fixed = {"records": "Record Library", "grundlagen": "Knowledge Bundle", "analyse": "Context Map", "capabilities": "Capability"}
    if target.parent == state.root and target.name in fixed and token != fixed[target.name]:
        state.add("topology.form_invalid", context, f"{label} must be {fixed[target.name]}; use its fixed form")
        return None
    if token == "Context Map" and not (target.parent == state.root and target.name == "analyse"):
        state.add("topology.form_invalid", context, f"{label} is a Context Map outside analyse/; Context Map lives only in analyse/; move it there or use the parent's form")
        return None
    if target in state.forms:
        state.add("topology.form_invalid", context, f"{label} has a second Form line; keep exactly one")
        return None
    parent = target.parent
    if parent != state.root and parent in state.forms and state.forms[parent] not in {"Record Library", "Knowledge Bundle"}:
        state.add("topology.form_invalid", context, f"{label} cannot be a sub-level of a {state.forms[parent]}; remove the line or move the folder out")
        return None
    if parent != state.root and parent in state.forms and token != state.forms[parent]:
        state.add("topology.form_invalid", context, f"{label} is a {token} under the {state.forms[parent]} {state.name(parent)}/; declare it as a {state.forms[parent]} or move it")
        return None
    state.forms[target] = token
    try:
        if not target.is_dir() or target.is_symlink():
            state.add("topology.form_invalid", context, f"{label} is missing or a symlink; create a regular directory or correct its Form path")
            return None
    except (OSError, ValueError) as error:
        _unreadable(state, target, error)
        return None
    if hold:
        state.held.append({"path": label, "reason": hold[1].strip(), "decided_by": hold[2]})
    return target


def _token(state: Topology, value: str):
    """Code tokens, Pipeline and held rows reach here only from the root (checked by the caller)."""
    for form in LEVEL_FORMS:
        if re.fullmatch(re.escape(form) + r" per \S.*", value):
            return form, None
    if value in CODE_FORMS:
        return value, None
    if re.fullmatch(r"Pipeline per \S.*", value):
        return "Pipeline", None
    hold = re.fullmatch(r"none:[ \t]*(.*?); decided by (human:.*)", value)
    if hold and hold[1].strip() and re.fullmatch(state.human_pattern, hold[2]):
        return "none", hold
    return None, None


def _visit(state: Topology, folder: Path) -> None:
    try:
        if (folder / ROUTER).is_symlink() or (folder / ROUTER).exists() or _has_file(state, folder):
            _visit_readable(state, folder)
    except (OSError, ValueError) as error:
        _unreadable(state, folder, error)


def _visit_readable(state: Topology, folder: Path) -> None:
    body, children = _read_level(state, folder)
    entries = _entries(state, folder)
    if state.forms.get(folder) in {"Record Library", "Knowledge Bundle"}:
        children |= {entry for entry in entries if _declares_itself(state, entry)}
    for child in sorted(children):
        if not state.opaque(child):
            _visit(state, child)
    token = state.forms.get(folder)
    if (folder / ROUTER).is_file():
        _check_links(state, folder, body)
    SHAPES.get(token or "", lambda *_: None)(state, folder, body, entries)


def _declares_itself(state: Topology, entry: Path) -> bool:
    """An entry folder may declare its own form in its router, without a path."""
    context = entry / ROUTER
    try:
        if state.skip(context) or entry in state.forms or not entry.is_dir() or entry.is_symlink() or not context.is_file() or context.is_symlink():
            return False
        _, body = load_frontmatter_and_body(context, state.root)
    except (OSError, ValueError) as error:
        _unreadable(state, entry, error)
        return False
    except YAMLError:
        return False
    return any(line.startswith("Form:") and (_token(state, line[5:].strip())[0] is not None or re.fullmatch(r"none:[ \t]*\S.*", line[5:].strip())) for line in body_lines(body))


def _record_library(state: Topology, folder: Path, body: str, entries: list[Path]) -> None:
    level = state.name(folder) + "/"
    folders, files = [], []
    for entry in entries:
        if entry in state.attempted and entry not in state.forms:
            continue
        try:
            (folders if entry.is_dir() else files).append(entry)
        except (OSError, ValueError) as error:
            _unreadable(state, entry, error)
    sublevels = [entry for entry in folders if entry in state.forms]
    others = [entry for entry in folders + files if entry not in sublevels]
    if sublevels:
        for entry in others:
            state.add("topology.shape", entry, f"{entry.name} sits beside record-kind sub-levels of {level}; a level holds kinds or instances, not both: move it into its kind, or move the kinds to their own Record Library")
    elif folders and files:
        odd, shape, kind = (files, "folders", "file") if len(files) <= len(folders) else (folders, "files", "folder")
        action = f"if it is the kind's table, move it into {level}{ROUTER}; otherwise move it to the instance or record kind it belongs to" if kind == "file" else "split folders and files into separate record kinds, each with one shape"
        for entry in odd:
            state.add("topology.shape", entry, f"{entry.name} is a {kind} among the instance {shape} of {level}; {action}")
    single_table = not folders and len(files) == 1
    for entry in ([] if single_table else others):
        key = _normal(entry.name if entry in folders else entry.name.split(".", 1)[0])
        if entry in folders or key not in {"readme", "context"}:
            state.record_units.setdefault(key, []).append(entry)


def _dated(name: str) -> bool:
    match = DATED.match(name)
    if match:
        try:
            date.fromisoformat(match[0])
            return True
        except ValueError:
            pass
    return False


def _linked_entries(state: Topology, folder: Path, body: str, entries: list[Path], *, knowledge: bool = False) -> None:
    level = state.name(folder) + "/"
    context = folder / ROUTER
    has_router = not state.skip(context) and context.is_file() and not context.is_symlink()
    if not has_router:
        if not context.is_symlink() and not context.exists():
            state.add("topology.shape", folder, f"{level} has no {ROUTER}; add one that links every entry")
        return
    targets, spellings = set(), {}
    for link in _links(body):
        try:
            target = _link_target(link)
            if target and not SCHEME.match(target):
                located = _locate(folder, target, state)
                spellings.setdefault(_normal(os.path.abspath(folder / target)), target)
                if located is not None and _nfc(str(located)) == _nfc(os.path.normpath(folder / target)):
                    targets.add(_nfc(str(located.resolve())))
        except (OSError, ValueError, RuntimeError):
            continue
    for entry in entries:
        try:
            key = _normal(entry.name if entry.is_dir() else entry.name.split(".", 1)[0])
            matches = state.record_units.get(key, []) if knowledge else []
            if matches:
                matches = sorted(matches, key=lambda path: (not path.is_dir(), state.name(path)))
                record = state.name(matches[0]) + (f" and {len(matches) - 1} more" if len(matches) > 1 else "")
                state.add("topology.shape", entry, f"{state.name(entry)} has the name of record {record}; if it holds that record's material, move it there; otherwise rename it")
            elif knowledge and _dated(_normal(entry.name)):
                state.add("topology.shape", entry, f"{entry.name} is dated work; move it to its case, its Vorgang or Git history; a rule's validity date goes inside the file or after its name")
            elif entry in state.attempted and entry not in state.forms:
                continue
            elif knowledge and entry.is_dir() and entry not in state.forms:
                state.add("topology.shape", entry, f"{entry.name}/ is not a declared sub-level of {level}; if it holds foundations, declare it as a Knowledge Bundle with its own router; otherwise move it to its case or record")
            elif _nfc(str(entry.resolve())) not in targets and (not entry.is_dir() or _nfc(str((entry / ROUTER).resolve())) not in targets):
                if entry.is_symlink() and not entry.exists():
                    state.add("topology.shape", entry, f"{entry.name} is a broken symlink; remove it or restore its target")
                    continue
                alias = spellings.get(_normal(str(entry.absolute())))
                if alias is None and entry.is_dir():
                    alias = spellings.get(_normal(str((entry / ROUTER).absolute())))
                message = f"{entry.name} is linked as {alias!r}; use the on-disk spelling" if alias is not None else f"{entry.name} is not linked from {level}{ROUTER}; link it"
                if entry.is_dir():
                    message += "; link the entry itself, not a file inside it"
                state.add("topology.shape", entry, message)
        except (OSError, ValueError) as error:
            _unreadable(state, entry, error)


def _pipeline(state: Topology, folder: Path, body: str, entries: list[Path]) -> None:
    level = state.name(folder) + "/"
    for entry in entries:
        try:
            if not entry.is_dir():
                state.add("topology.shape", entry, f"{entry.name} is loose in process home {level}; move it into its process folder or out of the process home")
            elif not (entry / ROUTER).is_file():
                state.add("topology.shape", entry, f"Process folder {entry.name}/ has no {ROUTER}; add its router")
        except (OSError, ValueError) as error:
            _unreadable(state, entry, error)


SHAPES: dict[str, Callable[[Topology, Path, str, list[Path]], None]] = {
    "Record Library": _record_library,
    "Knowledge Bundle": lambda state, folder, body, entries: state.bundles.append((folder, body, entries)),
    "Pipeline": _pipeline,
    "Context Map": _linked_entries,
}


def _links(body: str) -> list[str]:
    # Destination atoms cannot consume an opener; failed long runs stay linear.
    visible = "\n".join(body_lines(body))
    atom = r"(?:\\[()]|[^\s()<>\\])"
    destination = rf"(?:{atom}|\((?:{atom})*\))+"
    pattern = rf"\]\([ \t]*(<[^<>\n]*>|{destination})(?:[ \t]+(?:\"[^\"\n]*\"|'[^'\n]*'|\([^()\n]*\)))?[ \t]*\)"
    return [match[1] for match in re.finditer(pattern, visible)]


def _link_target(link: str) -> str:
    return unquote(re.sub(r"\\([()])", r"\1", link.strip("<>").split("#", 1)[0]), errors="strict")


def _check_links(state: Topology, folder: Path, body: str, *, may_leave: bool = False) -> None:
    context = folder / ROUTER
    for link in _links(body):
        target = link
        try:
            target = _link_target(link)
            if not target or SCHEME.match(target):
                continue
            if target.startswith("/"):
                if not may_leave:
                    state.add("topology.shape", context, f"Link {target!r} is absolute; use a path relative to this CONTEXT.md")
                continue
            located = _locate(folder, target, state)
            resolved = (located or folder / target).resolve()
            inside = resolved.is_relative_to(state.root.resolve())
            if may_leave and not inside:
                continue
            if not inside:
                state.add("topology.shape", context, f"Link {target!r} leaves the workspace; name the source by release and revision instead")
            elif located is None:
                state.add("topology.shape", context, f"Link {target!r} does not resolve; correct or remove it")
            elif _locate(folder, target, state, aliases_ok=False) is None and not (
                    state.forms.get(folder) in {"Knowledge Bundle", "Context Map"} and (located.parent == folder or located.parent.parent == folder and located.name == ROUTER)):
                # A misspelt link to an entry of this level is reported once, on the entry.
                state.add("topology.shape", context, f"Link {target!r} differs from the on-disk spelling {state.name(located)!r}; use the on-disk spelling")
        except (OSError, ValueError, RuntimeError):
            state.add("topology.shape", context, f"Link {target!r} does not resolve; correct or remove it")
