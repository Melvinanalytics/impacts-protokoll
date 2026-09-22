"""Summarize matched Codex JSONL context-routing runs without claiming answer quality."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics


METRICS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "tool_calls",
    "tool_output_bytes",
    "answer_bytes",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_run(jsonl_path: Path, answer_path: Path) -> dict[str, int | str]:
    events = [json.loads(line) for line in jsonl_path.read_text().splitlines() if line.strip()]
    completed = [event for event in events if event.get("type") == "turn.completed"]
    if len(completed) != 1 or not isinstance(completed[0].get("usage"), dict):
        raise ValueError(f"{jsonl_path}: expected one turn.completed usage object")
    failed = [event for event in events if event.get("type") == "turn.failed"]
    if failed:
        raise ValueError(f"{jsonl_path}: turn.failed present")

    usage = completed[0]["usage"]
    commands = [
        event["item"]
        for event in events
        if event.get("type") == "item.completed"
        and event.get("item", {}).get("type") == "command_execution"
    ]
    answer = answer_path.read_bytes()
    return {
        "input_tokens": int(usage["input_tokens"]),
        "cached_input_tokens": int(usage["cached_input_tokens"]),
        "output_tokens": int(usage["output_tokens"]),
        "reasoning_output_tokens": int(usage["reasoning_output_tokens"]),
        "tool_calls": len(commands),
        "tool_output_bytes": sum(len(item.get("aggregated_output", "").encode()) for item in commands),
        "answer_bytes": len(answer),
        "jsonl_sha256": sha256(jsonl_path),
        "answer_sha256": hashlib.sha256(answer).hexdigest(),
    }


def summarize(runs: list[dict[str, int | str]]) -> dict[str, float | int]:
    if len(runs) < 3:
        raise ValueError("at least three runs required")
    return {metric: statistics.median(int(run[metric]) for run in runs) for metric in METRICS}


def reduction_percent(baseline: float, candidate: float) -> float:
    if baseline == 0:
        raise ValueError("baseline metric must be nonzero")
    return round((baseline - candidate) / baseline * 100, 2)


def paths(values: list[str], label: str) -> list[Path]:
    result = [Path(value) for value in values]
    if len(result) < 3:
        raise ValueError(f"{label}: at least three paths required")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-jsonl", action="append", required=True)
    parser.add_argument("--baseline-answer", action="append", required=True)
    parser.add_argument("--candidate-jsonl", action="append", required=True)
    parser.add_argument("--candidate-answer", action="append", required=True)
    args = parser.parse_args()

    baseline_jsonl = paths(args.baseline_jsonl, "baseline JSONL")
    baseline_answers = paths(args.baseline_answer, "baseline answers")
    candidate_jsonl = paths(args.candidate_jsonl, "candidate JSONL")
    candidate_answers = paths(args.candidate_answer, "candidate answers")
    if len(baseline_jsonl) != len(baseline_answers) or len(candidate_jsonl) != len(candidate_answers):
        raise ValueError("each JSONL input needs one matching answer file")

    baseline_runs = [read_run(log, answer) for log, answer in zip(baseline_jsonl, baseline_answers)]
    candidate_runs = [read_run(log, answer) for log, answer in zip(candidate_jsonl, candidate_answers)]
    baseline = summarize(baseline_runs)
    candidate = summarize(candidate_runs)
    comparison = {
        metric: reduction_percent(float(baseline[metric]), float(candidate[metric]))
        for metric in METRICS
    }
    print(json.dumps({
        "baseline_runs": baseline_runs,
        "candidate_runs": candidate_runs,
        "baseline_median": baseline,
        "candidate_median": candidate,
        "reduction_percent": comparison,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
