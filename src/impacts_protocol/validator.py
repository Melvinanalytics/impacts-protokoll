"""Structural, reference, and process-path validation."""

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from importlib import resources
import json
import os
from pathlib import Path
import re
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker

from .io import PathEscapeError, load_frontmatter, load_yaml
from .model import Issue, ValidationReport
from .workspace_contract import WORKSPACE_FOLDERS


SCHEMA_NAMES = {
    "leistung.yaml": "leistung",
    "hauptprozess.yaml": "hauptprozess",
    "teilprozess.yaml": "teilprozess",
    "arbeitsschritt.yaml": "arbeitsschritt",
    "vorgang.yaml": "vorgang",
    "wiedervorlage.yaml": "wiedervorlage",
    "paketaktivierungen.yaml": "paketaktivierungen",
}

FORMAT_CHECKER = FormatChecker()
RFC3339_DATE_TIME = re.compile(
    r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?"
    r"(?:Z|[+-](?P<offset_hour>\d{2}):(?P<offset_minute>\d{2}))\Z"
)
WORKSPACE_DIRECTORIES = set(WORKSPACE_FOLDERS)
REQUIRED_WORKSPACE_DIRECTORIES = WORKSPACE_DIRECTORIES - {"03_records"}
APPLICATION_FILENAMES = {
    "leistung.yaml",
    "hauptprozess.yaml",
    "teilprozess.yaml",
    "arbeitsschritt.yaml",
}
AUTHORITY_KINDS = {"file", "sqlite-local", "postgres-team", "external"}
LOCAL_AUTHORITY_KINDS = {"file", "sqlite-local"}
REMOTE_AUTHORITY_KINDS = {"postgres-team", "external"}
WORKSPACE_SCHEMA_KINDS = {"paketaktivierungen", "vorgang", "wiedervorlage"}
STABLE_ID = re.compile(r"\A[a-z0-9][a-z0-9._-]{0,127}\Z")
DATE_STAMP = re.compile(r"(?:\A|[-_.])\d{4}-\d{2}-\d{2}(?:\Z|[-_.])")
RUN_STAMP = re.compile(r"(?:\A|[-_.])run(?:\Z|[-_.][a-z0-9])")
SOR_REFERENCE = re.compile(r"\Asor:([^/\s]+)/([^/\s][^\s]*)\Z")


@FORMAT_CHECKER.checks("date-time")
def _is_rfc3339_timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return False
    match = RFC3339_DATE_TIME.fullmatch(value)
    if match is None:
        return False
    if match.group("offset_hour") is not None and (
        int(match.group("offset_hour")) > 23
        or int(match.group("offset_minute")) > 59
    ):
        return False
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


class SchemaRegistry:
    """Load protocol schemas and validate documents by schema name."""

    def __init__(self, schema_dir: Path | None = None):
        self.schema_dir = schema_dir
        self._validators: dict[str, Draft202012Validator] = {}

    def errors(self, schema_name: str, document: dict[str, Any]):
        validator = self._validators.get(schema_name)
        if validator is None:
            schema = json.loads(self._schema_text(schema_name))
            validator = Draft202012Validator(schema, format_checker=FORMAT_CHECKER)
            self._validators[schema_name] = validator
        return sorted(validator.iter_errors(document), key=lambda error: list(error.path))

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
            source_schema_dir = (
                Path(__file__).resolve().parents[2] / "02_protocol/schemas"
            )
            return (source_schema_dir / filename).read_text(encoding="utf-8")


@dataclass(frozen=True)
class _Document:
    kind: str
    path: Path
    data: dict[str, Any]


def validate_workspace(root: Path) -> ValidationReport:
    """Validate one file-native IMPACTS workspace."""
    root = Path(root)
    issues: list[Issue] = []
    if not root.is_dir():
        return ValidationReport(
            (Issue("workspace.not_found", str(root), "Workspace directory does not exist"),)
        )

    _validate_no_symlinks(root, issues)
    _validate_routing_names(root, issues)
    _validate_frontmatter(root, issues)
    _validate_json_files(root, issues)
    _validate_workspace_content(root, issues)
    documents = _load_documents(root, issues, allowed_kinds=WORKSPACE_SCHEMA_KINDS)
    _validate_required_routers(root, documents, issues)
    _validate_containment(root, documents, issues)
    _validate_references(root, documents, issues)
    _validate_generated_views(root, issues)
    active_packages = _validate_activation_record(root, documents, issues)
    records_required, remote_ids, authority_locality = _validate_data_authority(
        root, issues
    )
    _validate_workspace_layout(root, records_required, issues)
    _validate_process_bindings(root, active_packages, issues)
    local_ids = _validate_records(root, authority_locality, issues)
    _validate_vorgaenge(root, issues)
    _validate_snapshot_references(root, local_ids, remote_ids, issues)

    ordered = tuple(sorted(issues, key=lambda issue: (issue.path, issue.code, issue.message)))
    return ValidationReport(ordered)


def validate_application(root: Path) -> ValidationReport:
    """Validate one checked-out Application package without executing it."""
    root = Path(root)
    issues: list[Issue] = []
    if not root.is_dir():
        return ValidationReport(
            (
                Issue(
                    "application.not_found",
                    str(root),
                    "Application directory does not exist",
                ),
            )
        )
    _validate_no_symlinks(root, issues)
    _validate_routing_names(root, issues)
    _validate_frontmatter(root, issues)
    _validate_json_files(root, issues)
    documents = _load_documents(root, issues)
    _validate_required_routers(root, documents, issues)
    _validate_containment(root, documents, issues)
    _validate_references(root, documents, issues)
    _validate_application_hierarchy(root, documents, issues)
    for document in documents:
        if document.kind == "hauptprozess":
            _validate_process_paths(root, document, issues)
    ordered = tuple(
        sorted(issues, key=lambda issue: (issue.path, issue.code, issue.message))
    )
    return ValidationReport(ordered)


def _validate_activation_record(
    root: Path, documents: list[_Document], issues: list[Issue]
) -> set[tuple[str, str]]:
    activations = [
        document for document in documents if document.kind == "paketaktivierungen"
    ]
    expected_path = root / "00_steuerung/paketaktivierungen.yaml"
    canonical = [document for document in activations if document.path == expected_path]
    if len(canonical) != 1 or len(activations) != 1:
        _issue(
            issues,
            root,
            "activation.cardinality",
            expected_path,
            f"Expected one canonical activation record, found {len(activations)}",
        )
        return set()
    packages = canonical[0].data.get("packages")
    if not isinstance(packages, list):
        return set()
    identifiers = [
        identifier
        for package in packages
        if isinstance(package, dict)
        and isinstance((identifier := package.get("id")), str)
    ]
    duplicates = sorted(
        identifier
        for identifier in set(identifiers)
        if isinstance(identifier, str) and identifiers.count(identifier) > 1
    )
    for identifier in duplicates:
        _issue(
            issues,
            root,
            "capability.duplicate_activation",
            canonical[0].path,
            f"Package {identifier!r} is activated more than once",
        )
    return {
        (identifier, version)
        for package in packages
        if isinstance(package, dict)
        and package.get("activation") == "active"
        and isinstance((identifier := package.get("id")), str)
        and isinstance((version := package.get("version")), str)
    }


def _validate_data_authority(
    root: Path, issues: list[Issue]
) -> tuple[bool | None, set[str], dict[str, bool]]:
    path = root / "02_grundlagen/datenautoritaet.yaml"
    try:
        data = load_yaml(path, root)
    except FileNotFoundError:
        _issue(
            issues,
            root,
            "authority.missing",
            path,
            "Data authority contract is missing",
        )
        return None, set(), {}
    except (PathEscapeError, ValueError) as error:
        _issue(issues, root, "authority.invalid", path, str(error))
        return None, set(), {}
    records = data.get("records") if isinstance(data, dict) else None
    if not isinstance(records, dict) or not records:
        _issue(
            issues,
            root,
            "authority.invalid",
            path,
            "records must be a non-empty mapping",
        )
        return None, set(), {}
    kinds: set[str] = set()
    remote_ids: set[str] = set()
    authority_locality: dict[str, bool] = {}
    valid = True
    for name, config in records.items():
        if not _nonempty(name):
            _issue(
                issues,
                root,
                "authority.invalid",
                path,
                "record authority names must be non-empty strings",
            )
            valid = False
            continue
        if not isinstance(config, dict):
            _issue(
                issues,
                root,
                "authority.invalid",
                path,
                "record authority entries must be mappings",
            )
            valid = False
            continue
        kind = config.get("kind")
        if not isinstance(kind, str) or kind not in AUTHORITY_KINDS:
            _issue(
                issues,
                root,
                "authority.invalid",
                path,
                f"record authority {name!r} needs kind in {sorted(AUTHORITY_KINDS)!r}",
            )
            valid = False
            continue
        kinds.add(kind)
        authority_locality[name] = kind in LOCAL_AUTHORITY_KINDS
        writes = config.get("writes")
        if not isinstance(writes, str) or not writes.strip():
            _issue(
                issues,
                root,
                "authority.invalid",
                path,
                f"record authority {name!r} needs non-empty writes",
            )
            valid = False
        if kind in LOCAL_AUTHORITY_KINDS:
            if not _validate_local_authority_path(
                root, path, config.get("path"), issues
            ):
                valid = False
            if "authority_id" in config or "dsn_ref" in config:
                _issue(
                    issues,
                    root,
                    "authority.invalid",
                    path,
                    f"local authority {name!r} cannot declare authority_id or dsn_ref",
                )
                valid = False
        elif kind == "external":
            if not _nonempty(config.get("authority_id")) or "path" in config:
                _issue(
                    issues,
                    root,
                    "authority.invalid",
                    path,
                    f"external authority {name!r} needs authority_id and no path",
                )
                valid = False
        elif kind == "postgres-team":
            if (
                not _nonempty(config.get("authority_id"))
                or not _nonempty(config.get("dsn_ref"))
                or "path" in config
            ):
                _issue(
                    issues,
                    root,
                    "authority.invalid",
                    path,
                    f"postgres-team authority {name!r} needs authority_id, "
                    "dsn_ref, and no path",
                )
                valid = False
        authority_id = config.get("authority_id")
        if kind in REMOTE_AUTHORITY_KINDS and _nonempty(authority_id):
            remote_ids.add(authority_id)

    if not valid or not kinds:
        return None, set(), {}
    records_required = bool(kinds & LOCAL_AUTHORITY_KINDS)
    record_root_exists = _real_directory(root / "03_records")
    if not records_required and record_root_exists:
        _issue(
            issues,
            root,
            "authority.duplicate_record_store",
            root / "03_records",
            "Remote record authority requires no local record store",
        )
    if records_required and not record_root_exists:
        _issue(
            issues,
            root,
            "authority.missing_record_store",
            root / "03_records",
            "Local record authority requires 03_records",
        )
    return records_required, remote_ids, authority_locality


def _validate_local_authority_path(
    root: Path, contract_path: Path, value: object, issues: list[Issue]
) -> bool:
    if value != "03_records":
        code = (
            "authority.generated_view_write"
            if isinstance(value, str)
            and (value == "99_ansichten" or value.startswith("99_ansichten/"))
            else "authority.invalid"
        )
        _issue(
            issues,
            root,
            code,
            contract_path,
            "local record authority path must equal 03_records",
        )
        return False
    if (root / "03_records").is_symlink():
        _issue(
            issues,
            root,
            "authority.invalid",
            contract_path,
            "local authority path cannot be a symlink",
        )
        return False
    return True


def _issue(
    issues: list[Issue], root: Path, code: str, path: Path, message: str
) -> None:
    try:
        display_path = path.relative_to(root).as_posix()
    except ValueError:
        display_path = str(path)
    issues.append(Issue(code, display_path or ".", message))


def _validate_no_symlinks(root: Path, issues: list[Issue]) -> None:
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as error:
            _issue(issues, root, "structure.unreadable", directory, str(error))
            continue
        for entry in entries:
            if directory == root and entry.name == ".git":
                continue
            path = Path(entry.path)
            if entry.is_symlink():
                _issue(
                    issues,
                    root,
                    "structure.symlink",
                    path,
                    "Workspace entries cannot be symlinks",
                )
                continue
            if entry.is_dir(follow_symlinks=False):
                pending.append(path)


def _validate_workspace_layout(
    root: Path, records_required: bool | None, issues: list[Issue]
) -> None:
    expected = set(REQUIRED_WORKSPACE_DIRECTORIES)
    if records_required is True:
        expected.add("03_records")
    for name in sorted(expected):
        path = root / name
        if path.is_symlink():
            _issue(
                issues,
                root,
                "workspace.symlink_directory",
                path,
                "Canonical workspace directories cannot be symlinks",
            )
        elif not path.is_dir():
            _issue(
                issues,
                root,
                "workspace.missing_directory",
                path,
                "Canonical workspace directory is missing",
            )
    if records_required is False and (root / "03_records").is_symlink():
        _issue(
            issues,
            root,
            "workspace.symlink_directory",
            root / "03_records",
            "Canonical workspace directories cannot be symlinks",
        )
    for path in sorted(root.iterdir()):
        if path.name == ".git":
            continue
        if (
            path.is_symlink() or path.is_dir()
        ) and path.name not in WORKSPACE_DIRECTORIES:
            _issue(
                issues,
                root,
                "workspace.unexpected_directory",
                path,
                "Unexpected root directory",
            )


def _validate_workspace_content(root: Path, issues: list[Issue]) -> None:
    for path in sorted(
        candidate
        for candidate in root.rglob("*")
        if not candidate.is_symlink() and candidate.is_file()
    ):
        normalized = _normalized_yaml_filename(path.name)
        if normalized in APPLICATION_FILENAMES:
            _issue(
                issues,
                root,
                "workspace.embedded_application",
                path,
                "Application process documents belong in the external package",
            )
        if normalized.endswith(".quittung.yaml") or (
            normalized.endswith(".delta.yaml") and normalized != "delta.yaml"
        ):
            _issue(
                issues,
                root,
                "workspace.legacy_evidence",
                path,
                "Legacy evidence artifact is not part of the workspace contract",
            )


def _validate_process_bindings(
    root: Path,
    active_packages: set[tuple[str, str]],
    issues: list[Issue],
) -> None:
    process_root = root / "01_prozesse"
    if not _real_directory(process_root):
        return
    required = {"provenance.yaml", "delta.yaml"}
    for application in sorted(process_root.iterdir()):
        if application.name == ".gitkeep":
            continue
        if application.is_symlink() or not application.is_dir():
            _issue(
                issues,
                root,
                "process_binding.unexpected_entry",
                application,
                "01_prozesse contains only application binding directories",
            )
            continue
        entries = {entry.name for entry in application.iterdir()}
        for missing in sorted(required - entries):
            _issue(
                issues,
                root,
                "process_binding.missing_file",
                application / missing,
                "Application binding needs provenance.yaml and delta.yaml",
            )
        for unexpected in sorted(entries - required):
            _issue(
                issues,
                root,
                "process_binding.unexpected_entry",
                application / unexpected,
                "Application binding contains only provenance.yaml and delta.yaml",
            )
        for name in sorted(required & entries):
            path = application / name
            if path.is_symlink() or not path.is_file():
                _issue(
                    issues,
                    root,
                    "process_binding.unexpected_entry",
                    path,
                    "Application binding files must be regular workspace files",
                )
                continue
            try:
                document = load_yaml(path, root)
            except (PathEscapeError, ValueError):
                continue
            if name == "provenance.yaml":
                identifier = document.get("id")
                version = document.get("version")
                expected_identifier = f"application:{application.name}"
                if (
                    set(document) != {"id", "version"}
                    or identifier != expected_identifier
                    or not _nonempty(version)
                ):
                    _issue(
                        issues,
                        root,
                        "process_binding.invalid",
                        path,
                        "provenance.yaml needs the folder-bound Application id and version",
                    )
                if (
                    not isinstance(identifier, str)
                    or not isinstance(version, str)
                    or (identifier, version) not in active_packages
                ):
                    _issue(
                        issues,
                        root,
                        "process_binding.unresolved_package",
                        path,
                        "Application id and version need one active package activation",
                    )
            if name == "delta.yaml" and not _valid_process_delta(document):
                _issue(
                    issues,
                    root,
                    "process_binding.invalid",
                    path,
                    "delta.yaml allows only path-bound scalar changes",
                )


def _valid_process_delta(document: dict[str, Any]) -> bool:
    changes = document.get("changes")
    if set(document) != {"changes"} or not isinstance(changes, list):
        return False
    for change in changes:
        if not isinstance(change, dict) or set(change) != {"path", "value"}:
            return False
        path = change.get("path")
        value = change.get("value")
        if not isinstance(path, str) or not path.startswith("/") or path == "/":
            return False
        if isinstance(value, (dict, list)):
            return False
    return True


def _validate_records(
    root: Path,
    authority_locality: dict[str, bool],
    issues: list[Issue],
) -> set[str]:
    record_root = root / "03_records"
    if not _real_directory(record_root):
        return set()
    valid_ids: set[str] = set()
    for record_directory in sorted(record_root.iterdir()):
        if record_directory.name == ".gitkeep":
            continue
        if record_directory.is_symlink() or not record_directory.is_dir():
            _issue(
                issues,
                root,
                "record.invalid",
                record_directory,
                "Record entries must be non-symlink directories",
            )
            continue
        record_id = record_directory.name
        stable_identity = not (
            STABLE_ID.fullmatch(record_id) is None
            or DATE_STAMP.search(record_id)
            or RUN_STAMP.search(record_id)
        )
        if not stable_identity:
            _issue(
                issues,
                root,
                "record.invalid",
                record_directory,
                "Record directory needs a stable, non-dated ID",
            )
        record_path = record_directory / "record.yaml"
        if not record_path.is_file() or record_path.is_symlink():
            _issue(
                issues,
                root,
                "record.invalid",
                record_path,
                "Record directory needs a regular record.yaml",
            )
            continue
        try:
            record = load_yaml(record_path, root)
        except (PathEscapeError, ValueError):
            continue
        record_type = record.get("type")
        valid_record = record.get("id") == record_id and _nonempty(record_type)
        if not valid_record:
            _issue(
                issues,
                root,
                "record.invalid",
                record_path,
                "record.yaml needs matching id and non-empty type",
            )
        if isinstance(record_type, str) and authority_locality:
            local_authority = authority_locality.get(
                record_type, authority_locality.get("default")
            )
            if local_authority is not True:
                _issue(
                    issues,
                    root,
                    "authority.record_type",
                    record_path,
                    "Local Record type needs a local data authority",
                )
                valid_record = False
        if stable_identity and valid_record:
            valid_ids.add(record_id)
        for markdown in sorted(record_directory.rglob("*.md")):
            if markdown.is_symlink() or markdown.name == "CONTEXT.md":
                continue
            try:
                frontmatter = load_frontmatter(markdown, root)
            except (PathEscapeError, ValueError):
                continue
            if not _nonempty(frontmatter.get("type")):
                _issue(
                    issues,
                    root,
                    "graph.missing_type",
                    markdown,
                    "Record Markdown graph nodes need type frontmatter",
                )
    return valid_ids


def _validate_vorgaenge(root: Path, issues: list[Issue]) -> None:
    run_root = root / "06_vorgaenge"
    if not _real_directory(run_root):
        return
    required_files = {"vorgang.yaml"}
    required_directories = {"snapshot", "receipts", "freigaben"}
    for run in sorted(run_root.iterdir()):
        if run.name == ".gitkeep":
            continue
        if run.is_symlink() or not run.is_dir():
            _issue(
                issues,
                root,
                "vorgang.incomplete_structure",
                run,
                "Vorgang entries must be non-symlink directories",
            )
            continue
        missing = [
            run / name
            for name in sorted(required_files)
            if not (run / name).is_file() or (run / name).is_symlink()
        ]
        missing.extend(
            run / name
            for name in sorted(required_directories)
            if not _real_directory(run / name)
        )
        for path in missing:
            _issue(
                issues,
                root,
                "vorgang.incomplete_structure",
                path,
                "Vorgang needs vorgang.yaml, snapshot/, receipts/, and freigaben/",
            )
        vorgang_path = run / "vorgang.yaml"
        if vorgang_path in missing:
            continue
        try:
            vorgang = load_yaml(vorgang_path, root)
        except (PathEscapeError, ValueError):
            continue
        expected_id = f"vorgang:{run.name}"
        if vorgang.get("id") != expected_id:
            _issue(
                issues,
                root,
                "vorgang.path_identity",
                vorgang_path,
                f"Vorgang id must equal its canonical path id {expected_id!r}",
            )
        refs = _string_set(vorgang.get("receipt_refs"))
        receipt_root = run / "receipts"
        if refs is None or not _real_directory(receipt_root):
            continue
        receipt_ids, duplicate_ids = _receipt_ids(root, receipt_root)
        for identifier, paths in sorted(duplicate_ids.items()):
            _issue(
                issues,
                root,
                "receipt.duplicate_id",
                paths[0],
                f"Receipt id {identifier!r} is declared more than once in this Vorgang",
            )
        for reference in sorted(refs - receipt_ids):
            _issue(
                issues,
                root,
                "receipt.unresolved",
                vorgang_path,
                f"receipt_ref {reference!r} does not resolve in this Vorgang",
            )


def _receipt_ids(
    root: Path, receipt_root: Path
) -> tuple[set[str], dict[str, tuple[Path, ...]]]:
    paths_by_id: dict[str, list[Path]] = defaultdict(list)
    for path in sorted(receipt_root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            if path.suffix.lower() in {".yaml", ".yml"}:
                document = load_yaml(path, root)
            elif path.suffix.lower() == ".json":
                document = _load_json(path, root)
            else:
                continue
        except (OSError, UnicodeError, PathEscapeError, ValueError):
            continue
        if isinstance(document, dict) and _nonempty(document.get("id")):
            paths_by_id[document["id"]].append(path)
    unique = {
        identifier for identifier, paths in paths_by_id.items() if len(paths) == 1
    }
    duplicates = {
        identifier: tuple(paths)
        for identifier, paths in paths_by_id.items()
        if len(paths) > 1
    }
    return unique, duplicates


def _validate_snapshot_references(
    root: Path,
    local_ids: set[str],
    remote_ids: set[str],
    issues: list[Issue],
) -> None:
    run_root = root / "06_vorgaenge"
    if not _real_directory(run_root):
        return
    for run in sorted(run_root.iterdir()):
        snapshot_root = run / "snapshot"
        if run.is_symlink() or not _real_directory(snapshot_root):
            continue
        for path in sorted(snapshot_root.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            try:
                if path.suffix.lower() in {".yaml", ".yml"}:
                    document = load_yaml(path, root)
                elif path.suffix.lower() == ".json":
                    value = _load_json(path, root)
                    if not isinstance(value, dict):
                        continue
                    document = value
                else:
                    continue
            except (OSError, UnicodeError) as error:
                code = (
                    "format.invalid_json"
                    if path.suffix.lower() == ".json"
                    else "format.invalid_yaml"
                )
                _issue(issues, root, code, path, str(error))
                continue
            except (PathEscapeError, ValueError):
                continue
            if "record_ref" not in document:
                continue
            reference = document.get("record_ref")
            valid = isinstance(reference, str) and reference in local_ids
            if isinstance(reference, str):
                match = SOR_REFERENCE.fullmatch(reference)
                valid = valid or bool(match and match.group(1) in remote_ids)
            if not valid:
                _issue(
                    issues,
                    root,
                    "snapshot.invalid_record_ref",
                    path,
                    "record_ref must resolve to a local Record or declared "
                    "remote authority",
                )
def _validate_json_files(root: Path, issues: list[Issue]) -> None:
    for path in sorted(
        candidate
        for candidate in root.rglob("*")
        if not candidate.is_symlink()
        and candidate.is_file()
        and candidate.suffix.lower() == ".json"
    ):
        try:
            _load_json(path, root)
        except PathEscapeError as error:
            _issue(issues, root, "structure.path_escape", path, str(error))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            _issue(issues, root, "format.invalid_json", path, f"invalid JSON: {error}")


def _load_json(path: Path, root: Path) -> Any:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise PathEscapeError("source path resolves outside workspace root")
    return json.loads(
        resolved.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_json_object,
        parse_constant=_reject_json_constant,
    )


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def _real_directory(path: Path) -> bool:
    return path.is_dir() and not path.is_symlink()


def _normalized_yaml_filename(name: str) -> str:
    normalized = name.lower()
    if normalized.endswith(".yml"):
        return f"{normalized[:-4]}.yaml"
    return normalized


def _validate_routing_names(root: Path, issues: list[Issue]) -> None:
    for path in root.rglob("*"):
        if (
            path.is_symlink()
            or not path.is_file()
            or path.name.lower() not in {"context.md", "kontext.md"}
            or path.name == "CONTEXT.md"
        ):
            continue
        _issue(
            issues,
            root,
            "routing.noncanonical_filename",
            path,
            "Router filename must be CONTEXT.md",
        )


def _validate_frontmatter(root: Path, issues: list[Issue]) -> None:
    for path in sorted(root.rglob("*.md")):
        if path.is_symlink():
            continue
        try:
            load_frontmatter(path, root)
        except PathEscapeError as error:
            _issue(issues, root, "structure.path_escape", path, str(error))
        except ValueError as error:
            _issue(issues, root, "format.invalid_frontmatter", path, str(error))


def _load_documents(
    root: Path,
    issues: list[Issue],
    allowed_kinds: set[str] | None = None,
) -> list[_Document]:
    registry = SchemaRegistry()
    documents: list[_Document] = []
    for path in _yaml_paths(root):
        try:
            data = load_yaml(path, root)
        except PathEscapeError as error:
            _issue(issues, root, "structure.path_escape", path, str(error))
            continue
        except ValueError as error:
            _issue(issues, root, "format.invalid_yaml", path, str(error))
            continue
        normalized_name = _normalized_yaml_filename(path.name)
        schema_name = SCHEMA_NAMES.get(normalized_name)
        if schema_name is None or (
            allowed_kinds is not None and schema_name not in allowed_kinds
        ):
            continue
        documents.append(_Document(schema_name, path, data))
        for error in registry.errors(schema_name, data):
            location = ".".join(str(part) for part in error.absolute_path)
            suffix = f" at {location}" if location else ""
            _issue(
                issues,
                root,
                "schema.invalid",
                path,
                f"{error.message}{suffix}",
            )
    return documents


def _yaml_paths(root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in root.rglob("*")
            if not path.is_symlink()
            and path.is_file()
            and path.suffix.lower() in {".yaml", ".yml"}
        ),
        key=lambda path: path.as_posix().lower(),
    )


def _validate_required_routers(
    root: Path, documents: Iterable[_Document], issues: list[Issue]
) -> None:
    required_directories = {root}
    required_directories.update(
        document.path.parent
        for document in documents
        if document.kind in {
            "leistung",
            "hauptprozess",
            "teilprozess",
            "arbeitsschritt",
        }
        and _has_canonical_containment(root, document)
    )
    for directory in sorted(required_directories):
        router = directory / "CONTEXT.md"
        if not router.is_file() or router.is_symlink():
            _issue(
                issues,
                root,
                "routing.missing_router",
                router,
                "Required canonical router is missing",
            )
            continue
        try:
            frontmatter = load_frontmatter(router, root)
        except (PathEscapeError, ValueError):
            continue
        if not _nonempty(frontmatter.get("type")):
            _issue(
                issues,
                root,
                "routing.missing_type",
                router,
                "Required canonical router needs non-empty type frontmatter",
            )


def _expected_parts(kind: str) -> tuple[str, ...] | None:
    patterns = {
        "leistung": ("00_steuerung", "leistungen", "*", "leistung.yaml"),
        "hauptprozess": ("01_prozesse", "*", "hauptprozess.yaml"),
        "teilprozess": (
            "01_prozesse",
            "*",
            "teilprozesse",
            "*",
            "teilprozess.yaml",
        ),
        "arbeitsschritt": (
            "01_prozesse",
            "*",
            "teilprozesse",
            "*",
            "arbeitsschritte",
            "*",
            "arbeitsschritt.yaml",
        ),
        "vorgang": ("06_vorgaenge", "*", "vorgang.yaml"),
        "wiedervorlage": ("06_vorgaenge", "*", "wiedervorlage.yaml"),
    }
    return patterns.get(kind)


def _has_canonical_containment(root: Path, document: _Document) -> bool:
    pattern = _expected_parts(document.kind)
    if pattern is None:
        return True
    try:
        parts = document.path.relative_to(root).parts
    except ValueError:
        return False
    return len(parts) == len(pattern) and all(
        expected == "*" or actual == expected
        for actual, expected in zip(parts, pattern, strict=True)
    )


def _validate_containment(
    root: Path, documents: Iterable[_Document], issues: list[Issue]
) -> None:
    for document in documents:
        if _has_canonical_containment(root, document):
            continue
        if _expected_parts(document.kind) is None:
            continue
        _issue(
            issues,
            root,
            "structure.containment",
            document.path,
            f"{document.kind} document is outside its canonical workspace path",
        )


def _validate_references(
    root: Path, documents: list[_Document], issues: list[Issue]
) -> None:
    by_kind: dict[str, dict[str, _Document]] = defaultdict(dict)
    all_ids: dict[str, list[_Document]] = defaultdict(list)
    for document in documents:
        identifier = document.data.get("id")
        if isinstance(identifier, str) and identifier:
            all_ids[identifier].append(document)
            by_kind[document.kind].setdefault(identifier, document)

    for identifier, matches in all_ids.items():
        if len(matches) > 1:
            for document in matches:
                _issue(
                    issues,
                    root,
                    "reference.duplicate_id",
                    document.path,
                    f"ID {identifier!r} is declared more than once",
                )

    leistungen = by_kind["leistung"]
    hauptprozesse = by_kind["hauptprozess"]
    for identifier, leistung in leistungen.items():
        target_id = leistung.data.get("hauptprozess_ref")
        target = hauptprozesse.get(target_id) if isinstance(target_id, str) else None
        if target is None or target.data.get("leistung_ref") != identifier:
            _issue(
                issues,
                root,
                "reference.nonreciprocal",
                leistung.path,
                "Leistung and Hauptprozess references must be reciprocal",
            )
    for identifier, hauptprozess in hauptprozesse.items():
        target_id = hauptprozess.data.get("leistung_ref")
        target = leistungen.get(target_id) if isinstance(target_id, str) else None
        if target is None or target.data.get("hauptprozess_ref") != identifier:
            _issue(
                issues,
                root,
                "reference.nonreciprocal",
                hauptprozess.path,
                "Hauptprozess and Leistung references must be reciprocal",
            )

    for document in documents:
        if document.kind == "teilprozess":
            _validate_process_parent(
                root,
                document,
                "hauptprozess_ref",
                "hauptprozess.yaml",
                by_kind["hauptprozess"],
                issues,
            )
        elif document.kind == "arbeitsschritt":
            _validate_process_parent(
                root,
                document,
                "teilprozess_ref",
                "teilprozess.yaml",
                by_kind["teilprozess"],
                issues,
            )
        elif document.kind == "wiedervorlage":
            contained_path = document.path.parent / "vorgang.yaml"
            contained = next(
                (
                    candidate
                    for candidate in documents
                    if candidate.kind == "vorgang"
                    and candidate.path == contained_path
                ),
                None,
            )
            refs = document.data.get("receipt_refs")
            receipt_refs = _string_set(refs)
            continuation = document.data.get("continuation")
            contained_refs = (
                _string_set(contained.data.get("receipt_refs")) if contained else None
            )
            if (
                contained is None
                or document.data.get("vorgang_ref") != contained.data.get("id")
                or document.data.get("run_id") != contained.data.get("run_id")
                or receipt_refs is None
                or contained_refs is None
                or not receipt_refs <= contained_refs
                or not _nonempty(continuation)
            ):
                _issue(
                    issues,
                    root,
                    "reference.wiedervorlage",
                    document.path,
                    "Wiedervorlage must bind its containing Vorgang, stable run, "
                    "receipts, and external continuation ID",
                )


def _string_set(value: object) -> set[str] | None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        return None
    return set(value)


def _validate_application_hierarchy(
    root: Path, documents: list[_Document], issues: list[Issue]
) -> None:
    leistungen = [document for document in documents if document.kind == "leistung"]
    hauptprozesse = [
        document for document in documents if document.kind == "hauptprozess"
    ]
    teilprozesse = [document for document in documents if document.kind == "teilprozess"]
    arbeitsschritte = [
        document for document in documents if document.kind == "arbeitsschritt"
    ]
    if not leistungen:
        _issue(
            issues,
            root,
            "hierarchy.missing_root",
            root,
            "Application needs at least one Leistung",
        )
    if not hauptprozesse:
        _issue(
            issues,
            root,
            "hierarchy.missing_root",
            root,
            "Application needs at least one Hauptprozess",
        )
    for hauptprozess in hauptprozesse:
        identifier = hauptprozess.data.get("id")
        if isinstance(identifier, str) and not any(
            teilprozess.data.get("hauptprozess_ref") == identifier
            for teilprozess in teilprozesse
        ):
            _issue(
                issues,
                root,
                "hierarchy.missing_child",
                hauptprozess.path,
                "Hauptprozess needs at least one Teilprozess",
            )
    for teilprozess in teilprozesse:
        identifier = teilprozess.data.get("id")
        if isinstance(identifier, str) and not any(
            arbeitsschritt.data.get("teilprozess_ref") == identifier
            for arbeitsschritt in arbeitsschritte
        ):
            _issue(
                issues,
                root,
                "hierarchy.missing_child",
                teilprozess.path,
                "Teilprozess needs at least one Arbeitsschritt",
            )


def _validate_process_parent(
    root: Path,
    document: _Document,
    reference_field: str,
    parent_filename: str,
    parents_by_id: dict[str, _Document],
    issues: list[Issue],
) -> None:
    reference = document.data.get(reference_field)
    referenced_parent = parents_by_id.get(reference) if isinstance(reference, str) else None
    contained_parent = next(
        (parent for parent in document.path.parents if (parent / parent_filename).is_file()),
        None,
    )
    if (
        referenced_parent is None
        or contained_parent is None
        or referenced_parent.path.parent != contained_parent
    ):
        _issue(
            issues,
            root,
            "reference.process_parent",
            document.path,
            f"{reference_field} must resolve to the physically containing process",
        )


def _validate_generated_views(root: Path, issues: list[Issue]) -> None:
    view_root = root / "99_ansichten"
    if not _real_directory(view_root):
        return
    resolved_root = root.resolve()
    resolved_view_root = view_root.resolve()
    for path in sorted(
        candidate
        for candidate in view_root.rglob("*")
        if not candidate.is_symlink() and candidate.is_file()
    ):
        metadata_path = path
        try:
            if path.suffix.lower() in {".yaml", ".yml"}:
                data = load_yaml(path, root)
            elif path.suffix.lower() == ".md":
                data = load_frontmatter(path, root)
            elif path.suffix.lower() == ".json":
                value = _load_json(path, root)
                data = value if isinstance(value, dict) else {}
            else:
                metadata_path = path.with_name(f"{path.name}.provenance.yaml")
                data = (
                    load_yaml(metadata_path, root)
                    if metadata_path.is_file() and not metadata_path.is_symlink()
                    else {}
                )
        except PathEscapeError as error:
            _issue(issues, root, "structure.path_escape", metadata_path, str(error))
            continue
        except ValueError:
            continue
        if _claims_write_authority(data):
            _issue(
                issues,
                root,
                "view.write_authority",
                path,
                "Generated views cannot claim write authority",
            )
        generated_from = data.get("generated_from")
        if (
            data.get("generated") is not True
            or not isinstance(generated_from, list)
            or not generated_from
            or not all(_nonempty(item) for item in generated_from)
        ):
            _issue(
                issues,
                root,
                "view.missing_provenance",
                path,
                "Generated view needs generated: true and non-empty generated_from",
            )
            continue
        for reference in generated_from:
            reference_path = Path(reference)
            try:
                candidate = (
                    reference_path
                    if reference_path.is_absolute()
                    else root / reference_path
                )
                source = candidate.resolve()
            except (OSError, RuntimeError, ValueError):
                source = None
            if (
                source is None
                or reference_path.is_absolute()
                or not source.is_relative_to(resolved_root)
                or not source.is_file()
            ):
                _issue(
                    issues,
                    root,
                    "view.unresolved_provenance",
                    path,
                    "Generated source does not resolve inside workspace",
                )
                continue
            if source.is_relative_to(resolved_view_root):
                _issue(
                    issues,
                    root,
                    "view.non_authoritative_provenance",
                    path,
                    "Generated view provenance must terminate outside 99_ansichten",
                )


def _claims_write_authority(document: dict[str, Any]) -> bool:
    for field in ("writes", "write_authority"):
        if field not in document:
            continue
        value = document[field]
        if value not in (None, False, "", [], {}):
            return True
    return False


def _validate_process_paths(
    root: Path, document: _Document, issues: list[Issue]
) -> None:
    raw_nodes = document.data.get("nodes")
    if not isinstance(raw_nodes, list):
        return
    nodes: dict[str, dict[str, Any]] = {}
    for raw_node in raw_nodes:
        if not isinstance(raw_node, dict):
            continue
        node_id = raw_node.get("id")
        if not isinstance(node_id, str) or not node_id:
            continue
        if node_id in nodes:
            _issue(
                issues,
                root,
                "bpm.duplicate_node",
                document.path,
                f"Node ID {node_id!r} is declared more than once",
            )
            continue
        nodes[node_id] = raw_node

    entry = document.data.get("entry")
    if not isinstance(entry, str) or entry not in nodes:
        _issue(
            issues,
            root,
            "bpm.unresolved_entry",
            document.path,
            "Hauptprozess entry does not resolve to a declared node",
        )

    adjacency: dict[str, set[str]] = {node_id: set() for node_id in nodes}
    for node_id, node in nodes.items():
        successors = _node_successors(node, issues, root, document.path)
        for target in successors:
            if target not in nodes:
                _issue(
                    issues,
                    root,
                    "bpm.unresolved_target",
                    document.path,
                    f"Node {node_id!r} targets undeclared node {target!r}",
                )
            else:
                adjacency[node_id].add(target)

    reachable = _reachable(entry, adjacency) if isinstance(entry, str) else set()
    for node_id in nodes.keys() - reachable:
        _issue(
            issues,
            root,
            "bpm.unreachable",
            document.path,
            f"Node {node_id!r} is unreachable from the entry",
        )

    valid_outcomes: set[str] = set()
    for node_id in reachable:
        node = nodes[node_id]
        node_type = node.get("type")
        if node_type == "wait":
            trigger = node.get("trigger")
            owner = node.get("owner")
            if (
                not _nonempty(trigger)
                or not _nonempty(owner)
                or len(adjacency[node_id]) != 1
            ):
                _issue(
                    issues,
                    root,
                    "bpm.wait_trigger",
                    document.path,
                    f"Wait node {node_id!r} needs a trigger, owner, "
                    "and exactly one resolved continuation",
                )
            else:
                valid_outcomes.add(node_id)
        elif node_type == "handoff":
            artifact = node.get("artifact_ref")
            consumer = node.get("consumer_ref")
            if not isinstance(artifact, str) or not artifact.strip() or not isinstance(
                consumer, str
            ) or not consumer.strip():
                _issue(
                    issues,
                    root,
                    "bpm.handoff_consumer",
                    document.path,
                    f"Handoff node {node_id!r} needs an artifact and consumer",
                )
            else:
                valid_outcomes.add(node_id)
        elif node_type == "end":
            event = node.get("event")
            if not isinstance(event, str) or not event.strip():
                _issue(
                    issues,
                    root,
                    "bpm.unnamed_end",
                    document.path,
                    f"End node {node_id!r} needs a named event",
                )
            else:
                valid_outcomes.add(node_id)

    valid_cycle_nodes: set[str] = set()
    cyclic_components: list[set[str]] = []
    exit_candidates: list[tuple[set[str], set[str]]] = []
    for component in _strongly_connected_components(reachable, adjacency):
        cyclic = len(component) > 1 or any(
            node_id in adjacency[node_id] for node_id in component
        )
        if not cyclic:
            continue
        cyclic_components.append(component)
        continuation_declared = any(
            _nonempty(nodes[node_id].get("continuation_condition"))
            or _has_conditioned_route_within(nodes[node_id], component)
            for node_id in component
        )
        if continuation_declared:
            valid_cycle_nodes.update(component)
            continue
        exit_targets = set().union(
            *(
                _declared_exit_targets(nodes[node_id], adjacency[node_id], component)
                for node_id in component
            )
        )
        exit_candidates.append((component, exit_targets))

    unresolved_exit_candidates = exit_candidates
    while unresolved_exit_candidates:
        complete = _reverse_reachable(
            valid_outcomes | valid_cycle_nodes, reachable, adjacency
        )
        newly_valid = [
            (component, targets)
            for component, targets in unresolved_exit_candidates
            if targets & complete
        ]
        if not newly_valid:
            break
        for component, _ in newly_valid:
            valid_cycle_nodes.update(component)
        unresolved_exit_candidates = [
            candidate
            for candidate in unresolved_exit_candidates
            if candidate not in newly_valid
        ]

    for component in cyclic_components:
        if not component <= valid_cycle_nodes:
            _issue(
                issues,
                root,
                "bpm.cycle_without_condition",
                document.path,
                f"Cycle {sorted(component)!r} needs a continuation or complete exit path",
            )

    complete = _reverse_reachable(valid_outcomes | valid_cycle_nodes, reachable, adjacency)
    for node_id in sorted(reachable - complete):
        _issue(
            issues,
            root,
            "bpm.dead_end",
            document.path,
            f"Node {node_id!r} has no complete path to a valid outcome",
        )


def _node_successors(
    node: dict[str, Any], issues: list[Issue], root: Path, path: Path
) -> list[str]:
    raw_next = node.get("next")
    successors = (
        [target for target in raw_next if isinstance(target, str)]
        if isinstance(raw_next, list)
        else []
    )
    if node.get("type") != "gateway":
        if "routes" in node:
            _issue(
                issues,
                root,
                "bpm.invalid_routes",
                path,
                f"Non-gateway node {node.get('id')!r} cannot declare routes",
            )
        return successors
    routes = node.get("routes")
    complete_routes = (
        isinstance(routes, list)
        and bool(routes)
        and all(
            isinstance(route, dict)
            and _nonempty(route.get("condition"))
            and _nonempty(route.get("target"))
            for route in routes
        )
    )
    if not complete_routes or successors:
        _issue(
            issues,
            root,
            "bpm.incomplete_gateway",
            path,
            f"Gateway node {node.get('id')!r} needs conditioned routes",
        )
    gateway_successors: list[str] = []
    if isinstance(routes, list):
        gateway_successors.extend(
            route["target"]
            for route in routes
            if isinstance(route, dict) and isinstance(route.get("target"), str)
        )
    return gateway_successors


def _has_conditioned_route_within(
    node: dict[str, Any], component: set[str]
) -> bool:
    if node.get("type") != "gateway":
        return False
    routes = node.get("routes")
    return isinstance(routes, list) and any(
        isinstance(route, dict)
        and _nonempty(route.get("condition"))
        and route.get("target") in component
        for route in routes
    )


def _declared_exit_targets(
    node: dict[str, Any], successors: set[str], component: set[str]
) -> set[str]:
    targets: set[str] = set()
    if _nonempty(node.get("exit_condition")):
        targets.update(successors - component)
    routes = node.get("routes") if node.get("type") == "gateway" else None
    if isinstance(routes, list):
        targets.update(
            route["target"]
            for route in routes
            if isinstance(route, dict)
            and _nonempty(route.get("condition"))
            and isinstance(route.get("target"), str)
            and route["target"] not in component
        )
    return targets


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _reachable(entry: str, adjacency: dict[str, set[str]]) -> set[str]:
    if entry not in adjacency:
        return set()
    seen: set[str] = set()
    pending = [entry]
    while pending:
        node_id = pending.pop()
        if node_id in seen:
            continue
        seen.add(node_id)
        pending.extend(adjacency[node_id] - seen)
    return seen


def _reverse_reachable(
    starts: set[str], reachable: set[str], adjacency: dict[str, set[str]]
) -> set[str]:
    reverse: dict[str, set[str]] = defaultdict(set)
    for source in reachable:
        for target in adjacency[source] & reachable:
            reverse[target].add(source)
    seen = set(starts)
    pending = deque(starts)
    while pending:
        node_id = pending.popleft()
        for predecessor in reverse[node_id] - seen:
            seen.add(predecessor)
            pending.append(predecessor)
    return seen


def _strongly_connected_components(
    reachable: set[str], adjacency: dict[str, set[str]]
) -> list[set[str]]:
    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[set[str]] = []

    def visit(node_id: str) -> None:
        nonlocal index
        indices[node_id] = index
        lowlinks[node_id] = index
        index += 1
        stack.append(node_id)
        on_stack.add(node_id)
        for target in adjacency[node_id] & reachable:
            if target not in indices:
                visit(target)
                lowlinks[node_id] = min(lowlinks[node_id], lowlinks[target])
            elif target in on_stack:
                lowlinks[node_id] = min(lowlinks[node_id], indices[target])
        if lowlinks[node_id] != indices[node_id]:
            return
        component: set[str] = set()
        while True:
            target = stack.pop()
            on_stack.remove(target)
            component.add(target)
            if target == node_id:
                break
        components.append(component)

    for node_id in sorted(reachable):
        if node_id not in indices:
            visit(node_id)
    return components
