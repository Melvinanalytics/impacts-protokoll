from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from tempfile import TemporaryDirectory


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


def test_example_application_validates_on_its_own():
    report = validate(BEISPIEL)

    assert report.valid, report.issues


def test_walk_runs_the_vorgang_through_loop_wait_and_human_gate():
    check = _check_module()
    with TemporaryDirectory() as directory:
        result = check.walk(Path(directory))

        assert tuple(state.label for state in result.states) == EXPECTED_STATES
        assert all(state.valid for state in result.states), [
            (state.label, state.codes) for state in result.states if not state.valid
        ]


def test_walk_proves_the_input_hash_fires_on_mutation():
    check = _check_module()
    with TemporaryDirectory() as directory:
        result = check.walk(Path(directory))

        assert "hash.mismatch" in result.mutation_codes
        assert result.valid


def test_walk_main_prints_the_router_chain_and_passes(capsys):
    check = _check_module()

    exit_code = check.main()

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "ROUTER applications/prueffall/CONTEXT.md" in output
    assert "ROUTER applications/prueffall/vorpruefung/pruefen/CONTEXT.md" in output
    assert "STOP" in output
    assert output.rstrip().endswith("PASS cold walk")


def test_walk_imports_the_application_into_a_second_repository_with_equal_oid():
    check = _check_module()
    with TemporaryDirectory() as directory:
        result = check.walk(Path(directory))

        assert result.import_oid_equal
        assert result.import_state.label == "import prueffall in zweites repository"
        assert result.import_state.valid, result.import_state.codes
        assert result.valid


def test_walk_import_rejects_missing_capability_then_executes_materialized_tree():
    check = _check_module()
    with TemporaryDirectory() as directory:
        result = check.walk(Path(directory))

    assert "import.capability_materialized_and_executed" in _proofs(result)
    assert "import.missing_capability" in _rejections(result)


def test_walk_main_reports_the_import(capsys):
    check = _check_module()

    exit_code = check.main()

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "IMPORT tree oid gleich in zweitem Repository" in output


def _proofs(result):
    return getattr(result, "proofs", frozenset())


def _rejections(result):
    return getattr(result, "rejections", frozenset())


def test_walk_binds_and_replays_the_exact_capability_authority():
    check = _check_module()
    with TemporaryDirectory() as directory:
        result = check.walk(Path(directory))

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


def test_walk_materializes_source_from_bound_commit_and_rejects_false_provenance():
    check = _check_module()
    with TemporaryDirectory() as directory:
        result = check.walk(Path(directory))

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


def test_walk_connects_step_files_by_attempt_origin_and_content_digest():
    check = _check_module()
    with TemporaryDirectory() as directory:
        result = check.walk(Path(directory))

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


def test_walk_preflights_gate_before_mutation_and_requires_external_decision_fixture():
    check = _check_module()
    with TemporaryDirectory() as directory:
        result = check.walk(Path(directory))

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
