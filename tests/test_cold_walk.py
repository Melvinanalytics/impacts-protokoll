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
    assert "ROUTER applications/prueffall/hauptprozess/teilprozesse/vorpruefung/arbeitsschritte/pruefen/CONTEXT.md" in output
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


def test_walk_main_reports_the_import(capsys):
    check = _check_module()

    exit_code = check.main()

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "IMPORT tree oid gleich in zweitem Repository" in output
