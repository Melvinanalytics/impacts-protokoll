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
TAG = "v0.3.19"


def reports():
    interpreters = [{"report_version": 1, "source_commit": SOURCE, "run_url": RUN,
                     "run_attempt": 1, "python": version, "command": evidence.COMMAND,
                     "counts": {"tests": 25, "failures": 0, "errors": 0, "skipped": 1}}
                    for version in ("3.11.15", "3.14.6")]
    manifest, cases = evidence._corpus(ROOT)
    lines = [f"PASS {case['id']}" for case in cases]
    lines.append(
        f"Conformance summary: applicable={len(cases)} passed={len(cases)} "
        f"unsupported=0 failed=0 total={len(cases)}"
    )
    parsed = evidence.parse_conformance_output("\n".join(lines), ROOT)
    native = [
        {
            "report_version": 1,
            "evidence_kind": "native-conformance",
            "source_commit": SOURCE,
            "tag": TAG,
            "run_url": RUN,
            "run_attempt": 1,
            "runner_os": runner_os,
            "os_platform": os_platform,
            "python_implementation": "CPython",
            "python_version": "3.12.10",
            **parsed,
        }
        for runner_os, os_platform in (
            ("Windows", "Windows-2025ServerDatacenter-10.0.26100-SP0"),
            ("macOS", "macOS-15.0-arm64-arm-64bit"),
        )
    ]
    assert parsed["corpus_sha256"] == evidence.hashlib.sha256(manifest).hexdigest()
    return interpreters + native


def test_capture_whitelists_aggregate_counts_without_leaking_junit(tmp_path, monkeypatch):
    xml = tmp_path / "report.xml"
    xml.write_text('<testsuites><testsuite tests="25" failures="0" errors="0" skipped="1" '
                   'hostname="private-host"><testcase name="private-name"/></testsuite></testsuites>')
    monkeypatch.setattr(evidence.platform, "python_version", lambda: "3.11.15")
    result = evidence.capture(xml, SOURCE, RUN, 1)
    assert result == reports()[0]
    assert "private" not in json.dumps(result)


def test_notes_preserve_generated_body_are_idempotent_and_support_publish_retry():
    draft = {"tag_name": TAG, "draft": True, "body": "## What's Changed\nExisting notes.\n"}
    patch = evidence.release_patch(draft, reports(), SOURCE, RUN, 2, TAG)
    assert patch["tag_name"] == TAG
    assert patch["body"].startswith(draft["body"])
    assert "| 3.14.6 | 24 | 1 | 0 | 0 |" in patch["body"]
    assert "include subtests" in patch["body"]
    assert "build attempt 1" in patch["body"]
    assert "### Windows and macOS conformance evidence" in patch["body"]
    assert "Windows-2025ServerDatacenter-10.0.26100-SP0" in patch["body"]
    assert "CPython 3.12.10" in patch["body"]
    assert "Corpus SHA-256" in patch["body"]
    assert "independent verification" in patch["body"]
    assert evidence.release_patch({"draft": True, **patch}, reports(), SOURCE, RUN, 2, TAG) == patch


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
        evidence.release_patch({"tag_name": TAG, "draft": True}, values, SOURCE, RUN, 2, TAG)


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
        evidence.release_patch({"tag_name": TAG, "draft": True}, values, SOURCE, RUN, 2, TAG)


def test_release_notes_reject_missing_or_duplicate_native_reports():
    values = reports()
    with pytest.raises(ValueError, match="Windows and macOS"):
        evidence.release_patch({"tag_name": TAG, "draft": True}, values[:3], SOURCE, RUN, 2, TAG)
    duplicate = values[:3] + [copy.deepcopy(values[2])]
    with pytest.raises(ValueError, match="Windows and macOS"):
        evidence.release_patch({"tag_name": TAG, "draft": True}, duplicate, SOURCE, RUN, 2, TAG)


@pytest.mark.parametrize("change", [
    {"source_commit": "b" * 40}, {"tag": "v0.3.18"}, {"run_url": RUN + "4"},
    {"run_attempt": 3}, {"runner_os": "Linux"}, {"python_version": "3.11.15"},
    {"corpus_sha256": "b" * 64}, {"corpus_count": 1}, {"passed": 1},
    {"unsupported": 1}, {"failed": 1}, {"unsupported_cases": [{"id": "fake", "reason": "unsupported"}]},
])
def test_native_reports_reject_stale_or_inconsistent_evidence(change):
    values = reports()
    values[2].update(change)
    with pytest.raises(ValueError):
        evidence.release_patch({"tag_name": TAG, "draft": True}, values, SOURCE, RUN, 2, TAG)


def test_native_report_rejects_unsupported_case_that_corpus_does_not_mark_portable():
    values = reports()
    report = values[2]
    report["passed"] -= 1
    report["unsupported"] = 1
    report["unsupported_cases"] = [{"id": "application-valid", "reason": "host is not POSIX; arbitrary filename bytes are unavailable"}]
    with pytest.raises(ValueError, match="unknown or duplicate"):
        evidence.release_patch({"tag_name": TAG, "draft": True}, values, SOURCE, RUN, 2, TAG)


def test_dynamic_corpus_summary_keeps_unsupported_ids_and_reasons():
    _, cases = evidence._corpus(ROOT)
    eligible = next(case["id"] for case in cases if "invalid_utf8_file" in case)
    unsupported = f"UNSUPPORTED {eligible}: host is not POSIX; arbitrary filename bytes are unavailable"
    passed = [case["id"] for case in cases if case["id"] != eligible]
    text = "\n".join([
        *(f"PASS {case_id}" for case_id in passed),
        unsupported,
        f"Conformance summary: applicable={len(passed)} passed={len(passed)} unsupported=1 failed=0 total={len(cases)}",
    ])
    result = evidence.parse_conformance_output(text, ROOT)
    assert result["corpus_count"] == len(cases)
    assert result["passed"] == len(cases) - 1
    assert result["unsupported_cases"] == [{"id": eligible, "reason": "host is not POSIX; arbitrary filename bytes are unavailable"}]


def test_dynamic_filesystem_probe_unsupported_result_is_bound_to_declared_capability():
    _, cases = evidence._corpus(ROOT)
    case = next(case for case in cases if "filesystem_probe" in case)
    probe = case["filesystem_probe"]
    if probe["kind"] == "path-component":
        capability = f"{probe['length']}-byte path components"
    else:
        capability = {
            "case-sensitive": "case-sensitive paths",
            "unicode-distinct": "distinct Unicode spellings",
        }[probe["kind"]]
    reason = f"filesystem lacks {capability} capability (File exists)"
    lines = [f"PASS {candidate['id']}" for candidate in cases if candidate["id"] != case["id"]]
    lines.extend([
        f"UNSUPPORTED {case['id']}: {reason}",
        f"Conformance summary: applicable={len(cases) - 1} passed={len(cases) - 1} "
        f"unsupported=1 failed=0 total={len(cases)}",
    ])
    result = evidence.parse_conformance_output("\n".join(lines), ROOT)
    assert result["unsupported_cases"] == [{"id": case["id"], "reason": reason}]


@pytest.mark.parametrize("mutate", ["missing", "duplicate", "unknown", "failed-summary", "bad-reason"])
def test_native_output_rejects_missing_duplicate_or_inconsistent_case_results(mutate):
    _, cases = evidence._corpus(ROOT)
    lines = [f"PASS {case['id']}" for case in cases]
    passed_count = len(cases)
    unsupported_count = 0
    if mutate == "missing":
        lines.pop(0)
        passed_count -= 1
    elif mutate == "duplicate":
        lines.append(lines[0])
    elif mutate == "unknown":
        lines[0] = "PASS ghost-case"
    elif mutate == "bad-reason":
        eligible = next(case["id"] for case in cases if "invalid_utf8_file" in case)
        index = lines.index(f"PASS {eligible}")
        lines[index] = f"UNSUPPORTED {eligible}: permission denied"
        passed_count -= 1
        unsupported_count = 1
    failed = 1 if mutate == "failed-summary" else 0
    lines.append(
        f"Conformance summary: applicable={passed_count} passed={passed_count} "
        f"unsupported={unsupported_count} failed={failed} total={len(cases)}"
    )
    with pytest.raises(ValueError):
        evidence.parse_conformance_output("\n".join(lines), ROOT)


@pytest.mark.parametrize("draft", [
    {"draft": False}, {"draft": True, "body": evidence.START},
    {"draft": True, "body": evidence.END + evidence.START},
])
def test_published_or_ambiguous_notes_are_not_overwritten(draft):
    with pytest.raises(ValueError):
        evidence.release_patch({"tag_name": TAG, **draft}, reports(), SOURCE, RUN, 1, TAG)


def test_notes_reject_a_draft_attached_to_a_different_tag():
    with pytest.raises(ValueError, match="draft tag"):
        evidence.release_patch(
            {"tag_name": "untagged-48312c7106a2a0522ebc", "draft": True},
            reports(), SOURCE, RUN, 2, TAG,
        )
