#!/usr/bin/env python3
"""Walk one synthetic Vorgang and prove local, non-Core evidence chains."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unicodedata

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from impacts_protocol import init_workspace, validate
from impacts_protocol.model import derive_progress
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reference_files import input_file, source_home, references as file_references, content_digest as _content_digest, git as _git
from impacts_protocol.io import (
    DuplicateKeyError,
    load_frontmatter,
    load_yaml_strict,
)
from impacts_protocol.validator import SchemaRegistry, _approval_problem

BEISPIEL_ROOT = Path(__file__).resolve().parent / "beispiel"
BEISPIEL = BEISPIEL_ROOT / "hauptprozesse" / "prueffall"
CAPABILITY = BEISPIEL_ROOT / "capabilities" / "vollstaendigkeitsgrad"
GRUNDLAGEN = BEISPIEL_ROOT / "grundlagen"
HUMAN_DECISION = BEISPIEL_ROOT / "fixtures" / "human-decision-final.yaml"
GATE_REVISION = BEISPIEL_ROOT / "fixtures" / "gate-final-rejection.md"
HAUPTPROZESS = "prueffall"
VORGANG = "prueffall-001"
CALL_STEP = "vorpruefung/pruefen/CONTEXT.md"
DECISION_STEP = "entscheidung/entscheiden/CONTEXT.md"
CAPABILITY_MARKER = "{{CAPABILITY_TREE_OID}}"
SOURCE_REVISION_MARKER = "{{SOURCE_REVISION}}"

EXPECTED_PROOFS = frozenset(
    {
        "hauptprozess.handoff_mapping_drives_origin",
        "hauptprozess.source_requirement_drives_resolution",
        "capability.hauptprozess_tuple_executed",
        "capability.old_revision_replayed",
        "capability.path_resolved_at_workspace_revision",
        "source.bound_snapshot",
        "source.dirty_worktree_ignored",
        "handoff.content_and_origin_bound",
        "gate.failed_preflight_left_run_unchanged",
        "gate.open_has_no_decision",
        "gate.external_decision_fixture_consumed",
        "import.capability_materialized_and_executed",
        "wait.permitted_draft_preserves_current_state",
        "wait.resume_binds_new_attempt_inputs",
    }
)
EXPECTED_REJECTIONS = frozenset(
    {
        "loop.missing_bound",
        "handoff.old_label",
        "handoff.undeclared_slot",
        "capability.unbound_valid_tree",
        "capability.wrong_path",
        "capability.wrong_operation",
        "import.missing_capability",
        "source.wrong_digest",
        "source.wrong_control",
        "source.wrong_revision",
        "source.wrong_existing_path",
        "handoff.changed_consumer_bytes",
        "handoff.wrong_digest",
        "handoff.wrong_attempt",
        "handoff.wrong_producer_file",
        "handoff.useless_control_evidence",
        "wait.changed_bound_input",
        "wait.concurrent_laufpfad_entry",
        "wait.missing_response",
        "wait.response_mismatch",
        "wait.stale_draft_overwrite",
        "wait.unsafe_response_path",
    }
)


class ProofError(ValueError):
    """A local Cold-Walk evidence claim is false or incomplete."""


class FixtureInputError(ValueError):
    """A declared Cold-Walk input cannot be read or parsed."""


@dataclass(frozen=True)
class State:
    label: str
    valid: bool
    codes: tuple[str, ...]


@dataclass(frozen=True)
class CapabilityCall:
    call_id: str
    path: str
    tree_oid: str
    operation: str


@dataclass(frozen=True)
class SourceRef:
    input_path: str
    source: str
    path: str
    revision: str
    minimum_control: str

    @property
    def provenance_input(self) -> str:
        path = Path(self.input_path)
        return (path.parent / f"{path.stem}-herkunft{path.suffix}").as_posix()


@dataclass(frozen=True)
class Handoff:
    route: str
    producer_output: str
    consumer_slug: str
    consumer_input: str

    def origin(self, producer_slug: str, attempt: int) -> str:
        return (
            f"{producer_slug}/{attempt:03d}/"
            f"{self.producer_output}"
        )

    @property
    def provenance_input(self) -> str:
        path = Path(self.consumer_input)
        return (path.parent / f"{path.stem}-herkunft{path.suffix}").as_posix()


@dataclass(frozen=True)
class WalkResult:
    routers: tuple[str, ...]
    states: tuple[State, ...]
    mutation_codes: frozenset[str]
    import_state: State
    import_oid_equal: bool
    proofs: frozenset[str]
    rejections: frozenset[str]

    @property
    def valid(self) -> bool:
        return (
            all(state.valid for state in self.states)
            and "binding.reference_digest" in self.mutation_codes
            and self.import_state.valid
            and self.import_oid_equal
            and EXPECTED_PROOFS <= self.proofs
            and EXPECTED_REJECTIONS <= self.rejections
        )


class Harness:
    """Attempt folders and Laufpfad; extra proof behavior stays local to this evaluation."""

    def __init__(self, root: Path, revision: str):
        self.root = root
        self.revision = revision
        self.vorgang_root = root / "vorgaenge" / VORGANG
        self.laufpfad: list[dict] = []
        self.steps = _hauptprozess_steps(root, revision)
        _check_loop_bounds(root, revision, self.steps)
        self._schemas = SchemaRegistry()

    def attempt(self, slug: str, versuch: int) -> Path:
        return self.vorgang_root / slug / f"{versuch:03d}"

    def open(self, slug: str, versuch: int, inputs: dict[str, str]) -> dict:
        if self.laufpfad or self.vorgang_root.exists():
            raise ProofError("Successor must open through a checked advance")
        proposed = self._proposed_active_entry(slug, versuch)
        self._preflight_vorgang([proposed])
        if self.steps[slug].get("gate") == "human":
            raise ProofError("Human Gate must open through a proven producer handoff")
        # Initial opening has no current Vorgang, but still checks its bound entry
        # and complete input set before creating any attempt files.
        metadata, _ = _frontmatter_and_body(_git_show(self.root, self.revision, "CONTEXT.md").decode())
        if metadata["einstieg_ref"] != f"arbeitsschritt:{slug}" or versuch != 1:
            raise ProofError("Initial attempt differs from the Hauptprozess entry")
        self._require_inputs(slug, inputs)
        report = validate(self.root)
        if not report.valid:
            raise ProofError("Initial workspace fails validation")
        attempt = self.attempt(slug, versuch)
        _preflight_files(attempt, inputs)
        _write_files(attempt, inputs)
        entry = self._active_entry(slug, versuch, attempt)
        self.laufpfad.append(entry)
        self._write()
        return entry

    def wait(self, entry: dict, ausloeser: str, continuation_ref: str) -> None:
        self._preflight_current(entry)
        resume = {
            "ausloeser": ausloeser,
            "continuation_ref": continuation_ref,
        }
        proposed = dict(entry, status="wartend", wiedereinstieg=resume)
        self._preflight_vorgang([*self.laufpfad[:-1], proposed])
        entry["status"] = "wartend"
        entry["wiedereinstieg"] = resume
        self._write()

    def close(
        self,
        entry: dict,
        outputs: dict[str, str],
        route: str,
        freigabe: dict | None = None,
    ) -> None:
        self._preflight_current(entry)
        slug = entry["arbeitsschritt_ref"].removeprefix("arbeitsschritt:")
        if self.steps[slug].get("gate") == "human" or freigabe is not None:
            raise ProofError("Human Gate must close through a checked decision")
        self._preflight_terminal(slug, outputs, route)
        self._preflight_completion(entry, route)
        self._close_terminal(entry, outputs, route)

    def _close_terminal(self, entry, outputs, route, freigabe=None) -> None:
        slug = entry["arbeitsschritt_ref"].removeprefix("arbeitsschritt:")
        attempt = self.attempt(slug, entry["nummer"])
        _preflight_files(attempt, outputs)
        _write_outputs(attempt, outputs)
        self._complete_entry(entry, slug, attempt, route, freigabe)
        self._write()

    def close_human(self, entry: dict, decision: dict) -> None:
        self._preflight_current(entry)
        slug = entry["arbeitsschritt_ref"].removeprefix("arbeitsschritt:")
        if self.steps[slug].get("gate") != "human":
            raise ProofError("human fixture supplied to a non-gate step")
        if not isinstance(decision, dict):
            raise ProofError("synthetic Human-Decision fixture must be a mapping")
        route = decision.get("route")
        freigabe = decision.get("freigabe")
        output = decision.get("output")
        if not isinstance(route, str) or route not in {"freigegeben", "abgelehnt"}:
            raise ProofError("synthetic Human-Decision fixture has no Gate route")
        if not isinstance(freigabe, dict):
            raise ProofError("synthetic Human-Decision fixture has no human attribution")
        self._preflight_completion(entry, route, freigabe)
        fields = _fields(output) if isinstance(output, str) else {}
        if (
            not all(fields.get(name) for name in ("Prüfbericht", "Entscheidung", "Begründung"))
            or fields["Entscheidung"] != route
        ):
            raise ProofError("Gate output does not satisfy pruefung")
        source = yaml.safe_dump(decision, allow_unicode=True, sort_keys=False)
        report = input_file(self.attempt(slug, entry["nummer"]), "material/pruefbericht.md")
        evidence = (
            output + "\n## Empfangene synthetische Entscheidung\n\n```yaml\n"
            + source + "```\n\n"
            + f"Gebundener Hauptprozess: git-tree:{self.revision}\n"
            + f"Gebundener Prüfbericht: sha256:{_content_digest(report.read_bytes())}\n"
            + "Diese Quelle testet die Aufzeichnung; sie authentifiziert keine Person.\n"
        )
        outputs = {"output/entscheidung.md": evidence}
        self._preflight_terminal(slug, outputs, route)
        self._close_terminal(entry, outputs, route, freigabe)

    def advance(
        self,
        entry: dict,
        outputs: dict[str, str],
        route: str,
        next_slug: str,
        next_versuch: int,
        next_inputs: dict[str, str],
        resume: dict[str, str] | None = None,
    ) -> dict:
        """Run mutation-free preflight, then perform one logical Harness transition."""
        self._preflight_current(entry)
        proposed_next = self._opened_entry(self._proposed_active_entry(next_slug, next_versuch), resume)
        self._preflight_completion(entry, route, successor=proposed_next)
        if self.attempt(next_slug, next_versuch).exists() or source_home(self.attempt(next_slug, next_versuch)).exists():
            raise ProofError("Successor attempt already exists")
        slug = entry["arbeitsschritt_ref"].removeprefix("arbeitsschritt:")
        if self.steps[slug].get("gate") == "human":
            raise ProofError("Human Gate must close through a checked decision")
        if self.steps[slug]["routen"].get(route) != f"arbeitsschritt:{next_slug}":
            raise ProofError("Successor differs from the declared route")
        self._require_outputs(slug, outputs)
        self._require_inputs(next_slug, next_inputs)
        attempt = self.attempt(slug, entry["nummer"])
        next_attempt = self.attempt(next_slug, next_versuch)
        # Both surfaces must be writable under known caller-controlled
        # preconditions before either group creates files. This is not I/O rollback.
        _preflight_files(attempt, outputs)
        request_files = {}
        if "wiedereinstieg" in proposed_next:
            request = self.root / proposed_next["wiedereinstieg"]["continuation_ref"]
            try:
                relative = request.relative_to(next_attempt / "output")
            except ValueError as error:
                raise ProofError("Continuation request must be in the waiting attempt's output") from error
            request_files["output/" + relative.as_posix()] = (
                "Synthetic request recorded as sent; awaiting "
                + proposed_next["wiedereinstieg"]["ausloeser"] + "\n"
            )
        _preflight_files(next_attempt, {**next_inputs, **request_files})
        self._preflight_handoff(entry, outputs, route, next_slug, next_inputs)

        _write_outputs(attempt, outputs)
        self._complete_entry(entry, slug, attempt, route)
        handoff = _hauptprozess_handoff(self.root, self.revision, slug, route)
        captures = {key: value for key, value in next_inputs.items() if key != handoff.consumer_input}
        _write_files(next_attempt, captures)
        next_entry = self._opened_entry(self._active_entry(next_slug, next_versuch, next_attempt), resume)
        _write_files(next_attempt, request_files)
        self.laufpfad.append(next_entry)
        self._write()
        return next_entry

    def _opened_entry(self, entry: dict, resume: dict[str, str] | None = None) -> dict:
        """An attempt that can complete only after a declared Auslöser opens wartend.

        This harness prepares the packet before opening and requests the decision at opening.
        A harness preparing it inside the gate keeps that attempt aktiv until the request.
        """
        slug = entry["arbeitsschritt_ref"].removeprefix("arbeitsschritt:")
        if resume is None and self.steps[slug].get("gate") == "human":
            resume = {"ausloeser": "Entscheidung der benannten prüfenden Person",
                      "continuation_ref": (self.attempt(slug, entry["nummer"]) / "output/warten.md").relative_to(self.root).as_posix()}
        return entry if resume is None else dict(entry, status="wartend", wiedereinstieg=dict(resume))

    def state(self, label: str) -> State:
        report = validate(self.root)
        return State(label, report.valid, tuple(sorted({issue.code for issue in report.issues})))

    def _active_entry(self, slug: str, versuch: int, attempt: Path) -> dict:
        declared = self.steps[slug]["eingaben"]
        producer = self.laufpfad[-1] if self.laufpfad else None
        records = []
        mapping = None
        if producer is not None and producer.get("status") == "abgeschlossen":
            producer_slug = producer["arbeitsschritt_ref"].removeprefix("arbeitsschritt:")
            mapping = _hauptprozess_handoff(self.root, self.revision, producer_slug, producer["gewaehlte_route"])
        for name in declared:
            if mapping is not None and name == mapping.consumer_input:
                records.extend(dict(ref, eingabe=name) for ref in file_references(self.attempt(producer_slug, producer["nummer"]), [mapping.producer_output]))
            else:
                records.extend(file_references(attempt, [name]))
        (attempt / "output").mkdir(parents=True, exist_ok=True)
        return {"arbeitsschritt_ref": f"arbeitsschritt:{slug}", "nummer": versuch,
                "status": "aktiv", "gelesen": records}

    def _proposed_active_entry(self, slug: str, versuch: int) -> dict:
        if not isinstance(slug, str) or slug not in self.steps:
            raise ProofError("Attempt names no bound Arbeitsschritt")
        if not isinstance(versuch, int):
            raise ProofError("Attempt number must support integer folder naming")
        # Schema-shaped placeholder is only for proposed metadata checks.
        # _active_entry computes the stored hash from actual files after preflight.
        return {
            "arbeitsschritt_ref": f"arbeitsschritt:{slug}",
            "nummer": versuch,
            "status": "aktiv",
            "gelesen": [],
        }

    def _check_schema(self, name: str, metadata: dict) -> None:
        errors = self._schemas.errors(name, metadata)
        if errors:
            details = "; ".join(
                "/" + "/".join(str(part) for part in error.absolute_path)
                + ": " + error.message for error in errors
            )
            raise ProofError(f"Proposed {name} metadata fails schema: {details}")

    def _preflight_vorgang(self, entries: list[dict]) -> None:
        metadata = {
            "type": "vorgang", "protocol": "v0.5.0",
            "id": f"vorgang:{VORGANG}",
            "hauptprozess_revision": f"git-tree:{self.revision}",
            "laufpfad": entries,
        }
        self._check_schema("vorgang", metadata)
        try:
            json.dumps(metadata, ensure_ascii=False).encode("utf-8")
        except UnicodeEncodeError as error:
            raise ProofError("Proposed Vorgang metadata is not valid UTF-8") from error

    def _preflight_completion(
        self, entry: dict, route: str, freigabe: dict | None = None,
        *, successor: dict | None = None,
    ) -> None:
        proposed = dict(entry)
        proposed.pop("wiedereinstieg", None)
        # Never store this placeholder or treat it as execution evidence.
        # _complete_entry binds the actual output surface after files are written.
        proposed.update(status="abgeschlossen", gewaehlte_route=route, geschrieben=[])
        if freigabe is not None:
            proposed["freigabe"] = freigabe
        entries = [*self.laufpfad[:-1], proposed]
        if successor is not None:
            entries.append(successor)
        self._preflight_vorgang(entries)
        if freigabe is not None:
            problem = _approval_problem(freigabe)
            if problem is not None:
                raise ProofError(problem)

    def _complete_entry(
        self,
        entry: dict,
        slug: str,
        attempt: Path,
        route: str,
        freigabe: dict | None = None,
    ) -> None:
        entry.pop("wiedereinstieg", None)
        entry["status"] = "abgeschlossen"
        entry["gewaehlte_route"] = route
        entry["geschrieben"] = file_references(attempt, ["output"])
        if freigabe is not None:
            entry["freigabe"] = freigabe

    def _preflight_handoff(
        self,
        entry: dict,
        outputs: dict[str, str],
        route: str,
        next_slug: str,
        inputs: dict[str, str],
    ) -> None:
        producer_slug = entry["arbeitsschritt_ref"].removeprefix("arbeitsschritt:")
        if self.steps[producer_slug]["routen"].get(route) != f"arbeitsschritt:{next_slug}":
            raise ProofError("Successor differs from the declared route")
        self._require_inputs(next_slug, inputs)
        handoff = _hauptprozess_handoff(
            self.root, self.revision, producer_slug, route
        )
        if handoff.consumer_slug != next_slug:
            raise ProofError("Handoff target differs from Hauptprozess handoff")
        if handoff.producer_output not in outputs:
            raise ProofError("Producer output differs from Hauptprozess handoff")
        if handoff.consumer_input not in inputs:
            raise ProofError("Consumer input differs from Hauptprozess handoff")
        if handoff.provenance_input not in inputs:
            raise ProofError("Handoff provenance input missing")
        _verify_handoff(
            outputs[handoff.producer_output].encode("utf-8"),
            inputs[handoff.consumer_input].encode("utf-8"),
            inputs[handoff.provenance_input],
            handoff.origin(producer_slug, entry["nummer"]),
        )
        if producer_slug == "nachfordern":
            # This example checks the received source separately from the pending request.
            receipt_ref = _fields(inputs[handoff.provenance_input]).get("Eingangsquelle")
            if not isinstance(receipt_ref, str) or not receipt_ref:
                raise ProofError("Nachreichung has no received source file")
            relative = Path(receipt_ref)
            receipt = self.root / relative
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or not receipt.resolve().is_relative_to(self.root.resolve())
            ):
                raise ProofError("Unsafe response source path")
            if not receipt.is_file():
                raise ProofError("Nachreichung has no received source file")
            if receipt.read_bytes() != outputs[handoff.producer_output].encode("utf-8"):
                raise ProofError("Nachreichung differs from received source")

    def _preflight_current(self, entry: dict) -> None:
        if not self.laufpfad or self.laufpfad[-1] is not entry or entry.get("status") not in {"aktiv", "wartend"}:
            raise ProofError("Transition requires the current unresolved entry")
        persisted = load_frontmatter(self.vorgang_root / "CONTEXT.md")
        binding = {"type": "vorgang", "protocol": "v0.5.0", "id": f"vorgang:{VORGANG}", "hauptprozess_revision": f"git-tree:{self.revision}"}
        if any(persisted.get(key) != value for key, value in binding.items()):
            raise ProofError("Vorgang binding differs from the current harness binding")
        if persisted.get("laufpfad") != self.laufpfad:
            raise ProofError("Vorgang state differs from the current harness state")
        for reference in entry.get("gelesen", []):
            if "pfad" in reference:
                source = self.root / reference["pfad"]
                if not source.is_file() or "sha256:" + _content_digest(source.read_bytes()) != reference["sha256"]:
                    raise ProofError("Harness read differs from recorded reference")
        report = validate(self.root)
        if not report.valid:
            raise ProofError("Current Vorgang fails validation: " + ", ".join(sorted({issue.code for issue in report.issues})))

    def _require_inputs(self, slug: str, inputs: dict[str, str]) -> None:
        if not isinstance(inputs, dict):
            raise ProofError("Handoff inputs must be a file mapping")
        self._check_schema("arbeitsschritt", dict(self.steps[slug], eingaben=list(inputs)))
        if any(not name.startswith("material/") for name in inputs):
            raise ProofError("Synthetic input mapping uses material/ logical names")
        missing = set(self.steps[slug]["eingaben"]) - set(inputs)
        if missing:
            raise ProofError(f"Handoff inputs missing: {sorted(missing)}")

    def _require_outputs(self, slug: str, outputs: dict[str, str]) -> None:
        if not isinstance(outputs, dict):
            raise ProofError("Declared outputs must be a file mapping")
        self._check_schema("arbeitsschritt", dict(self.steps[slug], ausgaben=list(outputs)))
        missing = set(self.steps[slug]["ausgaben"]) - set(outputs)
        if missing:
            raise ProofError(f"Declared outputs missing: {sorted(missing)}")

    def _preflight_terminal(self, slug: str, outputs: dict[str, str], route: str) -> None:
        target = self.steps[slug]["routen"].get(route, "")
        if not target.startswith("end:"):
            raise ProofError("Nonterminal route requires a checked advance")
        self._require_outputs(slug, outputs)

    def _write(self) -> None:
        metadata = {
            "type": "vorgang", "protocol": "v0.5.0",
            "id": f"vorgang:{VORGANG}",
            "hauptprozess_revision": f"git-tree:{self.revision}",
            "laufpfad": self.laufpfad,
        }
        frontmatter = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).rstrip()
        current = self.laufpfad[-1]
        slug = current["arbeitsschritt_ref"].removeprefix("arbeitsschritt:")
        attempt = self.attempt(slug, current["nummer"])
        stand = []
        for output in self.steps[slug]["ausgaben"]:
            path = input_file(attempt, output)
            if path.is_file():
                stand.append(f"Ausgabe: [{output}]({path.relative_to(self.vorgang_root).as_posix()}).")
        body = "\n\n".join(stand)
        self.vorgang_root.mkdir(parents=True, exist_ok=True)
        (self.vorgang_root / "CONTEXT.md").write_text(
            f"---\n{frontmatter}\n---\n\n# Prüffall 001\n\nSynthetischer Vorgang des Cold Walk.\n\n## Nachweise\n\nPosition und Status aus `laufpfad` nach der Protokollregel ableiten.\n\n{body}\n",
            encoding="utf-8",
        )


def walk(base: Path, *, decision_path: Path | None = None) -> WalkResult:
    """Initialize, bind, run and mutate every declared evidence chain."""
    root, source_commit, capability_tree, revision, workspace_revision = _prepare_workspace(
        Path(base)
    )
    proofs: set[str] = set()
    rejections: set[str] = set()

    return_path = root / "hauptprozesse" / HAUPTPROZESS / "vorpruefung/nachfordern/CONTEXT.md"
    producer_path = root / "hauptprozesse" / HAUPTPROZESS / CALL_STEP
    probes = [
        ("loop.missing_bound", return_path, lambda text: re.sub(r"(?m)^Loop bound:.*\n?", "", text),
         lambda tree: Harness(root, tree)),
        ("handoff.old_label", producer_path,
         lambda text: text.replace("arbeitsschritt:entscheiden:material/", "arbeitsschritt:entscheiden/input/"),
         lambda tree: _hauptprozess_handoff(root, tree, "pruefen", "bestanden")),
        ("handoff.undeclared_slot", producer_path,
         lambda text: text.replace("arbeitsschritt:entscheiden:material/pruefbericht.md", "arbeitsschritt:entscheiden:material/unknown.md"),
         lambda tree: _hauptprozess_handoff(root, tree, "pruefen", "bestanden")),
    ]
    for code, path, mutate, check in probes:
        original = path.read_text(encoding="utf-8")
        path.write_text(mutate(original), encoding="utf-8")
        _git(root, "add", f"hauptprozesse/{HAUPTPROZESS}")
        _git(root, "commit", "-q", "-m", f"synthetic rejection {code}")
        tree = _git(root, "rev-parse", f"HEAD:hauptprozesse/{HAUPTPROZESS}")
        if _is_rejected(lambda: check(tree)):
            rejections.add(code)
        path.write_text(original, encoding="utf-8")
        _git(root, "add", f"hauptprozesse/{HAUPTPROZESS}")
        _git(root, "commit", "-q", "-m", f"restore synthetic source after {code}")

    call = _hauptprozess_call(root, revision)
    source_ref = _hauptprozess_source(root, revision)
    handoff = _hauptprozess_handoff(root, revision, "pruefen", "bestanden")
    rules, rules_provenance = _materialize_source(root, source_ref)
    _verify_source(root, source_ref, rules, rules_provenance)
    proofs.add("source.bound_snapshot")

    changed_step = root / "hauptprozesse" / HAUPTPROZESS / CALL_STEP
    changed_body = changed_step.read_text(encoding="utf-8")
    changed_body = changed_body.replace(
        "- Ursprung: `grundlagen/pruefregeln.md`",
        "- Ursprung: `grundlagen/andere-regeln.md`",
    ).replace(
        "`output/pruefbericht.md -> arbeitsschritt:entscheiden:material/pruefbericht.md`",
        "`output/pruefbericht.md -> arbeitsschritt:entscheiden:material/pruefbericht-alternativ.md`",
    )
    changed_step.write_text(changed_body, encoding="utf-8")
    changed_decision = root / "hauptprozesse" / HAUPTPROZESS / DECISION_STEP
    changed_decision_body = changed_decision.read_text(encoding="utf-8").replace(
        "material/pruefbericht-herkunft.md",
        "material/pruefbericht-alternativ-herkunft.md",
    ).replace(
        "material/pruefbericht.md",
        "material/pruefbericht-alternativ.md",
    )
    changed_decision.write_text(changed_decision_body, encoding="utf-8")
    _git(root, "add", f"hauptprozesse/{HAUPTPROZESS}")
    _git(root, "commit", "-q", "-m", "mutate hauptprozess source and handoff authority")
    changed_revision = _git(root, "rev-parse", f"HEAD:hauptprozesse/{HAUPTPROZESS}")
    changed_source = _hauptprozess_source(root, changed_revision)
    changed_handoff = _hauptprozess_handoff(root, changed_revision, "pruefen", "bestanden")
    changed_rules, _ = _materialize_source(root, changed_source)
    if changed_source.path != source_ref.path and changed_rules != rules:
        proofs.add("hauptprozess.source_requirement_drives_resolution")
    changed_harness = Harness(root, changed_revision)
    probe_entry = {"arbeitsschritt_ref": "arbeitsschritt:pruefen", "nummer": 2}
    probe_payload = "authority probe\n"
    changed_provenance = _handoff_provenance(
        changed_handoff.origin("pruefen", 2), probe_payload.encode("utf-8")
    )
    changed_inputs = {
        changed_handoff.consumer_input: probe_payload,
        changed_handoff.provenance_input: changed_provenance,
    }
    changed_harness._preflight_handoff(
        probe_entry,
        {changed_handoff.producer_output: probe_payload},
        "bestanden",
        changed_handoff.consumer_slug,
        changed_inputs,
    )
    old_inputs_rejected = _is_rejected(
        lambda: changed_harness._preflight_handoff(
            probe_entry,
            {changed_handoff.producer_output: probe_payload},
            "bestanden",
            changed_handoff.consumer_slug,
            {
                handoff.consumer_input: probe_payload,
                handoff.provenance_input: changed_provenance,
            },
        )
    )
    if changed_handoff.consumer_input != handoff.consumer_input and old_inputs_rejected:
        proofs.add("hauptprozess.handoff_mapping_drives_origin")

    wrong_path_body = changed_step.read_text(encoding="utf-8").replace(
        "capabilities/vollstaendigkeitsgrad/CONTEXT.md",
        "capabilities/falsch/CONTEXT.md",
    )
    changed_step.write_text(wrong_path_body, encoding="utf-8")
    _git(root, "add", f"hauptprozesse/{HAUPTPROZESS}")
    _git(root, "commit", "-q", "-m", "mutate hauptprozess capability path")
    wrong_path_revision = _git(root, "rev-parse", f"HEAD:hauptprozesse/{HAUPTPROZESS}")
    wrong_path_workspace_revision = _git(root, "rev-parse", "HEAD")
    wrong_path_call = _hauptprozess_call(root, wrong_path_revision)

    (root / source_ref.path).write_text("dirty working tree\n", encoding="utf-8")
    dirty_rules, dirty_provenance = _materialize_source(root, source_ref)
    _verify_source(root, source_ref, dirty_rules, dirty_provenance)
    if dirty_rules == rules:
        proofs.add("source.dirty_worktree_ignored")

    source_mutations = {
        "source.wrong_digest": rules_provenance.replace(
            f"sha256:{_content_digest(rules)}", f"sha256:{'0' * 64}"
        ),
        "source.wrong_control": rules_provenance.replace(
            source_ref.minimum_control, "beliebig geprüft"
        ),
        "source.wrong_revision": rules_provenance.replace(
            source_commit, _git(root, "rev-parse", "HEAD")
        ),
        "source.wrong_existing_path": rules_provenance.replace(
            "grundlagen/pruefregeln.md", "grundlagen/andere-regeln.md"
        ),
    }
    for code, claim in source_mutations.items():
        if _is_rejected(lambda claim=claim: _verify_source(root, source_ref, rules, claim)):
            rejections.add(code)

    first_record = (BEISPIEL_ROOT / "fixtures/initial-record.md").read_bytes()
    first_result = _execute_capability(
        root, revision, call, workspace_revision, rules, first_record
    )
    if first_result["sentinel"] == "vollstaendigkeitsgrad-v1" and call.tree_oid == capability_tree:
        proofs.add("capability.hauptprozess_tuple_executed")
        proofs.add("capability.path_resolved_at_workspace_revision")

    if _is_rejected(
        lambda: _execute_capability(
            root,
            wrong_path_revision,
            wrong_path_call,
            wrong_path_workspace_revision,
            rules,
            first_record,
        )
    ):
        rejections.add("capability.wrong_path")

    capability_file = root / "capabilities" / "vollstaendigkeitsgrad" / "run.py"
    capability_file.write_text(
        capability_file.read_text(encoding="utf-8").replace(
            "vollstaendigkeitsgrad-v1", "vollstaendigkeitsgrad-v2"
        ),
        encoding="utf-8",
    )
    _git(root, "add", "capabilities/vollstaendigkeitsgrad/run.py")
    _git(root, "commit", "-q", "-m", "mutate capability after hauptprozess binding")
    second_tree = _git(root, "rev-parse", "HEAD:capabilities/vollstaendigkeitsgrad")

    if _is_rejected(
        lambda: _execute_capability(
            root,
            revision,
            replace(call, tree_oid=second_tree),
            workspace_revision,
            rules,
            first_record,
        )
    ):
        rejections.add("capability.unbound_valid_tree")
    if _is_rejected(
        lambda: _execute_capability(
            root,
            revision,
            replace(call, operation="andere-operation"),
            workspace_revision,
            rules,
            first_record,
        )
    ):
        rejections.add("capability.wrong_operation")
    replay = _execute_capability(
        root, revision, call, workspace_revision, rules, first_record
    )
    if replay == first_result and replay["sentinel"] == "vollstaendigkeitsgrad-v1":
        proofs.add("capability.old_revision_replayed")

    harness = Harness(root, revision)
    states = []
    common_inputs = {
        source_ref.input_path: rules.decode("utf-8"),
        source_ref.provenance_input: rules_provenance,
    }

    entry = harness.open(
        "pruefen",
        1,
        {**_record_inputs(root, "records/antrag-001/erstantrag.md", first_record.decode("utf-8")), **common_inputs},
    )
    states.append(harness.state("pruefen 001 aktiv"))
    first_report = _render_report(call, workspace_revision, first_result)
    clarification = _hauptprozess_handoff(root, revision, "pruefen", "klaerung")

    # nachfordern can complete only after the applicant delivers, so its attempt opens wartend.
    response_ref = "records/antrag-001/nachreichung.md"
    entry = harness.advance(
        entry,
        {"output/pruefbericht.md": first_report},
        "klaerung",
        "nachfordern",
        1,
        {
            clarification.consumer_input: first_report,
            clarification.provenance_input: _handoff_provenance(
                clarification.origin("pruefen", 1), first_report.encode("utf-8")
            ),
        },
        resume={"ausloeser": "unterlagen-nachgereicht", "continuation_ref": f"vorgaenge/{VORGANG}/nachfordern/001/output/warten.md"},
    )
    states.append(harness.state("nachfordern 001 wartend nach klaerung"))

    # Exercise file/state compatibility through Core, not autonomous permission checks.
    waiting_attempt = harness.attempt("nachfordern", 1)
    waiting_input = input_file(waiting_attempt, "material/pruefbericht.md")
    bound_report = waiting_input.read_bytes()
    vorgang_file = harness.vorgang_root / "CONTEXT.md"
    waiting_state = load_frontmatter(vorgang_file)
    finding = next(
        (line.removeprefix("Befund: fehlt: ")
        for line in bound_report.decode("utf-8").splitlines()
        if line.startswith("Befund: fehlt: ")),
        None,
    )
    if not finding:
        raise ProofError("Bound report has no missing-field finding for the draft")
    draft = f"Entwurf für menschliche Rückfrage: Bitte {finding} nachreichen.\n"
    draft_path = waiting_attempt / "output/nachforderung.md"
    _write_files(waiting_attempt, {"output/nachforderung.md": draft})
    harness._write()
    visible_state = vorgang_file.read_text(encoding="utf-8")
    if (
        draft_path.read_text(encoding="utf-8") == draft
        and load_frontmatter(vorgang_file) == waiting_state
        and waiting_input.read_bytes() == bound_report
        and not {"gewaehlte_route", "freigabe", "geschrieben"} & entry.keys()
        and "nachfordern/001/output/nachforderung.md" in visible_state
        and "nachfordern/001/output/warten.md" in visible_state
        and derive_progress(harness.laufpfad, {step["id"]: step for step in harness.steps.values()}, {})["status"] == "wartend"
        and harness.state("draft while waiting").valid
    ):
        proofs.add("wait.permitted_draft_preserves_current_state")

    waiting_input.write_text("Neue, ungebundene Aussage\n", encoding="utf-8")
    if "binding.reference_digest" in harness.state("mutated waiting input").codes:
        rejections.add("wait.changed_bound_input")
    waiting_input.write_bytes(bound_report)

    # Both input surfaces exist; the violation is a waiting entry before the last entry.
    premature = harness.attempt("nachfordern", 2)
    _write_files(premature, {
        "material/pruefbericht.md": bound_report.decode("utf-8"),
        "material/pruefbericht-herkunft.md": (input_file(waiting_attempt, "material/pruefbericht-herkunft.md")).read_text(encoding="utf-8"),
    })
    harness.laufpfad.append(harness._active_entry("nachfordern", 2, premature))
    harness._write()
    if "execution.attempt" in harness.state("active entry after waiting entry").codes:
        rejections.add("wait.concurrent_laufpfad_entry")
    harness.laufpfad.pop()
    shutil.rmtree(premature)
    harness._write()

    second_record = (CAPABILITY / "fixtures/vollstaendig.md").read_text(encoding="utf-8")
    response_handoff = _hauptprozess_handoff(root, revision, "nachfordern", "nachgereicht")
    response_origin = response_handoff.origin("nachfordern", 1)
    response_provenance = (
        _handoff_provenance(response_origin, second_record.encode("utf-8"))
        + f"Eingangsquelle: {response_ref}\n"
    )
    response_inputs = {
        response_handoff.consumer_input: second_record,
        response_handoff.provenance_input: response_provenance,
        **common_inputs,
    }
    outputs = {"output/nachforderung.md": draft, response_handoff.producer_output: second_record}
    before_response = _directory_digest(harness.vorgang_root)
    if _is_rejected(
        lambda: harness.advance(entry, outputs, "nachgereicht", "pruefen", 2, response_inputs),
        "no received source file",
    ):
        if _directory_digest(harness.vorgang_root) == before_response:
            rejections.add("wait.missing_response")

    # External receipt and a human edit are synthetic fixtures, not agent-generated approval.
    _write_files(root, {response_ref: "Nicht der behauptete Eingang\n"})
    if _is_rejected(
        lambda: harness.advance(entry, outputs, "nachgereicht", "pruefen", 2, response_inputs),
        "differs from received source",
    ):
        if _directory_digest(harness.vorgang_root) == before_response:
            rejections.add("wait.response_mismatch")
    _write_files(root, {response_ref: second_record})
    external = root.parent / "outside-response.md"
    external.write_text(second_record, encoding="utf-8")
    escape_link = root / "records/antrag-001/response-link.md"
    escape_link.symlink_to(external)
    unsafe_paths = (str(external), "../outside-response.md", "records/antrag-001/response-link.md")
    refused = []
    try:
        for unsafe in unsafe_paths:
            # Exercise the receipt path independently of the continuation record.
            candidate_inputs = {
                **response_inputs,
                response_handoff.provenance_input: response_provenance.replace(response_ref, unsafe),
            }
            refused.append(_is_rejected(
                lambda: harness.advance(entry, outputs, "nachgereicht", "pruefen", 2, candidate_inputs),
                "Unsafe response source path",
            ))
    finally:
        harness._write()
        escape_link.unlink()
        external.unlink()
    if all(refused) and _directory_digest(harness.vorgang_root) == before_response:
        rejections.add("wait.unsafe_response_path")
    edited_draft = draft + "Bitte geben Sie bei der Rückmeldung das Aktenzeichen an.\n"
    draft_path.write_text(edited_draft, encoding="utf-8")
    before_retry = _directory_digest(harness.vorgang_root)
    try:
        harness.advance(entry, outputs, "nachgereicht", "pruefen", 2, response_inputs)
    except ProofError as error:
        if "Existing output differs" in str(error) and _directory_digest(harness.vorgang_root) == before_retry:
            rejections.add("wait.stale_draft_overwrite")

    # Use the reviewed on-disk draft and actual receipt, not stale in-memory drafts.
    outputs = {
        "output/nachforderung.md": draft_path.read_text(encoding="utf-8"),
        response_handoff.producer_output: (root / response_ref).read_text(encoding="utf-8"),
    }
    entry = harness.advance(
        entry,
        outputs,
        "nachgereicht",
        "pruefen",
        2,
        response_inputs,
    )
    states.append(harness.state("pruefen 002 aktiv nach nachgereicht"))

    second_attempt = harness.attempt("pruefen", 2)
    _verify_handoff(
        (waiting_attempt / response_handoff.producer_output).read_bytes(),
        input_file(second_attempt, response_handoff.consumer_input).read_bytes(),
        input_file(second_attempt, response_handoff.provenance_input).read_text(encoding="utf-8"),
        response_origin,
    )
    if (
        (input_file(harness.attempt("pruefen", 1), "material/antrag.md")).read_bytes() == first_record
        and waiting_input.read_bytes() == bound_report
        and (input_file(second_attempt, "material/antrag.md")).read_text(encoding="utf-8") == second_record
        and harness.laufpfad[-2]["status"] == "abgeschlossen"
        and entry["status"] == "aktiv"
        and draft_path.read_text(encoding="utf-8") == edited_draft
        and harness.laufpfad[-2]["geschrieben"] == file_references(waiting_attempt, ["output/"])
        and (waiting_attempt / response_handoff.producer_output).read_bytes() == (root / response_ref).read_bytes()
    ):
        proofs.add("wait.resume_binds_new_attempt_inputs")
    second_result = _execute_capability(
        root,
        revision,
        call,
        workspace_revision,
        input_file(second_attempt, source_ref.input_path).read_bytes(),
        (input_file(second_attempt, "material/antrag.md")).read_bytes(),
    )
    second_report = _render_report(call, workspace_revision, second_result)
    origin = handoff.origin("pruefen", entry["nummer"])
    handoff_provenance = _handoff_provenance(origin, second_report.encode("utf-8"))

    valid_gate_inputs = {
        handoff.consumer_input: second_report,
        handoff.provenance_input: handoff_provenance,
    }
    gate_mutations = {
        "handoff.changed_consumer_bytes": {
            **valid_gate_inputs,
            handoff.consumer_input: "changed\n",
        },
        "handoff.wrong_digest": {
            **valid_gate_inputs,
            handoff.provenance_input: handoff_provenance.replace(
                f"sha256:{_content_digest(second_report.encode('utf-8'))}",
                f"sha256:{'0' * 64}",
            ),
        },
        "handoff.wrong_attempt": {
            **valid_gate_inputs,
            handoff.provenance_input: handoff_provenance.replace(
                "/002/", "/001/"
            ),
        },
        "handoff.wrong_producer_file": {
            **valid_gate_inputs,
            handoff.provenance_input: handoff_provenance.replace(
                "/output/pruefbericht.md", "/output/anderer-bericht.md"
            ),
        },
        "handoff.useless_control_evidence": {
            **valid_gate_inputs,
            handoff.provenance_input: re.sub(
                r"(?m)^Kontrollnachweis:.*$",
                "Kontrollnachweis: ja",
                handoff_provenance,
            ),
        },
    }
    unchanged_rejections = 0
    for code, mutated_inputs in gate_mutations.items():
        before = (
            _directory_digest(harness.vorgang_root),
            json.dumps(harness.laufpfad, sort_keys=True),
        )
        rejected = _is_rejected(
            lambda mutated_inputs=mutated_inputs: harness.advance(
                entry,
                {handoff.producer_output: second_report},
                "bestanden",
                handoff.consumer_slug,
                1,
                mutated_inputs,
            )
        )
        after = (
            _directory_digest(harness.vorgang_root),
            json.dumps(harness.laufpfad, sort_keys=True),
        )
        if rejected and before == after:
            rejections.add(code)
            unchanged_rejections += 1
    if unchanged_rejections == len(gate_mutations):
        proofs.add("gate.failed_preflight_left_run_unchanged")

    entry = harness.advance(
        entry,
        {handoff.producer_output: second_report},
        "bestanden",
        handoff.consumer_slug,
        1,
        valid_gate_inputs,
    )
    states.append(harness.state("entscheiden 001 wartend nach bestanden human-gate"))

    producer = harness.attempt("pruefen", 2) / "output/pruefbericht.md"
    consumer = input_file(harness.attempt("entscheiden", 1), "material/pruefbericht.md")
    provenance = input_file(harness.attempt("entscheiden", 1), "material/pruefbericht-herkunft.md")
    _verify_handoff(producer.read_bytes(), consumer.read_bytes(), provenance.read_text(), origin)
    if "geschrieben" in harness.laufpfad[-2] and "gelesen" in harness.laufpfad[-1]:
        proofs.add("handoff.content_and_origin_bound")
    if "gewaehlte_route" not in entry and "freigabe" not in entry:
        proofs.add("gate.open_has_no_decision")

    decision = _load_human_decision(decision_path or HUMAN_DECISION)
    harness.close_human(entry, decision)
    if (
        entry.get("freigabe") == decision["freigabe"]
        and entry.get("gewaehlte_route") == decision["route"]
    ):
        proofs.add("gate.external_decision_fixture_consumed")
    ending = harness.steps["entscheiden"]["routen"][decision["route"]]
    states.append(harness.state(f"entscheiden 001 abgeschlossen {decision['route']} {ending}"))

    (harness.attempt("pruefen", 1) / "output/pruefbericht.md").write_text(
        "Bericht manipuliert\n", encoding="utf-8"
    )
    mutation = frozenset(issue.code for issue in validate(root).issues)

    import_state, import_oid_equal, import_proofs, import_rejections = (
        _import_into_second_repository(
            base,
            root,
            revision,
            workspace_revision,
            call,
            rules,
            rules_provenance,
        )
    )
    proofs.update(import_proofs)
    rejections.update(import_rejections)
    return WalkResult(
        tuple(_router_chain(root)),
        tuple(states),
        mutation,
        import_state,
        import_oid_equal,
        frozenset(proofs),
        frozenset(rejections),
    )


def _prepare_workspace(base: Path) -> tuple[Path, str, str, str, str]:
    root = init_workspace(base / "workspace", language="de")
    shutil.copytree(BEISPIEL, root / "hauptprozesse" / HAUPTPROZESS)
    shutil.copytree(CAPABILITY, root / "capabilities" / "vollstaendigkeitsgrad")
    shutil.copytree(GRUNDLAGEN, root / "grundlagen")
    with (root / "CONTEXT.md").open("a") as router:
        router.write("\nForm: capabilities/ Capability\nForm: grundlagen/ Knowledge Bundle per topic\n")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "cold-walk@example.invalid")
    _git(root, "config", "user.name", "Cold Walk")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "synthetic hauptprozess sources")
    source_commit = _git(root, "rev-parse", "HEAD")
    capability_tree = _git(root, "rev-parse", "HEAD:capabilities/vollstaendigkeitsgrad")

    step = root / "hauptprozesse" / HAUPTPROZESS / CALL_STEP
    body = step.read_text(encoding="utf-8")
    if CAPABILITY_MARKER not in body or SOURCE_REVISION_MARKER not in body:
        raise ProofError("Hauptprozess has no Capability or source revision marker")
    step.write_text(
        body.replace(CAPABILITY_MARKER, capability_tree).replace(
            SOURCE_REVISION_MARKER, source_commit
        ),
        encoding="utf-8",
    )
    _git(root, "add", f"hauptprozesse/{HAUPTPROZESS}")
    _git(root, "commit", "-q", "-m", "bind hauptprozess capability tuple")
    # Retain the legacy bound definition in this workspace's history. The
    # corrected gate is a new Hauptprozess revision, and all new Vorgaenge bind it.
    gate = root / "hauptprozesse" / HAUPTPROZESS / DECISION_STEP
    gate.write_bytes(GATE_REVISION.read_bytes())
    _git(root, "add", f"hauptprozesse/{HAUPTPROZESS}")
    _git(root, "commit", "-q", "-m", "revise gate to record decision and final rejection")
    workspace_revision = _git(root, "rev-parse", "HEAD")
    revision = _git(root, "rev-parse", f"HEAD:hauptprozesse/{HAUPTPROZESS}")
    return root, source_commit, capability_tree, revision, workspace_revision


def _hauptprozess_call(root: Path, hauptprozess_revision: str) -> CapabilityCall:
    text = _hauptprozess_body(root, hauptprozess_revision, CALL_STEP)
    values = {}
    for name in ("Aufruf-ID", "Capability-Pfad", "Capability-Revision", "Operation"):
        match = re.search(rf"(?m)^- {re.escape(name)}:\s*`?([^`\n]+)`?$", text)
        if not match:
            raise ProofError(f"Hauptprozess call lacks {name}")
        values[name] = match.group(1).strip()
    revision = values["Capability-Revision"]
    if not re.fullmatch(r"git-tree:[0-9a-f]{40}", revision):
        raise ProofError("Capability revision is not a Git tree")
    return CapabilityCall(
        call_id=values["Aufruf-ID"],
        path=values["Capability-Pfad"],
        tree_oid=revision.removeprefix("git-tree:"),
        operation=values["Operation"],
    )


def _hauptprozess_source(root: Path, hauptprozess_revision: str) -> SourceRef:
    text = _hauptprozess_body(root, hauptprozess_revision, CALL_STEP)
    values = {}
    for name in (
        "Quell-Eingabe",
        "Herkunft",
        "Ursprung",
        "Stand",
        "Erforderliche Kontrolle",
    ):
        match = re.search(rf"(?m)^- {re.escape(name)}:\s*`?([^`\n]+)`?$", text)
        if not match:
            raise ProofError(f"Hauptprozess source requirement lacks {name}")
        values[name] = match.group(1).strip()
    stand = values["Stand"]
    if not stand.startswith("git:"):
        raise ProofError("Hauptprozess source revision is not Git-bound")
    return SourceRef(
        input_path=values["Quell-Eingabe"],
        source=values["Herkunft"],
        path=values["Ursprung"],
        revision=stand.removeprefix("git:"),
        minimum_control=values["Erforderliche Kontrolle"],
    )


def _check_loop_bounds(root: Path, revision: str, steps: dict) -> None:
    """Check readable bounds on DFS return edges; the harness judges limit meaning."""
    active, visited = set(), set()

    def visit(slug):
        active.add(slug)
        for target in steps[slug]["routen"].values():
            other = target.removeprefix("arbeitsschritt:")
            if other not in steps:
                continue
            if other in active:
                paths = [p for p in _hauptprozess_context_paths(root, revision)
                         if p.endswith(f"/{slug}/CONTEXT.md")]
                body = _hauptprozess_body(root, revision, paths[0]) if len(paths) == 1 else ""
                if not re.search(r"(?m)^Loop bound: \S.*$", body):
                    raise ProofError(f"Loop bound missing for {slug} -> {other}")
            elif other not in visited:
                visit(other)
        active.remove(slug)
        visited.add(slug)

    metadata, _ = _frontmatter_and_body(_git_show(root, revision, "CONTEXT.md").decode("utf-8"))
    visit(metadata["einstieg_ref"].removeprefix("arbeitsschritt:"))


def _hauptprozess_handoff(
    root: Path,
    hauptprozess_revision: str,
    producer_slug: str,
    route: str,
) -> Handoff:
    step_path = next(
        (
            path
            for path in _hauptprozess_context_paths(root, hauptprozess_revision)
            if path.count("/") == 2 and path.endswith(f"/{producer_slug}/CONTEXT.md")
        ),
        None,
    )
    if step_path is None:
        raise ProofError(f"Hauptprozess has no producer step {producer_slug}")
    text = _hauptprozess_body(root, hauptprozess_revision, step_path)
    pattern = re.compile(
        r"(?m)^Bei Route `([^`]+)`: `([^`]+) -> "
        r"arbeitsschritt:([^:/`]+):([^`]+)`\.$"
    )
    matches = [match for match in pattern.finditer(text) if match.group(1) == route]
    if len(matches) != 1:
        raise ProofError(
            f"Hauptprozess handoff for {producer_slug}/{route} is not unique"
        )
    match = matches[0]
    steps = _hauptprozess_steps(root, hauptprozess_revision)
    consumer = steps.get(match.group(3))
    if consumer is None or match.group(4) not in consumer["eingaben"]:
        raise ProofError("Handoff target does not name a declared consumer input slot")
    return Handoff(
        route=match.group(1),
        producer_output=match.group(2),
        consumer_slug=match.group(3),
        consumer_input=match.group(4),
    )


def _hauptprozess_context_paths(root: Path, hauptprozess_revision: str) -> tuple[str, ...]:
    return tuple(
        path
        for path in _git(root, "ls-tree", "-r", "--name-only", hauptprozess_revision).splitlines()
        if path.endswith("CONTEXT.md")
    )


def _hauptprozess_body(root: Path, hauptprozess_revision: str, path: str) -> str:
    text = _git_show(root, hauptprozess_revision, path).decode("utf-8")
    _, body = _frontmatter_and_body(text)
    return body


def _check_capability_revisions(body: str) -> None:
    """Require each named Capability to have a local revision-bound call."""
    named = set(re.findall(r"\bcapabilities/([a-zA-Z0-9_-]+)", body))
    bound = set(re.findall(
        r"(?m)^- Capability-Pfad:[ \t]*`?capabilities/([a-zA-Z0-9_-]+)/CONTEXT\.md`?[ \t]*\n"
        r"- Capability-Revision:[ \t]*`?git-tree:[0-9a-f]{40}`?[ \t]*$",
        body,
    ))
    if missing := named - bound:
        raise ProofError(
            "Capability lacks bound git-tree revision: " + ", ".join(sorted(missing))
        )


def _hauptprozess_steps(
    root: Path, hauptprozess_revision: str
) -> dict[str, dict]:
    metadata = {}
    for path in _hauptprozess_context_paths(root, hauptprozess_revision):
        match = re.fullmatch(r"[^/]+/([^/]+)/CONTEXT\.md", path)
        if not match:
            continue
        slug = match.group(1)
        step_metadata, body = _frontmatter_and_body(
            _git_show(root, hauptprozess_revision, path).decode("utf-8")
        )
        _check_capability_revisions(body)
        metadata[slug] = step_metadata
    return metadata


def _frontmatter_and_body(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        closing = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration as error:
        raise ProofError("Definition frontmatter has no closing delimiter") from error
    metadata = load_yaml_strict("\n".join(lines[1:closing])) or {}
    if not isinstance(metadata, dict):
        raise ProofError("Definition frontmatter is not an object")
    return metadata, "\n".join(lines[closing + 1 :])


def _execute_capability(
    root: Path,
    hauptprozess_revision: str,
    requested: CapabilityCall,
    workspace_revision: str,
    rules: bytes,
    record: bytes,
) -> dict:
    authoritative = _hauptprozess_call(root, hauptprozess_revision)
    if requested != authoritative:
        raise ProofError("requested Capability tuple differs from bound Hauptprozess")
    capability_path = Path(authoritative.path)
    if (
        capability_path.is_absolute()
        or ".." in capability_path.parts
        or len(capability_path.parts) != 3
        or capability_path.parts[0] != "capabilities"
        or capability_path.name != "CONTEXT.md"
    ):
        raise ProofError("Capability path is not a safe CONTEXT.md locator")
    capability_root = capability_path.parent.as_posix()
    resolved_tree = _resolve_tree(root, workspace_revision, capability_root)
    if resolved_tree != authoritative.tree_oid:
        raise ProofError("Capability path does not resolve to bound tree")
    archive = _git_archive(root, f"{workspace_revision}:{capability_root}")
    with TemporaryDirectory(prefix="impacts-capability-") as directory:
        target = Path(directory)
        subprocess.run(["tar", "-x", "-C", str(target)], input=archive, check=True)
        contract = (target / "CONTEXT.md").read_text(encoding="utf-8")
        match = re.search(r"(?m)^Operation:\s*`([^`]+)`$", contract)
        if not match or match.group(1) != authoritative.operation:
            raise ProofError("Capability operation differs from bound Hauptprozess")
        rules_path = target / "_input-rules.md"
        record_path = target / "_input-record.md"
        rules_path.write_bytes(rules)
        record_path.write_bytes(record)
        output = subprocess.check_output(
            [
                "python3",
                str(target / "run.py"),
                "--rules",
                str(rules_path),
                "--record",
                str(record_path),
            ],
            text=True,
        )
    result = json.loads(output)
    if result.get("operation") != authoritative.operation:
        raise ProofError("Capability result names another operation")
    return result


def _render_report(call: CapabilityCall, workspace_revision: str, result: dict) -> str:
    missing = ", ".join(result["missing"]) or "keine"
    status = "vollständig" if not result["missing"] else f"fehlt: {missing}"
    return (
        "# Prüfbericht\n\n"
        f"Aufruf-ID: {call.call_id}\n"
        f"Capability-Pfad: {call.path}\n"
        f"Capability-Workspace-Revision: git:{workspace_revision}\n"
        f"Capability-Revision: git-tree:{call.tree_oid}\n"
        f"Operation: {call.operation}\n"
        f"Rechensentinel: {result['sentinel']}\n"
        "Rechenregel: vorhandene Pflichtfelder / alle Pflichtfelder * 100\n"
        f"Vollständigkeitsgrad: {result['percent']} Prozent\n"
        f"Befund: {status}\n"
        "Prüfung: Ergebnis zwischen 0 und 100\n"
        "Technische Nutzungsbedingung: nur mit gebundenen Eingaben\n"
        "Nutzungsgrenze: synthetische Vorprüfung\n"
    )


def _materialize_source(root: Path, source: SourceRef) -> tuple[bytes, str]:
    payload = _git_show(root, source.revision, source.path)
    digest = _content_digest(payload)
    provenance = (
        f"Herkunft: {source.source}\n"
        f"Ursprung: {source.path}\n"
        f"Stand: git:{source.revision}\n"
        f"Content-Digest: sha256:{digest}\n"
        f"Erforderliche Kontrolle: {source.minimum_control}\n"
        f"Kontrollnachweis: git:{source.revision}:{source.path} gelesen\n"
    )
    return payload, provenance


def _verify_source(root: Path, expected: SourceRef, payload: bytes, provenance: str) -> None:
    fields = _fields(provenance)
    expected_fields = {
        "Herkunft": expected.source,
        "Ursprung": expected.path,
        "Stand": f"git:{expected.revision}",
        "Content-Digest": f"sha256:{_content_digest(payload)}",
        "Erforderliche Kontrolle": expected.minimum_control,
    }
    for name, value in expected_fields.items():
        if fields.get(name) != value:
            raise ProofError(f"source provenance mismatch: {name}")
    _reachable_commit(root, expected.revision)
    with _source_bytes_readable(expected.revision, expected.path):
        committed = _git_show(root, expected.revision, expected.path)
    if committed != payload:
        raise ProofError("source snapshot differs from bound Git object")
    expected_control = f"git:{expected.revision}:{expected.path} gelesen"
    if fields.get("Kontrollnachweis") != expected_control:
        raise ProofError("source control evidence differs")


def _handoff_provenance(origin: str, payload: bytes) -> str:
    digest = _content_digest(payload)
    return (
        "Herkunft: vorheriger Arbeitsschritt\n"
        f"Ursprung: {origin}\n"
        "Stand: aktueller Vorgang\n"
        f"Content-Digest: sha256:{digest}\n"
        "Erforderliche Kontrolle: bytegleich mit versuchsqualifiziertem Ursprung\n"
        f"Kontrollnachweis: sha256:{digest} abgeglichen\n"
    )


def _verify_handoff(
    producer: bytes, consumer: bytes, provenance: str, expected_origin: str,
) -> None:
    fields = _fields(provenance)
    digest = _content_digest(producer)
    if producer != consumer:
        raise ProofError("handoff bytes differ")
    if fields.get("Ursprung") != expected_origin:
        raise ProofError("handoff origin differs")
    if fields.get("Herkunft") != "vorheriger Arbeitsschritt":
        raise ProofError("handoff source differs")
    if fields.get("Stand") != "aktueller Vorgang":
        raise ProofError("handoff state differs")
    if fields.get("Content-Digest") != f"sha256:{digest}":
        raise ProofError("handoff content digest differs")
    if (
        fields.get("Erforderliche Kontrolle")
        != "bytegleich mit versuchsqualifiziertem Ursprung"
    ):
        raise ProofError("handoff required control differs")
    if fields.get("Kontrollnachweis") != f"sha256:{digest} abgeglichen":
        raise ProofError("handoff control evidence differs")


def _fields(text: str) -> dict[str, str]:
    fields = {}
    recognized = {"Herkunft", "Ursprung", "Stand", "Content-Digest", "Erforderliche Kontrolle", "Kontrollnachweis", "Eingangsquelle", "Prüfbericht", "Entscheidung", "Begründung"}
    for line in text.splitlines():
        name, separator, value = line.partition(":")
        if separator:
            name = name.strip()
            if name in recognized and name in fields:
                raise ProofError(f"Duplicate recognized evidence label: {name}")
            fields[name] = value.strip()
    return fields


def _directory_digest(root: Path) -> str:
    if not root.exists():
        return _content_digest(b"")
    entries = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        entries.append((path.relative_to(root).as_posix(), _content_digest(path.read_bytes())))
    return _content_digest(json.dumps(entries, separators=(",", ":")).encode("utf-8"))


def _is_rejected(operation, expected_message: str | None = None) -> bool:
    try:
        operation()
    except ProofError as error:
        return expected_message is None or expected_message in str(error)
    return False


def _import_into_second_repository(
    base: Path,
    source: Path,
    revision: str,
    source_workspace_revision: str,
    call: CapabilityCall,
    rules: bytes,
    rules_provenance: str,
) -> tuple[State, bool, frozenset[str], frozenset[str]]:
    """Import the Hauptprozess, reject its missing Capability, then materialize and execute that Capability."""
    source_commit = _reachable_commit(source, source_workspace_revision)
    source_reference = f"{Path(source).resolve().as_posix()}@{source_commit}"
    kunde = init_workspace(Path(base) / "kunde", language="de")
    target = kunde / "hauptprozesse" / HAUPTPROZESS
    target.mkdir()
    hauptprozess_root = f"hauptprozesse/{HAUPTPROZESS}"
    with _source_bytes_readable(source_commit, hauptprozess_root):
        archive = _git_archive(source, f"{source_commit}:{hauptprozess_root}")
    subprocess.run(["tar", "-x", "-C", str(target)], input=archive, check=True)
    _git(kunde, "init", "-q", "-b", "main")
    _git(kunde, "config", "user.email", "cold-walk@example.invalid")
    _git(kunde, "config", "user.name", "Cold Walk")
    _git(kunde, "add", ".")
    _git(
        kunde,
        "commit",
        "-q",
        "-m",
        f"import hauptprozesse/{HAUPTPROZESS} from {source_reference} (tree {revision})",
    )
    imported = _git(kunde, "rev-parse", f"HEAD:hauptprozesse/{HAUPTPROZESS}")
    hauptprozess_only_revision = _git(kunde, "rev-parse", "HEAD")
    proofs = set()
    rejections = set()
    record = b"Name: Kundenrepo\nGeburtsdatum: 01.01.1990\n"
    imported_call = _hauptprozess_call(kunde, imported)
    imported_source = _hauptprozess_source(kunde, imported)
    _verify_source(source, imported_source, rules, rules_provenance)

    if _is_rejected(
        lambda: _execute_capability(
            kunde,
            imported,
            imported_call,
            hauptprozess_only_revision,
            rules,
            record,
        )
    ):
        rejections.add("import.missing_capability")

    capability_root = Path(call.path).parent
    target_capability = kunde / capability_root
    target_capability.mkdir(parents=True)
    with (kunde / "CONTEXT.md").open("a") as router:
        router.write("\nForm: capabilities/ Capability\n")
    with _source_bytes_readable(source_commit, capability_root.as_posix()):
        capability_archive = _git_archive(
            source, f"{source_commit}:{capability_root.as_posix()}"
        )
    subprocess.run(
        ["tar", "-x", "-C", str(target_capability)],
        input=capability_archive,
        check=True,
    )
    _git(kunde, "add", capability_root.as_posix())
    _git(
        kunde,
        "commit",
        "-q",
        "-m",
        (
            f"materialize {capability_root.as_posix()} from "
            f"{source_reference} (tree {call.tree_oid})"
        ),
    )
    imported_workspace_revision = _git(kunde, "rev-parse", "HEAD")
    imported_result = _execute_capability(
        kunde,
        imported,
        imported_call,
        imported_workspace_revision,
        rules,
        record,
    )
    if (
        _resolve_tree(kunde, imported_workspace_revision, capability_root.as_posix())
        == call.tree_oid
        and imported_result.get("sentinel") == "vollstaendigkeitsgrad-v1"
    ):
        proofs.add("import.capability_materialized_and_executed")

    harness = Harness(kunde, imported)
    harness.open(
        "pruefen",
        1,
        {
            **_record_inputs(kunde, "records/antrag-001/erstantrag.md", record.decode("utf-8")),
            imported_source.input_path: rules.decode("utf-8"),
            imported_source.provenance_input: rules_provenance,
        },
    )
    return (
        harness.state("import prueffall in zweites repository"),
        imported == revision,
        frozenset(proofs),
        frozenset(rejections),
    )


def main() -> int:
    """Run the walk in a disposable repository and report every state."""
    try:
        with TemporaryDirectory(prefix="impacts-cold-walk-") as directory:
            result = walk(Path(directory))
    except FixtureInputError as error:
        print(f"FAIL cold walk: {error}")
        return 1
    for router in result.routers:
        print(f"ROUTER {router}")
    for state in result.states:
        verdict = "PASS" if state.valid else "FAIL " + ", ".join(state.codes)
        print(f"STATE {state.label}: {verdict}")
        if state.label.endswith("human-gate"):
            print("STOP Human Gate: offener Schritt hat weder Route noch Freigabe.")
    fired = "binding.reference_digest" in result.mutation_codes
    print(f"MUTATION input geändert: {'binding.reference_digest' if fired else 'nicht erkannt'}")
    import_verdict = "PASS" if result.import_state.valid else "FAIL " + ", ".join(
        result.import_state.codes
    )
    print(f"STATE {result.import_state.label}: {import_verdict}")
    print(
        "IMPORT tree oid gleich in zweitem Repository: "
        f"{'ja' if result.import_oid_equal else 'nein'}"
    )
    for proof in sorted(EXPECTED_PROOFS):
        print(f"PROOF {proof}: {'PASS' if proof in result.proofs else 'FAIL'}")
    for rejection in sorted(EXPECTED_REJECTIONS):
        print(f"REJECTION {rejection}: {'PASS' if rejection in result.rejections else 'FAIL'}")
    print("PASS cold walk" if result.valid else "FAIL cold walk")
    return 0 if result.valid else 1


def _load_human_decision(path: Path) -> dict:
    try:
        decision = load_yaml_strict(path.read_text(encoding="utf-8"))
    except DuplicateKeyError as error:
        line = f":{error.line}" if error.line is not None else ""
        raise FixtureInputError(
            f"{path}{line}: duplicate key: {error.key!r}; remove duplicate key and keep one value."
        ) from None
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        line = getattr(error, "line", None)
        mark = getattr(error, "problem_mark", None) or getattr(
            error, "context_mark", None
        )
        if line is None and mark is not None:
            line = mark.line + 1
        location = f":{line}" if line is not None else ""
        detail = getattr(error, "problem", None) or str(error)
        raise FixtureInputError(
            f"{path}{location}: invalid human-decision YAML ({detail}); correct the YAML fixture."
        ) from None
    if not isinstance(decision, dict):
        raise FixtureInputError(
            f"{path}: human-decision YAML must be a mapping; provide one route, freigabe, and output."
        )
    return decision


def _router_chain(root: Path) -> list[str]:
    hauptprozess = root / "hauptprozesse" / HAUPTPROZESS
    entry = load_frontmatter(hauptprozess / "CONTEXT.md")["einstieg_ref"].removeprefix(
        "arbeitsschritt:"
    )
    step = next(hauptprozess.glob(f"*/{entry}/CONTEXT.md"))
    chain = [
        root / "CONTEXT.md",
        hauptprozess / "CONTEXT.md",
        step.parent.parent / "CONTEXT.md",
        step,
    ]
    return [path.relative_to(root).as_posix() for path in chain]


def _write_outputs(attempt: Path, outputs: dict[str, str]) -> None:
    """Bind existing editable files only if the caller used their actual current bytes."""
    for relative, value in outputs.items():
        path = input_file(attempt, relative)
        if path.exists() and path.read_bytes() != value.encode("utf-8"):
            raise ProofError(f"Existing output differs; read and review current file: {relative}")
    _write_files(attempt, outputs)


def _preflight_files(attempt: Path, files: dict[str, str]) -> None:
    """Reject predictable path/content failures without creating either surface."""
    paths = set()
    portable_paths = {}
    for relative, content in files.items():
        if (
            not isinstance(relative, str)
            or not relative
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or Path(relative).as_posix() != relative
            or "\\" in relative
            or any(ord(char) < 32 for char in relative)
        ):
            raise ProofError(f"File mapping requires a canonical relative filename: {relative!r}")
        if not isinstance(content, str):
            raise ProofError(f"File mapping content must be text: {relative!r}")
        try:
            relative.encode("utf-8")
            content.encode("utf-8")
        except UnicodeEncodeError as error:
            raise ProofError(f"File mapping is not valid UTF-8: {relative!r}") from error
        path = Path(relative)
        if any(len(part.encode("utf-8")) > 255 or part.endswith((".", " ")) for part in path.parts):
            raise ProofError(f"File mapping has an unsupported filename component: {relative!r}")
        portable_key = tuple(
            unicodedata.normalize("NFC", part).casefold() for part in path.parts
        )
        if portable_key in portable_paths:
            raise ProofError(f"File mapping has a portable filename alias: {relative!r}")
        portable_paths[portable_key] = relative
        paths.add(path)
    for portable_key, relative in portable_paths.items():
        if any(portable_key[:length] in portable_paths for length in range(1, len(portable_key))):
            raise ProofError(f"File mapping has a parent-file collision: {relative!r}")
    for relative in paths:
        path = input_file(attempt, relative)
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ProofError(f"File mapping target is not a regular file: {relative.as_posix()!r}")
        for parent in path.parents:
            if parent.exists() and not parent.is_dir():
                raise ProofError(f"File mapping parent is not a directory: {parent}")
            if parent == attempt or attempt in parent.parents:
                if parent.is_symlink():
                    raise ProofError(f"File mapping parent is a symlink: {parent}")


def _record_inputs(root: Path, path: str, payload: str) -> dict[str, str]:
    """Supply an external synthetic receipt, then capture its actual bytes and source."""
    _write_files(root, {path: payload})
    router = root / "CONTEXT.md"
    declaration = "Form: records/ Record Library per source record"
    if declaration not in router.read_text():
        with router.open("a") as handle:
            handle.write("\n" + declaration + "\n")
    received = (root / path).read_bytes()
    return {
        "material/antrag.md": received.decode("utf-8"),
        "material/antrag-herkunft.md": (
            f"Herkunft: synthetischer Eingang\nUrsprung: {path}\n"
            f"Content-Digest: sha256:{_content_digest(received)}\n"
            "Kontrollnachweis: bytegleich mit gespeicherter Eingangsdatei\n"
        ),
    }


def _write_files(attempt: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = input_file(attempt, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _reachable_commit(root: Path, revision: str) -> str:
    """Return the full commit, or stop when the configured source lacks it."""
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "--quiet", f"{revision}^{{commit}}"],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise ProofError(
            f"source revision unreachable in configured source repository: {revision}"
        )
    return result.stdout.strip()


@contextmanager
def _source_bytes_readable(revision: str, path: str) -> Iterator[None]:
    """Stop when the configured source has the commit but cannot supply its bytes."""
    try:
        yield
    except subprocess.CalledProcessError as error:
        raise ProofError(
            f"source bytes unreadable in configured source repository: {revision}:{path}"
        ) from error


def _git_show(root: Path, revision: str, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), "show", f"{revision}:{path}"])


def _git_archive(root: Path, revision: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(root), "archive", "--format=tar", revision]
    )


def _resolve_tree(root: Path, revision: str, path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", f"{revision}:{path}"],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise ProofError("Capability path is absent at workspace revision")
    return result.stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
