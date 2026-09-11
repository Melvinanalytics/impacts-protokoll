"""Synthetic arithmetic and dependency tests through the example's public CLI."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


EXAMPLE = Path(__file__).resolve().parents[1] / "06_evaluations/computation-walk"


def snapshot():
    return json.loads((EXAMPLE / "scenario.json").read_text())


def run(tmp_path, data):
    path = tmp_path / "input.json"
    payload = json.dumps(data, ensure_ascii=False).encode()
    path.write_bytes(payload)
    result = subprocess.run([sys.executable, str(EXAMPLE / "run.py"), str(path)], capture_output=True, text=True, timeout=10)
    assert "Traceback" not in result.stderr
    assert path.read_bytes() == payload
    return result, payload


def evaluate(tmp_path, data):
    process, payload = run(tmp_path, data)
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result["input_digest"] == "sha256:" + hashlib.sha256(payload).hexdigest()
    assert result["interpretation"] == "conditional scenario; no observed impact or authorization"
    return result["results"]


@pytest.mark.parametrize("production_effort,reach,review_hours,extra,volume,profit", [
    (2, .5, 120, 0, "80", "12000"),
    (1, .5, 120, 2000, "120", "26000"),
    (1, .75, 120, 3000, "120", "25000"),
    (1, .75, 160, 3000, "160", "41000"),
    (2, .25, 120, 0, "60", "4000"),
    (1, .25, 120, 2000, "60", "2000"),
])
def test_complete_scenario_recomputes_system_result(tmp_path, production_effort, reach, review_hours, extra, volume, profit):
    data = snapshot()
    data["resources"]["production"]["effort"]["value"] = production_effort
    data["resources"]["review"]["hours"]["value"] = review_hours
    data["demand"]["reach"]["value"] = reach
    data["economics"]["incremental_cost"]["value"] = extra
    result = evaluate(tmp_path, data)
    assert result["modeled_volume"]["value"] == volume
    assert result["operating_result"]["value"] == profit


def test_unknown_preserves_independent_results_and_asks_specific_question(tmp_path):
    data = snapshot()
    data["resources"]["review"]["hours"].update(value=None, status="open")
    result = evaluate(tmp_path, data)
    assert result["demand"]["value"] == "120"
    assert result["capacity:production"]["value"] == "80"
    assert result["unit_contribution"]["value"] == "400"
    for key in ("capacity:review", "modeled_volume", "operating_result"):
        assert result[key]["value"] is None
        assert result[key]["blockers"][0]["input"] == "resources.review.hours"
        assert result[key]["blockers"][0]["question"]
        assert "resources.review.hours" in result[key]["inputs"]


def test_zero_is_known_and_not_replaced_by_unknown(tmp_path):
    data = snapshot()
    data["demand"]["reach"]["value"] = 0
    result = evaluate(tmp_path, data)
    assert result["modeled_volume"]["value"] == "0"
    assert result["operating_result"]["value"] == "-20000"


@pytest.mark.parametrize("change", [
    {"value": 0}, {"value": -1}, {"value": True}, {"value": "NaN"},
    {"value": "Infinity"}, {"unit": "minute/case"},
    {"status": "confirmed"}, {"origin": ""}, {"status": "open"},
])
def test_invalid_effort_blocks_dependent_outputs_not_other_arithmetic(tmp_path, change):
    data = snapshot()
    data["resources"]["production"]["effort"].update(change)
    result = evaluate(tmp_path, data)
    assert result["demand"]["value"] == "120"
    assert result["modeled_volume"]["value"] is None


def test_unconfirmed_model_assumption_blocks_combined_bound(tmp_path):
    data = snapshot()
    data["assumptions"]["non_overlapping_pools"] = False
    result = evaluate(tmp_path, data)
    assert result["capacity:production"]["value"] == "80"
    assert result["modeled_volume"]["value"] is None


def test_successful_result_keeps_its_assumption_dependencies(tmp_path):
    data = snapshot()
    result = evaluate(tmp_path, data)
    required = {f"assumptions.{name}" for name in data["assumptions"]}
    assert required <= set(result["modeled_volume"]["inputs"])
    assert required <= set(result["operating_result"]["inputs"])


def test_capacity_only_does_not_require_a_commercial_funnel(tmp_path):
    data = snapshot()
    del data["demand"]
    del data["economics"]
    result = evaluate(tmp_path, data)
    assert result["capacity:production"]["value"] == "80"
    assert "modeled_volume" not in result
    assert "operating_result" not in result


@pytest.mark.parametrize("field,value", [("kind", "observation"), ("subject", ""), ("window", ""), ("as_of", "2026-09-07")])
def test_incomplete_or_mislabelled_snapshot_fails_cleanly(tmp_path, field, value):
    data = snapshot()
    data[field] = value
    result, _ = run(tmp_path, data)
    assert result.returncode != 0
    assert result.stderr.strip()


def test_replay_is_deterministic_and_changed_input_changes_binding(tmp_path):
    data = snapshot()
    first, _ = run(tmp_path, data)
    second, _ = run(tmp_path, data)
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    changed = copy.deepcopy(data)
    changed["economics"]["price"]["value"] = 510
    third, _ = run(tmp_path, changed)
    assert json.loads(first.stdout)["input_digest"] != json.loads(third.stdout)["input_digest"]
    assert json.loads(third.stdout)["results"]["operating_result"]["value"] == "12800"


def test_duplicate_snapshot_keys_are_rejected_before_interpretation(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text('{"subject":"conflicting-case",' + json.dumps(snapshot())[1:])
    result = subprocess.run([sys.executable, str(EXAMPLE / "run.py"), str(path)], capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert "duplicate" in result.stderr.lower()


@pytest.mark.parametrize("value", [-0.1, 1.01, True])
def test_invalid_share_cannot_create_a_demand_result(tmp_path, value):
    data = snapshot()
    data["demand"]["reach"]["value"] = value
    result = evaluate(tmp_path, data)
    assert result["demand"]["value"] is None
    assert result["capacity:production"]["value"] == "80"


def test_negative_contribution_is_reported_not_suppressed(tmp_path):
    data = snapshot()
    data["economics"]["price"]["value"] = 50
    result = evaluate(tmp_path, data)
    assert result["unit_contribution"]["value"] == "-50"
    assert result["operating_result"]["value"] == "-24000"
