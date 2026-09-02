"""Read-only validation for the minimal file-native IMPACTS contract."""

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from importlib import resources
import json
from pathlib import Path
import re
import subprocess
import tarfile
from tempfile import TemporaryDirectory
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .hashing import HashSurfaceError, surface_hash
from .io import load_frontmatter_and_body
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
        if (
            isinstance(root_type, str)
            and root_type in {"workspace", "application"}
            and set(metadata) != {"type"}
        ):
            _add(
                issues,
                "routing.type",
                root / "CONTEXT.md",
                root,
                "Root router frontmatter must contain only type",
            )
        if root_type == "workspace":
            _validate_workspace(root, issues)
        elif root_type == "application":
            _validate_application(root, issues)
        elif metadata is not None:
            _add(issues, "routing.type", root / "CONTEXT.md", root, "Root type must be workspace or application")
    except (OSError, RuntimeError) as error:
        _add(issues, "structure.invalid", root, root, f"Core tree cannot be read: {error}")
    return ValidationReport(_ordered(issues))


def _validate_workspace(root: Path, issues: list[Issue]) -> None:
    for folder in WORKSPACE_FOLDERS:
        path = root / folder
        if path.is_symlink():
            _add(issues, "structure.symlink", path, root, "Core folder is a symlink")
        elif not path.is_dir():
            _add(issues, "structure.invalid", path, root, "Required workspace folder is missing")
    applications = root / "applications"
    if applications.is_dir() and not applications.is_symlink():
        for path in sorted(applications.iterdir(), key=lambda item: item.name):
            if path.is_symlink():
                _add(issues, "structure.symlink", path, root, "Application is a symlink")
            elif path.is_dir():
                _validate_application(path, issues)
            else:
                _add(issues, "structure.invalid", path, root, "Applications contains a non-directory")
    runs = root / "vorgaenge"
    if runs.is_dir() and not runs.is_symlink():
        for path in sorted(runs.iterdir(), key=lambda item: item.name):
            if path.is_symlink():
                _add(issues, "structure.symlink", path, root, "Vorgang is a symlink")
            elif path.is_dir():
                _validate_vorgang(path, root, issues)
            else:
                _add(issues, "structure.invalid", path, root, "Vorgaenge contains a non-directory")


def _validate_application(
    root: Path, issues: list[Issue], *, check_slug: bool = True
) -> Application | None:
    before = len(issues)
    _reject_symlinks(root, root, issues)
    if check_slug and SLUG.fullmatch(root.name) is None:
        _add(issues, "structure.invalid", root, root, "Application folder needs a slug")
    router = _load_context(root / "CONTEXT.md", root, issues, expected_type="application")
    if router is None:
        return None

    _validate_exact_children(root, root, issues, {"hauptprozess"})
    process_root = root / "hauptprozess"
    _validate_exact_children(process_root, root, issues, {"teilprozesse"})
    process = _load_context(
        process_root / "CONTEXT.md",
        root,
        issues,
        expected_type="hauptprozess",
        schema_name="hauptprozess",
    )
    parts_root = process_root / "teilprozesse"
    part_dirs = _child_directories(parts_root, root, issues, "Teilprozess")
    if not part_dirs:
        _add(issues, "structure.invalid", parts_root, root, "Hauptprozess needs at least one Teilprozess")

    steps: dict[str, tuple[Path, dict[str, Any]]] = {}
    for part_root in part_dirs:
        _validate_exact_children(part_root, root, issues, {"arbeitsschritte"})
        part = _load_context(
            part_root / "CONTEXT.md",
            root,
            issues,
            expected_type="teilprozess",
            schema_name="teilprozess",
        )
        if part is not None and part.get("id") != f"teilprozess:{part_root.name}":
            _add(issues, "structure.invalid", part_root, root, "Teilprozess ID must match folder slug")
        step_dirs = _child_directories(
            part_root / "arbeitsschritte", root, issues, "Arbeitsschritt"
        )
        if not step_dirs:
            _add(
                issues,
                "structure.invalid",
                part_root / "arbeitsschritte",
                root,
                "Teilprozess needs at least one Arbeitsschritt",
            )
        for step_root in step_dirs:
            _validate_exact_children(step_root, root, issues, set())
            step = _load_context(
                step_root / "CONTEXT.md",
                root,
                issues,
                expected_type="arbeitsschritt",
                schema_name="arbeitsschritt",
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

    if process is None:
        return None
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
        _add(issues, "reference.unresolved", root / "hauptprozess/CONTEXT.md", root, "Hauptprozess entry does not resolve")
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

    can_end = set(direct_end)
    changed = True
    while changed:
        changed = False
        for step_id, targets in adjacency.items():
            if step_id not in can_end and targets & can_end:
                can_end.add(step_id)
                changed = True
    for step_id in sorted(set(steps) - can_end):
        _add(issues, "process.no_end", steps[step_id][0], root, f"No reachable end from: {step_id}")


def _validate_vorgang(run_root: Path, workspace: Path, issues: list[Issue]) -> None:
    _reject_symlinks(run_root, workspace, issues)
    document = _load_context(
        run_root / "CONTEXT.md",
        workspace,
        issues,
        expected_type="vorgang",
        schema_name="vorgang",
    )
    if document is None:
        return
    if document.get("id") != f"vorgang:{run_root.name}":
        _add(issues, "structure.invalid", run_root, workspace, "Vorgang ID must match folder slug")
    application = _resolve_application(
        workspace, document.get("application_revision"), run_root, issues
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
            / "arbeitsschritte"
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
                application,
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
            run_root / "arbeitsschritte" / slug / f"{number:03d}",
            workspace,
            "Attempt directory and Laufpfad differ",
        )


def _validate_completed_entry(
    entry: dict[str, Any],
    step: dict[str, Any],
    application: Application,
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
) -> Application | None:
    if not isinstance(revision, str) or not revision.startswith("git-tree:"):
        _add(issues, "revision.invalid", run_root / "CONTEXT.md", workspace, "Application revision is invalid")
        return None
    oid = revision.removeprefix("git-tree:")
    repository = _git(workspace, "rev-parse", "--show-toplevel")
    if repository is None or Path(repository).resolve() != workspace.resolve():
        _add(issues, "revision.invalid", run_root / "CONTEXT.md", workspace, "Workspace root must be the Git repository root")
        return None
    object_type = _git(workspace, "cat-file", "-t", oid)
    if object_type != "tree" or not _tree_is_reachable_application(workspace, oid):
        _add(issues, "revision.invalid", run_root / "CONTEXT.md", workspace, "Application tree is missing or unreachable")
        return None
    try:
        archive = subprocess.run(
            ["git", "-C", str(workspace), "archive", "--format=tar", oid],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        _add(issues, "revision.invalid", run_root / "CONTEXT.md", workspace, "Git cannot read the Application tree")
        return None
    if archive.returncode != 0:
        _add(issues, "revision.invalid", run_root / "CONTEXT.md", workspace, "Application tree cannot be read")
        return None
    with TemporaryDirectory(prefix="impacts-application-") as directory:
        target = Path(directory)
        if not _extract_tree_archive(archive.stdout, target):
            _add(issues, "revision.invalid", run_root / "CONTEXT.md", workspace, "Application tree contains an unsafe entry")
            return None
        nested: list[Issue] = []
        application = _validate_application(target, nested, check_slug=False)
        if application is None or nested:
            _add(issues, "revision.invalid", run_root / "CONTEXT.md", workspace, "Application tree violates the V1 contract")
            return None
        return application


def _tree_is_reachable_application(workspace: Path, oid: str) -> bool:
    commits = _git(workspace, "rev-list", "--all")
    if commits is None:
        return False
    for commit in commits.splitlines():
        listing = _git(workspace, "ls-tree", "-r", "-d", commit, "--", "applications")
        if listing is None:
            continue
        for line in listing.splitlines():
            metadata, separator, path = line.partition("\t")
            parts = metadata.split()
            path_parts = Path(path).parts
            if (
                separator
                and len(parts) == 3
                and parts[2] == oid
                and len(path_parts) == 2
                and SLUG.fullmatch(path_parts[1]) is not None
            ):
                return True
    return False


def _extract_tree_archive(payload: bytes, target: Path) -> bool:
    try:
        with tarfile.open(fileobj=BytesIO(payload), mode="r:") as archive:
            members = archive.getmembers()
            for member in members:
                relative = Path(member.name)
                if relative.is_absolute() or ".." in relative.parts or member.issym() or member.islnk():
                    return False
                if not member.isdir() and not member.isfile():
                    return False
            for member in members:
                destination = target / member.name
                if member.isdir():
                    destination.mkdir(parents=True, exist_ok=True)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    source = archive.extractfile(member)
                    if source is None:
                        return False
                    destination.write_bytes(source.read())
    except (OSError, tarfile.TarError):
        return False
    return True


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


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
    steps_root = run_root / "arbeitsschritte"
    if _has_symlink_component(steps_root, run_root) or not steps_root.is_dir():
        return result
    for step_root in steps_root.iterdir():
        if not step_root.is_dir() or step_root.is_symlink():
            _add(issues, "run.invalid", step_root, workspace, "Invalid workstep run directory")
            continue
        for attempt in step_root.iterdir():
            if not attempt.is_dir() or attempt.is_symlink() or len(attempt.name) != 3 or not attempt.name.isdigit() or int(attempt.name) < 1:
                _add(issues, "run.invalid", attempt, workspace, "Attempt directory must be a positive three-digit number")
                continue
            result.add((step_root.name, int(attempt.name)))
    return result


def _load_context(
    path: Path,
    root: Path,
    issues: list[Issue],
    *,
    expected_type: str | None = None,
    schema_name: str | None = None,
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
    if expected_type is not None and metadata.get("type") != expected_type:
        _add(issues, "routing.type", path, root, f"Router type must be {expected_type}")
    if require_body and not body.strip():
        _add(issues, "routing.missing", path, root, "Arbeitsschritt processing body is missing")
    if expected_type == "application" and set(metadata) != {"type"}:
        _add(
            issues,
            "routing.type",
            path,
            root,
            "Application router frontmatter must contain only type",
        )
    if schema_name is not None:
        try:
            errors = SCHEMA_REGISTRY.errors(schema_name, metadata)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            _add(issues, "format.invalid", path, root, str(error))
        else:
            for error in errors:
                _add(issues, "schema.invalid", path, root, error.message)
    return metadata


def _child_directories(
    path: Path, root: Path, issues: list[Issue], label: str
) -> list[Path]:
    if _has_symlink_component(path, root):
        _add(issues, "structure.symlink", path, root, f"{label} collection is a symlink")
        return []
    if not path.is_dir():
        return []
    children: list[Path] = []
    for child in sorted(path.iterdir(), key=lambda item: item.name):
        if child.is_symlink():
            _add(issues, "structure.symlink", child, root, f"{label} is a symlink")
        elif child.is_dir():
            children.append(child)
        else:
            _add(issues, "structure.invalid", child, root, f"{label} collection contains a non-directory")
    return children


def _validate_exact_children(
    path: Path,
    root: Path,
    issues: list[Issue],
    allowed_directories: set[str],
) -> None:
    if _has_symlink_component(path, root) or not path.is_dir():
        return
    allowed = {"CONTEXT.md", *allowed_directories}
    for child in path.iterdir():
        if child.name not in allowed:
            _add(issues, "structure.invalid", child, root, "Unknown Application entry")
        elif child.name == "CONTEXT.md" and not child.is_file():
            _add(issues, "structure.invalid", child, root, "CONTEXT.md must be a file")
        elif child.name in allowed_directories and not child.is_dir():
            _add(issues, "structure.invalid", child, root, "Application collection must be a directory")


def _reject_symlinks(path: Path, root: Path, issues: list[Issue]) -> None:
    if path.is_symlink():
        _add(issues, "structure.symlink", path, root, "Application root is a symlink")
        return
    for child in path.rglob("*"):
        if child.is_symlink():
            _add(issues, "structure.symlink", child, root, "Core tree contains a symlink")


def _has_symlink_component(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    current = root
    if current.is_symlink():
        return True
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


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
