import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "06_evaluations" / "context-efficiency" / "measure.py"
SPEC = importlib.util.spec_from_file_location("context_efficiency_measure", MODULE_PATH)
MEASURE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MEASURE
SPEC.loader.exec_module(MEASURE)


def write_run(tmp_path: Path, name: str, *, input_tokens: int, tool_output: str = "abc"):
    log = tmp_path / f"{name}.jsonl"
    answer = tmp_path / f"{name}.md"
    events = [
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"type": "command_execution", "aggregated_output": tool_output}},
        {"type": "turn.completed", "usage": {
            "input_tokens": input_tokens,
            "cached_input_tokens": 10,
            "output_tokens": 20,
            "reasoning_output_tokens": 5,
        }},
    ]
    log.write_text("\n".join(json.dumps(event) for event in events) + "\n")
    answer.write_text("supported answer\n")
    return log, answer


def test_read_run_uses_reported_usage_and_actual_tool_bytes(tmp_path):
    log, answer = write_run(tmp_path, "run", input_tokens=100, tool_output="äbc")

    result = MEASURE.read_run(log, answer)

    assert result["input_tokens"] == 100
    assert result["tool_calls"] == 1
    assert result["tool_output_bytes"] == len("äbc".encode())
    assert result["answer_bytes"] == len(answer.read_bytes())
    assert len(result["jsonl_sha256"]) == len(result["answer_sha256"]) == 64


def test_summary_requires_repetition_and_uses_median(tmp_path):
    runs = [MEASURE.read_run(*write_run(tmp_path, f"run-{value}", input_tokens=value)) for value in (100, 40, 70)]

    assert MEASURE.summarize(runs)["input_tokens"] == 70
    with pytest.raises(ValueError, match="at least three runs"):
        MEASURE.summarize(runs[:2])


def test_reduction_reports_negative_values_for_regression():
    assert MEASURE.reduction_percent(100, 75) == 25.0
    assert MEASURE.reduction_percent(100, 120) == -20.0
