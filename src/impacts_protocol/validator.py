"""Read-only validation for the minimal file-native IMPACTS contract."""

from collections import deque
from contextlib import ExitStack
from dataclasses import dataclass, replace
from datetime import datetime
from importlib import resources
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
from typing import Any, Callable, Iterable

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .hashing import HashSurfaceError, surface_hash
from .io import _has_symlink_component, load_frontmatter_and_body
from .model import Issue, ValidationReport
from .workspace_contract import WORKSPACE_FOLDERS


SCHEMA_NAMES = (
    "leistung",
    "hauptprozess",
    "teilprozess",
    "arbeitsschritt",
    "vorgang",
)
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


@dataclass(frozen=True)
class Application:
    root: Path
    hauptprozess: dict[str, Any]
    arbeitsschritte: dict[str, tuple[Path, dict[str, Any]]]


class SchemaRegistry:
    """Load the five packaged protocol schemas as one reference registry."""

    def __init__(self, schema_dir: Path | None = None):
        self.schema_dir = schema_dir
        self._validators: dict[str, Draft202012Validator] = {}
        self._schemas: dict[str, dict[str, Any]] | None = None

    def errors(self, schema_name: str, document: dict[str, Any]):
        validator = self._validators.get(schema_name)
        if validator is None:
            schemas = self._load_schemas()
            registry = Registry().with_resources(
                (schema["$id"], Resource.from_contents(schema))
                for schema in schemas.values()
            )
            validator = Draft202012Validator(
                schemas[schema_name],
                registry=registry,
                format_checker=FormatChecker(),
            )
            self._validators[schema_name] = validator
        return sorted(
            validator.iter_errors(document),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )

    def _load_schemas(self) -> dict[str, dict[str, Any]]:
        if self._schemas is not None:
            return self._schemas
        self._schemas = {
            name: json.loads(self._schema_text(name)) for name in SCHEMA_NAMES
        }
        return self._schemas

    def _schema_text(self, schema_name: str) -> str:
        filename = f"{schema_name}.schema.json"
        if self.schema_dir is not None:
            return (self.schema_dir / filename).read_text(encoding="utf-8")
        try:
            return (
                resources.files("impacts_protocol.schemas")
                .joinpath(filename)
                .read_text(encoding="utf-8")
            )
        except ModuleNotFoundError:
            return (
                Path(__file__).resolve().parents[2]
                / "02_protocol"
                / "schemas"
                / filename
            ).read_text(encoding="utf-8")


SCHEMA_REGISTRY = SchemaRegistry()


def validate(root: Path) -> ValidationReport:
    """Validate a Workspace or Application without changing files."""
    root = Path(root)
    issues: list[Issue] = []
    if root.is_symlink():
        return ValidationReport(
            (Issue("structure.symlink", str(root), "Root directory is a symlink"),)
        )
    if not root.is_dir():
        return ValidationReport(
            (Issue("structure.invalid", str(root), "Root directory does not exist"),)
        )
    try:
        metadata = _load_context(root / "CONTEXT.md", root, issues)
        root_type = metadata.get("type") if metadata is not None else None
        if root_type == "workspace" and set(metadata) != {"type"}:
            _add(
                issues,
                "routing.type",
                root / "CONTEXT.md",
                root,
                "Root router frontmatter must contain only type",
            )
        if root_type == "workspace":
            _validate_workspace(root, issues)
        elif root_type == "hauptprozess":
            _validate_application(root, issues)
        elif metadata is not None:
            _add(issues, "routing.type", root / "CONTEXT.md", root, "Root type must be workspace or hauptprozess")
    except (OSError, RuntimeError) as error:
        _add(issues, "structure.invalid", root, root, f"Core tree cannot be read: {error}")
    return ValidationReport(_ordered(issues))


def _validate_workspace(root: Path, issues: list[Issue]) -> None:
    for folder in WORKSPACE_FOLDERS:
        path = root / folder
        if path.is_symlink():
            _add(issues, "structure.symlink", path, root, "Core folder is a symlink")
        elif path.exists() and not path.is_dir():
            _add(issues, "structure.invalid", path, root, "Workspace collection must be a directory")
    applications = root / "applications"
    if applications.is_dir() and not applications.is_symlink():
        for path in sorted(applications.iterdir(), key=lambda item: item.name):
            if path.is_symlink():
                _add(issues, "structure.symlink", path, root, "Application is a symlink")
            elif path.is_dir():
                before = len(issues)
                _validate_application(path, issues)
                prefix = path.relative_to(root)
                issues[before:] = [
                    replace(
                        issue,
                        path=(prefix if issue.path == "." else prefix / issue.path).as_posix(),
                    )
                    for issue in issues[before:]
                ]
            else:
                _add(issues, "structure.invalid", path, root, "Applications contains a non-directory")
    runs = root / "vorgaenge"
    # Definitions are immutable; run files and Git refs are rechecked on every call.
    definitions: dict[str, Application | str] = {}
    reachable = _ReachableApplications(workspace=root)
    with ExitStack() as snapshots:
        if runs.is_dir() and not runs.is_symlink():
            for path in sorted(runs.iterdir(), key=lambda item: item.name):
                if path.is_symlink():
                    _add(issues, "structure.symlink", path, root, "Vorgang is a symlink")
                elif path.is_dir():
                    _validate_vorgang(path, root, issues, definitions, snapshots, reachable)
                else:
                    _add(issues, "structure.invalid", path, root, "Vorgaenge contains a non-directory")


def _validate_application(
    root: Path, issues: list[Issue], *, check_slug: bool = True
) -> Application | None:
    before = len(issues)
    _reject_symlinks(root, root, issues)
    if check_slug and SLUG.fullmatch(root.name) is None:
        _add(issues, "structure.invalid", root, root, "Application folder needs a slug")
    process = _load_context(
        root / "CONTEXT.md",
        root,
        issues,
        kind="hauptprozess",
    )
    if process is None:
        return None
    if check_slug and process.get("id") != f"hauptprozess:{root.name}":
        _add(issues, "structure.invalid", root, root, "Hauptprozess ID must match folder slug")
    part_dirs = _slug_children(root, root, issues, "Teilprozess")
    if not part_dirs:
        _add(issues, "structure.invalid", root, root, "Hauptprozess needs at least one Teilprozess")

    steps: dict[str, tuple[Path, dict[str, Any]]] = {}
    for part_root in part_dirs:
        part = _load_context(
            part_root / "CONTEXT.md",
            root,
            issues,
            kind="teilprozess",
        )
        if part is not None and part.get("id") != f"teilprozess:{part_root.name}":
            _add(issues, "structure.invalid", part_root, root, "Teilprozess ID must match folder slug")
        step_dirs = _slug_children(part_root, root, issues, "Arbeitsschritt")
        if not step_dirs:
            _add(
                issues,
                "structure.invalid",
                part_root,
                root,
                "Teilprozess needs at least one Arbeitsschritt",
            )
        for step_root in step_dirs:
            if _slug_children(step_root, root, issues, "Arbeitsschritt"):
                _add(issues, "structure.invalid", step_root, root, "Arbeitsschritt must not contain subfolders")
            step = _load_context(
                step_root / "CONTEXT.md",
                root,
                issues,
                kind="arbeitsschritt",
                require_body=True,
            )
            if step is None or not isinstance(step.get("id"), str):
                continue
            step_id = step["id"]
            if step_id != f"arbeitsschritt:{step_root.name}":
                _add(issues, "structure.invalid", step_root, root, "Arbeitsschritt ID must match folder slug")
            if step_id in steps:
                _add(issues, "reference.duplicate", step_root, root, f"Duplicate Arbeitsschritt ID: {step_id}")
            else:
                steps[step_id] = (step_root, step)

    application = Application(root, process, steps)
    _validate_graph(application, issues)
    if len(issues) > before and not steps:
        return None
    return application


def _validate_graph(application: Application, issues: list[Issue]) -> None:
    root = application.root
    steps = application.arbeitsschritte
    entry = application.hauptprozess.get("einstieg_ref")
    if not isinstance(entry, str) or entry not in steps:
        _add(issues, "reference.unresolved", root / "CONTEXT.md", root, "Hauptprozess entry does not resolve")
        return

    adjacency: dict[str, set[str]] = {step_id: set() for step_id in steps}
    direct_end: set[str] = set()
    for step_id, (path, step) in steps.items():
        routes = step.get("routen")
        if not isinstance(routes, dict):
            continue
        if step.get("gate") == "human" and set(routes) != {"freigegeben", "abgelehnt"}:
            _add(issues, "process.gate", path / "CONTEXT.md", root, "Human gate needs freigegeben and abgelehnt routes")
        for target in routes.values():
            if not isinstance(target, str):
                continue
            if target.startswith("end:"):
                direct_end.add(step_id)
            elif target in steps:
                adjacency[step_id].add(target)
            else:
                _add(issues, "reference.unresolved", path / "CONTEXT.md", root, f"Route target does not resolve: {target}")

    reachable: set[str] = set()
    queue = deque([entry])
    while queue:
        step_id = queue.popleft()
        if step_id in reachable:
            continue
        reachable.add(step_id)
        queue.extend(adjacency.get(step_id, ()))
    for step_id in sorted(set(steps) - reachable):
        _add(issues, "process.unreachable", steps[step_id][0], root, f"Unreachable Arbeitsschritt: {step_id}")

    predecessors: dict[str, set[str]] = {step_id: set() for step_id in steps}
    for step_id, targets in adjacency.items():
        for target in targets:
            predecessors[target].add(step_id)
    can_end = set(direct_end)
    queue = deque(direct_end)
    while queue:
        for step_id in predecessors[queue.popleft()]:
            if step_id not in can_end:
                can_end.add(step_id)
                queue.append(step_id)
    for step_id in sorted(set(steps) - can_end):
        _add(issues, "process.no_end", steps[step_id][0], root, f"No reachable end from: {step_id}")


def _validate_vorgang(
    run_root: Path, workspace: Path, issues: list[Issue],
    definitions: dict[str, Application | str], snapshots: ExitStack,
    reachable: "_ReachableApplications",
) -> None:
    _reject_symlinks(run_root, workspace, issues)
    document = _load_context(
        run_root / "CONTEXT.md",
        workspace,
        issues,
        kind="vorgang",
    )
    if document is None:
        return
    if document.get("id") != f"vorgang:{run_root.name}":
        _add(issues, "structure.invalid", run_root, workspace, "Vorgang ID must match folder slug")
    application = _resolve_application(
        workspace, document.get("application_revision"), run_root, issues, definitions, snapshots, reachable
    )
    if application is None:
        return
    entries = document.get("laufpfad")
    if not isinstance(entries, list) or not entries:
        _add(issues, "run.invalid", run_root / "CONTEXT.md", workspace, "Laufpfad must be non-empty")
        return
    entry_ref = application.hauptprozess.get("einstieg_ref")
    if not isinstance(entries[0], dict) or entries[0].get("arbeitsschritt_ref") != entry_ref:
        _add(issues, "run.invalid", run_root / "CONTEXT.md", workspace, "Laufpfad must start at Application entry")

    seen_attempts: set[tuple[str, int]] = set()
    expected_attempts: set[tuple[str, int]] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            _add(issues, "run.invalid", run_root / "CONTEXT.md", workspace, "Laufpfad entry must be an object")
            continue
        step_id = entry.get("arbeitsschritt_ref")
        attempt_number = entry.get("versuch")
        if not isinstance(step_id, str) or step_id not in application.arbeitsschritte:
            _add(issues, "reference.unresolved", run_root / "CONTEXT.md", workspace, f"Unknown Laufpfad step: {step_id}")
            continue
        if not isinstance(attempt_number, int) or isinstance(attempt_number, bool) or attempt_number < 1:
            _add(issues, "run.invalid", run_root / "CONTEXT.md", workspace, "Versuch must be a positive integer")
            continue
        key = (step_id, attempt_number)
        if key in seen_attempts:
            _add(issues, "reference.duplicate", run_root / "CONTEXT.md", workspace, f"Duplicate attempt: {key}")
        seen_attempts.add(key)
        expected_attempts.add((step_id.removeprefix("arbeitsschritt:"), attempt_number))
        attempt_root = (
            run_root
            / step_id.removeprefix("arbeitsschritt:")
            / f"{attempt_number:03d}"
        )
        if not attempt_root.is_dir() or attempt_root.is_symlink():
            _add(issues, "run.invalid", attempt_root, workspace, "Attempt directory is missing or unsafe")
            continue

        step = application.arbeitsschritte[step_id][1]
        status = entry.get("status")
        is_last = index == len(entries) - 1
        if status == "aktiv":
            if not is_last or any(field in entry for field in ("gewaehlte_route", "ausgabe_hash", "wiedereinstieg", "freigabe")):
                _add(issues, "run.invalid", run_root / "CONTEXT.md", workspace, "Active entry has invalid position or fields")
        elif status == "wartend":
            reentry = entry.get("wiedereinstieg")
            if not is_last or not isinstance(reentry, dict) or any(field in entry for field in ("gewaehlte_route", "ausgabe_hash", "freigabe")):
                _add(issues, "run.invalid", run_root / "CONTEXT.md", workspace, "Waiting entry needs only its reentry contract")
        elif status == "abgeschlossen":
            _validate_completed_entry(
                entry,
                step,
                entries,
                index,
                run_root,
                workspace,
                issues,
            )
        else:
            _add(issues, "run.invalid", run_root / "CONTEXT.md", workspace, f"Unknown run status: {status}")

        input_hash = _surface_hash(attempt_root, step.get("eingaben"), workspace, issues)
        if input_hash is not None and entry.get("eingabe_hash") != input_hash:
            _add(issues, "hash.mismatch", attempt_root, workspace, "Input hash does not match attempt files")
        if status == "abgeschlossen":
            output_hash = _surface_hash(attempt_root, step.get("ausgaben"), workspace, issues)
            if output_hash is not None and entry.get("ausgabe_hash") != output_hash:
                _add(issues, "hash.mismatch", attempt_root, workspace, "Output hash does not match attempt files")

    actual_attempts = _attempt_directories(run_root, workspace, issues)
    for slug, number in sorted(actual_attempts ^ expected_attempts):
        _add(
            issues,
            "run.invalid",
            run_root / slug / f"{number:03d}",
            workspace,
            "Attempt directory and Laufpfad differ",
        )


def _validate_completed_entry(
    entry: dict[str, Any],
    step: dict[str, Any],
    entries: list[Any],
    index: int,
    run_root: Path,
    workspace: Path,
    issues: list[Issue],
) -> None:
    if "wiedereinstieg" in entry:
        _add(issues, "run.invalid", run_root / "CONTEXT.md", workspace, "Completed entry must not carry reentry")
    route = entry.get("gewaehlte_route")
    routes = step.get("routen")
    if (
        not isinstance(routes, dict)
        or not isinstance(route, str)
        or route not in routes
        or not isinstance(entry.get("ausgabe_hash"), str)
    ):
        _add(issues, "run.invalid", run_root / "CONTEXT.md", workspace, "Completed entry needs a declared route and output hash")
        target = None
    else:
        target = routes[route]
    is_last = index == len(entries) - 1
    if isinstance(target, str) and target.startswith("arbeitsschritt:"):
        next_ref = entries[index + 1].get("arbeitsschritt_ref") if not is_last and isinstance(entries[index + 1], dict) else None
        if next_ref != target:
            _add(issues, "run.invalid", run_root / "CONTEXT.md", workspace, "Next Laufpfad entry must follow selected route")
    elif isinstance(target, str) and target.startswith("end:") and not is_last:
        _add(issues, "run.invalid", run_root / "CONTEXT.md", workspace, "Laufpfad continues after end route")

    approval = entry.get("freigabe")
    if step.get("gate") == "human":
        if not _valid_human_approval(approval):
            _add(issues, "trust.invalid", run_root / "CONTEXT.md", workspace, "Human gate needs human attribution and timestamp")
    elif approval is not None:
        _add(issues, "trust.invalid", run_root / "CONTEXT.md", workspace, "Non-human gate must not carry approval")


def _valid_human_approval(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {"by", "at"}:
        return False
    actor, timestamp = value.get("by"), value.get("at")
    if not isinstance(actor, str) or not actor.startswith("human:") or not actor.removeprefix("human:").strip():
        return False
    if not isinstance(timestamp, str):
        return False
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _resolve_application(
    workspace: Path,
    revision: Any,
    run_root: Path,
    issues: list[Issue],
    definitions: dict[str, Application | str],
    snapshots: ExitStack,
    reachable: "_ReachableApplications",
) -> Application | None:
    if not isinstance(revision, str) or re.fullmatch(r"git-tree:(?:[0-9a-f]{40}|[0-9a-f]{64})", revision) is None:
        _add(issues, "revision.invalid", run_root / "CONTEXT.md", workspace, "Application revision is invalid")
        return None

    def reject(message: str) -> None:
        definitions[revision] = message
        _add(issues, "revision.invalid", run_root / "CONTEXT.md", workspace, message)

    cached = definitions.get(revision)
    if isinstance(cached, Application):
        return cached
    if isinstance(cached, str):
        reject(cached)
        return None
    oid = revision.removeprefix("git-tree:")
    repository = _git(workspace, "rev-parse", "--show-toplevel")
    if repository is None or Path(repository).resolve() != workspace.resolve():
        reject("Workspace root must be the Git repository root")
        return None
    if _git(workspace, "cat-file", "-t", oid) != "tree":
        reject("Application tree is missing or unreachable")
        return None
    # Keep the paths in Application alive until all dependent runs were checked.
    target = Path(snapshots.enter_context(TemporaryDirectory(prefix="impacts-application-")))
    if not _materialize_tree(workspace, oid, target):
        reject("Application tree is unreadable or contains an unsafe entry")
        return None
    nested: list[Issue] = []
    application = _validate_application(target, nested, check_slug=False)
    if application is None or nested:
        details = "; ".join(
            f"{issue.path}: {issue.code}: {issue.message}" for issue in _ordered(nested)
        )
        message = (
            f"Application {revision} does not satisfy the Core contract; "
            "preserve existing historical bindings and use a corrected Application tree for a new Run"
        )
        reject(f"{message}: {details}" if details else message)
        return None
    slug = application.hauptprozess["id"].removeprefix("hauptprozess:")
    if not reachable.contains(oid, slug):
        reject("Application tree is missing or unreachable at its declared slug")
        return None
    definitions[revision] = application
    return application


class _GitBatch:
    """One bounded-lifetime Git process; read exactly one raw object at a time."""

    def __init__(self, root: Path):
        self.process = subprocess.Popen(
            ["git", "--no-replace-objects", "-C", str(root), "cat-file", "--batch"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        self.failed = False

    def read(self, oid: str) -> tuple[str, bytes] | None:
        if self.failed or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", oid):
            self.failed = True
            return None
        try:
            assert self.process.stdin is not None and self.process.stdout is not None
            self.process.stdin.write(oid.encode("ascii") + b"\n")
            self.process.stdin.flush()
            header = self.process.stdout.readline()
            match = re.fullmatch(rb"([0-9a-f]{40}|[0-9a-f]{64}) (\w+) ([0-9]+)\n", header)
            if match is None or match[1].decode("ascii") != oid:
                self.failed = True
                return None
            size = int(match[3])
            content = self.process.stdout.read(size)
            if len(content) != size or self.process.stdout.read(1) != b"\n":
                self.failed = True
                return None
            return match[2].decode("ascii"), content
        except (OSError, UnicodeError, ValueError):
            self.failed = True
            return None

    def close(self) -> bool:
        try:
            if self.failed:
                self.process.kill()
                self.process.wait()
                return False
            assert self.process.stdin is not None
            self.process.stdin.close()
            return self.process.wait() == 0 and not self.failed
        except OSError:
            self.process.kill()
            self.process.wait()
            return False


def _batch_collect(
    root: Path, oids: set[str], kind: str,
    extract: Callable[[str, bytes], Iterable[Any] | None],
) -> set[Any] | None:
    if not oids:
        return set()
    try:
        batch = _GitBatch(root)
    except OSError:
        return None
    result: set[Any] = set()
    count = 0
    for oid in sorted(oids):
        item = batch.read(oid)
        if item is None or item[0] != kind:
            batch.failed = True
            break
        values = extract(oid, item[1])
        if values is None:
            batch.failed = True
            break
        result.update(values)
        count += 1
    return result if batch.close() and count == len(oids) else None


def _tree_entries(raw: bytes, oid_length: int) -> list[tuple[bytes, bytes, str]] | None:
    entries = []
    position = 0
    while position < len(raw):
        end = raw.find(b"\0", position)
        if end < 0 or end + 1 + oid_length > len(raw):
            return None
        mode_name = raw[position:end].split(b" ", 1)
        if len(mode_name) != 2:
            return None
        object_id = raw[end + 1:end + 1 + oid_length].hex()
        entries.append((mode_name[0], mode_name[1], object_id))
        position = end + 1 + oid_length
    return entries


class _ReachableApplications:
    """Per-validation map from reachable commits to applications/<slug> trees."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.index: set[tuple[str, str]] | None = None

    def contains(self, oid: str, slug: str) -> bool:
        if self.index is None:
            self.index = self._build()
        return (oid, slug) in self.index

    def _build(self) -> set[tuple[str, str]]:
        commits = _git(self.workspace, "rev-list", "--all")
        if commits is None:
            return set()
        commit_ids = set(commits.splitlines())
        def root_tree(_oid: str, content: bytes) -> list[str] | None:
            match = re.match(rb"tree ([0-9a-f]{40}|[0-9a-f]{64})\n", content)
            return [match[1].decode("ascii")] if match else None

        roots = _batch_collect(self.workspace, commit_ids, "commit", root_tree)
        if roots is None:
            return set()

        def application_tree(root_oid: str, content: bytes) -> list[str] | None:
            entries = _tree_entries(content, len(root_oid) // 2)
            if entries is None:
                return None
            return [
                entry_oid for mode, name, entry_oid in entries
                if mode in {b"40000", b"040000"} and name == b"applications"
            ]

        applications = _batch_collect(self.workspace, roots, "tree", application_tree)
        if applications is None:
            return set()

        def application_entries(app_oid: str, content: bytes) -> list[tuple[str, str]] | None:
            entries = _tree_entries(content, len(app_oid) // 2)
            if entries is None:
                return None
            found = []
            for mode, name, tree_oid in entries:
                if mode in {b"40000", b"040000"}:
                    try:
                        slug = name.decode("ascii")
                    except UnicodeError:
                        continue
                    if SLUG.fullmatch(slug):
                        found.append((tree_oid, slug))
            return found

        return _batch_collect(self.workspace, applications, "tree", application_entries) or set()


def _materialize_tree(workspace: Path, oid: str, target: Path) -> bool:
    """Read exact Git objects, without archive attributes or replacement refs."""
    listing = _git(workspace, "ls-tree", "-rtz", oid)
    if listing is None:
        return False
    reserved_names = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"} | {
        prefix + digit for prefix in ("COM", "LPT") for digit in "123456789¹²³"
    }
    try:
        entries = {}
        for entry in filter(None, listing.split("\0")):
            metadata, separator, name = entry.partition("\t")
            mode, kind, object_id = metadata.split()
            relative = Path(name)
            if not separator or relative.is_absolute() or any(part in {"", ".", ".."} for part in name.split("/")):
                return False
            # A bound Git name must retain its identity on either filesystem.
            if any(
                part.endswith((".", " "))
                or any(ord(char) < 32 or char in '\\:*?"<>|' for char in part)
                or part.partition(".")[0].rstrip(" ").upper() in reserved_names
                for part in name.split("/")
            ):
                return False
            if name in entries or (mode, kind) not in {
                ("040000", "tree"), ("100644", "blob"), ("100755", "blob"),
            }:
                return False
            entries[name] = (mode, kind, object_id)
        for name in entries:
            for parent in Path(name).parents:
                if parent != Path(".") and entries.get(parent.as_posix(), (None, None))[1] != "tree":
                    return False
        batch = _GitBatch(workspace) if any(kind == "blob" for _, kind, _ in entries.values()) else None
        valid = True
        try:
            for name, (mode, kind, object_id) in entries.items():
                destination = target / name
                if kind == "tree":
                    destination.mkdir()
                else:
                    assert batch is not None
                    item = batch.read(object_id)
                    if item is None or item[0] != "blob":
                        batch.failed = True
                        valid = False
                        break
                    # Exclusive creation also rejects aliases on case-insensitive or
                    # Unicode-normalizing filesystems instead of overwriting bytes.
                    with destination.open("xb") as output:
                        output.write(item[1])
        finally:
            if batch is not None and not batch.close():
                valid = False
        if not valid:
            return False
    except (OSError, ValueError):
        return False
    return True


def _git(root: Path, *args: str, binary: bool = False) -> str | bytes | None:
    try:
        result = subprocess.run(
            ["git", "--no-replace-objects", "-C", str(root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=not binary,
            check=False,
        )
    except (OSError, UnicodeError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout if binary else result.stdout.strip()


def _surface_hash(
    attempt_root: Path,
    declared: Any,
    workspace: Path,
    issues: list[Issue],
) -> str | None:
    if not isinstance(declared, list) or not all(isinstance(item, str) for item in declared):
        return None
    try:
        return surface_hash(attempt_root, declared)
    except HashSurfaceError as error:
        _add(issues, error.code, error.path, workspace, error.message)
        return None


def _attempt_directories(
    run_root: Path, workspace: Path, issues: list[Issue]
) -> set[tuple[str, int]]:
    result: set[tuple[str, int]] = set()
    for step_root in run_root.iterdir():
        if step_root.name == "CONTEXT.md":
            continue
        if not step_root.is_dir() or step_root.is_symlink() or SLUG.fullmatch(step_root.name) is None:
            _add(issues, "run.invalid", step_root, workspace, "Invalid Arbeitsschritt run directory")
            continue
        attempts = list(step_root.iterdir())
        if not attempts:
            _add(issues, "run.invalid", step_root, workspace, "Unreached Arbeitsschritt run directory")
        for attempt in attempts:
            if not attempt.is_dir() or attempt.is_symlink() or re.fullmatch(r"[0-9]{3}", attempt.name) is None or int(attempt.name) < 1:
                _add(issues, "run.invalid", attempt, workspace, "Attempt directory must be a positive three-digit number")
                continue
            result.add((step_root.name, int(attempt.name)))
    return result


def _load_context(
    path: Path,
    root: Path,
    issues: list[Issue],
    *,
    kind: str | None = None,
    require_body: bool = False,
) -> dict[str, Any] | None:
    if _has_symlink_component(path, root):
        _add(issues, "structure.symlink", path, root, "Router is a symlink")
        return None
    if not path.is_file():
        _add(issues, "routing.missing", path, root, "Required CONTEXT.md is missing")
        return None
    try:
        metadata, body = load_frontmatter_and_body(path, root)
    except ValueError as error:
        _add(issues, "format.invalid", path, root, str(error))
        return None
    if kind is not None and metadata.get("type") != kind:
        _add(issues, "routing.type", path, root, f"Router type must be {kind}")
    if require_body and not body.strip():
        _add(issues, "routing.missing", path, root, "Arbeitsschritt processing body is missing")
    if kind is not None:
        try:
            errors = SCHEMA_REGISTRY.errors(kind, metadata)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            _add(issues, "format.invalid", path, root, str(error))
        else:
            for error in errors:
                pointer = "/" + "/".join(
                    str(part).replace("~", "~0").replace("/", "~1")
                    for part in error.absolute_path
                ) if error.absolute_path else "<root>"
                _add(issues, "schema.invalid", path, root, f"{pointer}: {error.message}")
    return metadata


def _slug_children(
    path: Path, root: Path, issues: list[Issue], label: str
) -> list[Path]:
    """Return the slug-named subfolders of one process node; flag everything else."""
    if _has_symlink_component(path, root) or not path.is_dir():
        return []
    children: list[Path] = []
    for child in sorted(path.iterdir(), key=lambda item: item.name):
        if child.is_symlink():
            _add(issues, "structure.symlink", child, root, f"{label} is a symlink")
        elif child.name == "CONTEXT.md":
            if not child.is_file():
                _add(issues, "structure.invalid", child, root, "CONTEXT.md must be a file")
        elif child.is_dir():
            if SLUG.fullmatch(child.name) is None:
                _add(issues, "structure.invalid", child, root, f"{label} folder needs a slug")
            else:
                children.append(child)
        else:
            _add(issues, "structure.invalid", child, root, "Unknown Application entry")
    return children


def _reject_symlinks(path: Path, root: Path, issues: list[Issue]) -> None:
    if path.is_symlink():
        _add(issues, "structure.symlink", path, root, "Application root is a symlink")
        return
    for child in path.rglob("*"):
        if child.is_symlink():
            _add(issues, "structure.symlink", child, root, "Core tree contains a symlink")


def _add(
    issues: list[Issue], code: str, path: Path, root: Path, message: str
) -> None:
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        relative = str(path)
    issues.append(Issue(code, relative or ".", message))


def _ordered(issues: list[Issue]) -> tuple[Issue, ...]:
    unique = {(issue.code, issue.path, issue.message): issue for issue in issues}
    return tuple(unique[key] for key in sorted(unique))
