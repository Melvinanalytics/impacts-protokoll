from contextlib import redirect_stdout
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import yaml


ROOT = Path(__file__).resolve().parents[1]
CHECK_PATH = ROOT / "06_evaluations" / "complexity-budget" / "check.py"
BUDGET_PATH = ROOT / "06_evaluations" / "complexity-budget" / "budget.yaml"


def _check_module():
    spec = spec_from_file_location("impacts_complexity_budget", CHECK_PATH)
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_target_budget_is_five_five_fifteen():
    budget = yaml.safe_load(BUDGET_PATH.read_text(encoding="utf-8"))
    assert budget["version"] == 4
    assert budget["limits"] == {
        "root_dirs": 5,
        "protocol_schemas": 5,
        "max_total_required_fields_per_schema": 15,
    }
    assert budget["approvals"] == []
    assert budget["initial_release"] == {
        "tag": "v0.2.0",
        "approved_by": "human:melvin",
        "reason": "Human-confirmed V1 boundary for initial public V0.2 release",
        "limits": {
            "root_dirs": 5,
            "protocol_schemas": 5,
            "max_total_required_fields_per_schema": 15,
        },
    }


def test_repository_stays_within_target_budget():
    check = _check_module()
    with redirect_stdout(StringIO()) as output:
        exit_code = check.main()
    assert exit_code == 0, output.getvalue()


def test_required_counter_includes_nested_contracts():
    check = _check_module()
    assert check._required_count(
        {"required": ["root"], "properties": {"root": {"required": ["a", "b"]}}}
    ) == 3


def test_budget_rejects_nonhuman_attribution():
    check = _check_module()
    with TemporaryDirectory() as directory:
        budget_path = Path(directory) / "budget.yaml"
        budget = yaml.safe_load(BUDGET_PATH.read_text(encoding="utf-8"))
        budget["approvals"] = [
            {
                "field": "root_dirs",
                "from": 5,
                "to": 6,
                "approved_by": "agent:codex",
                "reason": "self approval",
            }
        ]
        budget_path.write_text(yaml.safe_dump(budget), encoding="utf-8")
        check.BUDGET = budget_path
        with redirect_stdout(StringIO()) as output:
            exit_code = check.main()
    assert exit_code == 1
    assert "approved_by human:<id>" in output.getvalue()


def test_joint_budget_and_fallback_increase_cannot_bypass_release_tag():
    check = _check_module()
    with TemporaryDirectory() as directory:
        temporary_root = Path(directory)
        history = temporary_root / "history"
        baseline_budget = history / "06_evaluations/complexity-budget/budget.yaml"
        baseline_budget.parent.mkdir(parents=True)
        baseline_budget.write_text(BUDGET_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        subprocess.run(["git", "init", "-b", "main", str(history)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(history), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(history), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(history), "add", "."], check=True)
        subprocess.run(["git", "-C", str(history), "commit", "-m", "v0.2 baseline"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(history), "tag", "v0.2.0"], check=True)
        (history / "marker").write_text("next", encoding="utf-8")
        subprocess.run(["git", "-C", str(history), "add", "marker"], check=True)
        subprocess.run(["git", "-C", str(history), "commit", "-m", "next release"], check=True, capture_output=True)

        mutated_path = temporary_root / "budget.yaml"
        mutated = yaml.safe_load(BUDGET_PATH.read_text(encoding="utf-8"))
        mutated["limits"]["root_dirs"] = 6
        mutated_path.write_text(yaml.safe_dump(mutated), encoding="utf-8")

        check.HISTORY_REPO = history
        check.BUDGET = mutated_path
        check.PORTABLE_BASELINE = {**getattr(check, "PORTABLE_BASELINE", {}), "root_dirs": 6}
        check.PORTABLE_LIMITS = {**getattr(check, "PORTABLE_LIMITS", {}), "root_dirs": 6}
        with redirect_stdout(StringIO()) as output:
            exit_code = check.main()

    assert exit_code == 1
    assert "Budget increase" in output.getvalue()
