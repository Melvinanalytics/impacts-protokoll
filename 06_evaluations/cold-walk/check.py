#!/usr/bin/env python3
"""Walk one synthetic Vorgang and prove local, non-Core evidence chains."""

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory

import yaml

from impacts_protocol import init_workspace, surface_hash, validate
from impacts_protocol.io import load_frontmatter

BEISPIEL_ROOT = Path(__file__).resolve().parent / "beispiel"
BEISPIEL = BEISPIEL_ROOT / "applications" / "prueffall"
CAPABILITY = BEISPIEL_ROOT / "capabilities" / "vollstaendigkeitsgrad"
GRUNDLAGEN = BEISPIEL_ROOT / "grundlagen"
HUMAN_DECISION = BEISPIEL_ROOT / "fixtures" / "human-decision.yaml"
APPLICATION = "prueffall"
VORGANG = "prueffall-001"
CALL_STEP = "vorpruefung/pruefen/CONTEXT.md"
DECISION_STEP = "entscheidung/entscheiden/CONTEXT.md"
CAPABILITY_MARKER = "{{CAPABILITY_TREE_OID}}"
SOURCE_REVISION_MARKER = "{{SOURCE_REVISION}}"

EXPECTED_PROOFS = frozenset(
    {
        "application.handoff_mapping_drives_origin",
        "application.source_requirement_drives_resolution",
        "capability.application_tuple_executed",
        "capability.old_revision_replayed",
        "capability.path_resolved_at_workspace_revision",
        "source.bound_snapshot",
        "source.dirty_worktree_ignored",
        "handoff.content_and_origin_bound",
        "gate.failed_preflight_left_run_unchanged",
        "gate.open_has_no_decision",
        "gate.external_decision_fixture_consumed",
        "import.capability_materialized_and_executed",
    }
)
EXPECTED_REJECTIONS = frozenset(
    {
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
    }
)


class ProofError(ValueError):
    """A local Cold-Walk evidence claim is false or incomplete."""


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
            and "hash.mismatch" in self.mutation_codes
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
        self.run_root = root / "vorgaenge" / VORGANG
        self.laufpfad: list[dict] = []
        self.steps = _application_steps(root, revision)

    def attempt(self, slug: str, versuch: int) -> Path:
        return self.run_root / slug / f"{versuch:03d}"

    def open(self, slug: str, versuch: int, inputs: dict[str, str]) -> dict:
        if self.steps[slug].get("gate") == "human":
            raise ProofError("Human Gate must open through a proven producer handoff")
        attempt = self.attempt(slug, versuch)
        _write_files(attempt, inputs)
        entry = self._active_entry(slug, versuch, attempt)
        self.laufpfad.append(entry)
        self._write()
        return entry

    def wait(self, entry: dict, ausloeser: str, continuation_ref: str) -> None:
        entry["status"] = "wartend"
        entry["wiedereinstieg"] = {
            "ausloeser": ausloeser,
            "continuation_ref": continuation_ref,
        }
        self._write()

    def close(
        self,
        entry: dict,
        outputs: dict[str, str],
        route: str,
        freigabe: dict | None = None,
    ) -> None:
        slug = entry["arbeitsschritt_ref"].removeprefix("arbeitsschritt:")
        attempt = self.attempt(slug, entry["versuch"])
        _write_files(attempt, outputs)
        self._complete_entry(entry, slug, attempt, route, freigabe)
        self._write()

    def close_human(self, entry: dict, decision: dict) -> None:
        slug = entry["arbeitsschritt_ref"].removeprefix("arbeitsschritt:")
        if self.steps[slug].get("gate") != "human":
            raise ProofError("human fixture supplied to a non-gate step")
        route = decision.get("route")
        freigabe = decision.get("freigabe")
        output = decision.get("output")
        if route not in {"freigegeben", "abgelehnt"}:
            raise ProofError("synthetic Human-Decision fixture has no Gate route")
        if not isinstance(freigabe, dict) or not str(freigabe.get("by", "")).startswith("human:"):
            raise ProofError("synthetic Human-Decision fixture has no human attribution")
        if not isinstance(output, str) or not {"Prüfbericht:", "Begründung:"} <= set(
            line.partition(" ")[0] for line in output.splitlines()
        ):
            raise ProofError("Gate output does not satisfy pruefung")
        self.close(entry, {"output/entscheidung.md": output}, route, freigabe)

    def advance(
        self,
        entry: dict,
        outputs: dict[str, str],
        route: str,
        next_slug: str,
        next_versuch: int,
        next_inputs: dict[str, str],
    ) -> dict:
        """Run mutation-free preflight, then perform one logical Harness transition."""
        if self.steps[next_slug].get("gate") == "human":
            self._preflight_gate(entry, outputs, route, next_slug, next_inputs)

        slug = entry["arbeitsschritt_ref"].removeprefix("arbeitsschritt:")
        attempt = self.attempt(slug, entry["versuch"])
        next_attempt = self.attempt(next_slug, next_versuch)
        _write_files(attempt, outputs)
        _write_files(next_attempt, next_inputs)
        self._complete_entry(entry, slug, attempt, route)
        next_entry = self._active_entry(next_slug, next_versuch, next_attempt)
        self.laufpfad.append(next_entry)
        self._write()
        return next_entry

    def state(self, label: str) -> State:
        report = validate(self.root)
        return State(label, report.valid, tuple(sorted({issue.code for issue in report.issues})))

    def _active_entry(self, slug: str, versuch: int, attempt: Path) -> dict:
        return {
            "arbeitsschritt_ref": f"arbeitsschritt:{slug}",
            "versuch": versuch,
            "status": "aktiv",
            "eingabe_hash": surface_hash(attempt, self.steps[slug]["eingaben"]),
        }

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
        entry["ausgabe_hash"] = surface_hash(attempt, self.steps[slug]["ausgaben"])
        if freigabe is not None:
            entry["freigabe"] = freigabe

    def _preflight_gate(
        self,
        entry: dict,
        outputs: dict[str, str],
        route: str,
        next_slug: str,
        inputs: dict[str, str],
    ) -> None:
        missing = set(self.steps[next_slug]["eingaben"]) - set(inputs)
        if missing:
            raise ProofError(f"Gate inputs missing: {sorted(missing)}")
        producer_slug = entry["arbeitsschritt_ref"].removeprefix("arbeitsschritt:")
        handoff = _application_handoff(
            self.root, self.revision, producer_slug, route
        )
        if handoff.consumer_slug != next_slug:
            raise ProofError("Gate target differs from Application handoff")
        if handoff.producer_output not in outputs:
            raise ProofError("Gate producer output differs from Application handoff")
        if handoff.consumer_input not in inputs:
            raise ProofError("Gate consumer input differs from Application handoff")
        if handoff.provenance_input not in inputs:
            raise ProofError("Gate provenance input missing")
        _verify_handoff(
            outputs[handoff.producer_output].encode("utf-8"),
            inputs[handoff.consumer_input].encode("utf-8"),
            inputs[handoff.provenance_input],
            handoff.origin(producer_slug, entry["versuch"]),
        )

    def _write(self) -> None:
        metadata = {
            "type": "vorgang",
            "id": f"vorgang:{VORGANG}",
            "application_revision": f"git-tree:{self.revision}",
            "laufpfad": self.laufpfad,
        }
        frontmatter = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).rstrip()
        self.run_root.mkdir(parents=True, exist_ok=True)
        (self.run_root / "CONTEXT.md").write_text(
            f"---\n{frontmatter}\n---\n\n# Prüffall 001\n\nSynthetischer Lauf des Cold Walk.\n",
            encoding="utf-8",
        )


def walk(base: Path) -> WalkResult:
    """Initialize, bind, run and mutate every declared evidence chain."""
    root, source_commit, capability_tree, revision, workspace_revision = _prepare_workspace(
        Path(base)
    )
    proofs: set[str] = set()
    rejections: set[str] = set()

    call = _application_call(root, revision)
    source_ref = _application_source(root, revision)
    handoff = _application_handoff(root, revision, "pruefen", "bestanden")
    rules, rules_provenance = _materialize_source(root, source_ref)
    _verify_source(root, source_ref, rules, rules_provenance)
    proofs.add("source.bound_snapshot")

    changed_step = root / "applications" / APPLICATION / CALL_STEP
    changed_body = changed_step.read_text(encoding="utf-8")
    changed_body = changed_body.replace(
        "- Ursprung: `grundlagen/pruefregeln.md`",
        "- Ursprung: `grundlagen/andere-regeln.md`",
    ).replace(
        "`output/pruefbericht.md -> arbeitsschritt:entscheiden/input/pruefbericht.md`",
        "`output/pruefbericht.md -> arbeitsschritt:entscheiden/input/pruefbericht-alternativ.md`",
    )
    changed_step.write_text(changed_body, encoding="utf-8")
    changed_decision = root / "applications" / APPLICATION / DECISION_STEP
    changed_decision_body = changed_decision.read_text(encoding="utf-8").replace(
        "input/pruefbericht-herkunft.md",
        "input/pruefbericht-alternativ-herkunft.md",
    ).replace(
        "input/pruefbericht.md",
        "input/pruefbericht-alternativ.md",
    )
    changed_decision.write_text(changed_decision_body, encoding="utf-8")
    _git(root, "add", f"applications/{APPLICATION}")
    _git(root, "commit", "-q", "-m", "mutate application source and handoff authority")
    changed_revision = _git(root, "rev-parse", f"HEAD:applications/{APPLICATION}")
    changed_source = _application_source(root, changed_revision)
    changed_handoff = _application_handoff(root, changed_revision, "pruefen", "bestanden")
    changed_rules, _ = _materialize_source(root, changed_source)
    if changed_source.path != source_ref.path and changed_rules != rules:
        proofs.add("application.source_requirement_drives_resolution")
    changed_harness = Harness(root, changed_revision)
    probe_entry = {"arbeitsschritt_ref": "arbeitsschritt:pruefen", "versuch": 2}
    probe_payload = "authority probe\n"
    changed_provenance = _handoff_provenance(
        changed_handoff.origin("pruefen", 2), probe_payload.encode("utf-8")
    )
    changed_inputs = {
        changed_handoff.consumer_input: probe_payload,
        changed_handoff.provenance_input: changed_provenance,
    }
    changed_harness._preflight_gate(
        probe_entry,
        {changed_handoff.producer_output: probe_payload},
        "bestanden",
        changed_handoff.consumer_slug,
        changed_inputs,
    )
    old_inputs_rejected = _is_rejected(
        lambda: changed_harness._preflight_gate(
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
        proofs.add("application.handoff_mapping_drives_origin")

    wrong_path_body = changed_step.read_text(encoding="utf-8").replace(
        "capabilities/vollstaendigkeitsgrad/CONTEXT.md",
        "capabilities/falsch/CONTEXT.md",
    )
    changed_step.write_text(wrong_path_body, encoding="utf-8")
    _git(root, "add", f"applications/{APPLICATION}")
    _git(root, "commit", "-q", "-m", "mutate application capability path")
    wrong_path_revision = _git(root, "rev-parse", f"HEAD:applications/{APPLICATION}")
    wrong_path_workspace_revision = _git(root, "rev-parse", "HEAD")
    wrong_path_call = _application_call(root, wrong_path_revision)

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

    first_record = b"Name: Erika Beispiel\nGeburtsdatum:\n"
    first_result = _execute_capability(
        root, revision, call, workspace_revision, rules, first_record
    )
    if first_result["sentinel"] == "vollstaendigkeitsgrad-v1" and call.tree_oid == capability_tree:
        proofs.add("capability.application_tuple_executed")
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
    _git(root, "commit", "-q", "-m", "mutate capability after application binding")
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
        {"input/antrag.md": first_record.decode("utf-8"), **common_inputs},
    )
    states.append(harness.state("pruefen 001 aktiv"))
    first_report = _render_report(call, workspace_revision, first_result)

    entry = harness.advance(
        entry,
        {"output/pruefbericht.md": first_report},
        "klaerung",
        "nachfordern",
        1,
        {"input/pruefbericht.md": first_report},
    )
    states.append(harness.state("nachfordern 001 aktiv nach klaerung"))

    harness.wait(entry, "unterlagen-nachgereicht", "records/antrag-001")
    states.append(harness.state("nachfordern 001 wartend"))

    second_record = "Name: Erika Beispiel\nGeburtsdatum: 01.01.1990\n"
    entry = harness.advance(
        entry,
        {"output/nachforderung.md": "Bitte Geburtsdatum nachreichen\n"},
        "nachgereicht",
        "pruefen",
        2,
        {"input/antrag.md": second_record, **common_inputs},
    )
    states.append(harness.state("pruefen 002 aktiv nach nachgereicht"))

    second_attempt = harness.attempt("pruefen", 2)
    second_result = _execute_capability(
        root,
        revision,
        call,
        workspace_revision,
        (second_attempt / source_ref.input_path).read_bytes(),
        (second_attempt / "input/antrag.md").read_bytes(),
    )
    second_report = _render_report(call, workspace_revision, second_result)
    origin = handoff.origin("pruefen", entry["versuch"])
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
            _directory_digest(harness.run_root),
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
            _directory_digest(harness.run_root),
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
    states.append(harness.state("entscheiden 001 aktiv nach bestanden human-gate"))

    producer = harness.attempt("pruefen", 2) / "output/pruefbericht.md"
    consumer = harness.attempt("entscheiden", 1) / "input/pruefbericht.md"
    provenance = harness.attempt("entscheiden", 1) / "input/pruefbericht-herkunft.md"
    _verify_handoff(producer.read_bytes(), consumer.read_bytes(), provenance.read_text(), origin)
    if "ausgabe_hash" in harness.laufpfad[-2] and "eingabe_hash" in harness.laufpfad[-1]:
        proofs.add("handoff.content_and_origin_bound")
    if "gewaehlte_route" not in entry and "freigabe" not in entry:
        proofs.add("gate.open_has_no_decision")

    decision = yaml.safe_load(HUMAN_DECISION.read_text(encoding="utf-8"))
    harness.close_human(entry, decision)
    if (
        entry.get("freigabe") == decision["freigabe"]
        and entry.get("gewaehlte_route") == decision["route"]
    ):
        proofs.add("gate.external_decision_fixture_consumed")
    states.append(harness.state("entscheiden 001 abgeschlossen freigegeben end:entschieden"))

    (harness.attempt("pruefen", 1) / "input/antrag.md").write_text(
        "Antrag manipuliert\n", encoding="utf-8"
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
    root = init_workspace(base / "workspace")
    shutil.copytree(BEISPIEL, root / "applications" / APPLICATION)
    shutil.copytree(CAPABILITY, root / "capabilities" / "vollstaendigkeitsgrad")
    shutil.copytree(GRUNDLAGEN, root / "grundlagen")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "cold-walk@example.invalid")
    _git(root, "config", "user.name", "Cold Walk")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "synthetic application sources")
    source_commit = _git(root, "rev-parse", "HEAD")
    capability_tree = _git(root, "rev-parse", "HEAD:capabilities/vollstaendigkeitsgrad")

    step = root / "applications" / APPLICATION / CALL_STEP
    body = step.read_text(encoding="utf-8")
    if CAPABILITY_MARKER not in body or SOURCE_REVISION_MARKER not in body:
        raise ProofError("Application has no Capability or source revision marker")
    step.write_text(
        body.replace(CAPABILITY_MARKER, capability_tree).replace(
            SOURCE_REVISION_MARKER, source_commit
        ),
        encoding="utf-8",
    )
    _git(root, "add", f"applications/{APPLICATION}")
    _git(root, "commit", "-q", "-m", "bind application capability tuple")
    workspace_revision = _git(root, "rev-parse", "HEAD")
    revision = _git(root, "rev-parse", f"HEAD:applications/{APPLICATION}")
    return root, source_commit, capability_tree, revision, workspace_revision


def _application_call(root: Path, application_revision: str) -> CapabilityCall:
    text = _application_body(root, application_revision, CALL_STEP)
    values = {}
    for name in ("Aufruf-ID", "Capability-Pfad", "Capability-Revision", "Operation"):
        match = re.search(rf"(?m)^- {re.escape(name)}:\s*`?([^`\n]+)`?$", text)
        if not match:
            raise ProofError(f"Application call lacks {name}")
        values[name] = match.group(1).strip()
    revision = values["Capability-Revision"]
    if not revision.startswith("git-tree:"):
        raise ProofError("Capability revision is not a Git tree")
    return CapabilityCall(
        call_id=values["Aufruf-ID"],
        path=values["Capability-Pfad"],
        tree_oid=revision.removeprefix("git-tree:"),
        operation=values["Operation"],
    )


def _application_source(root: Path, application_revision: str) -> SourceRef:
    text = _application_body(root, application_revision, CALL_STEP)
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
            raise ProofError(f"Application source requirement lacks {name}")
        values[name] = match.group(1).strip()
    stand = values["Stand"]
    if not stand.startswith("git:"):
        raise ProofError("Application source revision is not Git-bound")
    return SourceRef(
        input_path=values["Quell-Eingabe"],
        source=values["Herkunft"],
        path=values["Ursprung"],
        revision=stand.removeprefix("git:"),
        minimum_control=values["Erforderliche Kontrolle"],
    )


def _application_handoff(
    root: Path,
    application_revision: str,
    producer_slug: str,
    route: str,
) -> Handoff:
    step_path = next(
        (
            path
            for path in _application_context_paths(root, application_revision)
            if path.count("/") == 2 and path.endswith(f"/{producer_slug}/CONTEXT.md")
        ),
        None,
    )
    if step_path is None:
        raise ProofError(f"Application has no producer step {producer_slug}")
    text = _application_body(root, application_revision, step_path)
    pattern = re.compile(
        r"(?m)^Bei Route `([^`]+)`: `([^`]+) -> "
        r"arbeitsschritt:([^/`]+)/([^`]+)`\.$"
    )
    matches = [match for match in pattern.finditer(text) if match.group(1) == route]
    if len(matches) != 1:
        raise ProofError(
            f"Application handoff for {producer_slug}/{route} is not unique"
        )
    match = matches[0]
    return Handoff(
        route=match.group(1),
        producer_output=match.group(2),
        consumer_slug=match.group(3),
        consumer_input=match.group(4),
    )


def _application_context_paths(root: Path, application_revision: str) -> tuple[str, ...]:
    return tuple(
        path
        for path in _git(root, "ls-tree", "-r", "--name-only", application_revision).splitlines()
        if path.endswith("CONTEXT.md")
    )


def _application_body(root: Path, application_revision: str, path: str) -> str:
    text = _git_show(root, application_revision, path).decode("utf-8")
    _, body = _frontmatter_and_body(text)
    return body


def _application_steps(
    root: Path, application_revision: str
) -> dict[str, dict]:
    metadata = {}
    for path in _application_context_paths(root, application_revision):
        match = re.fullmatch(r"[^/]+/([^/]+)/CONTEXT\.md", path)
        if not match:
            continue
        slug = match.group(1)
        step_metadata, _ = _frontmatter_and_body(
            _git_show(root, application_revision, path).decode("utf-8")
        )
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
        raise ProofError("Application frontmatter has no closing delimiter") from error
    metadata = yaml.safe_load("\n".join(lines[1:closing])) or {}
    if not isinstance(metadata, dict):
        raise ProofError("Application frontmatter is not an object")
    return metadata, "\n".join(lines[closing + 1 :])


def _execute_capability(
    root: Path,
    application_revision: str,
    requested: CapabilityCall,
    workspace_revision: str,
    rules: bytes,
    record: bytes,
) -> dict:
    authoritative = _application_call(root, application_revision)
    if requested != authoritative:
        raise ProofError("requested Capability tuple differs from bound Application")
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
            raise ProofError("Capability operation differs from bound Application")
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
    producer: bytes, consumer: bytes, provenance: str, expected_origin: str
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
    for line in text.splitlines():
        name, separator, value = line.partition(":")
        if separator:
            fields[name.strip()] = value.strip()
    return fields


def _content_digest(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _directory_digest(root: Path) -> str:
    if not root.exists():
        return _content_digest(b"")
    entries = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        entries.append((path.relative_to(root).as_posix(), _content_digest(path.read_bytes())))
    return _content_digest(json.dumps(entries, separators=(",", ":")).encode("utf-8"))


def _is_rejected(operation) -> bool:
    try:
        operation()
    except ProofError:
        return True
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
    """Import the Application, reject its missing Capability, then materialize and run it."""
    kunde = init_workspace(Path(base) / "kunde")
    target = kunde / "applications" / APPLICATION
    target.mkdir()
    archive = _git_archive(source, revision)
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
        (
            f"import applications/{APPLICATION} from "
            f"{source.name}@{source_workspace_revision[:12]} (tree {revision})"
        ),
    )
    imported = _git(kunde, "rev-parse", f"HEAD:applications/{APPLICATION}")
    application_only_revision = _git(kunde, "rev-parse", "HEAD")
    proofs = set()
    rejections = set()
    record = b"Name: Kundenrepo\nGeburtsdatum: 01.01.1990\n"
    imported_call = _application_call(kunde, imported)
    imported_source = _application_source(kunde, imported)

    if _is_rejected(
        lambda: _execute_capability(
            kunde,
            imported,
            imported_call,
            application_only_revision,
            rules,
            record,
        )
    ):
        rejections.add("import.missing_capability")

    capability_root = Path(call.path).parent
    target_capability = kunde / capability_root
    target_capability.mkdir(parents=True)
    capability_archive = _git_archive(
        source, f"{source_workspace_revision}:{capability_root.as_posix()}"
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
            f"{source.name}@{source_workspace_revision[:12]} "
            f"(tree {call.tree_oid})"
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
            "input/antrag.md": record.decode("utf-8"),
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
    with TemporaryDirectory(prefix="impacts-cold-walk-") as directory:
        result = walk(Path(directory))
    for router in result.routers:
        print(f"ROUTER {router}")
    for state in result.states:
        verdict = "PASS" if state.valid else "FAIL " + ", ".join(state.codes)
        print(f"STATE {state.label}: {verdict}")
        if state.label.endswith("human-gate"):
            print("STOP Human Gate: offener Schritt hat weder Route noch Freigabe.")
    fired = "hash.mismatch" in result.mutation_codes
    print(f"MUTATION input geändert: {'hash.mismatch' if fired else 'nicht erkannt'}")
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


def _router_chain(root: Path) -> list[str]:
    application = root / "applications" / APPLICATION
    entry = load_frontmatter(application / "CONTEXT.md")["einstieg_ref"].removeprefix(
        "arbeitsschritt:"
    )
    step = next(application.glob(f"*/{entry}/CONTEXT.md"))
    chain = [
        root / "CONTEXT.md",
        application / "CONTEXT.md",
        step.parent.parent / "CONTEXT.md",
        step,
    ]
    return [path.relative_to(root).as_posix() for path in chain]


def _write_files(attempt: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = attempt / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


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
