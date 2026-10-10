from contextlib import redirect_stdout
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

import pytest


ROOT = Path(__file__).resolve().parents[1]
COLD_WALK = ROOT / "06_evaluations" / "cold-walk"
CHECK_PATH = COLD_WALK / "check.py"
BEISPIEL = COLD_WALK / "beispiel" / "applications" / "prueffall"
from impacts_protocol import validate


def _tree_bytes(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def _producer(tmp_path):
    check = _check_module()
    root, _, _, revision, _ = check._prepare_workspace(tmp_path)
    source = check._application_source(root, revision)
    rules, provenance = check._materialize_source(root, source)
    harness = check.Harness(root, revision)
    entry = harness.open("pruefen", 1, {
        "input/antrag.md": "Synthetic application.\n",
        "input/antrag-herkunft.md": "Herkunft: synthetic\n",
        source.input_path: rules.decode(), source.provenance_input: provenance,
    })
    payload = "Synthetic handoff report.\n"
    handoff = check._application_handoff(root, revision, "pruefen", "bestanden")
    inputs = {handoff.consumer_input: payload, handoff.provenance_input: check._handoff_provenance(handoff.origin("pruefen", 1), payload.encode())}
    return check, harness, entry, handoff, payload, inputs


def _terminal(tmp_path, *, open_attempt=True):
    from tests.support import write_context, write_workstep, git
    check = _check_module()
    root = check.init_workspace(tmp_path / "terminal-workspace")
    app = root / "applications/prueffall"
    write_context(app / "CONTEXT.md", {
        "type": "hauptprozess", "id": "hauptprozess:prueffall",
        "leistung": {"ergebnis": "Synthetic final report", "kennzahl": "time", "abnahme": ["final report"]},
        "einstieg_ref": "arbeitsschritt:finish",
    })
    part = app / "work"
    write_context(part / "CONTEXT.md", {"type": "teilprozess", "id": "teilprozess:work", "ergebnis": "Synthetic report"})
    write_workstep(part, "finish")
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Synthetic fixture")
    git(root, "add", ".")
    git(root, "commit", "-m", "synthetic terminal Application")
    harness = check.Harness(root, git(root, "rev-parse", "HEAD:applications/prueffall"))
    entry = harness.open("finish", 1, {"input/auftrag.md": "Synthetic task"}) if open_attempt else None
    return check, harness, entry


def _run_snapshot(harness):
    return (
        _tree_bytes(harness.run_root),
        {p.relative_to(harness.run_root).as_posix() for p in harness.run_root.rglob("*")},
        deepcopy(harness.laufpfad),
    )


@pytest.mark.parametrize("attempt", [True, False, 0, -1, 1000, "1", None, 1.0])
def test_proposed_successor_attempt_rejects_before_writes(tmp_path, attempt):
    check, harness, entry, handoff, payload, inputs = _producer(tmp_path)
    before = _run_snapshot(harness)
    with pytest.raises(check.ProofError):
        harness.advance(entry, {handoff.producer_output: payload}, "bestanden", "entscheiden", attempt, inputs)
    assert _run_snapshot(harness) == before


@pytest.mark.parametrize("trigger,reference", [
    (" ", "receipt.md"), ("resume", "\t\n"), ("", "receipt.md"),
    ("resume", None), ("resume\ud800", "receipt.md"), ("resume", "receipt\ud800.md"),
])
def test_proposed_wait_metadata_rejects_before_writes(tmp_path, trigger, reference):
    check, harness, entry, *_ = _producer(tmp_path)
    before = _run_snapshot(harness)
    with pytest.raises(check.ProofError):
        harness.wait(entry, trigger, reference)
    assert _run_snapshot(harness) == before


@pytest.mark.parametrize("approval", [
    {"by": "human:synthetic"},
    {"at": "2040-01-01T00:00:00Z"},
    {"by": "human:", "at": "2040-01-01T00:00:00Z"},
    {"by": "human: ", "at": "2040-01-01T00:00:00Z"},
    {"by": "agent:synthetic", "at": "2040-01-01T00:00:00Z"},
    {"by": "human::synthetic", "at": "2040-01-01T00:00:00Z"},
    {"by": 42, "at": "2040-01-01T00:00:00Z"},
    {"by": "human:synthetic", "at": "not-a-date"},
    {"by": "human:synthetic", "at": "2040-02-30T12:00:00+01:00"},
    {"by": "human:synthetic", "at": "2040-01-01T00:00:00"},
    {"by": "human:synthetic", "at": None},
    {"by": "human:synthetic", "at": "2040-01-01T00:00:00Z", "extra": "unsupported"},
])
def test_proposed_human_approval_rejects_before_writes(tmp_path, approval):
    check, harness, entry, handoff, payload, inputs = _producer(tmp_path)
    gate = harness.advance(entry, {handoff.producer_output: payload}, "bestanden", "entscheiden", 1, inputs)
    decision = check._load_human_decision(check.HUMAN_DECISION)
    decision["freigabe"] = approval
    before = _run_snapshot(harness)
    with pytest.raises(check.ProofError):
        harness.close_human(gate, decision)
    assert _run_snapshot(harness) == before


@pytest.mark.parametrize("surface", ["input", "output"])
@pytest.mark.parametrize("mutation", [
    "none-value", "bytes-value", "surrogate-value", "none-key", "surrogate-key",
    "absolute-path", "parent-path", "wrong-folder", "parent-collision", "noncanonical-path",
    "existing-parent-file",
])
def test_proposed_handoff_mapping_rejects_before_either_surface_writes(tmp_path, surface, mutation):
    check, harness, current, handoff, payload, inputs = _producer(tmp_path)
    outputs = {handoff.producer_output: payload}
    files = inputs if surface == "input" else outputs
    extra = f"{surface}/extra.md"
    if mutation == "none-value":
        files[extra] = None
    elif mutation == "bytes-value":
        files[extra] = b"unsupported bytes"
    elif mutation == "surrogate-value":
        files[handoff.producer_output if surface == "output" else extra] = "review\ud800"
    elif mutation == "none-key":
        files[None] = "extra"
    elif mutation == "surrogate-key":
        files[f"{surface}/extra\ud800.md"] = "extra"
    elif mutation == "absolute-path":
        files[(harness.run_root / "outside.md").as_posix()] = "extra"
    elif mutation == "parent-path":
        files[f"{surface}/../../outside.md"] = "extra"
    elif mutation == "wrong-folder":
        files["output/extra.md" if surface == "input" else "input/extra.md"] = "extra"
    elif mutation == "parent-collision":
        files[(handoff.consumer_input if surface == "input" else handoff.producer_output) + "/child"] = "extra"
    elif mutation == "noncanonical-path":
        files[f"{surface}/./extra.md"] = "extra"
    else:
        if surface == "input":
            (harness.run_root / "entscheiden").write_text("existing parent file")
        else:
            blocker = harness.attempt("pruefen", 1) / "output/blocker"
            blocker.parent.mkdir()
            blocker.write_text("existing parent file")
            files["output/blocker/child"] = "extra"
    before = _run_snapshot(harness)
    with pytest.raises(check.ProofError):
        harness.advance(current, outputs, "bestanden", "entscheiden", 1, inputs)
    assert _run_snapshot(harness) == before


@pytest.mark.parametrize("surface", ["input", "output"])
@pytest.mark.parametrize("position", ["leaf", "parent"])
@pytest.mark.parametrize("component", ["a" * 256, "é" * 128, "trailing.", "trailing "])
def test_unsupported_filename_components_reject_before_either_surface_writes(tmp_path, surface, position, component):
    check, harness, entry, handoff, payload, inputs = _producer(tmp_path)
    outputs = {handoff.producer_output: payload}
    files = inputs if surface == "input" else outputs
    relative = f"{surface}/{component}" + ("/child.md" if position == "parent" else "")
    files[relative] = "Synthetic extra file.\n"
    before = _run_snapshot(harness)
    with pytest.raises(check.ProofError, match="unsupported filename component"):
        harness.advance(entry, outputs, "bestanden", "entscheiden", 1, inputs)
    assert _run_snapshot(harness) == before


@pytest.mark.parametrize("position", ["leaf", "parent"])
@pytest.mark.parametrize("component", ["a" * 255, "é" * 127 + "a"])
def test_255_byte_filename_components_preserve_valid_handoff_and_raw_hashes(tmp_path, position, component):
    check, harness, entry, handoff, payload, inputs = _producer(tmp_path)
    assert len(component.encode("utf-8")) == 255
    suffix = component + ("/child.md" if position == "parent" else "")
    extra = "Synthetic extra file.\n"
    outputs = {handoff.producer_output: payload, f"output/{suffix}": extra}
    inputs[f"input/{suffix}"] = extra
    consumer = harness.advance(entry, outputs, "bestanden", "entscheiden", 1, inputs)
    assert (harness.attempt("pruefen", 1) / f"output/{suffix}").read_bytes() == extra.encode()
    assert (harness.attempt("entscheiden", 1) / f"input/{suffix}").read_bytes() == extra.encode()
    assert entry["ausgabe_hash"] == check.surface_hash(harness.attempt("pruefen", 1), harness.steps["pruefen"]["ausgaben"])
    assert consumer["eingabe_hash"] == check.surface_hash(harness.attempt("entscheiden", 1), harness.steps["entscheiden"]["eingaben"])
    assert validate(harness.root).valid


def test_proposed_terminal_mapping_rejects_existing_directory_before_writes(tmp_path):
    check, harness, entry = _terminal(tmp_path)
    (harness.attempt("finish", 1) / "output/directory").mkdir(parents=True)
    before = _run_snapshot(harness)
    with pytest.raises(check.ProofError):
        harness.close(entry, {"output/ergebnis.md": "final", "output/directory": "extra"}, "fertig")
    assert _run_snapshot(harness) == before


@pytest.mark.parametrize("component", ["a" * 256, "é" * 128, "trailing.", "trailing "])
def test_initial_filename_components_reject_before_writes(tmp_path, component):
    check, harness, _ = _terminal(tmp_path, open_attempt=False)
    before = _run_snapshot(harness)
    with pytest.raises(check.ProofError, match="unsupported filename component"):
        harness.open("finish", 1, {"input/auftrag.md": "task", f"input/{component}": "extra"})
    assert _run_snapshot(harness) == before
    assert not harness.run_root.exists()


@pytest.mark.parametrize("component", ["a" * 256, "é" * 128, "trailing.", "trailing "])
def test_terminal_filename_components_reject_before_writes(tmp_path, component):
    check, harness, entry = _terminal(tmp_path)
    before = _run_snapshot(harness)
    with pytest.raises(check.ProofError, match="unsupported filename component"):
        harness.close(entry, {"output/ergebnis.md": "final", f"output/{component}": "extra"}, "fertig")
    assert _run_snapshot(harness) == before


@pytest.mark.parametrize("surface", ["input", "output"])
@pytest.mark.parametrize("collision", ["case", "unicode", "case-parent", "unicode-parent"])
def test_proposed_portable_name_collisions_reject_before_writes(tmp_path, surface, collision):
    check, harness, current, handoff, payload, inputs = _producer(tmp_path)
    outputs = {handoff.producer_output: payload}
    files = inputs if surface == "input" else outputs
    if collision.startswith("case"):
        original = handoff.consumer_input if surface == "input" else handoff.producer_output
        alias = original.upper().replace(surface.upper() + "/", surface + "/", 1)
    else:
        original = f"{surface}/caf\u00e9.md"
        alias = f"{surface}/cafe\u0301.md"
        files[original] = "original extra content"
    if collision.endswith("parent"):
        alias += "/child.md"
    files[alias] = "different alias content"
    before = _run_snapshot(harness)
    with pytest.raises(check.ProofError):
        harness.advance(current, outputs, "bestanden", "entscheiden", 1, inputs)
    assert _run_snapshot(harness) == before


def test_distinct_unicode_and_case_names_preserve_valid_handoff(tmp_path):
    check, harness, current, handoff, payload, inputs = _producer(tmp_path)
    inputs.update({"input/caf\u00e9-1.md": "first", "input/CAF\u00c9-2.md": "second"})
    outputs = {handoff.producer_output: payload, "output/caf\u00e9-1.md": "first", "output/CAF\u00c9-2.md": "second"}
    consumer = harness.advance(current, outputs, "bestanden", "entscheiden", 1, inputs)
    assert consumer["status"] == "aktiv"
    assert (harness.attempt("entscheiden", 1) / "input/caf\u00e9-1.md").read_text() == "first"
    assert (harness.attempt("entscheiden", 1) / "input/CAF\u00c9-2.md").read_text() == "second"
    assert validate(harness.root).valid


def test_valid_proposed_transition_neighbors_keep_extra_files_and_real_hashes(tmp_path):
    check, harness, entry, handoff, payload, inputs = _producer(tmp_path)
    harness.wait(entry, "resume", "opaque:synthetic-receipt")
    outputs = {handoff.producer_output: payload, "output/notes/context.md": "extra output"}
    inputs["input/notes/context.md"] = "extra input"
    consumer = harness.advance(entry, outputs, "bestanden", "entscheiden", 2, inputs)
    decision = check._load_human_decision(check.HUMAN_DECISION)
    decision["freigabe"]["at"] = "2040-02-29T23:59:59+02:00"
    harness.close_human(consumer, decision)
    assert (harness.attempt("pruefen", 1) / "output/notes/context.md").read_text() == "extra output"
    attempt = harness.attempt("entscheiden", 2)
    assert (attempt / "input/notes/context.md").read_text() == "extra input"
    assert consumer["eingabe_hash"] == check.surface_hash(attempt, harness.steps["entscheiden"]["eingaben"])
    assert consumer["ausgabe_hash"] == check.surface_hash(attempt, harness.steps["entscheiden"]["ausgaben"])
    assert validate(harness.root).valid


@pytest.mark.parametrize("mutation", ["input", "stale-entry", "stale-router", "stale-revision", "stale-id", "stale-type", "wrong-route", "existing-successor"])
def test_transition_rejects_before_any_run_writes(tmp_path, mutation):
    check, harness, entry, handoff, payload, inputs = _producer(tmp_path)
    candidate = entry
    if mutation == "input":
        (harness.attempt("pruefen", 1) / "input/antrag.md").write_text("tampered")
        assert "hash.mismatch" in {issue.code for issue in validate(harness.root).issues}
    elif mutation == "stale-entry":
        candidate = dict(entry)
    elif mutation == "stale-router":
        path = harness.run_root / "CONTEXT.md"
        path.write_text(path.read_text().replace("status: aktiv", "status: wartend"))
    elif mutation == "existing-successor":
        (harness.attempt("entscheiden", 1) / "input").mkdir(parents=True)
    elif mutation.startswith("stale-"):
        from tests.support import read_context, replace_context
        path = harness.run_root / "CONTEXT.md"
        metadata = read_context(path)
        field = {"stale-revision": "application_revision", "stale-id": "id", "stale-type": "type"}[mutation]
        metadata[field] = ("git-tree:" + check._git(harness.root, "rev-parse", "HEAD^:applications/prueffall") if field == "application_revision" else "vorgang:other" if field == "id" else "workspace")
        replace_context(path, metadata)
        if field == "application_revision":
            assert validate(harness.root).valid
    before = _tree_bytes(harness.run_root)
    with pytest.raises(check.ProofError):
        harness.advance(candidate, {handoff.producer_output: payload}, "klaerung" if mutation == "wrong-route" else "bestanden", "entscheiden", 1, inputs)
    assert _tree_bytes(harness.run_root) == before


@pytest.mark.parametrize("operation", ["wait", "close", "open", "advance"])
def test_all_local_successor_mutations_recheck_current_bound_input(tmp_path, operation):
    check, harness, entry, handoff, payload, inputs = _producer(tmp_path)
    (harness.attempt("pruefen", 1) / "input/antrag.md").write_text("tampered")
    assert "hash.mismatch" in {issue.code for issue in validate(harness.root).issues}
    before = _run_snapshot(harness)
    with pytest.raises(check.ProofError):
        if operation == "wait":
            harness.wait(entry, "resume", "response.md")
        elif operation == "close":
            harness.close(entry, {handoff.producer_output: payload}, "bestanden")
        elif operation == "open":
            harness.open("entscheiden", 1, inputs)
        else:
            harness.advance(entry, {handoff.producer_output: payload}, "bestanden", "entscheiden", 1, inputs)
    assert _run_snapshot(harness) == before


@pytest.mark.parametrize("mutation", ["wrong-route", "missing-input", "missing-output"])
def test_immediate_consumer_requires_declared_route_and_complete_surfaces(tmp_path, mutation):
    check, harness, entry, handoff, payload, inputs = _producer(tmp_path)
    if mutation == "missing-input":
        inputs.pop(handoff.provenance_input)
    outputs = {} if mutation == "missing-output" else {handoff.producer_output: payload}
    before = _run_snapshot(harness)
    with pytest.raises(check.ProofError):
        harness.advance(entry, outputs, "absent" if mutation == "wrong-route" else "bestanden", "entscheiden", 1, inputs)
    assert _run_snapshot(harness) == before


@pytest.mark.parametrize("label", ["Ursprung", "Content-Digest", "Kontrollnachweis"])
@pytest.mark.parametrize("identical", [False, True])
def test_handoff_reader_rejects_duplicate_recognized_labels(label, identical):
    check = _check_module()
    payload = b"Synthetic handoff.\n"
    origin = "pruefen/001/output/pruefbericht.md"
    canonical = check._handoff_provenance(origin, payload)
    check._verify_handoff(payload, payload, canonical, origin)
    value = check._fields(canonical)[label] if identical else "contradictory synthetic evidence"
    with pytest.raises(check.ProofError, match="Duplicate recognized evidence label"):
        check._verify_handoff(payload, payload, f"{label}: {value}\n" + canonical, origin)


def test_new_gate_revision_preserves_legacy_definition_bytes(tmp_path):
    check = _check_module()
    root, _, _, revision, _ = check._prepare_workspace(tmp_path)
    historical = check._git_show(root, "HEAD^", "applications/prueffall/" + check.DECISION_STEP)
    assert historical == (BEISPIEL / check.DECISION_STEP).read_bytes()
    assert check._git_show(root, revision, check.DECISION_STEP) == check.GATE_REVISION.read_bytes()
    assert check._git(root, "rev-parse", "HEAD^:applications/prueffall") != revision


def test_final_rejection_ends_new_run_negatively(tmp_path):
    check = _check_module()
    import yaml
    decision = yaml.safe_load(check.HUMAN_DECISION.read_text())
    decision["route"] = "abgelehnt"
    decision["output"] = "Prüfbericht: vollständig\nEntscheidung: abgelehnt\nBegründung: synthetische endgültige Ablehnung\n"
    path = tmp_path / "rejection.yaml"
    path.write_text(yaml.safe_dump(decision, allow_unicode=True))
    result = check.walk(tmp_path / "negative", decision_path=path)
    assert result.valid
    assert result.states[-1].label == "entscheiden 001 abgeschlossen abgelehnt end:abgelehnt"


@pytest.mark.parametrize("output", [
    "Prüfbericht: vollständig\nBegründung: vorhanden\n",
    "Prüfbericht: vollständig\nEntscheidung: abgelehnt\nBegründung: vorhanden\n",
    "Prüfbericht: vollständig\nEntscheidung: freigegeben\nBegründung: \n",
])
def test_gate_requires_actual_matching_decision_output_before_writes(tmp_path, output):
    check, harness, entry, handoff, payload, inputs = _producer(tmp_path)
    gate = harness.advance(entry, {handoff.producer_output: payload}, "bestanden", "entscheiden", 1, inputs)
    decision = check._load_human_decision(check.HUMAN_DECISION)
    decision["output"] = output
    before = _tree_bytes(harness.run_root)
    with pytest.raises(check.ProofError, match="Gate output"):
        harness.close_human(gate, decision)
    assert _tree_bytes(harness.run_root) == before


def test_public_close_cannot_leave_a_half_closed_nonterminal_run(tmp_path):
    check, harness, entry, handoff, payload, inputs = _producer(tmp_path)
    before = _tree_bytes(harness.run_root)
    with pytest.raises(check.ProofError, match="Nonterminal"):
        harness.close(entry, {handoff.producer_output: payload}, "bestanden")
    assert _tree_bytes(harness.run_root) == before
    assert entry["status"] == "aktiv"


@pytest.mark.parametrize("mutation", ["input", "binding"])
def test_terminal_close_rechecks_current_inputs_and_identity_before_writes(tmp_path, mutation):
    check, harness, entry = _terminal(tmp_path)
    if mutation == "input":
        (harness.attempt("finish", 1) / "input/auftrag.md").write_text("tampered")
    else:
        from tests.support import read_context, replace_context
        path = harness.run_root / "CONTEXT.md"
        metadata = read_context(path)
        metadata["id"] = "vorgang:other"
        replace_context(path, metadata)
    before = _run_snapshot(harness)
    with pytest.raises(check.ProofError):
        harness.close(entry, {"output/ergebnis.md": "final result"}, "fertig")
    assert _run_snapshot(harness) == before
    assert entry["status"] == "aktiv"


@pytest.mark.parametrize("operation", ["close", "advance", "open"])
def test_gate_cannot_bypass_dedicated_decision_check(tmp_path, operation):
    check, harness, entry, handoff, payload, inputs = _producer(tmp_path)
    gate = harness.advance(entry, {handoff.producer_output: payload}, "bestanden", "entscheiden", 1, inputs)
    before = _tree_bytes(harness.run_root)
    with pytest.raises(check.ProofError):
        if operation == "close":
            harness.close(gate, {"output/entscheidung.md": "unverified"}, "freigegeben", {"by": "human:synthetic", "at": "2040-01-01T00:00:00Z"})
        elif operation == "advance":
            harness.advance(gate, {"output/entscheidung.md": "unverified"}, "freigegeben", "pruefen", 2, {})
        else:
            harness.open("entscheiden", 2, inputs)
    assert _tree_bytes(harness.run_root) == before

EXPECTED_STATES = (
    "pruefen 001 aktiv",
    "nachfordern 001 aktiv nach klaerung",
    "nachfordern 001 wartend",
    "pruefen 002 aktiv nach nachgereicht",
    "entscheiden 001 aktiv nach bestanden human-gate",
    "entscheiden 001 abgeschlossen freigegeben end:entschieden",
)


def _check_module():
    spec = spec_from_file_location("impacts_cold_walk", CHECK_PATH)
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def walk_result():
    check = _check_module()
    with TemporaryDirectory() as directory:
        yield check.walk(Path(directory))


@pytest.fixture(scope="module")
def main_result():
    check = _check_module()
    output = StringIO()
    with redirect_stdout(output):
        exit_code = check.main()
    return exit_code, output.getvalue()


def test_example_application_validates_on_its_own():
    report = validate(BEISPIEL)

    assert report.valid, report.issues


def test_walk_runs_the_vorgang_through_loop_wait_and_human_gate(walk_result):
    result = walk_result

    assert tuple(state.label for state in result.states) == EXPECTED_STATES
    assert all(state.valid for state in result.states), [
        (state.label, state.codes) for state in result.states if not state.valid
    ]


def test_walk_proves_the_input_hash_fires_on_mutation(walk_result):
    result = walk_result

    assert "hash.mismatch" in result.mutation_codes
    assert result.valid


def test_walk_main_prints_the_router_chain_and_passes(main_result):
    exit_code, output = main_result
    assert exit_code == 0
    assert "ROUTER applications/prueffall/CONTEXT.md" in output
    assert "ROUTER applications/prueffall/vorpruefung/pruefen/CONTEXT.md" in output
    assert "STOP" in output
    assert output.rstrip().endswith("PASS cold walk")


def test_cold_walk_script_binds_its_checkout_source(tmp_path):
    checkout = tmp_path / "checkout"
    shutil.copytree(COLD_WALK, checkout / "06_evaluations" / "cold-walk")
    shutil.copytree(ROOT / "02_protocol", checkout / "02_protocol")
    shutil.copytree(ROOT / "src", checkout / "src")
    hashing = checkout / "src" / "impacts_protocol" / "hashing.py"
    source = hashing.read_text(encoding="utf-8")
    hashing.write_text(
        source.replace(
            '    attempt_root = Path(attempt_root)\n',
            '    return "sha256:" + "0" * 64\n',
            1,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(checkout / "06_evaluations" / "cold-walk" / "check.py")],
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "FAIL cold walk" in result.stdout


def test_cold_walk_rejects_duplicate_human_decision_keys_in_subprocess(tmp_path):
    checkout = tmp_path / "checkout"
    shutil.copytree(COLD_WALK, checkout / "06_evaluations" / "cold-walk")
    shutil.copytree(ROOT / "02_protocol", checkout / "02_protocol")
    shutil.copytree(ROOT / "src", checkout / "src")
    decision = (
        checkout
        / "06_evaluations"
        / "cold-walk"
        / "beispiel"
        / "fixtures"
        / "human-decision-final.yaml"
    )
    with decision.open("a", encoding="utf-8") as fixture:
        fixture.write("route: abgelehnt\n")

    check_path = checkout / "06_evaluations" / "cold-walk" / "check.py"
    result = subprocess.run(
        [sys.executable, str(check_path)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "FAIL cold walk:" in result.stdout
    assert "human-decision-final.yaml:9" in result.stdout
    assert "duplicate key: 'route'" in result.stdout
    assert "remove duplicate" in result.stdout
    assert "Traceback" not in result.stdout + result.stderr
    assert result.stderr == ""


def test_cold_walk_main_preserves_unexpected_proof_tracebacks(monkeypatch):
    check = _check_module()

    def fail(_base):
        raise check.ProofError("unexpected harness invariant")

    monkeypatch.setattr(check, "walk", fail)
    with pytest.raises(check.ProofError, match="unexpected harness invariant"):
        check.main()


def test_human_decision_yaml_syntax_error_reports_path_line_and_remedy(tmp_path):
    check = _check_module()
    path = tmp_path / "human-decision.yaml"
    path.write_text("route: [\n", encoding="utf-8")

    with pytest.raises(check.FixtureInputError) as error:
        check._load_human_decision(path)

    assert f"{path}:2" in str(error.value)
    assert "invalid human-decision YAML" in str(error.value)
    assert "correct the YAML fixture" in str(error.value)


def test_walk_imports_the_application_into_a_second_repository_with_equal_oid(walk_result):
    result = walk_result

    assert result.import_oid_equal
    assert result.import_state.label == "import prueffall in zweites repository"
    assert result.import_state.valid, result.import_state.codes
    assert result.valid


def test_walk_import_rejects_missing_capability_then_executes_materialized_tree(walk_result):
    result = walk_result

    assert "import.capability_materialized_and_executed" in _proofs(result)
    assert "import.missing_capability" in _rejections(result)


def test_permitted_preparation_keeps_wait_state_and_bound_inputs(walk_result):
    assert {
        "wait.permitted_draft_preserves_current_state",
        "wait.resume_binds_new_attempt_inputs",
    } <= walk_result.proofs
    assert {
        "wait.changed_bound_input",
        "wait.concurrent_laufpfad_entry",
        "wait.missing_response",
        "wait.response_mismatch",
        "wait.stale_draft_overwrite",
        "wait.unsafe_response_path",
    } <= walk_result.rejections


def test_walk_main_reports_the_import(main_result):
    exit_code, output = main_result
    assert exit_code == 0
    assert "IMPORT tree oid gleich in zweitem Repository" in output


def _proofs(result):
    return getattr(result, "proofs", frozenset())


def _rejections(result):
    return getattr(result, "rejections", frozenset())


def test_walk_binds_and_replays_the_exact_capability_authority(walk_result):
    result = walk_result

    assert {
        "capability.application_tuple_executed",
        "capability.path_resolved_at_workspace_revision",
        "capability.old_revision_replayed",
    } <= _proofs(result)
    assert {
        "capability.unbound_valid_tree",
        "capability.wrong_path",
        "capability.wrong_operation",
    } <= _rejections(result)


def test_walk_materializes_source_from_bound_commit_and_rejects_false_provenance(walk_result):
    result = walk_result

    assert {
        "application.source_requirement_drives_resolution",
        "source.bound_snapshot",
        "source.dirty_worktree_ignored",
    } <= _proofs(result)
    assert {
        "source.wrong_digest",
        "source.wrong_control",
        "source.wrong_revision",
        "source.wrong_existing_path",
    } <= _rejections(result)


def test_walk_connects_step_files_by_attempt_origin_and_content_digest(walk_result):
    result = walk_result

    assert {
        "application.handoff_mapping_drives_origin",
        "handoff.content_and_origin_bound",
    } <= _proofs(result)
    assert {
        "handoff.changed_consumer_bytes",
        "handoff.wrong_digest",
        "handoff.wrong_attempt",
        "handoff.wrong_producer_file",
        "handoff.useless_control_evidence",
    } <= _rejections(result)


def test_walk_preflights_gate_before_mutation_and_requires_external_decision_fixture(walk_result):
    result = walk_result

    assert {
        "gate.failed_preflight_left_run_unchanged",
        "gate.open_has_no_decision",
        "gate.external_decision_fixture_consumed",
    } <= _proofs(result)
    assert {
        "handoff.changed_consumer_bytes",
        "handoff.wrong_digest",
        "handoff.wrong_attempt",
        "handoff.wrong_producer_file",
        "handoff.useless_control_evidence",
    } <= _rejections(result)
