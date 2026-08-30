#!/usr/bin/env python3
"""Komplexitätsbudget gegen private Git- oder portable Public-Baseline prüfen."""

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
ACCEPTED_BASELINE_REVISION = "2c0aaa5d425cdd9a3daf9ffa9a5d800c84c625a5"
PORTABLE_BASELINE = {
    "root_dirs": 6,
    "protocol_schemas": 7,
    "max_total_required_fields_per_schema": 20,
}
PORTABLE_LIMITS = {
    "root_dirs": 6,
    "protocol_schemas": 9,
    "max_total_required_fields_per_schema": 21,
}


def measure() -> dict:
    roots = [p.name for p in REPO.iterdir() if p.is_dir()]
    schemas = sorted((REPO / "02_protocol" / "schemas").glob("*.json"))
    counts = {p.name: _required_count(json.loads(p.read_text(encoding="utf-8"))) for p in schemas}
    return _measurement(roots, counts)


def accepted_baseline() -> dict[str, int]:
    """Measure committed architecture without trusting mutable budget values."""
    revision = _baseline_revision()
    if revision is None:
        return dict(PORTABLE_BASELINE)
    roots = _git("ls-tree", "-d", "--name-only", revision).splitlines()
    paths = [
        p for p in _git("ls-tree", "-r", "--name-only", revision, "02_protocol/schemas").splitlines()
        if p.endswith(".json")
    ]
    counts = {Path(p).name: _required_count(json.loads(_git("show", f"{revision}:{p}"))) for p in paths}
    measured = _measurement(roots, counts)
    return {field: int(measured[field]) for field in METRICS}


def accepted_limits() -> dict[str, int]:
    """Read limits from the accepted revision when its budget is inspectable."""
    revision = _baseline_revision()
    if revision is None:
        return dict(PORTABLE_LIMITS)
    try:
        relative = BUDGET.resolve().relative_to(HISTORY_REPO.resolve()).as_posix()
        previous = yaml.safe_load(_git("show", f"{revision}:{relative}"))
        limits = previous.get("limits") if isinstance(previous, dict) else None
        if not isinstance(limits, dict) or set(limits) != set(METRICS):
            raise ValueError("accepted budget limits have an invalid form")
        if not all(
            isinstance(limits[field], int) and not isinstance(limits[field], bool)
            for field in METRICS
        ):
            raise ValueError("accepted budget limits must be integers")
        return {field: int(limits[field]) for field in METRICS}
    except (ValueError, subprocess.CalledProcessError):
        return accepted_baseline()


def main() -> int:
    try:
        budget = yaml.safe_load(BUDGET.read_text(encoding="utf-8"))
        baseline_limits = accepted_limits()
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"VERLETZUNG: Budget oder Git-Baseline nicht prüfbar: {error}")
        return 1
    if not isinstance(budget, dict) or budget.get("version") != 3:
        print("VERLETZUNG: budget.yaml braucht version 3.")
        return 1
    if set(budget) != {"version", "limits", "approvals"}:
        print("VERLETZUNG: budget.yaml erlaubt nur version, limits und approvals.")
        return 1
    limits, approvals = budget.get("limits"), budget.get("approvals")
    if not isinstance(limits, dict) or set(limits) != set(METRICS) or not isinstance(approvals, list):
        print("VERLETZUNG: limits oder approvals besitzen eine ungültige Form.")
        return 1
    for field, value in limits.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            print(f"VERLETZUNG: {field} braucht eine nichtnegative Ganzzahl.")
            return 1
    for approval in approvals:
        if not isinstance(approval, dict):
            print("VERLETZUNG: approval muss ein Objekt sein.")
            return 1
        by = approval.get("approved_by")
        if not isinstance(by, str) or HUMAN_ATTRIBUTION.fullmatch(by) is None:
            print(f"VERLETZUNG: approval braucht approved_by human:<id>: {approval}")
            return 1
        if approval.get("field") not in METRICS or not str(approval.get("reason", "")).strip():
            print(f"VERLETZUNG: approval braucht Messfeld und Begründung: {approval}")
            return 1
    for field in METRICS:
        if limits[field] <= baseline_limits[field]:
            continue
        matching = [a for a in approvals if a.get("field") == field and a.get("from") == baseline_limits[field] and a.get("to") == limits[field]]
        if not matching:
            print(f"VERLETZUNG: Budgeterhöhung ohne dokumentierte human:-Attribution: {field} {baseline_limits[field]} -> {limits[field]}")
            return 1
    actual = measure()
    failures = []
    for field in METRICS:
        value, limit = actual[field], limits[field]
        status = "ok" if value <= limit else "VERLETZUNG"
        print(f"{status:10} {field:40} ist={value:3} limit={limit}")
        if value > limit:
            failures.append(field)
    if failures:
        print("\nBudget verletzt:", ", ".join(failures))
        print("Struktur vereinfachen oder eine human:-Attribution mit Begründung dokumentieren.")
        return 1
    print("\nKomplexitätsbudget eingehalten.")
    return 0


def _git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(HISTORY_REPO), *args], text=True, stderr=subprocess.STDOUT)


def _baseline_revision() -> str | None:
    git_metadata = HISTORY_REPO / ".git"
    if not git_metadata.exists() and not git_metadata.is_symlink():
        return None
    _git("rev-parse", "--verify", "HEAD^{commit}")
    _git("rev-list", "--objects", "HEAD")
    object_type = _git_object_type(ACCEPTED_BASELINE_REVISION)
    if object_type is None:
        return None
    if object_type != "commit":
        raise ValueError(
            f"accepted baseline must be a commit, got {object_type!r}"
        )
    _git("cat-file", "-e", f"{ACCEPTED_BASELINE_REVISION}^{{commit}}")
    return ACCEPTED_BASELINE_REVISION


def _git_object_type(object_name: str) -> str | None:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(HISTORY_REPO),
            "cat-file",
            "--batch-check=%(objectname) %(objecttype)",
        ],
        input=f"{object_name}\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    output = result.stdout.strip()
    if output == f"{object_name} missing":
        return None
    prefix = f"{object_name} "
    if output.startswith(prefix) and "\n" not in output:
        return output.removeprefix(prefix)
    raise ValueError(f"unexpected git object response: {output!r}")


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
