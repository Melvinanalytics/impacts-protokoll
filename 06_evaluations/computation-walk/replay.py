#!/usr/bin/env python3
"""WP18 stage A: read-only digest replay of one closed synthetic calculation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HOME = Path(__file__).resolve().parent


def digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def result_bytes(results: dict) -> bytes:
    """The step output is canonical calculation results, excluding CLI runtime metadata."""
    return (json.dumps(results, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def replay(home: Path = HOME, candidate: Path | None = None) -> dict:
    record = json.loads((home / "closed-attempt.json").read_bytes())
    if record["status"] != "abgeschlossen" or record["selected_route"] != "end:calculated":
        raise ValueError("record is not the closed calculation attempt")
    for key in ("input", "rule", "output"):
        ref = record[key]
        path = Path(ref["path"])
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("record reference must stay inside the fixture")
        if digest((home / path).read_bytes()) != ref["sha256"]:
            raise ValueError(f"recorded {key} digest mismatch")
    rule = candidate if candidate is not None else home / record["rule"]["path"]
    process = subprocess.run([sys.executable, str(rule.resolve()), str((home / record["input"]["path"]).resolve())],
                             capture_output=True, timeout=10, check=True)
    report = json.loads(process.stdout)
    if report["input_digest"] != record["input"]["sha256"]:
        raise ValueError("candidate did not report the bound input digest")
    actual = digest(result_bytes(report["results"]))
    if actual != record["output"]["sha256"]:
        raise ValueError("replayed output digest differs from closed attempt")
    return {"match": True, "output_digest": actual,
            "candidate_rule_digest": digest(rule.read_bytes()),
            "recorded_rule_digest": record["rule"]["sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, help="Candidate deterministic rule, with run.py's CLI contract")
    args = parser.parse_args()
    try:
        print(json.dumps(replay(candidate=args.candidate), sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"Replay failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
