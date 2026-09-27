#!/usr/bin/env python3
"""Deterministic, file-backed synthetic delivery replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
INPUT_FILES = (
    "case.json",
    "evidence/o-17-workbook-report.json",
    "sources/capacity_slot.json",
    "sources/material_ready.json",
)
MANIFEST = "inputs.sha256.json"
STATE = "state.json"


class ReplayError(Exception):
    """Expected invalid replay state or integrity failure."""


def encode_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReplayError(f"cannot read JSON file: {path.name}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encode_json(value), encoding="utf-8", newline="\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_for(workspace: Path) -> dict[str, Any]:
    return {
        "format": "synthetic-replay-inputs-v1",
        "sha256": {name: digest(workspace / name) for name in INPUT_FILES},
    }


def verify_inputs(workspace: Path) -> dict[str, str]:
    manifest_path = workspace / MANIFEST
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ReplayError("invalid input manifest")
    expected = manifest.get("sha256")
    if manifest.get("format") != "synthetic-replay-inputs-v1" or not isinstance(expected, dict):
        raise ReplayError("invalid input manifest")
    if set(expected) != set(INPUT_FILES):
        raise ReplayError("input manifest file set mismatch")

    actual: dict[str, str] = {}
    for name in INPUT_FILES:
        path = workspace / name
        try:
            actual[name] = digest(path)
        except OSError as exc:
            raise ReplayError(f"missing replay input: {name}") from exc
        if expected[name] != actual[name]:
            raise ReplayError(f"input digest mismatch: {name}")
    return actual


def initialize(workspace: Path) -> None:
    if workspace.exists() and any(workspace.iterdir()):
        raise ReplayError("workspace must be absent or empty")
    workspace.mkdir(parents=True, exist_ok=True)
    shutil.copytree(FIXTURES, workspace, dirs_exist_ok=True)
    write_json(workspace / MANIFEST, manifest_for(workspace))


def parse_date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise ReplayError(f"invalid date in {label}")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ReplayError(f"invalid date in {label}") from exc
    if parsed.isoformat() != value:
        raise ReplayError(f"invalid date in {label}")
    return parsed


def add_workdays(start: date, count: int) -> date:
    result = start
    added = 0
    while added < count:
        result += timedelta(days=1)
        if result.weekday() < 5:
            added += 1
    return result


def calculate(workspace: Path, source_hashes: dict[str, str]) -> dict[str, Any]:
    case = read_json(workspace / "case.json")
    material = read_json(workspace / "sources/material_ready.json")
    capacity = read_json(workspace / "sources/capacity_slot.json")
    workbook_report = read_json(workspace / "evidence/o-17-workbook-report.json")
    material_date = parse_date(material.get("value"), "material-ready")
    capacity_date = parse_date(capacity.get("value"), "capacity-slot")
    base_date = max(material_date, capacity_date)
    candidate = add_workdays(base_date, 2)
    rule = case["prescribed_rule"]
    check_vector = next(
        (
            row
            for row in case["r7_check_vectors"]
            if row["material_ready"] == material_date.isoformat()
            and row["capacity_slot"] == capacity_date.isoformat()
        ),
        None,
    )

    return {
        "case_id": case["case_id"],
        "simulation": True,
        "input_sha256": source_hashes,
        "delivery_time_definitions": case["delivery_time_definitions"],
        "calculated_delivery_time_values": {
            "sales": None,
            "sales_reason": "accepted-order and customer-confirmed-arrival dates absent",
            "production": None,
            "production_reason": "R7 does not calculate machine hours; machine-hour evidence absent",
        },
        "rule_and_practice": {
            "prescribed_r7": rule["formula"],
            "prescribed_revision": rule["revision"],
            "planner_workbook_practice": case["planner_workbook_practice"],
            "workbook_comparison_or_execution": "not performed",
            "o17_report": workbook_report,
        },
        "candidate_estimate": {
            "material_ready": material["value"],
            "material_ready_revision": material["revision"],
            "capacity_slot": capacity["value"],
            "capacity_slot_revision": capacity["revision"],
            "max_input_date": base_date.isoformat(),
            "working_days_added": 2,
            "estimated_date": candidate.isoformat(),
            "meaning": "candidate estimate only; not an accepted date or customer commitment",
        },
        "deterministic_check": {
            "manifest_matches_listed_input_bytes": True,
            "r7_known_vector_matches": check_vector is not None
            and check_vector["expected_candidate_date"] == candidate.isoformat(),
            "expected_candidate_date": None
            if check_vector is None
            else check_vector["expected_candidate_date"],
            "scope": "listed fixture vectors and fixed weekday arithmetic only",
        },
        "human_decision": case["human_decision"],
        "customer_commitment": "blocked",
        "limits": case["limits"],
    }


def resume(workspace: Path) -> dict[str, Any]:
    hashes = verify_inputs(workspace)
    result = calculate(workspace, hashes)
    state_path = workspace / STATE
    history: list[dict[str, Any]] = []
    if state_path.exists():
        previous = read_json(state_path)
        if not isinstance(previous, dict) or not isinstance(previous.get("history"), list):
            raise ReplayError("invalid replay state")
        history = previous["history"]
    result["sequence"] = len(history) + 1
    if history:
        prior_candidate = history[-1].get("candidate_estimate", {})
        result["continued_from_files"] = {
            "previous_sequence": history[-1].get("sequence"),
            "previous_estimated_date": prior_candidate.get("estimated_date"),
        }
    else:
        result["continued_from_files"] = None
    history.append(result)
    write_json(state_path, {"history": history})
    return result


def revise_material(workspace: Path, value: str) -> dict[str, str]:
    verify_inputs(workspace)
    parsed = parse_date(value, "material-ready update")
    path = workspace / "sources/material_ready.json"
    material = read_json(path)
    current = material.get("revision", "")
    match = re.fullmatch(r"MR-(\d+)", current)
    if match is None:
        raise ReplayError("unexpected material-ready revision token")
    material["revision"] = f"MR-{int(match.group(1)) + 1}"
    material["value"] = parsed.isoformat()
    write_json(path, material)
    write_json(workspace / MANIFEST, manifest_for(workspace))
    return {
        "source": "quelle:material-ready",
        "revision": material["revision"],
        "value": material["value"],
        "scope": "synthetic fixture update; no external source write",
    }


def call_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def integrity_demo(workspace: Path, scratch: Path) -> tuple[str, str]:
    tampered = scratch / "single-file-tamper"
    coordinated = scratch / "coordinated-rewrite"
    shutil.copytree(workspace, tampered)
    shutil.copytree(workspace, coordinated)

    tamper_source = tampered / "sources/material_ready.json"
    material = read_json(tamper_source)
    material["value"] = "2026-09-22"
    write_json(tamper_source, material)
    detected = call_cli("verify", "--workspace", str(tampered))
    if detected.returncode == 0 or "input digest mismatch" not in detected.stderr:
        raise ReplayError("single-file tamper was not detected")

    rewrite_source = coordinated / "sources/material_ready.json"
    material = read_json(rewrite_source)
    material["revision"] = "MR-3"
    material["value"] = "2026-09-22"
    write_json(rewrite_source, material)
    write_json(coordinated / MANIFEST, manifest_for(coordinated))
    accepted = call_cli("verify", "--workspace", str(coordinated))
    if accepted.returncode != 0:
        raise ReplayError("coordinated rewrite fixture did not pass manifest check")
    return (
        "single-file content change: detected against unchanged manifest",
        "content plus digest rewrite: passes manifest check; authenticity is outside guarantee",
    )


def demo() -> None:
    with tempfile.TemporaryDirectory(prefix="delivery-replay-") as temporary:
        scratch = Path(temporary)
        workspace = scratch / "workspace"
        initialize(workspace)

        baseline = call_cli("resume", "--workspace", str(workspace))
        if baseline.returncode:
            raise ReplayError(baseline.stderr.strip())
        print("SESSION 1 — synthetic baseline")
        print(baseline.stdout, end="")

        print("SYNTHETIC SOURCE REVISION")
        print(encode_json(revise_material(workspace, "2026-09-21")), end="")

        resumed = call_cli("resume", "--workspace", str(workspace))
        if resumed.returncode:
            raise ReplayError(resumed.stderr.strip())
        print("FRESH SESSION 2 — resumed from workspace files")
        print(resumed.stdout, end="")

        print("INTEGRITY BOUNDARY")
        for finding in integrity_demo(workspace, scratch):
            print(f"- {finding}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("demo", help="run complete isolated replay")
    for command, help_text in (
        ("init", "copy synthetic fixture files into a workspace"),
        ("resume", "verify inputs and continue replay from workspace files"),
        ("verify", "check listed input bytes against the local manifest"),
    ):
        command_parser = subparsers.add_parser(command, help=help_text)
        command_parser.add_argument("--workspace", required=True, type=Path)
    revise_parser = subparsers.add_parser(
        "revise-material", help="revise synthetic material-ready fixture input"
    )
    revise_parser.add_argument("--workspace", required=True, type=Path)
    revise_parser.add_argument("--date", required=True)

    args = parser.parse_args()
    try:
        if args.command == "demo":
            demo()
        elif args.command == "init":
            initialize(args.workspace)
            print(f"initialized synthetic workspace: {args.workspace}")
        elif args.command == "resume":
            print(encode_json(resume(args.workspace)), end="")
        elif args.command == "verify":
            verified = verify_inputs(args.workspace)
            print(
                encode_json(
                    {
                        "status": "manifest_matches_listed_input_bytes",
                        "input_sha256": verified,
                        "source_authenticity": "not established",
                    }
                ),
                end="",
            )
        elif args.command == "revise-material":
            print(encode_json(revise_material(args.workspace, args.date)), end="")
    except ReplayError as exc:
        print(f"replay error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
