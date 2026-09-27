from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPLAY = (
    ROOT
    / "06_evaluations"
    / "business-operations-wave"
    / "delivery-replay"
    / "replay.py"
)


def invoke(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPLAY), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_fresh_process_resumes_changed_source_and_keeps_decision_open(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    initialized = invoke("init", "--workspace", str(workspace))
    assert initialized.returncode == 0, initialized.stderr

    baseline = invoke("resume", "--workspace", str(workspace))
    assert baseline.returncode == 0, baseline.stderr
    first = json.loads(baseline.stdout)
    assert first["candidate_estimate"]["estimated_date"] == "2026-09-22"
    assert first["human_decision"]["status"] == "open"
    assert first["customer_commitment"] == "blocked"

    revised = invoke(
        "revise-material",
        "--workspace",
        str(workspace),
        "--date",
        "2026-09-21",
    )
    assert revised.returncode == 0, revised.stderr
    continued = invoke("resume", "--workspace", str(workspace))
    assert continued.returncode == 0, continued.stderr
    second = json.loads(continued.stdout)
    assert second["sequence"] == 2
    assert second["continued_from_files"]["previous_estimated_date"] == "2026-09-22"
    assert second["candidate_estimate"]["estimated_date"] == "2026-09-23"
    assert second["candidate_estimate"]["material_ready_revision"] == "MR-2"
    assert second["deterministic_check"]["r7_known_vector_matches"] is True
    assert second["customer_commitment"] == "blocked"


def test_meanings_rule_practice_and_o17_report_stay_separate(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    assert invoke("init", "--workspace", str(workspace)).returncode == 0
    completed = invoke("resume", "--workspace", str(workspace))
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)

    sales = result["delivery_time_definitions"]["sales"]
    production = result["delivery_time_definitions"]["production"]
    assert sales["address"] == production["address"] == "kennzahl:lieferzeit"
    assert sales["namespace"] != production["namespace"]
    assert "calendar days" in sales["meaning"]
    assert "machine hours" in production["meaning"]
    assert result["calculated_delivery_time_values"]["sales"] is None
    assert result["calculated_delivery_time_values"]["production"] is None

    split = result["rule_and_practice"]
    assert split["prescribed_r7"] == "max(material-ready, capacity-slot) + 2 working days"
    assert split["planner_workbook_practice"]["formula"] == "material-ready + 5 calendar days"
    assert split["workbook_comparison_or_execution"] == "not performed"
    assert split["o17_report"]["formula"] == "open"
    assert split["o17_report"]["evidence_label"] == "reported"


def test_single_file_tamper_fails_and_coordinated_rewrite_is_outside_guarantee() -> None:
    completed = invoke("demo")
    assert completed.returncode == 0, completed.stderr
    assert "FRESH SESSION 2 — resumed from workspace files" in completed.stdout
    assert "single-file content change: detected against unchanged manifest" in completed.stdout
    assert "content plus digest rewrite: passes manifest check; authenticity is outside guarantee" in completed.stdout
    assert '"external_action": "not performed"' in completed.stdout
    assert '"business_benefit": "not measured"' in completed.stdout
    assert '"nontechnical_user_proof": "not performed"' in completed.stdout
    assert '"time_claim": "none"' in completed.stdout
