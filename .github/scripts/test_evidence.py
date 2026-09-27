"""Publish compact workflow test evidence without exposing raw JUnit or logs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import xml.etree.ElementTree as ET

START = "<!-- impacts-test-evidence:start -->"
END = "<!-- impacts-test-evidence:end -->"
COMMAND = "python -m pytest -q --junitxml=<temporary-report>"
FIELDS = {"report_version", "source_commit", "run_url", "run_attempt", "python", "command", "counts"}
NATIVE_FIELDS = {
    "report_version", "evidence_kind", "source_commit", "tag", "run_url", "run_attempt",
    "runner_os", "os_platform", "python_implementation", "python_version",
    "corpus_sha256", "corpus_count", "passed", "unsupported", "failed", "unsupported_cases",
}
SUMMARY = re.compile(
    r"^Conformance summary: applicable=(\d+) passed=(\d+) unsupported=(\d+) failed=(\d+) total=(\d+)$"
)
PASS = re.compile(r"^PASS ([A-Za-z0-9_.-]+)(?: \([1-9][0-9]* fresh processes\))?$")
UNSUPPORTED = re.compile(r"^UNSUPPORTED ([A-Za-z0-9_.-]+): (.+)$")
NATIVE_UNSUPPORTED_REASONS = (
    "host is not POSIX; arbitrary filename bytes are unavailable",
)


def _corpus(root: Path) -> tuple[bytes, list[dict]]:
    raw = (root / "06_evaluations/conformance/cases.json").read_bytes()
    manifest = json.loads(raw.decode("utf-8"))
    cases = manifest.get("cases") if isinstance(manifest, dict) else None
    if not isinstance(cases, list) or not cases:
        raise ValueError("conformance corpus must contain a non-empty cases array")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or any(not isinstance(value, str) or not value for value in identifiers):
        raise ValueError("conformance corpus case IDs must be non-empty strings")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("conformance corpus case IDs must be unique")
    return raw, cases


def _unsupported_reason_allowed(case: dict, reason: str) -> bool:
    if "invalid_utf8_file" in case:
        if reason in NATIVE_UNSUPPORTED_REASONS:
            return True
        prefix = "filesystem rejects non-UTF-8 filename ("
        if reason.startswith(prefix) and reason.endswith(")") and reason[len(prefix):-1].strip():
            return True
    probe = case.get("filesystem_probe")
    if isinstance(probe, dict):
        kind = probe.get("kind")
        if kind == "case-sensitive":
            capability = "case-sensitive paths"
        elif kind == "path-component" and type(probe.get("length")) is int and probe["length"] > 0:
            capability = f'{probe["length"]}-byte path components'
        elif kind == "unicode-distinct":
            capability = "distinct Unicode spellings"
        else:
            capability = None
        if capability is not None:
            prefix = f"filesystem lacks {capability} capability ("
            if reason.startswith(prefix) and reason.endswith(")") and reason[len(prefix):-1].strip():
                return True
    bad_folder_count = len(case.get("bad_folders", []))
    if type(case.get("bad_folder_length")) is int:
        bad_folder_count += 1
    match = re.fullmatch(
        r"filesystem cannot preserve requested folder spelling for bad-folder probe ([1-9][0-9]*)",
        reason,
    )
    return match is not None and int(match.group(1)) <= bad_folder_count


def parse_conformance_output(text: str, root: Path) -> dict:
    """Check complete runner output against this checkout's frozen case list."""
    raw, cases = _corpus(root)
    case_by_id = {case["id"]: case for case in cases}
    outcomes: dict[str, tuple[str, str | None]] = {}
    summary: tuple[int, int, int, int, int] | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        summary_match = SUMMARY.fullmatch(line)
        if summary_match:
            if summary is not None:
                raise ValueError("conformance output contains duplicate summaries")
            summary = tuple(int(value) for value in summary_match.groups())
            continue
        passed = PASS.fullmatch(line)
        unsupported = UNSUPPORTED.fullmatch(line)
        if line.startswith("FAIL "):
            raise ValueError(f"conformance runner reported failure: {line}")
        if passed:
            case_id, kind, reason = passed.group(1), "passed", None
        elif unsupported:
            case_id, kind, reason = unsupported.group(1), "unsupported", unsupported.group(2)
        else:
            raise ValueError(f"unexpected conformance output line: {line!r}")
        if case_id not in case_by_id:
            raise ValueError(f"conformance output contains unknown case: {case_id}")
        if case_id in outcomes:
            raise ValueError(f"conformance output repeats case: {case_id}")
        if kind == "unsupported":
            case = case_by_id[case_id]
            if not any(key in case for key in ("invalid_utf8_file", "filesystem_probe", "bad_folders", "bad_folder_length")):
                raise ValueError(f"case cannot be unsupported on this host: {case_id}")
            if not _unsupported_reason_allowed(case, reason or ""):
                raise ValueError(f"unsupported reason is outside the portability boundary: {reason!r}")
        outcomes[case_id] = (kind, reason)

    expected_ids = set(case_by_id)
    if set(outcomes) != expected_ids:
        missing = sorted(expected_ids - set(outcomes))
        extra = sorted(set(outcomes) - expected_ids)
        raise ValueError(f"conformance output does not cover corpus cases; missing={missing}, extra={extra}")
    if summary is None:
        raise ValueError("conformance output has no summary")
    applicable, passed_count, unsupported_count, failed_count, total = summary
    observed_passed = sum(kind == "passed" for kind, _ in outcomes.values())
    observed_unsupported = sum(kind == "unsupported" for kind, _ in outcomes.values())
    if (
        total != len(cases)
        or total != len(outcomes)
        or passed_count != observed_passed
        or unsupported_count != observed_unsupported
        or failed_count != 0
        or applicable != observed_passed
        or observed_passed == 0
    ):
        raise ValueError("conformance summary is inconsistent with case outcomes")
    return {
        "corpus_sha256": hashlib.sha256(raw).hexdigest(),
        "corpus_count": len(cases),
        "passed": passed_count,
        "unsupported": unsupported_count,
        "failed": failed_count,
        "unsupported_cases": [
            {"id": case_id, "reason": reason}
            for case_id, (kind, reason) in sorted(outcomes.items())
            if kind == "unsupported"
        ],
    }


def validate_native(
    report: dict,
    source: str,
    run_url: str,
    tag: str,
    root: Path,
    expected_attempt: int | None = None,
) -> None:
    if not isinstance(report, dict) or set(report) != NATIVE_FIELDS:
        raise ValueError("unexpected native evidence fields")
    if not re.fullmatch(r"[0-9a-f]{40}", source):
        raise ValueError("expected a full source commit")
    if not re.fullmatch(r"https://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/actions/runs/[1-9][0-9]*", run_url):
        raise ValueError("expected a GitHub workflow run URL")
    if not isinstance(tag, str) or not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError("expected a semantic release tag")
    attempt = report["run_attempt"]
    if type(attempt) is not int or attempt < 1 or (expected_attempt is not None and attempt != expected_attempt):
        raise ValueError("native evidence has a stale or invalid workflow attempt")
    if (
        type(report["report_version"]) is not int or report["report_version"] != 1
        or report["evidence_kind"] != "native-conformance"
        or report["source_commit"] != source or report["tag"] != tag
        or report["run_url"] != run_url
    ):
        raise ValueError("native evidence does not match this source, tag, and workflow run")
    if not isinstance(report["runner_os"], str) or report["runner_os"] not in {"Windows", "macOS"}:
        raise ValueError("native evidence must come from Windows or macOS")
    if (
        not isinstance(report["os_platform"], str) or not report["os_platform"]
        or any(char in report["os_platform"] for char in "\r\n|")
        or not report["os_platform"].startswith(report["runner_os"] + "-")
    ):
        raise ValueError("native evidence needs an exact OS platform string")
    if report["python_implementation"] != "CPython" or not isinstance(report["python_version"], str) or not re.fullmatch(r"3\.12\.[0-9]+", report["python_version"]):
        raise ValueError("native evidence needs the exact CPython 3.12 runtime")
    raw, cases = _corpus(root)
    expected = {
        "corpus_sha256": hashlib.sha256(raw).hexdigest(),
        "corpus_count": len(cases),
    }
    if any(report[key] != value for key, value in expected.items()):
        raise ValueError("native evidence is stale for this conformance corpus")
    for key in ("corpus_count", "passed", "unsupported", "failed"):
        if type(report[key]) is not int or report[key] < 0:
            raise ValueError("native evidence counts must be nonnegative integers")
    if report["failed"] != 0 or report["passed"] == 0 or report["passed"] + report["unsupported"] != report["corpus_count"]:
        raise ValueError("native evidence counts are inconsistent or unsuccessful")
    unsupported_cases = report["unsupported_cases"]
    if not isinstance(unsupported_cases, list) or len(unsupported_cases) != report["unsupported"]:
        raise ValueError("native evidence unsupported cases do not match the count")
    eligible = {
        case["id"] for case in cases
        if any(key in case for key in ("invalid_utf8_file", "filesystem_probe", "bad_folders", "bad_folder_length"))
    }
    seen: set[str] = set()
    for item in unsupported_cases:
        if not isinstance(item, dict) or set(item) != {"id", "reason"}:
            raise ValueError("malformed unsupported native case")
        case_id, reason = item["id"], item["reason"]
        if not isinstance(case_id, str) or case_id not in eligible or case_id in seen:
            raise ValueError("native evidence has an unknown or duplicate unsupported case")
        case = next(case for case in cases if case["id"] == case_id)
        if not isinstance(reason, str) or not _unsupported_reason_allowed(case, reason):
            raise ValueError("native evidence has an unsupported portability reason")
        seen.add(case_id)
    # A report cannot claim a different count or omit the reported unsupported cases.
    if report["unsupported"] != len(seen):
        raise ValueError("native evidence unsupported case list is inconsistent")


def capture_native(
    log: Path,
    root: Path,
    source: str,
    run_url: str,
    attempt: int,
    tag: str,
    expected_os: str | None = None,
) -> dict:
    try:
        observed_source = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, encoding="ascii"
        ).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError(f"cannot read checked-out source commit: {error}") from error
    if observed_source != source:
        raise ValueError("native evidence source does not match checked-out HEAD")
    runner_os = {"Windows": "Windows", "Darwin": "macOS"}.get(platform.system())
    if runner_os not in {"Windows", "macOS"} or (expected_os is not None and runner_os != expected_os):
        raise ValueError(f"native runner OS is {runner_os!r}, expected {expected_os!r}")
    parsed = parse_conformance_output(log.read_text(encoding="utf-8-sig"), root)
    os_platform = platform.platform()
    report = {
        "report_version": 1,
        "evidence_kind": "native-conformance",
        "source_commit": source,
        "tag": tag,
        "run_url": run_url,
        "run_attempt": attempt,
        "runner_os": runner_os,
        "os_platform": os_platform,
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        **parsed,
    }
    validate_native(report, source, run_url, tag, root, expected_attempt=attempt)
    return report


def validate(report: dict, source: str, run_url: str, attempt: int) -> None:
    if not isinstance(report, dict) or set(report) != FIELDS:
        raise ValueError("unexpected test evidence fields")
    if not re.fullmatch(r"[0-9a-f]{40}", source):
        raise ValueError("expected a full source commit")
    if not re.fullmatch(r"https://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/actions/runs/[1-9][0-9]*", run_url):
        raise ValueError("expected a GitHub workflow run URL")
    if type(attempt) is not int or attempt < 1:
        raise ValueError("expected a positive workflow attempt")
    if (type(report["report_version"]) is not int or report["report_version"] != 1 or report["source_commit"] != source
            or report["run_url"] != run_url or report["run_attempt"] != attempt
            or type(report["run_attempt"]) is not int
            or report["command"] != COMMAND):
        raise ValueError("test evidence does not match this source and workflow attempt")
    if not isinstance(report["python"], str) or not re.fullmatch(r"3\.(11|14)\.[0-9]+", report["python"]):
        raise ValueError("expected an exact supported Python version")
    counts = report["counts"]
    if not isinstance(counts, dict) or set(counts) != {"tests", "failures", "errors", "skipped"}:
        raise ValueError("unexpected JUnit counts")
    if any(type(n) is not int or n < 0 for n in counts.values()):
        raise ValueError("JUnit counts must be nonnegative integers")
    if counts["failures"] or counts["errors"] or counts["tests"] <= counts["skipped"]:
        raise ValueError("test evidence must contain successful tests and no failures or errors")


def capture(xml: Path, source: str, run_url: str, attempt: int) -> dict:
    root = ET.parse(xml).getroot()
    # pytest emits one suite. Do not sum parent and child aggregate counters.
    if root.tag != "testsuites" or len(root) != 1 or root[0].tag != "testsuite":
        raise ValueError("expected one pytest JUnit suite")
    report = {
        "report_version": 1, "source_commit": source, "run_url": run_url,
        "run_attempt": attempt, "python": platform.python_version(), "command": COMMAND,
        "counts": {key: int(root[0].attrib[key]) for key in ("tests", "failures", "errors", "skipped")},
    }
    validate(report, source, run_url, attempt)
    return report


def release_patch(
    draft: dict, reports: list[dict], source: str, run_url: str, attempt: int, tag: str,
    root: Path | None = None,
) -> dict:
    if draft.get("draft") is not True:
        raise ValueError("test evidence may only update an unpublished draft")
    if not isinstance(tag, str) or not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError("expected a semantic release tag")
    if draft.get("tag_name") != tag:
        raise ValueError("draft tag does not match requested release tag")
    if not isinstance(reports, list):
        raise ValueError("test evidence reports must be an array")
    python_reports = [report for report in reports if isinstance(report, dict) and "python" in report]
    native_reports = [report for report in reports if isinstance(report, dict) and "runner_os" in report]
    if len(reports) != len(python_reports) + len(native_reports):
        raise ValueError("unexpected or malformed test evidence report")
    if len(python_reports) != 2:
        raise ValueError("expected exactly one successful report for Python 3.11 and 3.14")
    if len(native_reports) != 2:
        raise ValueError("expected exactly one successful native report for Windows and macOS")
    native_root = root or Path(__file__).resolve().parents[2]
    build_attempts = set()
    for report in python_reports:
        build_attempt = report.get("run_attempt")
        validate(report, source, run_url, build_attempt)
        if build_attempt > attempt:
            raise ValueError("test evidence comes from a future workflow attempt")
        build_attempts.add(build_attempt)
    if {report["python"].rsplit(".", 1)[0] for report in python_reports} != {"3.11", "3.14"}:
        raise ValueError("expected exactly one successful report for Python 3.11 and 3.14")
    for report in native_reports:
        build_attempt = report.get("run_attempt")
        validate_native(report, source, run_url, tag, native_root, expected_attempt=build_attempt)
        if build_attempt > attempt:
            raise ValueError("native evidence comes from a future workflow attempt")
        build_attempts.add(build_attempt)
    if {report["runner_os"] for report in native_reports} != {"Windows", "macOS"}:
        raise ValueError("expected exactly one successful native report for Windows and macOS")
    if len(build_attempts) != 1:
        raise ValueError("all test and native evidence must come from the same build attempt")
    build_attempt = next(iter(build_attempts))
    rows = []
    for report in sorted(python_reports, key=lambda r: r["python"]):
        c = report["counts"]
        rows.append(f'| {report["python"]} | {c["tests"] - c["skipped"]} | {c["skipped"]} | {c["failures"]} | {c["errors"]} |')
    native_rows = []
    for report in sorted(native_reports, key=lambda r: r["runner_os"]):
        unsupported = report["unsupported_cases"]
        detail = "; ".join(f'`{item["id"]}`: {item["reason"]}' for item in unsupported) or "none"
        native_rows.append(
            f'| {report["runner_os"]} | `{report["os_platform"]}` | '
            f'{report["python_implementation"]} {report["python_version"]} | '
            f'`{report["corpus_sha256"]}` | {report["corpus_count"]} | '
            f'{report["passed"]} | {report["unsupported"]} | {detail} |'
        )
    section = "\n".join([
        START, "## Workflow test evidence", "",
        f"Release tag: `{tag}`. Source commit: `{source}`. [Release workflow]({run_url}/attempts/{build_attempt}), build attempt {build_attempt}.", "",
        f"Command on each interpreter: `{COMMAND}`.", "",
        "| Python | Passed JUnit cases | Skipped | Failures | Errors |",
        "|---|---:|---:|---:|---:|", *rows, "",
        "JUnit cases include subtests; these totals are not pytest's primary-test count. "
        "This is workflow-reported evidence for the tagged source, not an independent verification "
        "or a build attestation. Raw logs are not required to read these results.", "",
        "### Windows and macOS conformance evidence", "",
        "The manifest digest identifies `06_evaluations/conformance/cases.json`; unsupported outcomes appear with their case IDs and runner reasons.", "",
        "| Runner | Exact OS platform | Python runtime | Corpus SHA-256 | Cases | Passed | Unsupported | Unsupported cases and reasons |",
        "|---|---|---|---|---:|---:|---:|---|", *native_rows, "",
        "These results describe only the named runners and corpus revision. They are workflow-reported evidence, not independent verification or a build attestation.", END,
    ])
    body = draft.get("body") or ""
    if not isinstance(body, str):
        raise ValueError("invalid release body")
    if START in body or END in body:
        if body.count(START) != 1 or body.count(END) != 1 or body.index(END) < body.index(START):
            raise ValueError("ambiguous existing test evidence section")
        body = body[:body.index(START)] + section + body[body.index(END) + len(END):]
    else:
        body = body.rstrip() + "\n\n" + section + "\n"
    return {"tag_name": tag, "body": body}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("capture", "notes", "native-check", "native-capture"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--source")
    parser.add_argument("--run-url")
    parser.add_argument("--attempt", type=int)
    parser.add_argument("--tag")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--xml", type=Path)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--expected-os")
    parser.add_argument("--draft", type=Path)
    parser.add_argument("--reports", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "capture":
            if args.xml is None or args.output is None or args.source is None or args.run_url is None or args.attempt is None:
                parser.error("capture requires --xml, --output, --source, --run-url, and --attempt")
            result = capture(args.xml, args.source, args.run_url, args.attempt)
        elif args.mode == "notes":
            if any(value is None for value in (args.draft, args.reports, args.tag, args.source, args.run_url, args.attempt, args.output)):
                parser.error("notes requires --draft, --reports, --tag, --source, --run-url, --attempt, and --output")
            reports = [json.loads(p.read_text()) for p in sorted(args.reports.glob("*.json"))]
            result = release_patch(
                json.loads(args.draft.read_text()), reports, args.source,
                args.run_url, args.attempt, args.tag, args.root,
            )
        elif args.mode == "native-check":
            if args.log is None:
                parser.error("native-check requires --log")
            parse_conformance_output(args.log.read_text(encoding="utf-8-sig"), args.root)
            return 0
        else:
            if any(value is None for value in (args.log, args.output, args.source, args.run_url, args.attempt, args.tag)):
                parser.error("native-capture requires --log, --output, --source, --run-url, --attempt, and --tag")
            result = capture_native(
                args.log, args.root, args.source, args.run_url,
                args.attempt, args.tag, args.expected_os,
            )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (ValueError, KeyError, OSError, ET.ParseError) as exc:
        parser.exit(1, f"test evidence: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
