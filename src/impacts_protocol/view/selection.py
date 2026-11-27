"""Fix one immutable selection and turn it into page models.

A Hauptprozess is copied first, so Core and the view see the same bytes. A Vorgang is
drawn on the Git tree it binds. A workspace is the inventory of every entry under
hauptprozesse/ and vorgaenge/, each its own selection, plus the Ist-Prozess files under
analyse/, read from the working files (Core does not check them); if the
inventory, an Ist-Prozess file or HEAD changes while the view is generated, nothing is written. Known limit: a Vorgang is validated on
live workspace files; its whole folder must be byte-identical before validation and after
reading, but a change undone in between stays undetected.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import stat
import subprocess
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from .project import SUBJECT_HEADINGS
from impacts_protocol.generator import WORKSPACE_FOLDERS
from impacts_protocol.io import load_frontmatter, load_frontmatter_and_body
from impacts_protocol.hashing import _has_symlink_component
from impacts_protocol.topology import NAVIGATION, blocks_vorgaenge, body_lines
from impacts_protocol.validator import SCHEMA_REGISTRY, validate

# Private on purpose: a bound revision must be materialized exactly as the validator does.
from impacts_protocol.validator import _materialize_tree

from . import project
from .read import Unreadable, issue_list, read_hauptprozess, read_file, read_vorgang

FORMAT = "impacts-view/5"
TREE = re.compile(r"git-tree:([0-9a-f]{40}|[0-9a-f]{64})")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
IST = "analyse"  # source material, not a Core folder: kept out of WORKSPACE_FOLDERS and its issue filter
OUTPUT_TEXT_EXTS = frozenset({".md", ".txt", ".json", ".yaml", ".yml", ".csv"})
OUTPUT_PREVIEW_LIMIT = 12_000
VIEW_LINE = re.compile(r"^View:[ \t]+(.+?)(?:[ \t]+\|[ \t]+(.+?))?[ \t]*$")
RECORD_LIB_LINE = re.compile(r"^Form:[ \t]+([^/\s]+)/[ \t]+Record Library per \S")
BRIDGE_PREFIXES = ("Reality and Leistungsstückliste bridge:", "Realitäts- und Leistungsstücklisten-Brücke:")


def git(folder: Path, *args: str) -> str | None:
    try:
        done = subprocess.run(["git", "--no-replace-objects", "-C", str(folder), *args], capture_output=True, text=True)
    except OSError:
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def workspace_of(folder: Path) -> Path | None:
    top = git(folder, "rev-parse", "--show-toplevel")
    return Path(top).resolve() if top else None


def kind_of(path: Path) -> str:
    """hauptprozess, vorgang or workspace, from the selected path and its frontmatter type."""
    path = path.resolve()
    if path.is_file():
        if path.name == "CONTEXT.md" and path.parent.parent.name == "vorgaenge":
            return "vorgang"
        raise SystemExit(f"{path}: select a Hauptprozess folder, a workspace folder or vorgaenge/<slug>/CONTEXT.md")
    try:
        kind = load_frontmatter(path / "CONTEXT.md").get("type")
    except (OSError, ValueError) as error:
        raise SystemExit(f"{path}: cannot read CONTEXT.md: {error}")
    if kind in ("workspace", "hauptprozess"):
        return "workspace" if kind == "workspace" else "hauptprozess"
    raise SystemExit(f"{path}: CONTEXT.md type must be workspace or hauptprozess, found {kind!r}")


def refused(kind: str, selection: dict, issues: list[dict]) -> dict:
    return {"format": FORMAT, "kind": kind, "selection": selection, "issues": issues}


def unreadable(kind: str, selection: dict, path: str, error: Exception) -> dict:
    return refused(kind, selection, [{"code": "view.unreadable", "path": path, "message": str(error)}])


def tree_oid(folder: Path, algorithm: str) -> str:
    """The Git tree id these exact bytes would have, computed without touching any repository."""
    entries = []
    for child in folder.iterdir():
        if child.is_dir():
            if not any(child.iterdir()):
                continue
            entries.append((child.name + "/", "40000", child.name, bytes.fromhex(tree_oid(child, algorithm))))
        else:
            data = child.read_bytes()
            blob = hashlib.new(algorithm, b"blob %d\0" % len(data) + data).digest()
            mode = "100755" if os.stat(child).st_mode & 0o100 else "100644"
            entries.append((child.name, mode, child.name, blob))
    body = b"".join(f"{mode} {name}".encode() + b"\0" + oid for _, mode, name, oid in sorted(entries))
    return hashlib.new(algorithm, b"tree %d\0" % len(body) + body).hexdigest()


@contextmanager
def hauptprozess_copy(root: Path):
    """Copy only what Core allows in a Hauptprozess tree: folders, CONTEXT.md and symlinks (which Core
    rejects). Any other entry is reported before its payload is copied."""
    with TemporaryDirectory(prefix="impacts-view-") as folder:
        copy, unknown = Path(folder) / root.name, []

        def skip(directory: str, names: list[str]) -> set[str]:
            odd = {n for n in names if n != "CONTEXT.md" and not Path(directory, n).is_symlink()
                   and not Path(directory, n).is_dir()}
            unknown.extend(Path(directory, n).relative_to(root).as_posix() for n in sorted(odd))
            return odd

        shutil.copytree(root, copy, symlinks=True, ignore=skip)
        yield copy, unknown


def digest(nodes: list[dict]) -> str:
    listing = "".join(f"{n['path']}\0{n['sha256']}\n" for n in sorted(nodes, key=lambda n: n["path"]))
    return "sha256:" + hashlib.sha256(listing.encode()).hexdigest()


def hauptprozess_page(root: Path, algorithm: str | None = None) -> dict:
    """`algorithm` is the workspace's Git object format; given, the page records the tree id of
    the bytes it actually read."""
    selection = {"hauptprozess": root.name, "folder": root.name, "revision": None, "vorgang": None, "tree": None}
    try:
        with hauptprozess_copy(root.resolve()) as (copy, unknown):
            if unknown:
                return refused("hauptprozess", selection, [{"code": "structure.level", "path": p,
                                                           "message": "Unknown Hauptprozess entry"} for p in unknown])
            issues, nodes = read_hauptprozess(copy, root.name, check_slug=True)
            if algorithm and not issues:
                selection["tree"] = tree_oid(copy, algorithm)
    except (Unreadable, OSError, ValueError) as error:
        return unreadable("hauptprozess", selection, root.name, error)
    if issues:
        return refused("hauptprozess", selection, issues)
    project.annotate(nodes)
    selection.update(hauptprozess=nodes[0]["id"], revision=digest(nodes))
    return {"format": FORMAT, "kind": "hauptprozess", "selection": selection, "issues": [],
            "nodes": nodes, "vorgang": None, "view": None, "stand": project.stand(nodes, None, None),
            "map": project.map_tree(nodes, None, None)}


def vorgang_issues(report, vorgang_rel: str) -> list[dict]:
    """This Vorgang's issues plus every finding that blocks all Vorgänge (blocks_vorgaenge):
    a broken workspace router or an unreadable or misplaced folder means Core may not have
    checked this Vorgang at all. Navigation and router-shape findings never block; the
    overview lists those outside the Core folders, a Hauptprozess page those inside it."""
    return issue_list([i for i in report.issues
                       if i.path == vorgang_rel or i.path.startswith(vorgang_rel + "/") or blocks_vorgaenge(i)])


def hauptprozess_notes(report, rel: str) -> list[dict]:
    """Navigation findings inside one Hauptprozess folder, such as a broken body link: shown on
    its page as notes; they never refuse it."""
    return issue_list([i for i in report.issues if i.path.startswith(rel + "/") and i.code in NAVIGATION])


def bound_hauptprozess(workspace: Path, revision: str, cache: dict) -> tuple[list[dict], list[dict]]:
    """A bound tree is immutable; read it once per generation."""
    if revision not in cache:
        with TemporaryDirectory(prefix="impacts-view-") as folder:
            if not _materialize_tree(workspace, TREE.fullmatch(revision).group(1), Path(folder)):
                raise Unreadable(f"cannot read {revision}")
            cache[revision] = read_hauptprozess(Path(folder), revision, check_slug=False)
            project.annotate(cache[revision][1])
    return cache[revision]


def legacy_vorgang_projection(path: Path, workspace: Path) -> dict | None:
    """Best-effort read projection for a `not_judged` Vorgang (`binding.md#snapshot-and-provenance`).
    Never adds Core issues and never counts as checked by this release."""
    rel = path.relative_to(workspace).as_posix()
    try:
        if path.is_symlink() or not path.is_file() or _has_symlink_component(path, workspace):
            return None
        content = read_file(path, rel)
    except (Unreadable, OSError, ValueError, yaml.YAMLError):
        return None
    meta = content["meta"] if isinstance(content.get("meta"), dict) else {}
    raw_entries = meta.get("laufpfad") if isinstance(meta.get("laufpfad"), list) else []
    entries = []
    for entry in raw_entries:
        if not isinstance(entry, dict):
            continue
        item = {key: entry[key] for key in ("arbeitsschritt_ref", "nummer", "status", "gewaehlte_route", "status_seit")
                if key in entry}
        if isinstance(entry.get("wiedereinstieg"), dict):
            item["wiedereinstieg"] = {k: entry["wiedereinstieg"][k]
                                      for k in ("ausloeser", "faellig", "continuation_ref")
                                      if k in entry["wiedereinstieg"]}
        if isinstance(entry.get("geschrieben"), list):
            item["geschrieben"] = [ref for ref in entry["geschrieben"] if isinstance(ref, dict) and "pfad" in ref]
        entries.append(item)
    return {
        "id": meta.get("id") if isinstance(meta.get("id"), str) else None,
        "title": content.get("title"),
        "protocol": meta.get("protocol") if isinstance(meta.get("protocol"), str) else None,
        "hauptprozess_revision": meta.get("hauptprozess_revision") if isinstance(meta.get("hauptprozess_revision"), str) else None,
        "subject": subject_record(path, workspace),
        "laufpfad": entries,
        "sections": content.get("sections", []),
        "path": rel,
        "sha256": content.get("sha256"),
    }


def _read_output_preview(target: Path, vorgang_dir: Path, workspace: Path) -> tuple[str | None, bool, str | None]:
    """Read a bounded UTF-8 text preview from a regular file inside `vorgang_dir`, without symlinks."""
    try:
        if target.is_symlink() or not target.is_file() or _has_symlink_component(target, workspace):
            return None, False, None
        resolved = target.resolve()
        if not resolved.is_relative_to(vorgang_dir.resolve()):
            return None, False, None
        raw = resolved.read_bytes()
        digest_hex = "sha256:" + hashlib.sha256(raw).hexdigest()
        if resolved.suffix.lower() not in OUTPUT_TEXT_EXTS:
            return None, False, digest_hex
        text = raw.decode("utf-8")
        truncated = len(text) > OUTPUT_PREVIEW_LIMIT
        return (text[:OUTPUT_PREVIEW_LIMIT] if truncated else text), truncated, digest_hex
    except (OSError, UnicodeError, RuntimeError):
        return None, False, None


def attempt_outputs(vorgang_dir: Path, workspace: Path, laufpfad: list[dict]) -> list[list[dict]]:
    """Readable previews for declared `geschrieben` outputs and open-attempt drafts (labelled draft=True)."""
    all_outputs: list[list[dict]] = []
    for entry in laufpfad:
        items: list[dict] = []
        seen: set[str] = set()
        for ref in entry.get("geschrieben") or []:
            if not isinstance(ref, dict) or not isinstance(ref.get("pfad"), str):
                continue
            rel = ref["pfad"]
            seen.add(rel)
            preview, truncated, _ = _read_output_preview(workspace / rel, vorgang_dir, workspace)
            items.append({
                "pfad": rel,
                "sha256": ref.get("sha256"),
                "draft": False,
                "preview": preview,
                "truncated": truncated,
            })
        if entry.get("status") in ("aktiv", "wartend"):
            step_ref = str(entry.get("arbeitsschritt_ref") or "")
            step_slug = step_ref.split(":", 1)[1] if ":" in step_ref else step_ref
            nummer = entry.get("nummer")
            if step_slug and isinstance(nummer, int):
                out_dir = vorgang_dir / step_slug / f"{nummer:03d}" / "output"
                if out_dir.is_dir() and not out_dir.is_symlink() and not _has_symlink_component(out_dir, workspace):
                    for candidate in sorted(out_dir.rglob("*")):
                        if candidate.is_symlink() or not candidate.is_file():
                            continue
                        rel = candidate.relative_to(workspace).as_posix()
                        if rel in seen:
                            continue
                        seen.add(rel)
                        preview, truncated, digest_hex = _read_output_preview(candidate, vorgang_dir, workspace)
                        items.append({
                            "pfad": rel,
                            "sha256": digest_hex,
                            "draft": True,
                            "preview": preview,
                            "truncated": truncated,
                        })
        all_outputs.append(items)
    return all_outputs


def vorgang_page(path: Path, workspace: Path, report, before: dict | Exception, cache: dict) -> dict:
    """`report` is Core's validation of `workspace`; `before` is the Vorgang folder's state captured before it."""
    vorgang_rel = path.parent.relative_to(workspace).as_posix()
    selection = {"hauptprozess": None, "revision": None, "vorgang": vorgang_rel}
    skipped = [item for item in report.not_judged if item.path == f"{vorgang_rel}/CONTEXT.md"]
    if not skipped and not report.workspace_judged:
        skipped = [item for item in report.not_judged if item.path == "CONTEXT.md" and not item.reason]
    if skipped:
        item = skipped[0]
        model = {"format": FORMAT, "kind": "vorgang", "selection": selection, "issues": [],
                 "not_judged": {"path": item.path, "protocol": item.protocol,
                                "validator_protocol": item.validator_protocol, "message": item.message}}
        legacy = legacy_vorgang_projection(path, workspace)
        if legacy is not None:
            model["legacy"] = legacy
        return model
    issues = vorgang_issues(report, vorgang_rel)
    if issues:
        return refused("vorgang", selection, issues)
    try:
        if isinstance(before, Exception):
            raise before
        vorgang = read_vorgang(path, f"{vorgang_rel}/CONTEXT.md")
        if before.get("CONTEXT.md") != vorgang["sha256"] or capture(path.parent) != before:
            raise Unreadable(f"{vorgang_rel} changed during generation; generate the view again")
        revision = TREE.fullmatch(str(vorgang["meta"]["hauptprozess_revision"]))
        if revision is None:
            raise Unreadable("the validated Vorgang has no hauptprozess_revision")
        issues, nodes = bound_hauptprozess(workspace, revision.group(0), cache)
    except (Unreadable, OSError, ValueError) as error:
        return unreadable("vorgang", selection, vorgang_rel, error)
    if issues:
        return refused("vorgang", selection, issues)
    selection.update(hauptprozess=nodes[0]["id"], revision=revision.group(0))
    project.annotate([vorgang])
    superseded = f"{vorgang_rel}/CONTEXT.md" in report.superseded
    view = project.phases(nodes, vorgang["meta"]["laufpfad"], superseded=superseded)
    subject = subject_record(path, workspace)
    view["subject_stage"] = subject["stage"] if subject else "open"
    outputs = attempt_outputs(path.parent, workspace, vorgang["meta"]["laufpfad"])
    page = {"format": FORMAT, "kind": "vorgang", "selection": selection, "issues": [], "nodes": nodes, "vorgang": vorgang,
            "subject": subject, "attempt_phases": [project.ATTEMPT_PHASE[e["status"]] for e in vorgang["meta"]["laufpfad"]],
            "view": view, "stand": project.stand(nodes, vorgang, view), "map": project.map_tree(nodes, vorgang, view)}
    if any(outputs):
        page["attempt_outputs"] = outputs
    return page


def subject_record(path: Path, workspace: Path) -> dict | None:
    """Resolve the single Subject link; its address is navigation, not a domain identity mapping."""
    try:
        body = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    headings = "|".join(re.escape(name) for name in SUBJECT_HEADINGS)
    section = re.search(r"(?ms)^## (?:" + headings + r")\n(.*?)(?=^## |\Z)", body)
    links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", section[1]) if section else []
    if len(links) != 1:
        return None
    relative, _, anchor = links[0].partition("#")
    original = path.parent / relative
    try:
        target = original.resolve()
        if not target.is_relative_to(workspace.resolve()) or not target.is_file() or _has_symlink_component(original, workspace):
            return None
        text = target.read_text(encoding="utf-8")
        stage = record_stages(text).get(anchor, "open")
    except (OSError, UnicodeError, RuntimeError):
        return None
    return {"record": target.relative_to(workspace.resolve()).as_posix() + ("#" + anchor if anchor else ""),
            "stage": stage}


def record_stages(text: str) -> dict[str, str]:
    """W4's Stage/Stufe line or anchored Stage/Stufe column; repeated declarations stay open."""
    found = {}
    lines = re.findall(r"(?m)^(?:Stage|Stufe):(.*?)$", text)
    if lines:
        found[""] = [line.strip() or "open" for line in lines]
    headers = []
    stage_idx = None
    for row in text.splitlines():
        if not row.startswith("|"):
            headers = []
            stage_idx = None
            continue
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        stage_cols = [i for i, cell in enumerate(cells) if cell in ("Stage", "Stufe")]
        if stage_cols:
            headers = cells
            stage_idx = stage_cols[0] if len(stage_cols) == 1 else None
        elif headers:
            for anchor in re.findall(r"<a id=[\"']([^\"']+)[\"']></a>", row):
                stage = (cells[stage_idx] if stage_idx is not None and len(cells) == len(headers) else "open")
                found.setdefault(anchor, []).append(stage or "open")
    return {anchor: values[0] if len(values) == 1 else "open" for anchor, values in found.items()}


def _record_library_roots(workspace: Path) -> list[Path]:
    """All declared top-level Record Library folders plus `records/`, without symlinks."""
    names: list[str] = []
    context = workspace / "CONTEXT.md"
    try:
        if context.is_file() and not context.is_symlink():
            _, body = load_frontmatter_and_body(context, workspace)
            for line in body_lines(body):
                if match := RECORD_LIB_LINE.match(line):
                    names.append(match.group(1))
    except (OSError, ValueError, yaml.YAMLError):
        pass
    if "records" not in names:
        names.append("records")
    roots = []
    for name in sorted(set(names)):
        folder = workspace / name
        if folder.is_dir() and not folder.is_symlink():
            roots.append(folder)
    return roots


def record_inventory(workspace: Path) -> list[dict]:
    """Readable Stage/Stufe records across declared Record Libraries, without following symlinks.

    The digest participates in the generation stability check, not in domain identity.
    """
    found = []
    for root in _record_library_roots(workspace):
        for directory, folders, files in os.walk(root, followlinks=False):
            folders[:] = sorted(name for name in folders if not Path(directory, name).is_symlink())
            for name in sorted(files):
                path = Path(directory, name)
                if path.suffix != ".md" or path.is_symlink() or not path.is_file():
                    continue
                try:
                    data = path.read_bytes()
                    stages = record_stages(data.decode("utf-8"))
                except (OSError, UnicodeError) as error:
                    raise SystemExit(f"cannot read record {path}: {error}") from error
                rel = path.relative_to(workspace).as_posix()
                found.extend({"record": rel + ("#" + anchor if anchor else ""), "stage": stage,
                              "sha256": hashlib.sha256(data).hexdigest()} for anchor, stage in stages.items())
    return found


def declared_views(workspace: Path) -> list[tuple[str, str | None]]:
    """Column-zero `View: <relative-path> [| <title>]` declarations in root CONTEXT.md."""
    context = workspace / "CONTEXT.md"
    found: list[tuple[str, str | None]] = []
    try:
        if not context.is_file() or context.is_symlink():
            return found
        _, body = load_frontmatter_and_body(context, workspace)
    except (OSError, ValueError, yaml.YAMLError):
        return found
    for line in body_lines(body):
        if match := VIEW_LINE.match(line):
            found.append((match.group(1).strip(), match.group(2).strip() if match.group(2) else None))
    return found


def view_inventory(workspace: Path) -> list[tuple[str, str | None, str]]:
    """Stability snapshot of declared `View:` entries."""
    items = []
    for rel, title in declared_views(workspace):
        target = workspace / rel
        if rel.startswith("/") or ".." in Path(rel).parts or not target.exists() or target.is_symlink() or _has_symlink_component(target, workspace):
            items.append((rel, title, "missing-or-invalid"))
        else:
            items.append((rel, title, entry_state(target)))
    return items


def system_view_pages(workspace: Path, entries: list[tuple[str, str | None, str]], used: set[str], pages: dict) -> list[dict]:
    """Build `s-*.html` system/market-topology view entries declared via `View:` in root CONTEXT.md."""
    summary = []
    for rel, explicit_title, state_token in entries:
        stem = rel.rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()
        slug = re.sub(r"[^a-z0-9]+", "-", stem).strip("-") or "view"
        page = page_name("s", slug, used)
        target = workspace / rel
        if rel.startswith("/") or ".." in Path(rel).parts or "\\" in rel:
            model = refused("system-view", {"view": rel, "title": explicit_title or stem},
                            [{"code": "view.unreadable", "path": rel, "message": "View path must be relative inside the workspace"}])
            pages[page] = model
            summary.append({"page": page, "file": rel, "title": explicit_title or stem, "source_kind": None, "issues": model["issues"]})
            continue
        if target.is_symlink() or _has_symlink_component(target, workspace) or not target.is_file():
            model = refused("system-view", {"view": rel, "title": explicit_title or stem},
                            [{"code": "view.unreadable", "path": rel, "message": f"View file {rel} is missing, not a regular file, or crosses a symlink"}])
            pages[page] = model
            summary.append({"page": page, "file": rel, "title": explicit_title or stem, "source_kind": None, "issues": model["issues"]})
            continue
        ext = target.suffix.lower()
        if ext == ".html":
            raw = target.read_bytes()
            sha = hashlib.sha256(raw).hexdigest()
            title = explicit_title
            if not title:
                m = re.search(r"<title>(.*?)</title>", raw.decode("utf-8", errors="replace"), re.I | re.S)
                title = re.sub(r"\s+", " ", m.group(1)).strip() if m else stem
            pages[page] = {
                "format": FORMAT, "kind": "system-view",
                "selection": {"view": rel, "title": title, "source_kind": "html", "sha256": sha},
                "issues": [],
            }
            summary.append({"page": page, "file": rel, "title": title, "source_kind": "html", "issues": []})
        elif ext == ".md":
            try:
                content = read_file(target, rel)
            except (Unreadable, OSError, ValueError, yaml.YAMLError) as error:
                model = unreadable("system-view", {"view": rel, "title": explicit_title or stem}, rel, error)
                pages[page] = model
                summary.append({"page": page, "file": rel, "title": explicit_title or stem, "source_kind": "markdown", "issues": model["issues"]})
                continue
            title = explicit_title or content.get("title") or stem
            node = {"id": rel, "kind": "system-view", "parent": None, "children": [], **content}
            pages[page] = {
                "format": FORMAT, "kind": "system-view",
                "selection": {"view": rel, "title": title, "source_kind": "markdown", "sha256": content["sha256"]},
                "issues": [], "nodes": [node],
            }
            summary.append({"page": page, "file": rel, "title": title, "source_kind": "markdown", "issues": []})
        else:
            model = refused("system-view", {"view": rel, "title": explicit_title or stem},
                            [{"code": "view.unreadable", "path": rel, "message": f"View file {rel} must end in .html or .md"}])
            pages[page] = model
            summary.append({"page": page, "file": rel, "title": explicit_title or stem, "source_kind": None, "issues": model["issues"]})
    return summary


def capture(folder: Path) -> dict | Exception:
    """Every entry of a Vorgang folder with its content hash or link target; the Vorgang's evidence included."""
    def fail(error: OSError):
        raise error  # an unreadable subfolder must not vanish from the state

    state = {}
    try:
        for top, dirs, files in os.walk(folder, onerror=fail):
            for name in dirs + files:
                path = Path(top, name)
                state[path.relative_to(folder).as_posix()] = entry_state(path)
    except OSError as error:
        return error
    return state


def entry_state(path: Path) -> str:
    """A link by target, a folder by kind, a regular file by streamed hash; a FIFO or other
    special file by kind only, never read, since reading it could block."""
    mode = os.lstat(path).st_mode
    if stat.S_ISLNK(mode):
        return "link:" + os.readlink(path)
    if stat.S_ISDIR(mode):
        return "dir"
    if not stat.S_ISREG(mode):
        return f"special:{stat.S_IFMT(mode):o}"
    handle = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(handle, "rb") as stream:
        if not stat.S_ISREG(os.fstat(handle).st_mode):  # swapped since lstat
            return "special:changed"
        return hashlib.file_digest(stream, "sha256").hexdigest()


def single_vorgang(path: Path) -> dict:
    path = path.resolve()
    workspace = workspace_of(path.parent)
    if workspace is None or path.parent.parent != workspace / "vorgaenge":
        raise SystemExit("a Vorgang must be <git workspace>/vorgaenge/<slug>/CONTEXT.md; Core validates no other place")
    before = capture(path.parent)
    return vorgang_page(path, workspace, validate(workspace), before, {})


def page_name(prefix: str, slug: str, used: set[str]) -> str:
    readable = SLUG.fullmatch(slug) and len(slug) <= 200  # stay well below the usual 255-byte file name limit
    name = f"{prefix}-{slug}.html" if readable else f"{prefix}-{hashlib.sha256(slug.encode()).hexdigest()[:12]}.html"
    if name in used:
        raise SystemExit(f"two selections would share the page {name}")
    used.add(name)
    return name


def kind_of_entry(path: Path) -> str:
    mode = os.lstat(path).st_mode
    return "link" if stat.S_ISLNK(mode) else "dir" if stat.S_ISDIR(mode) else "file" if stat.S_ISREG(mode) else "special"


def _is_candidate_hauptprozess(folder: Path) -> bool:
    context = folder / "CONTEXT.md"
    try:
        if not context.is_file() or context.is_symlink():
            return False
        return load_frontmatter(context).get("type") == "hauptprozess"
    except (OSError, ValueError, yaml.YAMLError):
        return False


def _is_bridge_content(path: Path, content: dict) -> bool:
    meta = content.get("meta") if isinstance(content.get("meta"), dict) else {}
    if meta.get("type") == "bridge":
        return True
    if meta.get("type") is not None:
        return False
    name = path.name.lower()
    title = (content.get("title") or "").strip()
    return name == "bridge.md" or name.endswith("-bridge.md") or title.startswith(BRIDGE_PREFIXES)


def _is_renderable_analysis(path: Path, rel: str) -> bool:
    try:
        content = read_file(path, rel)
    except (Unreadable, OSError, ValueError, yaml.YAMLError):
        return False
    meta = content.get("meta") if isinstance(content.get("meta"), dict) else {}
    return meta.get("type") == "ist-prozess" or _is_bridge_content(path, content)


def _nested_analysis_files(base: Path, folder: Path) -> list[tuple[str, str, str]]:
    """Collect nested `ist-prozess` or `bridge` Markdown files under one `analyse/` subfolder without following symlinks."""
    if _is_candidate_hauptprozess(folder):
        return []
    found: list[tuple[str, str, str]] = []
    for directory, subdirs, files in os.walk(folder, followlinks=False):
        subdirs[:] = sorted(name for name in subdirs
                            if not name.startswith((".", "_"))
                            and not Path(directory, name).is_symlink()
                            and not _is_candidate_hauptprozess(Path(directory, name)))
        for name in sorted(files):
            if name.startswith(".") or not name.endswith(".md") or name == "CONTEXT.md":
                continue
            path = Path(directory, name)
            if path.is_symlink() or not path.is_file():
                continue
            rel_in_ist = path.relative_to(base).as_posix()
            if _is_renderable_analysis(path, f"{IST}/{rel_in_ist}"):
                found.append((rel_in_ist, "file", entry_state(path)))
    return found


def inventory(workspace: Path) -> dict[str, list[tuple[str, str]] | None]:
    """Every entry under hauptprozesse/ and vorgaenge/, with what it is; nothing is skipped.
    Under analyse/ also each regular file's hash (including nested Ist-Prozess/Bridge captures
    inside case folders, excluding candidate Hauptprozess trees), since the view reads those
    files from the working tree (None: the folder does not exist)."""
    found = {}
    for folder in WORKSPACE_FOLDERS:
        base = workspace / folder
        entries = sorted(base.iterdir()) if base.is_dir() and not base.is_symlink() else []
        found[folder] = [(p.name, "link" if p.is_symlink() else "dir" if p.is_dir() else "file") for p in entries]
    # Refuse a linked analysis root before enumerating or reading any source files.
    base, found[IST] = workspace / IST, None
    if not base.is_symlink() and not base.exists():
        return found
    if base.is_symlink() or not base.is_dir():
        found[IST] = [(".", kind_of_entry(base), IST)]
        return found
    items: list[tuple[str, str, str]] = []
    for p in sorted(base.iterdir()):
        kind = kind_of_entry(p)
        if kind == "dir" and not p.name.startswith((".", "_")):
            nested = _nested_analysis_files(base, p)
            if nested:
                items.extend(nested)
                continue
        items.append((p.name, kind, entry_state(p) if kind == "file" else ""))
    found[IST] = items
    return found


SKIPPED = {"link", "dir", "special"}


def ist_page(path: Path, rel: str) -> dict:
    """The page model of one Ist-Prozess or Bridge file, or why the file is not one."""
    selection = {"ist_prozess": rel, "revision": "working-tree"}
    try:
        content = read_file(path, rel)
    except (Unreadable, OSError, ValueError, yaml.YAMLError) as error:
        return unreadable("ist-prozess", selection, rel, error)
    kind = content["meta"].get("type") if isinstance(content["meta"], dict) else None
    is_bridge = _is_bridge_content(path, content)
    if kind != "ist-prozess" and not is_bridge:
        return {"reason": "wrong-type", "type": kind} if kind is not None else {"reason": "missing-type"}
    node = {"id": rel, "kind": "ist-prozess", "parent": None, "children": [], **content}
    model = {"format": FORMAT, "kind": "ist-prozess", "selection": selection, "issues": [],
             "nodes": [node], "necessity": project.necessity(node)}
    if is_bridge:
        model["bridge"] = True
    return model


def ist_pages(workspace: Path, listing: list[tuple[str, str, str]], used: set[str], pages: dict) -> list[dict]:
    """Each Ist-Prozess or Bridge file becomes its own page; every other entry is listed with its reason."""
    skipped = []
    for name, kind, third in listing:
        rel = third if name == "." else f"{IST}/{name}"
        reason = kind if kind in SKIPPED else (None if name.endswith(".md") else "not-markdown")
        model = {"reason": reason} if reason else ist_page(workspace / rel, rel)
        if "reason" in model:
            skipped.append({"file": rel, **model})
        else:
            slug = name.removesuffix(".md").replace("/", "-")
            pages[page_name("i", slug, used)] = model
    return skipped


def entry_issues(report, rel: str, kind: str) -> list[dict]:
    issues = issue_list([i for i in report.issues if i.path == rel or i.path.startswith(rel + "/")])
    message = {"link": "is a symlink", "file": "is a file, not a folder"}[kind]
    return issues or [{"code": "structure.level", "path": rel, "message": message}]


def workspace_site(workspace: Path, only: set[str] | None = None) -> dict[str, dict]:
    """Every Hauptprozess and every Vorgang as its own page, plus an overview as index.html.
    With `only`, just the pages of those vorgaenge/ entries, each equal to its page in the full site."""
    workspace = workspace.resolve()
    if workspace_of(workspace) != workspace:
        raise SystemExit(f"{workspace} must be the root of a Git repository; Core resolves bound Vorgänge there")
    algorithm = git(workspace, "rev-parse", "--show-object-format") or "sha1"
    state = lambda: (inventory(workspace), git(workspace, "rev-parse", "--verify", "-q", "HEAD"),
                     record_inventory(workspace) if only is None else [],
                     view_inventory(workspace) if only is None else [])
    first = state()
    if only is not None and (unknown := sorted(only - {name for name, _ in first[0]["vorgaenge"]})):
        raise SystemExit(f"no entry in vorgaenge/ is named {', '.join(unknown)}")
    chosen = lambda name: only is None or name in only
    vorgaenge = {name: capture(workspace / "vorgaenge" / name) for name, kind in first[0]["vorgaenge"]
                 if kind == "dir" and chosen(name)}
    report = validate(workspace)
    used, pages, cache, heads = {"index.html"}, {}, {}, {}
    for name, kind in first[0]["hauptprozesse"] if only is None else []:
        rel = f"hauptprozesse/{name}"
        page = page_name("a", name, used)
        pages[page] = hauptprozess_page(workspace / rel, algorithm) if kind == "dir" else \
            refused("hauptprozess", {"hauptprozess": name, "folder": name, "revision": None, "vorgang": None, "tree": None},
                    entry_issues(report, rel, kind))
        # Notes come from the workspace report, so only the workspace site carries them,
        # on a shown and on a refused page alike.
        if kind == "dir" and (notes := hauptprozess_notes(report, rel)):
            pages[page]["notes"] = notes
        heads[name] = git(workspace, "rev-parse", f"{first[1]}:{rel}") if first[1] else None
    for name, kind in first[0]["vorgaenge"]:
        rel = f"vorgaenge/{name}"
        page = page_name("v", name, used)  # named for every entry, so a selected page keeps its full-site name
        if not chosen(name):
            continue
        pages[page] = vorgang_page(workspace / rel / "CONTEXT.md", workspace, report, vorgaenge[name], cache) if kind == "dir" else \
            refused("vorgang", {"hauptprozess": None, "revision": None, "vorgang": rel}, entry_issues(report, rel, kind))
    skipped = None if first[0][IST] is None or only is not None else ist_pages(workspace, first[0][IST], used, pages)
    system_views = [] if only is not None else system_view_pages(workspace, first[3], used, pages)
    if state() != first:
        raise SystemExit("the workspace inventory, an Ist-Prozess file, a record or HEAD changed while the view was generated; "
                         "nothing was written")
    if only is None:
        known = {f"{folder}/{name}" for folder in WORKSPACE_FOLDERS for name, _ in first[0][folder]}
        workspace_issues = [i for i in issue_list(report.issues)
                            if not i["path"].startswith(tuple(f + "/" for f in WORKSPACE_FOLDERS))
                            or "/".join(i["path"].split("/")[:2]) not in known]
        project.link_ist(pages)
        pages["index.html"] = project.overview(workspace.name, pages, heads, workspace_issues, bool(first[1]), skipped,
                                               SCHEMA_REGISTRY.schemas(), records=first[2], system_views=system_views)
    for name, model in pages.items():
        model["site"] = {"index": "index.html", "self": name}
    return pages
