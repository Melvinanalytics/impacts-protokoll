"""Public evidence must describe the tested bytes, never guessed or stale counts."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("test_evidence", ROOT / ".github/scripts/test_evidence.py")
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)
SOURCE = "a" * 40
RUN = "https://github.com/example/protocol/actions/runs/123"


def reports():
    return [{"report_version": 1, "source_commit": SOURCE, "run_url": RUN,
             "run_attempt": 1, "python": version, "command": evidence.COMMAND,
             "counts": {"tests": 25, "failures": 0, "errors": 0, "skipped": 1}}
            for version in ("3.11.15", "3.14.6")]


def test_capture_whitelists_aggregate_counts_without_leaking_junit(tmp_path, monkeypatch):
    xml = tmp_path / "report.xml"
    xml.write_text('<testsuites><testsuite tests="25" failures="0" errors="0" skipped="1" '
                   'hostname="private-host"><testcase name="private-name"/></testsuite></testsuites>')
    monkeypatch.setattr(evidence.platform, "python_version", lambda: "3.11.15")
    result = evidence.capture(xml, SOURCE, RUN, 1)
    assert result == reports()[0]
    assert "private" not in json.dumps(result)


def test_notes_preserve_generated_body_are_idempotent_and_support_publish_retry():
    draft = {"draft": True, "body": "## What's Changed\nExisting notes.\n"}
    patch = evidence.release_patch(draft, reports(), SOURCE, RUN, 2)
    assert patch["body"].startswith(draft["body"])
    assert "| 3.14.6 | 24 | 1 | 0 | 0 |" in patch["body"]
    assert "include subtests" in patch["body"]
    assert "build attempt 1" in patch["body"]
    assert "independent verification" in patch["body"]
    assert evidence.release_patch({"draft": True, **patch}, reports(), SOURCE, RUN, 2) == patch


@pytest.mark.parametrize("change", [
    {"source_commit": "b" * 40}, {"run_url": RUN + "4"}, {"run_attempt": 3},
    {"python": "3.12.1"}, {"command": "pytest smoke"}, {"report_version": True},
    {"counts": {"tests": 25, "failures": 1, "errors": 0, "skipped": 1}},
    {"counts": {"tests": 25, "failures": 0, "errors": 1, "skipped": 1}},
    {"counts": {"tests": 1, "failures": 0, "errors": 0, "skipped": 1}},
    {"counts": {"tests": -1, "failures": 0, "errors": 0, "skipped": 0}},
    {"counts": {"tests": True, "failures": 0, "errors": 0, "skipped": 0}},
])
def test_notes_reject_unmatched_or_unsuccessful_evidence(change):
    values = reports()
    values[0].update(change)
    with pytest.raises(ValueError):
        evidence.release_patch({"draft": True}, values, SOURCE, RUN, 2)


@pytest.mark.parametrize("kind", ["missing", "duplicate", "mixed-attempts"])
def test_both_interpreters_must_be_tested_in_one_build(kind):
    values = reports()
    if kind == "missing":
        values.pop()
    elif kind == "duplicate":
        values[1] = copy.deepcopy(values[0])
    else:
        values[1]["run_attempt"] = 2
    with pytest.raises(ValueError):
        evidence.release_patch({"draft": True}, values, SOURCE, RUN, 2)


@pytest.mark.parametrize("draft", [
    {"draft": False}, {"draft": True, "body": evidence.START},
    {"draft": True, "body": evidence.END + evidence.START},
])
def test_published_or_ambiguous_notes_are_not_overwritten(draft):
    with pytest.raises(ValueError):
        evidence.release_patch(draft, reports(), SOURCE, RUN, 1)
