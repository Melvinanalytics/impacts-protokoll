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


def read_run(
    jsonl_path: Path,
    answer_path: Path,
    *,
    side: str = "run",
    run_id: str = "unnamed",
) -> dict[str, int | str]:
    events = [json.loads(line) for line in jsonl_path.read_text().splitlines() if line.strip()]
    completed = [event for event in events if event.get("type") == "turn.completed"]
    if len(completed) != 1 or not isinstance(completed[0].get("usage"), dict):
        raise ValueError(f"{side} run {run_id} {jsonl_path}: expected one turn.completed usage object")
    failed = [event for event in events if event.get("type") == "turn.failed"]
    if failed:
        raise ValueError(f"{side} run {run_id} {jsonl_path}: turn.failed present")

    usage = completed[0]["usage"]
    commands = [
        (index, event["item"])
        for index, event in enumerate(events, 1)
        if event.get("type") == "item.completed"
        and event.get("item", {}).get("type") == "command_execution"
    ]
    for index, item in commands:
        if "aggregated_output" not in item:
            raise ValueError(
                f"{side} run {run_id} {jsonl_path} event {index} field aggregated_output: missing"
            )
        if not isinstance(item["aggregated_output"], str):
            raise ValueError(
                f"{side} run {run_id} {jsonl_path} event {index} field aggregated_output: expected string"
            )
    answer = answer_path.read_bytes()
    return {
        "run_id": run_id,
        "input_tokens": int(usage["input_tokens"]),
        "cached_input_tokens": int(usage["cached_input_tokens"]),
        "output_tokens": int(usage["output_tokens"]),
        "reasoning_output_tokens": int(usage["reasoning_output_tokens"]),
        "tool_calls": len(commands),
        "tool_output_bytes": sum(len(item["aggregated_output"].encode()) for _, item in commands),
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


def run_triples(values: list[list[str]], side: str) -> list[tuple[str, Path, Path]]:
    if len(values) < 3:
        raise ValueError(f"{side}: at least three run triples required")
    result = []
    for run_id, jsonl_path, answer_path in values:
        if not run_id.strip():
            raise ValueError(f"{side}: RUN_ID must be non-empty")
        result.append((run_id, Path(jsonl_path), Path(answer_path)))
    return result


def validate_unique_runs(*groups: tuple[str, list[tuple[str, Path, Path]]]) -> None:
    run_ids: dict[str, str] = {}
    log_hashes: dict[str, tuple[str, str, Path]] = {}
    for side, runs in groups:
        for run_id, jsonl_path, _ in runs:
            if run_id in run_ids:
                raise ValueError(
                    f"duplicate RUN_ID {run_id!r}: {run_ids[run_id]} and {side}"
                )
            run_ids[run_id] = side
            digest = sha256(jsonl_path)
            if digest in log_hashes:
                first_side, first_id, first_path = log_hashes[digest]
                raise ValueError(
                    "duplicate JSONL SHA-256 "
                    f"{digest}: {first_side} run {first_id} {first_path} and "
                    f"{side} run {run_id} {jsonl_path}"
                )
            log_hashes[digest] = (side, run_id, jsonl_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline-run",
        action="append",
        nargs=3,
        metavar=("RUN_ID", "JSONL", "ANSWER"),
        required=True,
    )
    parser.add_argument(
        "--candidate-run",
        action="append",
        nargs=3,
        metavar=("RUN_ID", "JSONL", "ANSWER"),
        required=True,
    )
    args = parser.parse_args(argv)

    baseline_inputs = run_triples(args.baseline_run, "baseline")
    candidate_inputs = run_triples(args.candidate_run, "candidate")
    validate_unique_runs(("baseline", baseline_inputs), ("candidate", candidate_inputs))

    baseline_runs = [
        read_run(log, answer, side="baseline", run_id=run_id)
        for run_id, log, answer in baseline_inputs
    ]
    candidate_runs = [
        read_run(log, answer, side="candidate", run_id=run_id)
        for run_id, log, answer in candidate_inputs
    ]
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
