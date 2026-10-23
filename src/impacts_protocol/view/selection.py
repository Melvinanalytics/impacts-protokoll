"""Fix one immutable selection and turn it into page models.

An Application is copied first, so Core and the view see the same bytes. A Vorgang is
drawn on the Git tree it binds. A workspace is the inventory of every entry under
applications/ and vorgaenge/, each its own selection, plus the Ist-Prozess files under
grundlagen/ist-prozesse/, read from the working files (Core does not check them); if the
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

from impacts_protocol.io import load_frontmatter
from impacts_protocol.validator import SCHEMA_REGISTRY, validate

# Private on purpose: a bound revision must be materialized exactly as the validator does.
from impacts_protocol.validator import _materialize_tree

from . import project
from .read import Unreadable, issue_list, read_application, read_file, read_vorgang

FORMAT = "impacts-view/3"
TREE = re.compile(r"git-tree:([0-9a-f]{40}|[0-9a-f]{64})")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
FOLDERS = ("applications", "vorgaenge")
IST = "grundlagen/ist-prozesse"  # source material, not a Core folder: kept out of FOLDERS and its issue filter


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
    """application, vorgang or workspace, from the selected path and its frontmatter type."""
    path = path.resolve()
    if path.is_file():
        if path.name == "CONTEXT.md" and path.parent.parent.name == "vorgaenge":
            return "vorgang"
        raise SystemExit(f"{path}: select an Application folder, a workspace folder or vorgaenge/<slug>/CONTEXT.md")
    try:
        kind = load_frontmatter(path / "CONTEXT.md").get("type")
    except (OSError, ValueError) as error:
        raise SystemExit(f"{path}: cannot read CONTEXT.md: {error}")
    if kind in ("workspace", "hauptprozess"):
        return "workspace" if kind == "workspace" else "application"
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
            mode = "100755" if os.stat(child).st_mode & 0o111 else "100644"
            entries.append((child.name, mode, child.name, blob))
    body = b"".join(f"{mode} {name}".encode() + b"\0" + oid for _, mode, name, oid in sorted(entries))
    return hashlib.new(algorithm, b"tree %d\0" % len(body) + body).hexdigest()


@contextmanager
def application_copy(root: Path):
    """Copy only what Core allows in an Application: folders, CONTEXT.md and symlinks (which Core
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


def application_page(root: Path, algorithm: str | None = None) -> dict:
    """`algorithm` is the workspace's Git object format; given, the page records the tree id of
    the bytes it actually read."""
    selection = {"application": root.name, "folder": root.name, "revision": None, "vorgang": None, "tree": None}
    try:
        with application_copy(root.resolve()) as (copy, unknown):
            if unknown:
                return refused("application", selection, [{"code": "structure.invalid", "path": p,
                                                           "message": "Unknown Application entry"} for p in unknown])
            issues, nodes = read_application(copy, root.name, check_slug=True)
            if algorithm and not issues:
                selection["tree"] = tree_oid(copy, algorithm)
    except (Unreadable, OSError, ValueError) as error:
        return unreadable("application", selection, root.name, error)
    if issues:
        return refused("application", selection, issues)
    project.annotate(nodes)
    selection.update(application=nodes[0]["id"], revision=digest(nodes))
    return {"format": FORMAT, "kind": "application", "selection": selection, "issues": [],
            "nodes": nodes, "vorgang": None, "view": None, "stand": project.stand(nodes, None, None),
            "map": project.map_tree(nodes, None, None)}


def vorgang_issues(report, vorgang_rel: str) -> list[dict]:
    """This Vorgang's issues plus every issue outside other Vorgänge and Applications: a broken
    workspace router or folder means Core may not have checked this Vorgang at all."""
    return issue_list([i for i in report.issues
                       if i.path == vorgang_rel or i.path.startswith(vorgang_rel + "/") or not i.path.startswith(tuple(f + "/" for f in FOLDERS))])


def bound_application(workspace: Path, revision: str, cache: dict) -> tuple[list[dict], list[dict]]:
    """A bound tree is immutable; read it once per generation."""
    if revision not in cache:
        with TemporaryDirectory(prefix="impacts-view-") as folder:
            if not _materialize_tree(workspace, TREE.fullmatch(revision).group(1), Path(folder)):
                raise Unreadable(f"cannot read {revision}")
            cache[revision] = read_application(Path(folder), revision, check_slug=False)
            project.annotate(cache[revision][1])
    return cache[revision]


def vorgang_page(path: Path, workspace: Path, report, before: dict | Exception, cache: dict) -> dict:
    """`report` is Core's validation of `workspace`; `before` is the Vorgang folder's state captured before it."""
    vorgang_rel = path.parent.relative_to(workspace).as_posix()
    selection = {"application": None, "revision": None, "vorgang": vorgang_rel}
    issues = vorgang_issues(report, vorgang_rel)
    if issues:
        return refused("vorgang", selection, issues)
    try:
        if isinstance(before, Exception):
            raise before
        vorgang = read_vorgang(path, f"{vorgang_rel}/CONTEXT.md")
        if before.get("CONTEXT.md") != vorgang["sha256"] or capture(path.parent) != before:
            raise Unreadable(f"{vorgang_rel} changed during generation; generate the view again")
        revision = TREE.fullmatch(str(vorgang["meta"]["application_revision"]))
        if revision is None:
            raise Unreadable("the validated Vorgang has no application_revision")
        issues, nodes = bound_application(workspace, revision.group(0), cache)
    except (Unreadable, OSError, ValueError) as error:
        return unreadable("vorgang", selection, vorgang_rel, error)
    if issues:
        return refused("vorgang", selection, issues)
    selection.update(application=nodes[0]["id"], revision=revision.group(0))
    project.annotate([vorgang])
    view = project.phases(nodes, vorgang["meta"]["laufpfad"])
    return {"format": FORMAT, "kind": "vorgang", "selection": selection, "issues": [], "nodes": nodes, "vorgang": vorgang,
            "view": view, "stand": project.stand(nodes, vorgang, view), "map": project.map_tree(nodes, vorgang, view)}


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


def inventory(workspace: Path) -> dict[str, list[tuple[str, str]] | None]:
    """Every entry under applications/ and vorgaenge/, with what it is; nothing is skipped.
    Under grundlagen/ist-prozesse/ also each regular file's hash, since the view reads those
    files from the working tree (None: the folder does not exist)."""
    found = {}
    for folder in FOLDERS:
        base = workspace / folder
        entries = sorted(base.iterdir()) if base.is_dir() and not base.is_symlink() else []
        found[folder] = [(p.name, "link" if p.is_symlink() else "dir" if p.is_dir() else "file") for p in entries]
    # Each part of the path is checked, so a linked grundlagen/ cannot lead the view outside the workspace.
    # A part that is a link or no folder stands as one entry "." whose third field is that part's path.
    base, found[IST] = workspace, None
    for rel in ("grundlagen", IST):
        base = workspace / rel
        if not base.is_symlink() and not base.exists():
            return found
        if base.is_symlink() or not base.is_dir():
            found[IST] = [(".", kind_of_entry(base), rel)]
            return found
    found[IST] = [(p.name, kind, entry_state(p) if kind == "file" else "")
                  for p in sorted(base.iterdir()) for kind in [kind_of_entry(p)]]
    return found


SKIPPED = {"link", "dir", "special"}


def ist_page(path: Path, rel: str) -> dict:
    """The page model of one Ist-Prozess file, or why the file is not one."""
    selection = {"ist_prozess": rel, "revision": "working-tree"}
    try:
        content = read_file(path, rel)
    except (Unreadable, OSError, ValueError, yaml.YAMLError) as error:
        return unreadable("ist-prozess", selection, rel, error)
    kind = content["meta"].get("type") if isinstance(content["meta"], dict) else None
    if kind != "ist-prozess":
        return {"reason": "wrong-type", "type": kind} if kind is not None else {"reason": "missing-type"}
    node = {"id": rel, "kind": "ist-prozess", "parent": None, "children": [], **content}
    return {"format": FORMAT, "kind": "ist-prozess", "selection": selection, "issues": [],
            "nodes": [node], "necessity": project.necessity(node)}


def ist_pages(workspace: Path, listing: list[tuple[str, str, str]], used: set[str], pages: dict) -> list[dict]:
    """Each Ist-Prozess file becomes its own page; every other entry is listed with its reason."""
    skipped = []
    for name, kind, third in listing:
        rel = third if name == "." else f"{IST}/{name}"
        reason = kind if kind in SKIPPED else (None if name.endswith(".md") else "not-markdown")
        model = {"reason": reason} if reason else ist_page(workspace / rel, rel)
        if "reason" in model:
            skipped.append({"file": rel, **model})
        else:
            pages[page_name("i", name.removesuffix(".md"), used)] = model
    return skipped


def entry_issues(report, rel: str, kind: str) -> list[dict]:
    issues = issue_list([i for i in report.issues if i.path == rel or i.path.startswith(rel + "/")])
    message = {"link": "is a symlink", "file": "is a file, not a folder"}[kind]
    return issues or [{"code": "structure.invalid", "path": rel, "message": message}]


def workspace_site(workspace: Path) -> dict[str, dict]:
    """Every Application and every Vorgang as its own page, plus an overview as index.html."""
    workspace = workspace.resolve()
    if workspace_of(workspace) != workspace:
        raise SystemExit(f"{workspace} must be the root of a Git repository; Core resolves bound Vorgänge there")
    algorithm = git(workspace, "rev-parse", "--show-object-format") or "sha1"
    state = lambda: (inventory(workspace), git(workspace, "rev-parse", "--verify", "-q", "HEAD"))
    first = state()
    vorgaenge = {name: capture(workspace / "vorgaenge" / name) for name, kind in first[0]["vorgaenge"] if kind == "dir"}
    report = validate(workspace)
    used, pages, cache, heads = {"index.html"}, {}, {}, {}
    for name, kind in first[0]["applications"]:
        rel = f"applications/{name}"
        page = page_name("a", name, used)
        pages[page] = application_page(workspace / rel, algorithm) if kind == "dir" else \
            refused("application", {"application": name, "folder": name, "revision": None, "vorgang": None, "tree": None},
                    entry_issues(report, rel, kind))
        heads[name] = git(workspace, "rev-parse", f"{first[1]}:{rel}") if first[1] else None
    for name, kind in first[0]["vorgaenge"]:
        rel = f"vorgaenge/{name}"
        page = page_name("v", name, used)
        pages[page] = vorgang_page(workspace / rel / "CONTEXT.md", workspace, report, vorgaenge[name], cache) if kind == "dir" else \
            refused("vorgang", {"application": None, "revision": None, "vorgang": rel}, entry_issues(report, rel, kind))
    skipped = None if first[0][IST] is None else ist_pages(workspace, first[0][IST], used, pages)
    if state() != first:
        raise SystemExit("the workspace inventory, an Ist-Prozess file or HEAD changed while the view was generated; "
                         "nothing was written")
    known = {f"{folder}/{name}" for folder in FOLDERS for name, _ in first[0][folder]}
    workspace_issues = [i for i in issue_list(report.issues)
                        if not i["path"].startswith(tuple(f + "/" for f in FOLDERS))
                        or "/".join(i["path"].split("/")[:2]) not in known]
    project.link_ist(pages)
    pages["index.html"] = project.overview(workspace.name, pages, heads, workspace_issues, bool(first[1]), skipped,
                                           SCHEMA_REGISTRY.schemas())
    for name, model in pages.items():
        model["site"] = {"index": "index.html", "self": name}
    return pages
