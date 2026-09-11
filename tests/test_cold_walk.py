from contextlib import redirect_stdout
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
COLD_WALK = ROOT / "06_evaluations" / "cold-walk"
CHECK_PATH = COLD_WALK / "check.py"
BEISPIEL = COLD_WALK / "beispiel" / "applications" / "prueffall"
from impacts_protocol import validate

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
