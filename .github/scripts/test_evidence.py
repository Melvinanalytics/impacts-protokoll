"""Publish compact workflow test evidence without exposing raw JUnit or logs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import re
import xml.etree.ElementTree as ET

START = "<!-- impacts-test-evidence:start -->"
END = "<!-- impacts-test-evidence:end -->"
COMMAND = "python -m pytest -q --junitxml=<temporary-report>"
FIELDS = {"report_version", "source_commit", "run_url", "run_attempt", "python", "command", "counts"}


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
    draft: dict, reports: list[dict], source: str, run_url: str, attempt: int, tag: str
) -> dict:
    if draft.get("draft") is not True:
        raise ValueError("test evidence may only update an unpublished draft")
    if not isinstance(tag, str) or not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError("expected a semantic release tag")
    if draft.get("tag_name") != tag:
        raise ValueError("draft tag does not match requested release tag")
    for report in reports:
        build_attempt = report.get("run_attempt") if isinstance(report, dict) else None
        validate(report, source, run_url, build_attempt)
        if build_attempt > attempt:
            raise ValueError("test evidence comes from a future workflow attempt")
    if len(reports) != 2 or {r["python"].rsplit(".", 1)[0] for r in reports} != {"3.11", "3.14"}:
        raise ValueError("expected exactly one successful report for Python 3.11 and 3.14")
    if len({r["run_attempt"] for r in reports}) != 1:
        raise ValueError("test reports must come from the same build attempt")
    build_attempt = reports[0]["run_attempt"]
    rows = []
    for report in sorted(reports, key=lambda r: r["python"]):
        c = report["counts"]
        rows.append(f'| {report["python"]} | {c["tests"] - c["skipped"]} | {c["skipped"]} | {c["failures"]} | {c["errors"]} |')
    section = "\n".join([
        START, "## Workflow test evidence", "",
        f"Source commit: `{source}`. [Release workflow]({run_url}/attempts/{build_attempt}), build attempt {build_attempt}.", "",
        f"Command on each interpreter: `{COMMAND}`.", "",
        "| Python | Passed JUnit cases | Skipped | Failures | Errors |",
        "|---|---:|---:|---:|---:|", *rows, "",
        "JUnit cases include subtests; these totals are not pytest's primary-test count. "
        "This is workflow-reported evidence for the tagged source, not an independent verification "
        "or a build attestation. Raw logs are not required to read these results.", END,
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
    parser.add_argument("mode", choices=("capture", "notes"))
    parser.add_argument("--source", required=True)
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--attempt", required=True, type=int)
    parser.add_argument("--tag")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--xml", type=Path)
    parser.add_argument("--draft", type=Path)
    parser.add_argument("--reports", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "capture":
            if args.xml is None:
                parser.error("capture requires --xml")
            result = capture(args.xml, args.source, args.run_url, args.attempt)
        else:
            if args.draft is None or args.reports is None or args.tag is None:
                parser.error("notes requires --draft, --reports, and --tag")
            reports = [json.loads(p.read_text()) for p in sorted(args.reports.glob("*.json"))]
            result = release_patch(
                json.loads(args.draft.read_text()), reports, args.source,
                args.run_url, args.attempt, args.tag,
            )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (ValueError, KeyError, OSError, ET.ParseError) as exc:
        parser.exit(1, f"test evidence: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
