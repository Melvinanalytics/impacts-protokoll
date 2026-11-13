"""Read-only validation for the minimal file-native IMPACTS contract."""

from collections import deque
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import date, datetime
from importlib import resources
import json
import hashlib
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
from typing import Any, Callable, Iterable

from yaml import YAMLError
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .hashing import HashSurfaceError, _has_symlink_component, file_references, file_sha256
from .io import load_frontmatter_and_body, load_yaml_strict
from .topology import body_lines, check_topology
from .model import Issue, NotJudged, ValidationReport, derive_progress, judged_counts
from .version import protocol_line, protocol_release
from .generator import WORKSPACE_FOLDERS


SCHEMA_NAMES = (
    "leistung",
    "hauptprozess",
    "teilprozess",
    "arbeitsschritt",
    "vorgang",
)
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
# `$` as in the schema patterns: every reference the schema admits is resolved, none is skipped.
END_REF = re.compile(r"end:[a-z0-9]+(?:-[a-z0-9]+)*$")
GATE_RULE = "; freigabe and a gate route come only from the responsible human's decision"
GATE_FIX = (
    "; preserve decision evidence; correct serialization only against its evidenced source, "
    "otherwise obtain the missing or corrected decision from the responsible human; "
    "block dependent use and preserve completed history"
)


def _definition_slug(name: str) -> str | None:
    """Remove a hand-written display prefix; preserve the stable domain slug."""
    if re.match(r"[0-9]{2}-", name):
        name = name[3:]
    return name if SLUG.fullmatch(name) else None


@dataclass(frozen=True)
class Hauptprozess:
    root: Path
    hauptprozess: dict[str, Any]
    arbeitsschritte: dict[str, tuple[Path, dict[str, Any]]]


class SchemaRegistry:
    """Load the five packaged protocol schemas as one reference registry."""

    def __init__(self):
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
            )
            self._validators[schema_name] = validator
        return sorted(
            validator.iter_errors(document),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )

    def schemas(self) -> dict[str, dict[str, Any]]:
        """The packaged schemas by name, as copies for readers such as the view."""
        return deepcopy(self._load_schemas())

    def _load_schemas(self) -> dict[str, dict[str, Any]]:
        if self._schemas is not None:
            return self._schemas
        self._schemas = {
            name: json.loads(self._schema_text(name)) for name in SCHEMA_NAMES
        }
        return self._schemas

    def _schema_text(self, schema_name: str) -> str:
        filename = f"{schema_name}.schema.json"
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


def validate(root: Path, *, release: str | None = None) -> ValidationReport:
    """Validate a Workspace or Hauptprozess without changing files."""
    release = protocol_release() if release is None else release
    if protocol_line(release) is None:
        raise ValueError(f"Invalid validator release: {release!r}")
    not_judged: list[NotJudged] = []
    external_references: list[dict] = []
    judged = judged_counts()
    pin = None
    held: tuple[dict, ...] = ()
    superseded: tuple[str, ...] = ()
    root = Path(root)
    issues: list[Issue] = []
    if root.is_symlink():
        return ValidationReport(
            (Issue("structure.symlink", str(root), "Root directory is a symlink; use a regular directory"),), release=release
        )
    if not root.is_dir():
        return ValidationReport(
            (Issue("structure.level", str(root), "Root directory does not exist; supply an existing workspace or Hauptprozess"),), release=release
        )
    try:
        metadata = _load_context(root / "CONTEXT.md", root, issues)
        root_type = metadata.get("type") if metadata is not None else None
        if root_type == "workspace" and not set(metadata) <= {"type", "protocol"}:
            _add(
                issues,
                "routing.type",
                root / "CONTEXT.md",
                root,
                "Root router frontmatter must contain only type and protocol",
            )
        if root_type == "workspace":
            pin = metadata.get("protocol") if isinstance(metadata.get("protocol"), str) else None
            if "protocol" not in metadata:
                _add(issues, "schema.invalid", root / "CONTEXT.md", root,
                     f"protocol pin missing; add protocol: {release} to the frontmatter")
            elif protocol_line(metadata.get("protocol")) is None:
                _add(issues, "schema.invalid", root / "CONTEXT.md", root,
                     "Workspace protocol must be a release tag vMAJOR.MINOR.PATCH")
            elif protocol_line(metadata["protocol"]) != protocol_line(release):
                not_judged.append(NotJudged("CONTEXT.md", metadata["protocol"], release))
                return ValidationReport((), tuple(not_judged), release=release, pin=pin)
            if issues:
                return ValidationReport(_ordered(issues), release=release, pin=pin)
            topology_issues, held, forms = check_topology(
                root, SCHEMA_REGISTRY.schemas()["vorgang"]["$defs"]["freigabe"]["properties"]["by"]["pattern"])
            issues.extend(topology_issues)
            superseded = _validate_workspace(root, issues, not_judged, release, metadata["protocol"], external_references, judged, forms)
        elif root_type == "hauptprozess":
            _validate_hauptprozess(root, issues, judged=judged)
        elif metadata is not None:
            _add(issues, "routing.type", root / "CONTEXT.md", root, "Root type must be workspace or hauptprozess")
    except (OSError, RuntimeError) as error:
        _add(issues, "structure.level", root, root, f"Core tree cannot be read: {error}; restore read access to the workspace and its regular files")
    return ValidationReport(_ordered(issues), tuple(not_judged), superseded, len(external_references),
                            tuple({"vorgang": ref["vorgang"], "pointer": ref["pointer"]} for ref in external_references),
                            release, pin, judged, held)


def _declared_stores(body: str) -> set[str]:
    """Read column-zero Ablage declarations outside Markdown code fences."""
    return {match[1] for line in body_lines(body)
            if (match := re.match(r"Ablage:[ \t]+(\S+)", line))}


def _validate_workspace(root: Path, issues: list[Issue], not_judged: list[NotJudged], release: str, workspace_pin: str, external_references: list[dict], judged: dict[str, int], forms: dict[Path, str]) -> tuple[str, ...]:
    for folder in WORKSPACE_FOLDERS:
        path = root / folder
        if path.is_symlink():
            _add(issues, "structure.symlink", path, root, "Core folder is a symlink; replace it with a regular directory")
        elif path.exists() and not path.is_dir():
            _add(issues, "structure.level", path, root, "Workspace collection must be a directory")
    hauptprozesse = root / "hauptprozesse"
    if hauptprozesse.is_dir() and not hauptprozesse.is_symlink():
        identities: set[str] = set()
        for path in sorted(hauptprozesse.iterdir(), key=lambda item: item.name):
            if path.is_symlink():
                _add(issues, "structure.symlink", path, root, "Hauptprozess is a symlink; use a regular definition directory")
            elif path.is_dir():
                slug = _definition_slug(path.name)
                if slug is not None:
                    if slug in identities:
                        _add(issues, "structure.duplicate_id", path, root, f"Duplicate Hauptprozess ID: hauptprozess:{slug}; give each definition a unique ID matching its folder slug")
                    identities.add(slug)
                before = len(issues)
                _validate_hauptprozess(path, issues, judged=judged)
                prefix = path.relative_to(root)
                issues[before:] = [
                    replace(
                        issue,
                        path=(prefix if issue.path == "." else prefix / issue.path).as_posix(),
                    )
                    for issue in issues[before:]
                ]
            else:
                _add(issues, "structure.level", path, root, "hauptprozesse/ contains a non-directory")
    # Retain the historical depth-one not-judged inventory; topology scans all depths.
    for child in sorted(root.iterdir()):
        if forms.get(child) == "none" or child.name.startswith(".") or child.name in {"hauptprozesse", "vorgaenge"}:
            continue
        try:
            if child.is_symlink() or not child.is_dir():
                continue
            candidates = sorted(child.iterdir())
        except (OSError, ValueError) as error:
            _add(issues, "topology.shape", child, root, f"{child.relative_to(root).as_posix()} cannot be read: {error}; restore read access")
            continue
        for candidate in candidates:
            try:
                context = candidate / "CONTEXT.md"
                if candidate.name.startswith(".") or candidate.is_symlink() or not candidate.is_dir() or context.is_symlink() or not context.is_file():
                    continue
                document, _ = load_frontmatter_and_body(context, root)
                if isinstance(document, dict) and document.get("type") == "hauptprozess":
                    not_judged.append(NotJudged(context.relative_to(root).as_posix(),
                                               document.get("protocol") if isinstance(document.get("protocol"), str) else None, release,
                                               "definition tree outside hauptprozesse/, not bindable"))
            except (ValueError, YAMLError):
                continue
            except OSError as error:
                _add(issues, "topology.shape", candidate, root, f"{candidate.relative_to(root).as_posix()} cannot be read: {error}; restore read access")
    vorgaenge = root / "vorgaenge"
    # Definitions are immutable; Vorgang files and Git refs are rechecked on every call.
    definitions: dict[str, Hauptprozess | str] = {}
    successors: dict[str, Path] = {}
    reachable = _ReachableHauptprozesse(workspace=root)
    with ExitStack() as snapshots:
        if vorgaenge.is_dir() and not vorgaenge.is_symlink():
            for path in sorted(vorgaenge.iterdir(), key=lambda item: item.name):
                if path.is_symlink():
                    _add(issues, "structure.symlink", path, root, "Vorgang is a symlink; use a regular Vorgang directory")
                elif path.is_dir():
                    before = len(issues)
                    _validate_vorgang(path, root, issues, definitions, snapshots, reachable, not_judged, release, workspace_pin, successors, external_references, judged)
                    router = (path / "CONTEXT.md").relative_to(root).as_posix()
                    issues[before:] = [replace(issue, path=router, message=f"{issue.path}: {issue.message}")
                                       if issue.path != router else issue for issue in issues[before:]]
                else:
                    _add(issues, "structure.level", path, root, "Vorgaenge contains a non-directory")

    _, body = load_frontmatter_and_body(root / "CONTEXT.md", root)
    stores = _declared_stores(body)
    for reference in external_references:
        store = reference["ablage"]
        if isinstance(store, str) and store not in stores:
            _add(issues, "binding.reference_missing", root / reference["vorgang"], root,
                 f"{reference['pointer']}: external store {store!r} is undeclared; declare 'Ablage: {store} <location>' in the workspace root router")

    # Export the checked relation with the report; consumers must not reread mutable
    # successor metadata or independently decide whether it supersedes old work.
    if any(not issue.path.startswith(("vorgaenge/", "hauptprozesse/")) for issue in issues):
        return ()
    return tuple(sorted(predecessor for predecessor, successor in successors.items()
                        if not any(issue.path == successor.relative_to(root).as_posix()
                                   or issue.path.startswith(successor.relative_to(root).as_posix() + "/")
                                   for issue in issues)))


def _validate_hauptprozess(
    root: Path, issues: list[Issue], *, check_slug: bool = True, judged: dict[str, int] | None = None
) -> Hauptprozess | None:
    before = len(issues)
    if judged is not None:
        judged["hauptprozess"] += 1
    _reject_symlinks(root, root, issues)
    root_slug = _definition_slug(root.name)
    root_slug_valid = root_slug is not None
    if check_slug and not root_slug_valid:
        _add(issues, "structure.level", root, root, _slug_message("Hauptprozess"))
    process = _load_context(
        root / "CONTEXT.md",
        root,
        issues,
        kind="hauptprozess",
    )
    if process is None:
        return None
    process_id = process.get("id")
    if (
        check_slug
        and root_slug_valid
        and isinstance(process_id, str)
        and process_id != f"hauptprozess:{root_slug}"
    ):
        _add(issues, "structure.level", root, root, _definition_id_message("Hauptprozess", process_id, root_slug))
    part_dirs, complete_tree = _slug_children(root, root, issues, "Teilprozess")
    if check_slug and not root_slug_valid:
        complete_tree = False
    if not part_dirs and complete_tree:
        _add(issues, "structure.level", root, root, "Hauptprozess needs at least one Teilprozess")

    steps: dict[str, tuple[Path, dict[str, Any]]] = {}
    if process.get("type") != "hauptprozess":
        complete_tree = False
    part_ids: set[str] = set()
    for part_root in part_dirs:
        if judged is not None:
            judged["teilprozess"] += 1
        part = _load_context(
            part_root / "CONTEXT.md",
            root,
            issues,
            kind="teilprozess",
        )
        if part is None or part.get("type") != "teilprozess":
            complete_tree = False
        if (
            part is not None
            and _definition_slug(part_root.name) is not None
            and isinstance(part.get("id"), str)
            and part.get("id") != f"teilprozess:{_definition_slug(part_root.name)}"
        ):
            _add(issues, "structure.level", part_root, root, _definition_id_message("Teilprozess", part.get('id'), _definition_slug(part_root.name)))
            complete_tree = False
        if part is not None and isinstance(part.get("id"), str):
            if part["id"] in part_ids:
                _add(issues, "structure.duplicate_id", part_root, root, f"Duplicate Teilprozess ID: {part['id']}; give each definition a unique ID matching its folder slug")
                complete_tree = False
            part_ids.add(part["id"])
        step_dirs, part_complete = _slug_children(part_root, root, issues, "Arbeitsschritt")
        complete_tree = complete_tree and part_complete
        if not step_dirs and part_complete:
            _add(
                issues,
                "structure.level",
                part_root,
                root,
                "Teilprozess needs at least one Arbeitsschritt",
            )
        for step_root in step_dirs:
            if judged is not None:
                judged["arbeitsschritt"] += 1
            nested_dirs, step_complete = _slug_children(step_root, root, issues, "Arbeitsschritt")
            if nested_dirs:
                _add(issues, "structure.level", step_root, root, "Arbeitsschritt must not contain subfolders")
            if not step_complete or nested_dirs:
                complete_tree = False
            step = _load_context(
                step_root / "CONTEXT.md",
                root,
                issues,
                kind="arbeitsschritt",
                require_body=True,
            )
            if step is None:
                complete_tree = False
                continue
            _validate_local_workstep(step_root, step, root, issues)
            if step.get("type") != "arbeitsschritt" or not isinstance(step.get("id"), str):
                complete_tree = False
                continue
            step_id = step["id"]
            if _definition_slug(step_root.name) is not None and step_id != f"arbeitsschritt:{_definition_slug(step_root.name)}":
                _add(issues, "structure.level", step_root, root, _definition_id_message("Arbeitsschritt", step_id, _definition_slug(step_root.name)))
                complete_tree = False
            if step_id in steps:
                _add(issues, "structure.duplicate_id", step_root, root, f"Duplicate Arbeitsschritt ID: {step_id}; give each definition a unique ID matching its folder slug")
                complete_tree = False
            else:
                steps[step_id] = (step_root, step)

    hauptprozess = Hauptprozess(root, process, steps)
    if complete_tree:
        _validate_graph(hauptprozess, issues)
    if len(issues) > before and not steps:
        return None
    return hauptprozess


def _validate_graph(hauptprozess: Hauptprozess, issues: list[Issue]) -> None:
    root = hauptprozess.root
    steps = hauptprozess.arbeitsschritte
    entry = hauptprozess.hauptprozess.get("einstieg_ref")
    if not isinstance(entry, str) or entry not in steps:
        _add(issues, "reference.unresolved", root / "CONTEXT.md", root, "Hauptprozess entry does not resolve; set einstieg_ref to a declared Arbeitsschritt ID")
        return

    adjacency: dict[str, set[str]] = {step_id: set() for step_id in steps}
    direct_end: set[str] = set()
    ends: set[str] = set()
    uncertain_routes: set[str] = set()
    for step_id, (path, step) in steps.items():
        routes = step.get("routen")
        if not isinstance(routes, dict) or not routes:
            uncertain_routes.add(step_id)
            continue
        for target in routes.values():
            if not isinstance(target, str):
                uncertain_routes.add(step_id)
                continue
            if target.startswith("end:"):
                direct_end.add(step_id)
                ends.add(target)
            elif target in steps:
                adjacency[step_id].add(target)
            else:
                _add(issues, "reference.unresolved", path / "CONTEXT.md", root, f"Route target does not resolve: {target}; use a declared Arbeitsschritt ID in this Hauptprozess or an end:<slug>")
                uncertain_routes.add(step_id)

    leistung = hauptprozess.hauptprozess.get("leistung")
    achieved = leistung.get("erreicht") if isinstance(leistung, dict) else None
    if isinstance(achieved, list):
        for ref in sorted({r for r in achieved if isinstance(r, str) and END_REF.match(r)}):
            if ref not in ends:
                _add(issues, "reference.unresolved", root / "CONTEXT.md", root, f"Achieving end does not resolve: {ref}; name an end targeted by this Hauptprozess in leistung.erreicht")

    # Unknown edges could make any currently unreachable node reachable.
    if not uncertain_routes:
        reachable: set[str] = set()
        queue = deque([entry])
        while queue:
            step_id = queue.popleft()
            if step_id in reachable:
                continue
            reachable.add(step_id)
            queue.extend(adjacency.get(step_id, ()))
        for step_id in sorted(set(steps) - reachable):
            _add(issues, "process.unreachable", steps[step_id][0], root, f"Unreachable Arbeitsschritt: {step_id}; connect it through declared routen from einstieg_ref")

    predecessors: dict[str, set[str]] = {step_id: set() for step_id in steps}
    for step_id, targets in adjacency.items():
        for target in targets:
            predecessors[target].add(step_id)
    # A route whose target is unknown may lead to an end. Only nodes unable to
    # reach either an end or such uncertainty are provably without an end.
    can_end = direct_end | uncertain_routes
    queue = deque(can_end)
    while queue:
        for step_id in predecessors[queue.popleft()]:
            if step_id not in can_end:
                can_end.add(step_id)
                queue.append(step_id)
    for step_id in sorted(set(steps) - can_end):
        _add(issues, "process.no_end", steps[step_id][0], root, f"No reachable end from: {step_id}; declare a route path to an end:<slug>")


def _validate_local_workstep(
    path: Path, step: dict[str, Any], root: Path, issues: list[Issue]
) -> None:
    routes = step.get("routen")
    if step.get("gate") == "human" and isinstance(routes, dict) and set(routes) not in ({"freigegeben", "abgelehnt"}, {"entschieden"}):
        _add(
            issues,
            "process.gate",
            path / "CONTEXT.md",
            root,
            f"Human gate has route keys {sorted(routes)!r}; use freigegeben and abgelehnt routes, or one entschieden route",
        )


def _definition_id_message(label: str, identifier: str, slug: str) -> str:
    message = f"{label} ID must match folder slug: found {identifier!r}, expected {label.lower()}:{slug}"
    if re.match(r"[^:]+:[0-9]{2}-", identifier):
        message += "; a two-digit first segment is a display prefix; the ID must omit it"
    return message


def _slug_message(label: str) -> str:
    return (
        f"{label} folder slug must use lowercase ASCII letters and digits, "
        "with single hyphens between words; example: bestellung-ausloesen"
    )


def _validate_vorgang(
    vorgang_root: Path, workspace: Path, issues: list[Issue],
    definitions: dict[str, Hauptprozess | str], snapshots: ExitStack,
    reachable: "_ReachableHauptprozesse",
    not_judged: list[NotJudged], release: str, workspace_pin: str, successors: dict[str, Path],
    external_references: list[dict], judged: dict[str, int],
) -> None:
    judged["vorgang"] += 1
    document = _load_context(
        vorgang_root / "CONTEXT.md",
        workspace,
        issues,
    )
    if document is None:
        return
    recorded = document.get("protocol")
    if (protocol_line(recorded) is not None
            and tuple(map(int, protocol_line(recorded))) > tuple(map(int, protocol_line(workspace_pin)))):
        _add(issues, "binding.revision", vorgang_root / "CONTEXT.md", workspace,
             f"Vorgang release {recorded} is newer than workspace pin {workspace_pin}; judge it in a workspace pinned to at least that release")
    entries = document.get("laufpfad")
    legacy = isinstance(entries, list) and any(
        isinstance(entry, dict) and "eingabe_hash" in entry for entry in entries
    )
    if ("protocol" not in document and legacy) or (
        protocol_line(recorded) is not None and protocol_line(recorded) != protocol_line(release)
    ):
        judged["vorgang"] -= 1
        not_judged.append(NotJudged(
            (vorgang_root / "CONTEXT.md").relative_to(workspace).as_posix(), recorded, release
        ))
        return
    judged["versuch"] += len(entries) if isinstance(entries, list) else 0
    if isinstance(entries, list):
        external_references.extend(
            {"vorgang": (vorgang_root / "CONTEXT.md").relative_to(workspace).as_posix(),
             "pointer": f"/laufpfad/{i}/{field}/{j}", "ablage": reference["ablage"]}
            for i, entry in enumerate(entries) if isinstance(entry, dict)
            for field in ("gelesen", "geschrieben") if isinstance(entry.get(field), list)
            for j, reference in enumerate(entry[field]) if isinstance(reference, dict) and "ablage" in reference
        )
    if "protocol" not in document:
        _add(issues, "schema.invalid", vorgang_root / "CONTEXT.md", workspace, f"protocol pin missing; add protocol: {release} to the frontmatter")
        return
    predecessor = document.get("vorgaenger")
    if isinstance(predecessor, str):
        if predecessor in successors:
            _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace,
                 f"Predecessor already has a judged successor: {successors[predecessor].name}; reference the continuing Vorgang instead of creating a second successor")
        else:
            successors[predecessor] = vorgang_root
    _reject_symlinks(vorgang_root, workspace, issues)
    if document.get("type") != "vorgang":
        _add(issues, "routing.type", vorgang_root / "CONTEXT.md", workspace, "Router type must be vorgang")
    try:
        errors = SCHEMA_REGISTRY.errors("vorgang", document)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        _add(issues, "format.invalid", vorgang_root / "CONTEXT.md", workspace, str(error) + "; correct the reported text or YAML syntax")
    else:
        for message in _schema_diagnostics(errors):
            _add(issues, "schema.invalid", vorgang_root / "CONTEXT.md", workspace, message)
    if protocol_line(recorded) is None:
        return
    vorgang_id = document.get("id")
    if isinstance(vorgang_id, str) and vorgang_id != f"vorgang:{vorgang_root.name}":
        _add(issues, "structure.level", vorgang_root / "CONTEXT.md", workspace, f"Vorgang ID must match folder slug: found {vorgang_id!r}, expected vorgang:{vorgang_root.name}")
    hauptprozess = _resolve_hauptprozess(
        workspace, document.get("hauptprozess_revision"), vorgang_root, issues, definitions, snapshots, reachable
    )
    if hauptprozess is None:
        return
    entries = document.get("laufpfad")
    if not isinstance(entries, list) or not entries:
        _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, "Laufpfad must be non-empty")
        return
    entry_refs = {hauptprozess.hauptprozess.get("einstieg_ref")}
    if "vorgaenger" in document:
        entry_refs.add(_predecessor_position(document["vorgaenger"], vorgang_root, workspace, hauptprozess, issues, release))
    if not isinstance(entries[0], dict) or entries[0].get("arbeitsschritt_ref") not in entry_refs:
        _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, "Laufpfad starts outside permitted positions; start at Hauptprozess entry or the continuing predecessor position")

    seen_attempts: set[tuple[str, int]] = set()
    sequence: dict[str, int] = {}
    expected_attempts: set[tuple[str, int]] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, f"/laufpfad/{index}: attempt must be an object")
            continue
        step_id = entry.get("arbeitsschritt_ref")
        attempt_number = entry.get("nummer")
        prefix = f"/laufpfad/{index} ({step_id}, nummer {attempt_number}): "
        if not isinstance(step_id, str) or step_id not in hauptprozess.arbeitsschritte:
            _add(issues, "execution.unknown_step", vorgang_root / "CONTEXT.md", workspace, prefix + f"Unknown Arbeitsschritt: {step_id}; use an ID from the bound Hauptprozess")
            continue
        if not isinstance(attempt_number, int) or isinstance(attempt_number, bool) or attempt_number < 1:
            _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, prefix + "Versuch must be a positive integer")
            continue
        key = (step_id, attempt_number)
        if key in seen_attempts:
            _add(issues, "execution.attempt_duplicate", vorgang_root / "CONTEXT.md", workspace, prefix + f"Duplicate attempt: {key}; record each Arbeitsschritt and nummer pair once, preserving earlier bound work")
        elif attempt_number > 999:
            _add(issues, "execution.attempt_limit", vorgang_root / "CONTEXT.md", workspace, prefix + "Attempt limit is 999")
            continue
        elif attempt_number != sequence.get(step_id, 0) + 1:
            _add(issues, "execution.attempt_sequence", vorgang_root / "CONTEXT.md", workspace, prefix + "Numbers must start at 1 and rise by 1 per Arbeitsschritt")
        sequence[step_id] = attempt_number
        seen_attempts.add(key)
        attempt_root = (
            vorgang_root
            / step_id.removeprefix("arbeitsschritt:")
            / f"{attempt_number:03d}"
        )
        if (attempt_root.is_symlink() or (attempt_root.exists() and not attempt_root.is_dir())
                or (not attempt_root.exists() and entry.get("status") not in {"aktiv", "wartend"})):
            _add(issues, "execution.attempt", attempt_root, workspace, prefix + "Attempt directory is missing or unsafe; restore the regular directory and its required output files")
            continue
        if attempt_root.exists():
            expected_attempts.add((step_id.removeprefix("arbeitsschritt:"), attempt_number))

        step = hauptprozess.arbeitsschritte[step_id][1]
        status = entry.get("status")
        is_last = index == len(entries) - 1
        if status in ("aktiv", "wartend"):
            if not is_last:
                _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, prefix + f"{status} entry must be the last entry")
            forbidden = ("gewaehlte_route", "geschrieben", "wiedereinstieg") if status == "aktiv" else ("gewaehlte_route", "geschrieben")
            for field in forbidden:
                if field in entry and not (field == "geschrieben" and entry[field] == []):
                    _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, prefix + f"{status} entry must not carry {field}")
            if "freigabe" in entry:
                reason = (
                    "; it is recorded when the gate entry completes with the human's route; "
                    "leave a human-written freigabe unchanged and preserve decision evidence"
                    if step.get("gate") == "human" else f"; {step_id} declares no gate"
                )
                _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, prefix + f"{status} entry must not carry freigabe" + reason)
            if status == "wartend" and not isinstance(entry.get("wiedereinstieg"), dict):
                _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, prefix + "wartend entry needs wiedereinstieg with ausloeser and continuation_ref")
        elif status == "abgebrochen":
            if not is_last or any(field in entry for field in ("gewaehlte_route", "wiedereinstieg")):
                _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace,
                     prefix + "abgebrochen must be last and carry no route or wiedereinstieg")
            problem = _approval_problem(entry.get("freigabe"))
            if problem:
                _add(issues, "trust.invalid", vorgang_root / "CONTEXT.md", workspace, prefix + problem)
            if not entry.get("geschrieben"):
                _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace,
                     prefix + "abgebrochen needs geschrieben with the recorded owner's decision")
        elif status == "abgeschlossen":
            _validate_completed_entry(
                entry,
                step,
                entries,
                index,
                vorgang_root,
                workspace,
                issues,
                prefix,
            )
        else:
            _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, prefix + f"Unknown attempt status: {status}; use aktiv, wartend, abgeschlossen or abgebrochen")
        # The schema pattern admits impossible dates such as February 31; parsing rejects them.
        resume = entry.get("wiedereinstieg")
        if status == "wartend" and isinstance(resume, dict) and isinstance(resume.get("continuation_ref"), str):
            relative = resume["continuation_ref"]
            path = workspace / relative
            if (Path(relative).is_absolute() or "\\" in relative
                    or any(part in {"", ".", ".."} for part in relative.split("/"))
                    or ":" in relative.split("/")[0]):
                _add(issues, "binding.reference_missing", vorgang_root / "CONTEXT.md", workspace,
                     prefix + f"continuation_ref {relative!r} has invalid spelling; use a workspace-relative file path without traversal")
            elif _has_symlink_component(path, workspace):
                _add(issues, "structure.symlink", path, workspace, prefix + "continuation_ref contains a symlink; reference a regular workspace file without symlink components")
            elif not path.is_file():
                _add(issues, "binding.reference_missing", path, workspace,
                     prefix + "continuation_ref has no regular working-tree file; supply the recorded continuation evidence at that path")
        for label, value in (("status_seit", entry.get("status_seit")),
                             ("wiedereinstieg.faellig", resume.get("faellig") if isinstance(resume, dict) else None)):
            if isinstance(value, str):
                try:
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace,
                         prefix + f"{label} must be a real calendar timestamp with offset; found {value!r}")

        if step.get("eingaben") and isinstance(entry.get("gelesen"), list):
            for error in Draft202012Validator({"minItems": 1}).iter_errors(entry["gelesen"]):
                _add(issues, "schema.invalid", vorgang_root / "CONTEXT.md", workspace,
                     prefix + f"gelesen: {error.message} (minItems: 1 for declared eingaben); cover slots {step['eingaben']!r} with gelesen references naming eingabe and their pfad, revision and sha256")
        if isinstance(step.get("eingaben"), list) and isinstance(entry.get("gelesen"), list) and entry["gelesen"]:
            covered = set()
            for reference in entry["gelesen"]:
                if not isinstance(reference, dict):
                    continue
                slot = reference.get("eingabe", reference.get("pfad"))
                if "eingabe" in reference and slot not in step["eingaben"]:
                    _add(issues, "binding.reference_missing", vorgang_root / "CONTEXT.md", workspace,
                         prefix + f"Unknown eingaben slot: {slot}; use one of {step['eingaben']!r}")
                for declared in step["eingaben"]:
                    if isinstance(slot, str) and (slot == declared or ("eingabe" not in reference and slot.startswith(declared.rstrip("/") + "/"))):
                        covered.add(declared)
            for missing in sorted(set(step["eingaben"]) - covered):
                _add(issues, "binding.reference_missing", vorgang_root / "CONTEXT.md", workspace,
                     prefix + f"gelesen does not cover eingaben slot: {missing}; add one gelesen reference with eingabe {missing!r} and its pfad, revision and sha256")
        for reference in entry.get("gelesen", []) if isinstance(entry.get("gelesen"), list) else []:
            _validate_reference(reference, workspace, vorgang_root, issues, prefix, entries[:index], reachable=reachable)
        if status in ("abgeschlossen", "abgebrochen"):
            written = entry.get("geschrieben")
            if status == "abgeschlossen" and not isinstance(written, list) and isinstance(step.get("ausgaben"), list):
                try:
                    file_references(attempt_root, step["ausgaben"])
                except HashSurfaceError as error:
                    _add(issues, error.code, error.path, workspace, prefix + error.message + "; restore the declared regular output files, preserving completed history")
            for reference in written if isinstance(written, list) else []:
                _validate_reference(reference, workspace, vorgang_root, issues, prefix, output_root=attempt_root / "output")
            if isinstance(written, list):
                try:
                    declared = step.get("ausgaben")
                    if status == "abgeschlossen" and isinstance(declared, list) and all(isinstance(name, str) for name in declared):
                        file_references(attempt_root, declared)
                    actual = {item["pfad"] for item in file_references(workspace, [(attempt_root / "output").relative_to(workspace).as_posix()])}
                except HashSurfaceError as error:
                    _add(issues, error.code, error.path, workspace, prefix + error.message + "; restore the declared regular output files, preserving completed history")
                else:
                    recorded_paths = {item.get("pfad") for item in written if isinstance(item, dict) and isinstance(item.get("pfad"), str)}
                    if actual != recorded_paths:
                        _add(issues, "binding.reference_missing", attempt_root, workspace, prefix + "geschrieben must list every output file exactly once")
                    elif len(written) != len(recorded_paths):
                        _add(issues, "execution.attempt", attempt_root, workspace, prefix + "Duplicate output reference; list each output file exactly once in geschrieben")

    actual_attempts = _attempt_directories(vorgang_root, workspace, issues)
    for slug, number in sorted(actual_attempts ^ expected_attempts):
        _add(
            issues,
            "execution.attempt",
            vorgang_root / slug / f"{number:03d}",
            workspace,
            "Attempt directory and Laufpfad differ; retain only attempts recorded in laufpfad",
        )


def _validate_completed_entry(
    entry: dict[str, Any],
    step: dict[str, Any],
    entries: list[Any],
    index: int,
    vorgang_root: Path,
    workspace: Path,
    issues: list[Issue],
    prefix: str,
) -> None:
    if "wiedereinstieg" in entry:
        _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, prefix + "abgeschlossen entry must not carry wiedereinstieg")
    route = entry.get("gewaehlte_route")
    routes = step.get("routen")
    target = None
    if not isinstance(routes, dict):
        _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, prefix + f"{step.get('id')} declares no routen")
    elif not isinstance(route, str) or route not in routes:
        message = f"gewaehlte_route {route!r} is not a "
        if step.get("gate") == "human":
            message += "gate route" + GATE_RULE + GATE_FIX
        else:
            message += f"routen key of {step.get('id')}; record the key that the actual pruefung result selects, one of {sorted(routes)}"
        _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, prefix + message)
    else:
        progress = derive_progress([entry], {**{t: {} for t in routes.values() if t.startswith("arbeitsschritt:")}, step["id"]: step}, {})
        target = progress["ended"] or progress["current"]
    if not isinstance(entry.get("geschrieben"), list):
        _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, prefix + "geschrieben missing or invalid; record every output file")
    is_last = index == len(entries) - 1
    if isinstance(target, str) and target.startswith("arbeitsschritt:"):
        next_ref = entries[index + 1].get("arbeitsschritt_ref") if not is_last and isinstance(entries[index + 1], dict) else None
        if not is_last and next_ref != target:
            _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, prefix + f"route {route!r} leads to {target}, but the next entry is {next_ref or 'missing'}")
    elif isinstance(target, str) and target.startswith("end:") and not is_last:
        _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, prefix + f"route {route!r} ends the Vorgang at {target}, but the Laufpfad continues")

    approval = entry.get("freigabe")
    if step.get("gate") == "human":
        problem = _approval_problem(approval)
        if problem is not None:
            _add(issues, "trust.invalid", vorgang_root / "CONTEXT.md", workspace, prefix + problem)
    elif approval is not None:
        _add(issues, "trust.invalid", vorgang_root / "CONTEXT.md", workspace, prefix + f"freigabe is allowed only on a gate: human Arbeitsschritt; {step.get('id')} declares no gate")


def _approval_problem(value: Any) -> str | None:
    if value is None:
        return "freigabe missing" + GATE_RULE + "; keep the dependent transition unresolved until they decide" + GATE_FIX
    if not isinstance(value, dict) or set(value) != {"by", "at"}:
        return f"freigabe must contain exactly by and at; found {value!r}" + GATE_FIX
    actor, timestamp = value.get("by"), value.get("at")
    if not isinstance(actor, str) or not actor.startswith("human:") or not actor.removeprefix("human:").strip():
        return f"freigabe.by must be human:<id>; found {actor!r}" + GATE_FIX
    if not isinstance(timestamp, str):
        # The schema already diagnoses this type; actor/key defects above are independent.
        return None
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return f"freigabe.at must be a valid timestamp with offset; found {timestamp!r}" + GATE_FIX
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return f"freigabe.at must include a timezone offset; found {timestamp!r}" + GATE_FIX
    return None


def _resolve_hauptprozess(
    workspace: Path,
    revision: Any,
    vorgang_root: Path,
    issues: list[Issue],
    definitions: dict[str, Hauptprozess | str],
    snapshots: ExitStack,
    reachable: "_ReachableHauptprozesse",
) -> Hauptprozess | None:
    if not isinstance(revision, str) or re.fullmatch(r"git-tree:(?:[0-9a-f]{40}|[0-9a-f]{64})", revision) is None:
        _add(issues, "binding.revision", vorgang_root / "CONTEXT.md", workspace, "Hauptprozess revision is invalid; set hauptprozess_revision to git-tree:<full tree OID>")
        return None

    def reject(message: str) -> None:
        definitions[revision] = message
        _add(issues, "binding.revision", vorgang_root / "CONTEXT.md", workspace, message)

    cached = definitions.get(revision)
    if isinstance(cached, Hauptprozess):
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
        reject("Hauptprozess tree is missing or unreachable; restore its history under hauptprozesse/ in a reachable commit")
        return None
    # Keep the paths in Hauptprozess alive until all dependent Vorgänge were checked.
    target = Path(snapshots.enter_context(TemporaryDirectory(prefix="impacts-hauptprozess-")))
    if not _materialize_tree(workspace, oid, target):
        reject("Hauptprozess tree is unreadable or contains an unsafe entry")
        return None
    nested: list[Issue] = []
    hauptprozess = _validate_hauptprozess(target, nested, check_slug=False)
    if hauptprozess is None or nested:
        details = "; ".join(
            f"{issue.path}: {issue.code}: {issue.message}" for issue in _ordered(nested)
        )
        message = (
            f"Hauptprozess {revision} does not satisfy the Core contract; "
            "preserve existing historical bindings and use a corrected Hauptprozess tree for a new Vorgang"
        )
        reject(f"{message}: {details}" if details else message)
        return None
    slug = hauptprozess.hauptprozess["id"].removeprefix("hauptprozess:")
    if not reachable.contains(oid, slug):
        reject("Hauptprozess tree is missing or unreachable at its declared slug")
        return None
    definitions[revision] = hauptprozess
    return hauptprozess


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
            if header == oid.encode("ascii") + b" missing\n":
                return None
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
    *, skip_unreadable: bool = False,
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
        if item is None and skip_unreadable and not batch.failed:
            count += 1
            continue
        if item is not None and item[0] != kind and skip_unreadable:
            count += 1
            continue
        if item is None or item[0] != kind:
            batch.failed = True
            break
        values = extract(oid, item[1])
        if values is None and skip_unreadable:
            count += 1
            continue
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


class _ReachableHauptprozesse:
    """Per-validation map from reachable commits to hauptprozesse/<slug> trees."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.index: set[tuple[str, str]] | None = None
        self.commits: set[str] = set()

    def contains(self, oid: str, slug: str) -> bool:
        if self.index is None:
            self.index = self._build()
        return (oid, slug) in self.index

    def contains_commit(self, oid: str) -> bool:
        if self.index is None:
            self.index = self._build()
        return oid in self.commits

    def _build(self) -> set[tuple[str, str]]:
        # Ordinary retained history excludes stash/auxiliary refs. Detached HEAD
        # remains a root; an unborn HEAD must not hide retained branch/tag history.
        head = _git(self.workspace, "rev-parse", "--verify", "HEAD^{commit}")
        head_root = (head,) if head is not None else ()
        roots_text = _git(
            self.workspace, "rev-list", "--branches", "--tags", "--remotes",
            *head_root, "--format=%H %T", "--no-commit-header", "--",
        )
        if roots_text is None:
            return set()
        pairs = [line.split() for line in roots_text.splitlines()]
        if any(len(pair) != 2 or any(re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", oid) is None for oid in pair) for pair in pairs):
            return set()
        self.commits = {commit for commit, _ in pairs}
        roots = {tree for _, tree in pairs}

        def hauptprozess_tree(root_oid: str, content: bytes) -> list[str] | None:
            entries = _tree_entries(content, len(root_oid) // 2)
            if entries is None:
                return None
            return [
                entry_oid for mode, name, entry_oid in entries
                if mode in {b"40000", b"040000"} and name == b"hauptprozesse"
            ]

        hauptprozesse = _batch_collect(
            self.workspace, roots, "tree", hauptprozess_tree, skip_unreadable=True,
        )
        if hauptprozesse is None:
            return set()

        def hauptprozess_entries(app_oid: str, content: bytes) -> list[tuple[str, str]] | None:
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
                    if (stable_slug := _definition_slug(slug)) is not None:
                        found.append((tree_oid, stable_slug))
            return found

        return _batch_collect(
            self.workspace, hauptprozesse, "tree", hauptprozess_entries, skip_unreadable=True,
        ) or set()


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


def _predecessor_position(value, vorgang_root, workspace, hauptprozess, issues, release):
    """Read position only, including legacy records; never judge their attempts."""
    path = workspace / value if isinstance(value, str) else workspace
    if (not isinstance(value, str) or re.fullmatch(r"vorgaenge/[a-z0-9]+(?:-[a-z0-9]+)*/CONTEXT\.md", value) is None
            or path == vorgang_root / "CONTEXT.md" or not path.is_file() or _has_symlink_component(path, workspace)):
        _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, "Invalid vorgaenger path; reference another existing vorgaenge/<slug>/CONTEXT.md without symlinks")
        return None
    try:
        predecessor, _ = load_frontmatter_and_body(path, workspace)
        last = predecessor["laufpfad"][-1]
        step_id = last["arbeitsschritt_ref"]
        if predecessor.get("type") != "vorgang" or step_id not in hauptprozess.arbeitsschritte:
            raise ValueError("Predecessor position is outside the bound Hauptprozess")
        if last.get("status") == "abgeschlossen":
            # Read the predecessor's own route without judging its old contract.
            revision = predecessor.get("hauptprozess_revision", "")
            if not revision and protocol_line(predecessor.get("protocol")) != protocol_line(release):
                # Read retained pre-v0.4 evidence; this is not a v0.4 binding alias.
                revision = predecessor.get("application_revision", "")
            if not isinstance(revision, str) or re.fullmatch(r"git-tree:(?:[0-9a-f]{40}|[0-9a-f]{64})", revision) is None:
                raise ValueError("Predecessor has no readable definition revision")
            tree = revision.removeprefix("git-tree:")
            listing = _git(workspace, "ls-tree", "-rz", tree, binary=True)
            routes = []
            for item in (listing or b"").split(b"\0"):
                metadata, _, name = item.partition(b"\t")
                if metadata.startswith((b"100644 blob ", b"100755 blob ")) and name.endswith(b"/CONTEXT.md"):
                    content = _git(workspace, "cat-file", "blob", f"{tree}:{name.decode('utf-8')}", binary=True)
                    parts = content.decode("utf-8-sig").split("---", 2) if content else []
                    step = load_yaml_strict(parts[1]) if len(parts) == 3 else None
                    if isinstance(step, dict) and step.get("id") == step_id:
                        route_table = step.get("routen")
                        routes.append(route_table.get(last.get("gewaehlte_route")) if isinstance(route_table, dict) else None)
            if len(routes) != 1:
                raise ValueError("Predecessor route does not resolve uniquely")
            step_id = derive_progress(
                [last], {**{ref: {} for ref in hauptprozess.arbeitsschritte},
                         step_id: {"routen": {last.get("gewaehlte_route"): routes[0]}}}, {}
            )["current"]
        elif last.get("status") == "abgebrochen":
            raise ValueError("Predecessor has no continuing Arbeitsschritt")
        elif last.get("status") not in {"aktiv", "wartend"}:
            raise ValueError("Predecessor status is invalid")
        if step_id not in hauptprozess.arbeitsschritte:
            raise ValueError("Predecessor has no continuing Arbeitsschritt")
        return step_id
    except (OSError, ValueError, KeyError, IndexError, TypeError, YAMLError) as error:
        _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, f"Cannot resolve vorgaenger: {error}; reference an existing predecessor with a continuing position in the bound Hauptprozess")
        return None


def _validate_reference(reference, workspace, vorgang_root, issues, prefix, prior=(), output_root=None, reachable=None):
    if not isinstance(reference, dict):
        return  # Schema owns malformed reference shapes.
    if "ablage" in reference:
        key = reference.get("schluessel")
        if isinstance(key, str) and not Path(key).is_absolute():
            try:
                target = (workspace / key).resolve()
                local_file = target.is_relative_to(workspace.resolve()) and target.is_file()
            except (OSError, ValueError, RuntimeError):
                local_file = False  # Opaque store keys need not be filesystem paths.
            if local_file:
                _add(issues, "binding.reference_missing", vorgang_root / "CONTEXT.md", workspace,
                     prefix + f"External-store key {key!r} resolves to a working-tree file; use a file reference")
        if output_root is not None:
            _add(issues, "execution.attempt", vorgang_root / "CONTEXT.md", workspace, prefix + "geschrieben needs a working-tree output reference")
        return  # External store digest verification belongs to the harness.
    relative, expected = reference.get("pfad"), reference.get("sha256")
    if not isinstance(relative, str) or not isinstance(expected, str):
        return
    path = workspace / relative
    if (Path(relative).is_absolute() or "\\" in relative or any(part in {"", ".", ".."} for part in relative.split("/")) or ":" in relative.split("/")[0]):
        _add(issues, "binding.reference_missing", vorgang_root / "CONTEXT.md", workspace, prefix + f"Reference path {relative!r} is outside the permitted spelling; use a workspace-relative path without traversal")
        return
    revision = reference.get("revision")
    output_match = re.fullmatch(r"vorgaenge/([a-z0-9]+(?:-[a-z0-9]+)*)/([a-z0-9]+(?:-[a-z0-9]+)*)/([0-9]{3})/output/(.+)", relative)
    try:
        if revision is not None:
            if output_match is not None:
                raise ValueError("Attempt output references must read working-tree bytes without revision")
            if output_root is not None:
                raise ValueError("geschrieben needs a working-tree output reference")
            if not isinstance(revision, str) or re.fullmatch(r"git-commit:(?:[0-9a-f]{40}|[0-9a-f]{64})", revision) is None:
                return
            commit = revision.removeprefix("git-commit:")
            if _git(workspace, "cat-file", "-t", commit) != "commit":
                raise ValueError("Reference commit is missing")
            if reachable is not None and not reachable.contains_commit(commit):
                raise ValueError("Reference commit is unreachable")
            # A recursive exact-path lookup cannot traverse a symlink or submodule.
            listing = _git(workspace, "ls-tree", "-rz", commit, "--", relative, binary=True)
            if (not listing or not listing.startswith((b"100644 blob ", b"100755 blob "))
                    or listing.partition(b"\t")[2] != relative.encode("utf-8") + b"\0"):
                raise ValueError("Reference blob is missing or unsafe")
            content = _git(workspace, "cat-file", "blob", f"{commit}:{relative}", binary=True)
            if content is None:
                raise ValueError("Reference blob is missing")
            actual = "sha256:" + hashlib.sha256(content).hexdigest()
        else:
            if _has_symlink_component(path, workspace):
                _add(issues, "structure.symlink", path, workspace, prefix + "Reference contains a symlink; reference a regular file without symlink components")
                return
            if output_root is not None:
                path.relative_to(output_root)
            else:
                if output_match is None:
                    raise ValueError("Unversioned reference must name an attempt output")
                producer_name, slug, number, _ = output_match.groups()
                if producer_name == vorgang_root.name:
                    producers = prior
                else:
                    context = workspace / "vorgaenge" / producer_name / "CONTEXT.md"
                    if not context.is_file() or _has_symlink_component(context, workspace):
                        raise ValueError("Reference producer router is unsafe")
                    producer, _ = load_frontmatter_and_body(context, workspace)
                    if producer.get("type") != "vorgang":
                        raise ValueError("Reference producer must be a Vorgang")
                    producers = producer.get("laufpfad", [])
                    if not isinstance(producers, list):
                        raise ValueError("Reference producer has no Laufpfad")
                if not any(isinstance(item, dict) and item.get("arbeitsschritt_ref") == f"arbeitsschritt:{slug}"
                           and item.get("nummer", item.get("versuch")) == int(number) and item.get("status") == "abgeschlossen" for item in producers):
                    raise ValueError("Reference producer must be a preceding completed attempt")
            if not path.is_file():
                raise ValueError("Reference has no regular file")
            actual = file_sha256(path)
        if actual != expected:
            _add(issues, "binding.reference_digest", path, workspace, prefix + "Reference digest does not match file bytes; restore the bound bytes or record an authorized new revision without rewriting completed history")
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as error:
        _add(issues, "binding.reference_missing", path, workspace, prefix + f"Reference cannot be read: {error}; restore the declared file and reachable revision, preserving bound history")


def _attempt_directories(
    vorgang_root: Path, workspace: Path, issues: list[Issue]
) -> set[tuple[str, int]]:
    result: set[tuple[str, int]] = set()
    for step_root in vorgang_root.iterdir():
        if step_root.name == "CONTEXT.md":
            continue
        if step_root.name == "_quellen" and step_root.is_dir() and not step_root.is_symlink():
            for capture in step_root.iterdir():
                if not capture.is_file() or capture.is_symlink():
                    _add(issues, "execution.attempt", capture, workspace,
                         "_quellen must be flat and contain only capture and provenance files")
            continue
        if step_root.name.startswith("_"):
            _add(issues, "execution.attempt", step_root, workspace,
                 "Only _quellen is permitted as an underscore-prefixed Vorgang child")
            continue
        if not step_root.is_dir() or step_root.is_symlink() or SLUG.fullmatch(step_root.name) is None:
            message = _slug_message("Arbeitsschritt") if SLUG.fullmatch(step_root.name) is None else "Invalid Arbeitsschritt directory in the Vorgang; use a regular slug directory for a recorded Arbeitsschritt"
            _add(issues, "execution.attempt", step_root, workspace, message)
            continue
        attempts = list(step_root.iterdir())
        if not attempts:
            _add(issues, "execution.attempt", step_root, workspace, "Unreached Arbeitsschritt directory in the Vorgang; keep only directories for recorded attempts")
        for attempt in attempts:
            if not attempt.is_dir() or attempt.is_symlink() or re.fullmatch(r"[0-9]{3}", attempt.name) is None or int(attempt.name) < 1:
                _add(issues, "execution.attempt", attempt, workspace, "Attempt directory must be a positive three-digit number")
                continue
            for child in attempt.iterdir():
                if child.name != "output" or not child.is_dir() or child.is_symlink():
                    _add(issues, "structure.attempt_child", child, workspace, "Attempt holds only output/")
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
        _add(issues, "structure.symlink", path, root, "Router is a symlink; restore a regular CONTEXT.md file")
        return None
    if not path.is_file():
        message = "Required CONTEXT.md is missing; add the router at this path"
        if kind is None and path == root / "CONTEXT.md":
            message += "; validate a workspace root or a Hauptprozess folder hauptprozesse/<slug>"
        _add(issues, "routing.missing", path, root, message)
        return None
    try:
        metadata, body = load_frontmatter_and_body(path, root)
    except ValueError as error:
        _add(issues, "format.invalid", path, root, str(error) + "; correct the reported text or YAML syntax")
        return None
    if kind is not None and not metadata:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        if not lines or lines[0].strip() != "---":
            _add(issues, "format.invalid", path, root, "line 1: frontmatter must open with --- on line 1; move any text above it into the body")
            return None
    if kind is not None and "type" in metadata and metadata["type"] != kind:
        _add(issues, "routing.type", path, root, f"Router type must be {kind}; found {metadata['type']!r}; correct type in this frontmatter")
    if require_body and not body.strip():
        _add(issues, "routing.missing", path, root, "Arbeitsschritt processing body is missing; add the declared processing instructions after frontmatter")
    if kind is not None:
        try:
            errors = SCHEMA_REGISTRY.errors(kind, metadata)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            _add(issues, "format.invalid", path, root, str(error) + "; correct the reported text or YAML syntax")
        else:
            for message in _schema_diagnostics(errors):
                _add(issues, "schema.invalid", path, root, message)
    return metadata


def _schema_diagnostics(errors: Iterable[Any]) -> tuple[str, ...]:
    """Format useful schema errors, keeping one primary type error per location."""
    ordered = sorted(
        errors,
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            0 if error.validator == "type" else 1,
            tuple(str(part) for part in error.absolute_schema_path),
        ),
    )
    type_paths = {
        tuple(error.absolute_path) for error in ordered if error.validator == "type"
    }
    seen_type_paths: set[tuple[Any, ...]] = set()
    messages: list[str] = []
    for error in ordered:
        instance_path = tuple(error.absolute_path)
        if error.validator == "type":
            if instance_path in seen_type_paths:
                continue
            seen_type_paths.add(instance_path)
        elif instance_path in type_paths:
            # Other keywords at exactly this malformed value do not add a
            # repair action; errors on sibling values remain reportable.
            continue

        pointer = "/" + "/".join(
            str(part).replace("~", "~0").replace("/", "~1")
            for part in error.absolute_path
        )
        message = f"{pointer}: {error.message}" if error.absolute_path else error.message
        if error.validator == "type" and error.validator_value == "string" and isinstance(error.instance, (bool, int, float, date)):
            native_type = type(error.instance).__name__
            found = f" ({error.instance.isoformat()})" if isinstance(error.instance, date) else f" (found {error.instance!r})"
            message = (
                f"{pointer}: YAML read this value as {native_type}{found}; supply a string type "
                "(quote plain scalar text and remove an explicit non-string tag if present)"
            )
            if "freigabe" in error.absolute_path:
                message += GATE_RULE + GATE_FIX
        if error.validator == "required" and isinstance(error.instance, dict):
            missing = [
                field for field in error.validator_value if field not in error.instance
            ]
            if missing:
                fields = ", ".join(f"`{field}`" for field in missing)
                message += f"; add {fields} to this frontmatter mapping"
        messages.append(message)
    return tuple(messages)


def _slug_children(
    path: Path, root: Path, issues: list[Issue], label: str
) -> tuple[list[Path], bool]:
    """Return slug-named child folders and whether their enumeration is complete."""
    if _has_symlink_component(path, root) or not path.is_dir():
        return [], False
    children: list[Path] = []
    complete = True
    try:
        entries = sorted(path.iterdir(), key=lambda item: item.name)
    except OSError as error:
        _add(issues, "structure.level", path, root, f"Cannot enumerate {label} folders: {error}; restore read access to the definition directory")
        return [], False
    for child in entries:
        if child.is_symlink():
            _add(issues, "structure.symlink", child, root, f"{label} is a symlink; use a regular definition directory")
            complete = False
        elif child.name == "CONTEXT.md":
            if not child.is_file():
                _add(issues, "structure.level", child, root, "CONTEXT.md must be a file")
                complete = False
        elif child.is_dir():
            if _definition_slug(child.name) is None:
                _add(issues, "structure.level", child, root, _slug_message(label))
                complete = False
            # Keep the readable directory in the walk so independent local
            # checks can still run; its invalid name prevents graph inference.
            children.append(child)
        else:
            _add(issues, "structure.level", child, root, "Unknown Hauptprozess entry; keep only CONTEXT.md and the declared definition directories")
    return children, complete


def _reject_symlinks(path: Path, root: Path, issues: list[Issue]) -> None:
    if path.is_symlink():
        _add(issues, "structure.symlink", path, root, "Hauptprozess root is a symlink; use a regular definition directory")
        return
    for child in path.rglob("*"):
        if child.is_symlink():
            _add(issues, "structure.symlink", child, root, "Core tree contains a symlink; replace it with the required regular file or directory")


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
