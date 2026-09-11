#!/usr/bin/env python3
"""Check the complexity budget against the preceding public release tag."""

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
HISTORY_REPO = REPO
BUDGET = Path(__file__).resolve().parent / "budget.yaml"
IGNORED_ROOT = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".superpowers",
    ".venv",
    "__pycache__",
    "build",
    "node_modules",
}
METRICS = ("root_dirs", "protocol_schemas", "max_total_required_fields_per_schema")
HUMAN_ATTRIBUTION = re.compile(r"human:[^:\s][^\s]*\Z")
RELEASE_TAG = re.compile(r"v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)\Z")


def measure() -> dict:
    roots = [p.name for p in REPO.iterdir() if p.is_dir()]
    schemas = sorted((REPO / "02_protocol" / "schemas").glob("*.json"))
    counts = {p.name: _required_count(json.loads(p.read_text(encoding="utf-8"))) for p in schemas}
    return _measurement(roots, counts)


def accepted_limits(budget: dict) -> dict[str, int]:
    """Read the immutable prior release boundary or the approved V0.2 bootstrap."""
    initial = budget["initial_release"]
    baseline_tag = _baseline_tag()
    if baseline_tag is None or _version_key(baseline_tag) < _version_key(initial["tag"]):
        return dict(initial["limits"])
    relative = "06_evaluations/complexity-budget/budget.yaml"
    previous = yaml.safe_load(_git("show", f"{baseline_tag}:{relative}"))
    limits = previous.get("limits") if isinstance(previous, dict) else None
    _validate_limits(limits, "release-tag limits")
    return {field: int(limits[field]) for field in METRICS}


def main() -> int:
    try:
        budget = yaml.safe_load(BUDGET.read_text(encoding="utf-8"))
        if not isinstance(budget, dict) or budget.get("version") != 4:
            raise ValueError("budget.yaml requires version 4")
        if set(budget) != {"version", "limits", "approvals", "initial_release"}:
            raise ValueError("budget.yaml has unknown fields")
        limits, approvals = budget.get("limits"), budget.get("approvals")
        _validate_limits(limits, "limits")
        _validate_initial_release(budget.get("initial_release"))
        if not isinstance(approvals, list):
            raise ValueError("approvals must be a list")
        baseline_limits = accepted_limits(budget)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"VIOLATION: Cannot verify budget or release baseline: {error}")
        return 1
    for approval in approvals:
        if not isinstance(approval, dict):
            print("VIOLATION: approval must be an object.")
            return 1
        by = approval.get("approved_by")
        if not isinstance(by, str) or HUMAN_ATTRIBUTION.fullmatch(by) is None:
            print(f"VIOLATION: approval requires approved_by human:<id>: {approval}")
            return 1
        if approval.get("field") not in METRICS or not str(approval.get("reason", "")).strip():
            print(f"VIOLATION: approval requires a metric and reason: {approval}")
            return 1
    for field in METRICS:
        if limits[field] <= baseline_limits[field]:
            continue
        matching = [a for a in approvals if a.get("field") == field and a.get("from") == baseline_limits[field] and a.get("to") == limits[field]]
        if not matching:
            print(f"VIOLATION: Budget increase without documented human: attribution: {field} {baseline_limits[field]} -> {limits[field]}")
            return 1
    actual = measure()
    failures = []
    for field in METRICS:
        value, limit = actual[field], limits[field]
        status = "ok" if value <= limit else "VIOLATION"
        print(f"{status:10} {field:40} actual={value:3} limit={limit}")
        if value > limit:
            failures.append(field)
    if failures:
        print("\nBudget exceeded:", ", ".join(failures))
        print("Simplify the structure or document a human: attribution with a reason.")
        return 1
    print("\nComplexity budget respected.")
    return 0


def _git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(HISTORY_REPO), *args], text=True, stderr=subprocess.STDOUT)


def _baseline_tag() -> str | None:
    git_metadata = HISTORY_REPO / ".git"
    if not git_metadata.exists() and not git_metadata.is_symlink():
        return None
    head = _git("rev-parse", "HEAD")
    tags = _git(
        "tag",
        "--merged",
        "HEAD",
        "--list",
        "v[0-9]*",
        "--sort=-version:refname",
    )
    for tag in tags.splitlines():
        if RELEASE_TAG.fullmatch(tag) is None:
            continue
        if _git("rev-list", "-n", "1", tag) != head:
            return tag
    return None


def _version_key(tag: str) -> tuple[int, int, int]:
    match = RELEASE_TAG.fullmatch(tag)
    if match is None:
        raise ValueError(f"invalid release tag: {tag}")
    return tuple(int(match.group(name)) for name in ("major", "minor", "patch"))


def _validate_limits(value, label: str) -> None:
    if not isinstance(value, dict) or set(value) != set(METRICS):
        raise ValueError(f"{label} has an invalid shape")
    if not all(
        isinstance(value[field], int)
        and not isinstance(value[field], bool)
        and value[field] >= 0
        for field in METRICS
    ):
        raise ValueError(f"{label} requires nonnegative integers")


def _validate_initial_release(value) -> None:
    expected = {"tag", "limits", "approved_by", "reason"}
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError("initial_release has an invalid shape")
    if RELEASE_TAG.fullmatch(str(value["tag"])) is None:
        raise ValueError("initial_release requires a release tag")
    _validate_limits(value["limits"], "initial_release limits")
    if HUMAN_ATTRIBUTION.fullmatch(str(value["approved_by"])) is None:
        raise ValueError("initial_release requires approved_by human:<id>")
    if not str(value["reason"]).strip():
        raise ValueError("initial_release requires a reason")


def _measurement(root_names: list[str], counts: dict[str, int]) -> dict:
    roots = sorted(name for name in root_names if not _ignored_root(name))
    return {
        "root_dirs": len(roots),
        "root_dir_names": roots,
        "protocol_schemas": len(counts),
        "max_total_required_fields_per_schema": max(counts.values()) if counts else 0,
        "required_field_counts": counts,
    }


def _ignored_root(name: str) -> bool:
    return name in IGNORED_ROOT or name.endswith(".egg-info")


def _required_count(value) -> int:
    if isinstance(value, dict):
        own = len(value.get("required", [])) if isinstance(value.get("required", []), list) else 0
        return own + sum(_required_count(child) for child in value.values())
    if isinstance(value, list):
        return sum(_required_count(child) for child in value)
    return 0


if __name__ == "__main__":
    sys.exit(main())
