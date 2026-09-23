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


def run_args(side, triples):
    args = []
    for run_id, log, answer in triples:
        args.extend([f"--{side}-run", run_id, str(log), str(answer)])
    return args


def triples(tmp_path, side, values=(100, 110, 120)):
    result = []
    for index, value in enumerate(values, 1):
        run_id = f"{side}-{index}"
        log, answer = write_run(tmp_path, run_id, input_tokens=value)
        answer.write_text(f"supported answer for {run_id}\n")
        result.append((run_id, log, answer))
    return result


@pytest.mark.parametrize("short_side", ["baseline", "candidate"])
def test_cli_requires_three_named_triples_per_side(tmp_path, short_side):
    baseline = triples(tmp_path, "baseline")[:2]
    candidate = triples(tmp_path, "candidate")

    if short_side == "candidate":
        baseline, candidate = triples(tmp_path, "baseline-full"), candidate[:2]

    with pytest.raises(ValueError, match=rf"{short_side}: at least three run triples required"):
        MEASURE.main(run_args("baseline", baseline) + run_args("candidate", candidate))


@pytest.mark.parametrize("duplicate_across_sides", [False, True])
def test_cli_rejects_duplicate_run_ids_within_or_across_sides(tmp_path, duplicate_across_sides):
    baseline = triples(tmp_path, "baseline")
    candidate = triples(tmp_path, "candidate")
    if duplicate_across_sides:
        candidate[0] = (baseline[0][0], candidate[0][1], candidate[0][2])
    else:
        baseline[1] = (baseline[0][0], baseline[1][1], baseline[1][2])

    with pytest.raises(ValueError, match="duplicate RUN_ID"):
        MEASURE.main(run_args("baseline", baseline) + run_args("candidate", candidate))


def test_cli_rejects_empty_run_id(tmp_path):
    baseline = triples(tmp_path, "baseline")
    candidate = triples(tmp_path, "candidate")
    baseline[0] = ("   ", baseline[0][1], baseline[0][2])

    with pytest.raises(ValueError, match="RUN_ID must be non-empty"):
        MEASURE.main(run_args("baseline", baseline) + run_args("candidate", candidate))


def test_cli_rejects_an_incomplete_named_triple(tmp_path):
    baseline = triples(tmp_path, "baseline")
    candidate = triples(tmp_path, "candidate")
    args = run_args("baseline", baseline) + run_args("candidate", candidate)

    with pytest.raises(SystemExit):
        MEASURE.main(args[:-1])


@pytest.mark.parametrize("duplicate_across_sides", [False, True])
def test_cli_rejects_duplicate_jsonl_bytes_within_or_across_sides(tmp_path, duplicate_across_sides):
    baseline = triples(tmp_path, "baseline")
    candidate = triples(tmp_path, "candidate")
    source = baseline[0][1]
    target = candidate[0][1] if duplicate_across_sides else baseline[1][1]
    target.write_bytes(source.read_bytes())

    with pytest.raises(ValueError, match="duplicate JSONL SHA-256"):
        MEASURE.main(run_args("baseline", baseline) + run_args("candidate", candidate))


@pytest.mark.parametrize("aggregated_output", [None, 123])
def test_read_run_rejects_missing_or_non_string_aggregated_output_with_context(tmp_path, aggregated_output):
    log, answer = write_run(tmp_path, "broken", input_tokens=100)
    events = [json.loads(line) for line in log.read_text().splitlines()]
    item = events[1]["item"]
    if aggregated_output is None:
        del item["aggregated_output"]
        expected = "missing"
    else:
        item["aggregated_output"] = aggregated_output
        expected = "expected string"
    log.write_text("\n".join(json.dumps(event) for event in events) + "\n")

    with pytest.raises(
        ValueError,
        match=rf"candidate.*candidate-2.*{log.name}.*event 2.*aggregated_output.*{expected}",
    ):
        MEASURE.read_run(log, answer, side="candidate", run_id="candidate-2")


def test_named_triple_attribution_survives_reordering(tmp_path, capsys):
    baseline = triples(tmp_path, "baseline", (100, 110, 120))
    candidate = triples(tmp_path, "candidate", (70, 80, 90))

    assert MEASURE.main(run_args("baseline", baseline) + run_args("candidate", candidate)) == 0
    first = json.loads(capsys.readouterr().out)
    assert MEASURE.main(run_args("baseline", list(reversed(baseline))) + run_args("candidate", [candidate[1], candidate[2], candidate[0]])) == 0
    second = json.loads(capsys.readouterr().out)

    def by_id(result, side):
        return {
            run["run_id"]: (run["jsonl_sha256"], run["answer_sha256"])
            for run in result[f"{side}_runs"]
        }

    expected_baseline = {
        run_id: (MEASURE.sha256(log), MEASURE.sha256(answer))
        for run_id, log, answer in baseline
    }
    expected_candidate = {
        run_id: (MEASURE.sha256(log), MEASURE.sha256(answer))
        for run_id, log, answer in candidate
    }
    assert by_id(first, "baseline") == expected_baseline
    assert by_id(first, "candidate") == expected_candidate
    assert by_id(first, "baseline") == by_id(second, "baseline")
    assert by_id(first, "candidate") == by_id(second, "candidate")
    assert first["baseline_median"] == second["baseline_median"]
    assert first["candidate_median"] == second["candidate_median"]
