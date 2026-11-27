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

from .generator import WORKSPACE_FOLDERS
from .io import load_frontmatter_and_body
from .model import Issue

LEVEL_FORMS = ("Record Library", "Knowledge Bundle", "Context Map")
CODE_FORMS = ("Capability", "Tool", "Check")
IMPLICIT = {"hauptprozesse", "vorgaenge", "__pycache__"}
ROOT_STANDARD_DOCS = frozenset({"agents.md", "claude.md", "gemini.md", "context.md", "readme.md", "contributing.md", "changelog.md", "license.md"})
DATED = re.compile(r"\d{4}-\d{2}-\d{2}")
SCHEME = re.compile(r"[a-z][a-z0-9+.-]*:", re.IGNORECASE)
ROUTER = "CONTEXT.md"
# Navigation and router-shape findings concern routes between files and the shape of a
# router; Core still reads and checks every Vorgang and Hauptprozess, so they never refuse
# a page. Structure findings may mean a level or definition was not read where it belongs.
NAVIGATION = frozenset({"topology.link_missing", "topology.link_broken", "topology.link_unindexed",
                        "topology.router_sections", "topology.router_size", "topology.table_contract"})
SECTIONS = (("Overview", "Übersicht"), ("What to load", "Was laden"))
ROUTER_BYTES = 24_000  # three quarters of the 8,000-token Knowledge Walk budget at about 4 bytes per token
HEADING = re.compile(r" {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
CONTRACT = re.compile(r"<!--[ \t]*impacts:table-contract\b(.*?)-->", re.DOTALL)
CONTRACT_FIELD = re.compile(r'\s+(heading|columns)="([^"\n]+)"')


def body_lines(body: str) -> Iterable[str]:
    """Yield visible Markdown outside comments and code, preserving indentation."""
    return _visible(body, mask_code=True).split("\n")


def _visible(body: str, *, mask_code: bool) -> str:
    """Text outside fences and comments; inline code is masked with spaces or kept as written.
    Masking keeps column-zero rules; a comment keeps only its line breaks."""
    parts = []
    for kind, text in _segments(body):
        if kind == "text" or kind == "code" and not mask_code:
            parts.append(text)
        elif kind == "code":
            parts.append(re.sub(r"[^\n]", " ", text))
        elif kind == "comment":
            parts.append("\n" * text.count("\n"))
    return "".join(parts)


FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")
SPECIAL = re.compile(r"`+|<!--|\n")
# A code span stays in its paragraph: a blank line, a fence or a heading line ends it.
PARAGRAPH_END = re.compile(r"\n(?=[ \t]*(?:\n|\Z)| {0,3}(?:`{3,}|~{3,}|#{1,6}(?:[ \t]|\n|\Z)))")


def _segments(body: str) -> list[tuple[str, str]]:
    """Split Markdown in one document-order pass into text, inline code, comment and fence
    segments. Whatever opens first wins: a `<!--` inside a fence or a code span (also one that
    crosses lines) opens no comment, and a fence inside a comment opens no fence. A code span
    closes within its paragraph or not at all."""
    body = re.sub(r"\r\n?", "\n", body)
    segments: list[tuple[str, str]] = []
    index, size = 0, len(body)
    while index < size:
        if index == 0 or body[index - 1] == "\n":
            line_end = body.find("\n", index)
            line_end = size if line_end < 0 else line_end + 1
            opener = FENCE.match(body, index, line_end)
            if opener:
                fence, close = opener[1], line_end
                while close < size:
                    end = body.find("\n", close)
                    end = size if end < 0 else end + 1
                    marker = FENCE.match(body, close, end)
                    close = end
                    if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                        break
                segments.append(("fence", body[index:close]))
                index = close
                continue
        special = SPECIAL.search(body, index)
        if special is None:
            segments.append(("text", body[index:]))
            break
        if special.start() > index:
            segments.append(("text", body[index:special.start()]))
        token = special[0]
        if token == "\n":
            segments.append(("text", "\n"))
            index = special.end()
        elif token == "<!--":
            end = body.find("-->", special.end())
            end = size if end < 0 else end + 3
            segments.append(("comment", body[special.start():end]))
            index = end
        else:
            end = PARAGRAPH_END.search(body, special.end())
            close = re.compile(r"(?<!`)" + token + r"(?!`)").search(body, special.end(), end.start() if end else size)
            if close is None:
                segments.append(("text", token))
                index = special.end()
            else:
                segments.append(("code", body[special.start():close.end()]))
                index = close.end()
    return segments


@dataclass
class Topology:
    root: Path
    human_pattern: str
    issues: list[Issue] = field(default_factory=list)
    forms: dict[Path, str] = field(default_factory=dict)
    held: list[dict] = field(default_factory=list)
    has_file: dict[Path, bool] = field(default_factory=dict)
    attempted: set[Path] = field(default_factory=set)
    listings: dict[Path, tuple[dict[str, Path], dict[str, Path]]] = field(default_factory=dict)
    anchors: dict[Path, set[str]] = field(default_factory=dict)
    ignored: set[str] = field(default_factory=set)
    # Folder links wait for the walk to end, so every declared level is known when judged.
    folder_links: list[tuple[Path, Path, Path, str]] = field(default_factory=list)
    protocol_source: Path | None = None
    protocol_listings: dict[Path, tuple[dict[str, Path], dict[str, Path]]] = field(default_factory=dict)

    def skip(self, path: Path) -> bool:
        if not path.is_relative_to(self.root):
            return False
        # Git lists names precomposed (NFC) on macOS; the disk may hold them decomposed.
        name = _nfc(path.relative_to(self.root).as_posix())
        return name in self.ignored or any(parent.as_posix() + "/" in self.ignored for parent in Path(name).parents if str(parent) != ".") or name + "/" in self.ignored

    def add(self, code: str, path: Path, message: str) -> None:
        self.issues.append(Issue(code, _safe(path.relative_to(self.root).as_posix() or "."), _safe(message)))

    def name(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def opaque(self, path: Path) -> bool:
        return self.forms.get(path) in CODE_FORMS + ("none",)


def blocks_vorgaenge(issue: Issue) -> bool:
    """A finding outside the two Core folders that is not navigation: Core may not have
    checked any Vorgang, so no Vorgang page is shown and no superseded relation is exported."""
    return not issue.path.startswith(tuple(folder + "/" for folder in WORKSPACE_FOLDERS)) and issue.code not in NAVIGATION


def check_topology(root: Path, human_pattern: str, *, protocol_source: Path | None = None) -> tuple[list[Issue], tuple[dict, ...], dict[str, str]]:
    """Return topology issues, held rows and the top-level forms by folder name, which
    stays the same however the caller spells the root."""
    # One spelling of the root, so `zz/../ws` and `ws` compare paths alike.
    root = Path(os.path.abspath(root))
    state = Topology(root, human_pattern, protocol_source=Path(os.path.abspath(protocol_source)) if protocol_source is not None else None)
    try:
        result = subprocess.run(["git", "-C", str(root), "ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z"], capture_output=True, check=True)
        state.ignored = {_nfc(name) for name in result.stdout.decode("utf-8", errors="surrogateescape").rstrip("\0").split("\0")}
    except (OSError, subprocess.CalledProcessError):
        pass
    body, children = _read_level(state, root)
    _check_links(state, root, body, may_leave=True, unindexed=True)
    _check_router_file(state, root / ROUTER)
    root_targets = _resolved_targets(state, root, body)
    for entry in _entries(state, root):
        try:
            if entry.is_dir() and entry.name not in IMPLICIT and entry not in state.attempted:
                state.add("topology.form_missing", entry, f"{entry.name}/ has no Form line; add `Form: {entry.name}/ <form> per <unit>` as a plain unindented line in the root CONTEXT.md; if it has no form, move its content to the case, record or Vorgang it serves or leave it to Git history; only a person may hold it")
            elif entry.is_file() and not entry.is_symlink() and entry.suffix.lower() == ".md" and entry.name.lower() not in ROOT_STANDARD_DOCS:
                if _nfc(str(entry.resolve())) not in root_targets:
                    state.add("topology.link_missing", entry, f"{entry.name} sits unlinked at the workspace root; move it into its declared form (records/, grundlagen/, analyse/) or link it from {ROUTER}")
        except (OSError, ValueError) as error:
            _unreadable(state, entry, error)
    for child in sorted(children):
        if not state.opaque(child):
            _visit(state, child)
    _scan_definitions(state, root)
    _check_definitions(state, root / "hauptprozesse")
    for folder, form in sorted(state.forms.items()):
        if folder.parent == root and form in CODE_FORMS:
            _check_code_routers(state, folder)
    for folder, form in sorted(state.forms.items()):
        if folder.parent == root and form in LEVEL_FORMS + ("Pipeline",) and not state.skip(folder) and folder.is_dir() and not folder.is_symlink() and _has_file(state, folder):
            if not {_nfc(str(folder.resolve())), _nfc(str((folder / ROUTER).resolve()))} & root_targets:
                state.add("topology.link_missing", folder, f"{folder.name}/ is not linked from the root {ROUTER}; link the folder or its {ROUTER} from the route that serves its readers")
    for context, folder, located, target in state.folder_links:
        try:
            unindexed = _unindexed(state, folder, located)
        except (OSError, ValueError):
            continue  # An unreadable target is reported where the walk reads it.
        if unindexed:
            state.add("topology.link_unindexed", context, f"Link {target!r} points to {state.name(located)}/, a folder outside this router's own entries with neither {ROUTER} nor README.md; link a file inside it or an entry of this level, or give the folder a {ROUTER}")
    top = {path.name: form for path, form in state.forms.items() if path.parent == root}
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
                # A path Git ignores is absent, as in a clean clone.
                children = [child for child in current.iterdir() if state is None or not state.skip(child)]
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
            if child.parent == state.root and child.name in WORKSPACE_FOLDERS:
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
        if not state.skip(folder / ROUTER) and ((folder / ROUTER).is_symlink() or (folder / ROUTER).exists()) or _has_file(state, folder):
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
    if not state.skip(folder / ROUTER) and (folder / ROUTER).is_file():
        level = token in LEVEL_FORMS and not (folder / ROUTER).is_symlink()
        _check_links(state, folder, body, unindexed=level)
        if level:
            _check_sections(state, folder, body)
        # A Record Library router links every instance, so it grows with the library.
        _check_router_file(state, folder / ROUTER, advice=SIZE_ADVICE.get(token) if level else None)
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
            if entry.name == "README.md" and entry.is_file() and not entry.is_symlink():
                continue  # A level's README describes the level; it is no record entry.
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
    # Instance folders and sub-levels need a router; a file kind's router, once present, links each file.
    linked = sublevels or (folders if folders and len(files) <= len(folders) else files)
    if linked and (linked is not files or (folder / ROUTER).exists() and not state.skip(folder / ROUTER)):
        _linked_entries(state, folder, body, linked)


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
        if state.skip(context):
            state.add("topology.link_missing", folder, f"{level}{ROUTER} is ignored by Git, so a clean clone lacks it; stop ignoring it")
        elif not context.is_symlink() and not context.exists():
            state.add("topology.link_missing", folder, f"{level} has no {ROUTER}; add one that links every entry")
        return
    targets, spellings = set(), {}
    for link in _links(body):
        try:
            target = _link_target(link)
            if target and not SCHEME.match(target):
                located = _locate(folder, target, state)
                spellings.setdefault(_normal(os.path.abspath(folder / target)), target)
                if located is not None and _nfc(str(located)) == _nfc(os.path.normpath(folder / target)):
                    # The entry's own path: a link to a symlink's target does not link the symlink.
                    targets.add(_nfc(str(located)))
        except (OSError, ValueError, RuntimeError):
            continue
    for entry in entries:
        try:
            if knowledge and _dated(_normal(entry.name)):
                state.add("topology.shape", entry, f"{entry.name} is dated work; move it to its case, its Vorgang or Git history; a rule's validity date goes inside the file or after its name")
            elif entry in state.attempted and entry not in state.forms:
                continue
            elif knowledge and entry.is_dir() and entry not in state.forms:
                state.add("topology.shape", entry, f"{entry.name}/ is not a declared sub-level of {level}; if it holds foundations, declare it as a Knowledge Bundle with its own router; otherwise move it to its case or record")
            elif _nfc(str(entry)) not in targets and (not entry.is_dir() or _nfc(str(entry / ROUTER)) not in targets):
                if entry.is_symlink() and not entry.exists():
                    state.add("topology.shape", entry, f"{entry.name} is a broken symlink; remove it or restore its target")
                    continue
                alias = spellings.get(_normal(str(entry.absolute())))
                if alias is None and entry.is_dir():
                    alias = spellings.get(_normal(str((entry / ROUTER).absolute())))
                if alias is not None and state.forms.get(folder) == "Record Library":
                    continue  # _check_links reports the spelling of every Record Library link
                suffix = "; link the entry itself, not a file inside it" if entry.is_dir() else ""
                if alias is not None:
                    state.add("topology.link_broken", entry, f"{entry.name} is linked as {alias!r}; use the on-disk spelling{suffix}")
                else:
                    state.add("topology.link_missing", entry, f"{entry.name} is not linked from {level}{ROUTER}; link it{suffix}")
        except (OSError, ValueError) as error:
            _unreadable(state, entry, error)


def _pipeline(state: Topology, folder: Path, body: str, entries: list[Path]) -> None:
    level = state.name(folder) + "/"
    for entry in entries:
        try:
            if not entry.is_dir():
                state.add("topology.shape", entry, f"{entry.name} is loose in process home {level}; move it into its process folder or out of the process home")
            elif state.skip(entry / ROUTER) or not (entry / ROUTER).is_file():
                state.add("topology.shape", entry, f"Process folder {entry.name}/ has no {ROUTER}; add its router")
            else:
                _check_router_file(state, entry / ROUTER, advice=None)
        except (OSError, ValueError) as error:
            _unreadable(state, entry, error)


SHAPES: dict[str, Callable[[Topology, Path, str, list[Path]], None]] = {
    "Record Library": _record_library,
    "Knowledge Bundle": lambda state, folder, body, entries: _linked_entries(state, folder, body, entries, knowledge=True),
    "Pipeline": _pipeline,
    "Context Map": _linked_entries,
}


_LINK_ATOM = r"(?:\\[()]|[^\s()<>\\])"
_LINK_DEST = rf"(?:{_LINK_ATOM}|\((?:{_LINK_ATOM})*\))+"
_LINK_SCAN = re.compile(
    rf"\]\([ \t]*(<[^<>\n]*>|{_LINK_DEST})(?:[ \t]+(?:\"[^\"\n]*\"|'[^'\n]*'|\([^()\n]*\)))?[ \t]*\)"
    r"|\]\([ \t]*((?:[^<>\n()\[\]]|\([^<>\n()\[\]]*\))+)[ \t]*\)"
)


def _scan_links(body: str) -> tuple[list[str], list[str]]:
    """Return valid inline link destinations and unbracketed destinations containing spaces.
    Destination atoms cannot consume an opener; failed long runs stay linear."""
    visible = "\n".join(body_lines(body))
    valid: list[str] = []
    spaced: list[str] = []
    for match in _LINK_SCAN.finditer(visible):
        if match[1] is not None:
            valid.append(match[1])
        else:
            raw = match[2].strip()
            if raw and any(char in " \t" for char in raw):
                spaced.append(raw)
    return valid, spaced


def _links(body: str) -> list[str]:
    return _scan_links(body)[0]


def _split_link(link: str) -> tuple[str, str]:
    cleaned = re.sub(r"\\([()])", r"\1", link.strip("<>"))
    raw_target, _, raw_fragment = cleaned.partition("#")
    return unquote(raw_target, errors="strict"), unquote(raw_fragment, errors="strict")


def _link_target(link: str) -> str:
    return _split_link(link)[0]


def _resolved_targets(state: Topology, folder: Path, body: str) -> set[str]:
    targets: set[str] = set()
    for link in _links(body):
        try:
            target = _link_target(link)
            if target and not SCHEME.match(target) and not target.startswith("/"):
                # A misspelt link still reaches its target; _check_links reports the spelling once.
                located = _locate(folder, target, state)
                if located is not None:
                    targets.add(_nfc(str(located.resolve())))
        except (OSError, ValueError, RuntimeError):
            continue
    return targets


def _prose(text: str) -> str:
    return _visible(text, mask_code=False)


def _title(text: str) -> str:
    """A heading's text as sections, contracts and anchors compare it: link text kept,
    backticks dropped."""
    return _nfc(re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text).replace("`", "").strip())


def _heading(line: str) -> tuple[int, str] | None:
    """Level and title of an ATX heading line of visible text, or None."""
    match = HEADING.match(line)
    return (len(match[1]), _title(match[2])) if match else None


def _markdown_anchors(text: str) -> set[str]:
    prose = _prose(text)
    found = {_nfc(anchor) for anchor in re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)', prose)}
    counts: dict[str, int] = {}
    for heading in filter(None, map(_heading, prose.split("\n"))):
        slug = _nfc(re.sub(r"[^\w\- ]", "", heading[1].lower()).replace(" ", "-"))
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        found.add(slug + (f"-{count}" if count else ""))
    return found


def _file_anchors(state: Topology, path: Path) -> set[str]:
    resolved = path.resolve()
    if resolved not in state.anchors:
        state.anchors[resolved] = _markdown_anchors(path.read_text(encoding="utf-8-sig", errors="replace"))
    return state.anchors[resolved]


def _check_links(state: Topology, folder: Path, body: str, *, may_leave: bool = False, unindexed: bool = False) -> None:
    context = folder / ROUTER
    links, spaced = _scan_links(body)
    for raw in spaced:
        state.add("topology.link_broken", context, f"Link {raw!r} contains spaces without angle brackets; wrap the path in '<...>' or encode spaces as '%20'")
    for link in links:
        target = link
        try:
            target, fragment = _split_link(link)
            if not target:
                if fragment and context.is_file() and context.suffix.lower() == ".md":
                    if _nfc(fragment) not in _file_anchors(state, context):
                        state.add("topology.link_broken", context, f"Anchor '#{fragment}' does not resolve in {state.name(context)}; correct or remove it")
                continue
            if SCHEME.match(target):
                continue
            if target.startswith("/"):
                if not may_leave:
                    state.add("topology.link_broken", context, f"Link {target!r} is absolute; use a path relative to this CONTEXT.md")
                continue
            located = _locate(folder, target, state)
            resolved = (located or folder / target).resolve()
            inside = resolved.is_relative_to(state.root.resolve())
            if may_leave and not inside:
                continue
            if not inside:
                state.add("topology.link_broken", context, f"Link {target!r} leaves the workspace; name the source by release and revision instead")
            elif located is None:
                ignored = state.skip(Path(os.path.normpath(folder / target))) and (folder / target).exists()
                reason = "points to a path Git ignores, which a clean clone lacks; link a committed file or stop ignoring it" if ignored else "does not resolve; correct or remove it"
                state.add("topology.link_broken", context, f"Link {target!r} {reason}")
            else:
                if _locate(folder, target, state, aliases_ok=False) is None and not (
                        state.forms.get(folder) in {"Knowledge Bundle", "Context Map"}
                        and (located.parent == folder or located.parent.parent == folder and located.name == ROUTER)):
                    # A misspelt link to an entry of this level is reported once, on the entry.
                    state.add("topology.link_broken", context, f"Link {target!r} differs from the on-disk spelling {state.name(located)!r}; use the on-disk spelling")
                if fragment and located.is_file() and located.suffix.lower() == ".md":
                    if _nfc(fragment) not in _file_anchors(state, located):
                        state.add("topology.link_broken", context, f"Link '{target}#{fragment}' has unresolved anchor '#{fragment}' in {state.name(located)}; correct or remove it")
                if unindexed:
                    state.folder_links.append((context, folder, located, target))
        except (OSError, ValueError, RuntimeError):
            state.add("topology.link_broken", context, f"Link {target!r} does not resolve; correct or remove it")


def _check_sections(state: Topology, folder: Path, body: str) -> None:
    titles = {heading[1].casefold() for heading in map(_heading, _prose(body).split("\n")) if heading}
    missing = [english for english, german in SECTIONS if english.casefold() not in titles and german.casefold() not in titles]
    if missing:
        names = " and ".join(f"'{name}'" for name in missing)
        noun, pronoun = ("sections", "them") if len(missing) > 1 else ("section", "it")
        state.add("topology.router_sections", folder / ROUTER, f"{state.name(folder / ROUTER)} lacks the {noun} {names}; add {pronoun} as `impacts template ebene` lays them out (German: 'Übersicht', 'Was laden')")


SPLIT = "move detail into linked sibling files and keep the router to routes"
ARBEITSSCHRITT_SPLIT = "move detail into linked sibling files or referenced foundations and keep the Arbeitsschritt body within the Knowledge Walk budget"
# A router that must link every entry cannot shed links, so the advice depends on the form.
# Record Library and Context Map routers have no size advice: they are not measured, since
# a Context Map cannot have sub-levels and a Record Library kind splits by period instead.
SIZE_ADVICE = {"Knowledge Bundle": "split it into declared Knowledge Bundle sub-levels, each with its own router that links its entries"}
PROTOCOL_CITATION = re.compile(r"02_protocol/([^#:\s<>`]+?)(?::\d+(?:-\d+)?)?(?:#([^\s<>`]+))?\Z")


def _locate_protocol(state: Topology, relative: str) -> tuple[Path | None, str | None]:
    """Resolve `02_protocol/...` strictly inside `protocol_source` without symlinks or `..`."""
    assert state.protocol_source is not None
    parts = [part for part in relative.split("/") if part not in {"", "."}]
    if not parts or any(part == ".." for part in parts):
        return None, "escapes the protocol source"
    current = state.protocol_source
    for part in parts:
        try:
            if current not in state.protocol_listings:
                children = list(current.iterdir())
                state.protocol_listings[current] = (
                    {_nfc(child.name): child for child in children},
                    {_normal(child.name): child for child in children},
                )
            exact, aliases = state.protocol_listings[current]
            candidate = exact.get(_nfc(part))
            if candidate is None:
                alias = aliases.get(_normal(part))
                if alias is not None:
                    return None, f"differs from on-disk spelling {alias.relative_to(state.protocol_source).as_posix()!r}"
                return None, "does not resolve in the protocol source"
            if candidate.is_symlink():
                return None, "crosses a symlink in the protocol source"
            current = candidate
        except (OSError, ValueError):
            return None, "cannot be read in the protocol source"
    if not current.exists():
        return None, "does not resolve in the protocol source"
    return current, None


def _check_protocol_citations(state: Topology, context: Path, body: str) -> None:
    """When `--protocol-source` is supplied, verify `02_protocol/<path>#<anchor>` code spans."""
    if state.protocol_source is None:
        return
    for kind, text in _segments(body):
        if kind != "code":
            continue
        inner = text.strip("`").strip()
        match = PROTOCOL_CITATION.fullmatch(inner)
        if match is None:
            continue
        target_rel, fragment = "02_protocol/" + match[1], match[2] or ""
        try:
            decoded_target = unquote(target_rel, errors="strict")
            decoded_fragment = unquote(fragment, errors="strict") if fragment else ""
        except UnicodeDecodeError:
            state.add("topology.link_broken", context, f"Protocol citation {inner!r} has invalid percent-encoding")
            continue
        located, problem = _locate_protocol(state, decoded_target)
        if located is None:
            state.add("topology.link_broken", context, f"Protocol citation {inner!r} {problem}; update the path or pin")
            continue
        if decoded_target.endswith("/") and not located.is_dir():
            state.add("topology.link_broken", context, f"Protocol citation {inner!r} names a directory but resolves to a file")
            continue
        if decoded_fragment:
            if not located.is_file() or located.suffix.lower() != ".md":
                state.add("topology.link_broken", context, f"Protocol citation {inner!r} has anchor '#{decoded_fragment}' on a non-Markdown target")
            elif _nfc(decoded_fragment) not in _file_anchors(state, located):
                state.add("topology.link_broken", context, f"Protocol citation {inner!r} has unresolved anchor '#{decoded_fragment}' in {decoded_target}; update the anchor")


def check_protocol_citations_tree(root: Path, protocol_source: Path) -> list[Issue]:
    """Check `02_protocol/...` code-span citations in a standalone Hauptprozess tree."""
    state = Topology(Path(os.path.abspath(root)), "", protocol_source=Path(os.path.abspath(protocol_source)))
    for context in sorted(state.root.rglob(ROUTER)):
        if any(part.startswith(("_", ".")) for part in context.relative_to(state.root).parts):
            continue
        if context.is_symlink() or not context.is_file():
            continue
        try:
            _, body = load_frontmatter_and_body(context, state.root)
        except (OSError, ValueError, YAMLError, RecursionError):
            continue
        _check_protocol_citations(state, context, body)
    return state.issues


def _check_router_file(state: Topology, context: Path, *, advice: str | None = SPLIT) -> None:
    """Size, when `advice` says how to shrink it, table contracts and optional protocol citations."""
    try:
        if state.skip(context) or context.is_symlink() or not context.is_file():
            return
        size = context.stat().st_size
        if advice and size > ROUTER_BYTES:
            state.add("topology.router_size", context, f"{state.name(context)} has {size:,} bytes, above the {ROUTER_BYTES:,}-byte router budget; {advice}")
        _, body = load_frontmatter_and_body(context, state.root)
    except (OSError, ValueError, YAMLError, RecursionError):
        return  # Unreadable routers are reported where they are read.
    _check_table_contracts(state, context, body)
    _check_protocol_citations(state, context, body)


def _check_table_contracts(state: Topology, context: Path, body: str) -> None:
    """Contracts live in real comments: a marker inside code declares nothing."""
    lines = _visible(body, mask_code=False).split("\n")
    for kind, text in _segments(body):
        marker = CONTRACT.fullmatch(text) if kind == "comment" else None
        if marker is None:
            continue
        fields = dict(match.groups() for match in CONTRACT_FIELD.finditer(marker[1]))
        rest = CONTRACT_FIELD.sub("", marker[1]).strip()
        columns = [column.strip().replace("\\|", "|") for column in re.split(r"(?<!\\),", fields.get("columns", "")) if column.strip()]
        if rest or "heading" not in fields or not columns:
            state.add("topology.table_contract", context, 'table-contract marker is malformed; write <!-- impacts:table-contract heading="<Heading>" columns="<Col1>, <Col2>" -->')
            continue
        heading = _title(fields["heading"])
        headers = _table_headers(lines, heading)
        label = ", ".join(columns)
        if not headers:
            state.add("topology.table_contract", context, f"required machine-written table columns {label} under '{heading}' are missing; restore the heading, its table and the header columns expected by workspace tools")
            continue
        for number, header in enumerate(headers, 1):
            absent = [column for column in columns if _nfc(column) not in (header or set())]
            where = f"'{heading}'" + (f" (section {number} of {len(headers)})" if len(headers) > 1 else "")
            if absent:
                state.add("topology.table_contract", context, f"required machine-written table columns {', '.join(absent)} under {where} are missing; restore the header columns expected by workspace tools")


def _cells(line: str) -> list[str]:
    """Cells of a table row; one unescaped outer pipe per side is the row's border."""
    row = line.strip()
    row = row[1:] if row.startswith("|") else row
    row = row[:-1] if row.endswith("|") and not row.endswith("\\|") else row
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", row)]


def _table_headers(lines: list[str], heading: str) -> list[set[str] | None]:
    """For each section titled `heading`, in any letter case, the header cells of its first
    table, or None. A table needs a delimiter row with as many cells as its header row."""
    found: list[set[str] | None] = []
    level = None
    for index, line in enumerate(lines):
        match = _heading(line)
        if match and level is not None and match[0] <= level:
            level = None
        if match and match[1].casefold() == heading.casefold():
            level = match[0]
            found.append(None)
            continue
        if level is None or found[-1] is not None or "|" not in line or index + 1 >= len(lines):
            continue
        header, delimiter = _cells(line), _cells(lines[index + 1])
        if len(header) == len(delimiter) and all(re.fullmatch(r":?-+:?", cell) for cell in delimiter):
            found[-1] = {_nfc(cell.strip("`").strip().replace("\\|", "|")) for cell in header}
    return found


def _unindexed(state: Topology, folder: Path, located: Path) -> bool:
    """A linked folder, other than an entry of the router's own level, with no index file.
    Exempt: a declared level, whose own rules govern it (a file-per-entry kind needs no
    router); code homes and held folders, which have no form to enter; and the Core folders,
    whose layout Core owns. An index is a regular file named exactly CONTEXT.md or README.md."""
    if not located.is_dir() or located.resolve().parent == folder.resolve():
        return False
    target = Path(os.path.normpath(located))
    if target in state.forms or any(state.opaque(path) for path in (target, *target.parents)):
        return False
    if any(path.parent == state.root and path.name in WORKSPACE_FOLDERS for path in (target, *target.parents)):
        return False
    try:
        return not any(child.name in (ROUTER, "README.md") and not state.skip(child) and child.is_file() and not child.is_symlink() for child in located.iterdir())
    except OSError:
        return False


def _check_code_routers(state: Topology, home: Path) -> None:
    """A code home's router and each direct entry's router, such as capabilities/<slug>/CONTEXT.md."""
    _check_router_file(state, home / ROUTER)
    try:
        entries = sorted(home.iterdir())
    except (OSError, ValueError):
        return  # Code homes are opaque; their readability is not judged here.
    for entry in entries:
        try:
            if not entry.name.startswith(".") and not state.skip(entry) and entry.is_dir() and not entry.is_symlink():
                _check_router_file(state, entry / ROUTER)
        except (OSError, ValueError):
            continue


def _check_definitions(state: Topology, folder: Path) -> None:
    """Links in each Hauptprozess, Teilprozess and Arbeitsschritt body resolve inside the workspace.
    Core reports unreadable or unparseable definitions; this check stays silent on them."""
    try:
        if state.skip(folder) or folder.is_symlink() or not folder.is_dir():
            return
        children = sorted(folder.iterdir())
    except (OSError, ValueError):
        return
    context = folder / ROUTER
    if folder.parent != state.root and context.is_file() and not context.is_symlink():
        try:
            meta, body = load_frontmatter_and_body(context, state.root)
        except (OSError, ValueError, YAMLError, RecursionError):
            meta, body = None, None
        if body is not None:
            if isinstance(meta, dict) and meta.get("type") == "arbeitsschritt":
                try:
                    size = context.stat().st_size
                except OSError:
                    size = 0
                if size > ROUTER_BYTES:
                    state.add("topology.router_size", context, f"{state.name(context)} has {size:,} bytes, above the {ROUTER_BYTES:,}-byte router budget; {ARBEITSSCHRITT_SPLIT}")
            _check_links(state, folder, body)
            _check_table_contracts(state, context, body)
            _check_protocol_citations(state, context, body)
    for child in children:
        if not child.name.startswith(("_", ".")):
            _check_definitions(state, child)
