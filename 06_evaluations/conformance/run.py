#!/usr/bin/env python3
"""Run frozen CLI conformance cases against a command supplied as JSON argv."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


HERE = Path(__file__).resolve().parent
MANIFEST_PATH = HERE / "cases.json"
RUN_ASSETS = HERE / "fixtures" / "common-run-assets"
REVISION_TOKEN = "@APPLICATION_REVISION@"
HASH_PREFIX = "sha256:"


class ConformanceError(Exception):
    """A fixture, process, or candidate report failed the frozen contract."""


def _relative_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ConformanceError(f"{label} must be a non-empty relative path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or not path.parts
        or path.as_posix() != value
        or "\\" in value
        or ":" in path.parts[0]
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise ConformanceError(f"{label} must be a normalized relative path")
    return Path(*path.parts)


def _load_manifest(path: Path | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest_path = path or MANIFEST_PATH
    try:
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except (OSError, json.JSONDecodeError, ConformanceError, RecursionError) as error:
        raise ConformanceError(f"cannot read cases.json: {error}") from error
    if not isinstance(manifest, dict) or type(manifest.get("corpus_version")) is not int:
        raise ConformanceError("cases.json needs integer corpus_version")
    if manifest["corpus_version"] != 1:
        raise ConformanceError("unsupported corpus_version")
    _relative_path(manifest.get("application_path"), "application_path")
    base_fixture = _relative_path(manifest.get("base_fixture"), "base_fixture")
    if not (HERE / base_fixture).is_dir():
        raise ConformanceError(f"base fixture not found: {base_fixture.as_posix()}")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ConformanceError("cases.json needs non-empty cases array")

    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ConformanceError("each case must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise ConformanceError("case IDs must be unique non-empty strings")
        seen.add(case_id)
        command = case.get("command")
        if command not in ("validate", "hash"):
            raise ConformanceError(f"{case_id}: command must be validate or hash")
        fixture = case.get("fixture")
        if fixture is not None:
            fixture_path = _relative_path(fixture, f"{case_id}.fixture")
            if not (HERE / fixture_path).is_dir():
                raise ConformanceError(f"{case_id}: fixture not found: {fixture}")
        if command == "hash":
            _relative_path(case.get("attempt"), f"{case_id}.attempt")
            surfaces = case.get("surfaces")
            if not isinstance(surfaces, list) or not surfaces:
                raise ConformanceError(f"{case_id}: surfaces must be non-empty array")
            for surface in surfaces:
                _relative_path(surface, f"{case_id}.surface")
        if case.get("git_binding", False) is not False and case.get("git_binding") is not True:
            raise ConformanceError(f"{case_id}: git_binding must be boolean")
        if case.get("history_fixture") is not None:
            history_fixture = _relative_path(case["history_fixture"], f"{case_id}.history_fixture")
            if not (HERE / history_fixture).is_dir():
                raise ConformanceError(f"{case_id}: history fixture not found")
            if case.get("git_binding") is not True:
                raise ConformanceError(f"{case_id}: history fixture needs Git binding")
        repeat = case.get("repeat", 1)
        if type(repeat) is not int or repeat < 1:
            raise ConformanceError(f"{case_id}: repeat must be positive integer")
        _validate_expected(case)
    return manifest, cases


def _validate_expected(case: dict[str, Any]) -> None:
    case_id = case["id"]
    expected = case.get("expected")
    if not isinstance(expected, dict):
        raise ConformanceError(f"{case_id}: expected outcome must be an object")
    exit_code = expected.get("exit_code")
    if type(exit_code) is not int or exit_code not in (0, 1):
        raise ConformanceError(f"{case_id}: expected exit_code must be 0 or 1")
    codes = expected.get("issue_codes")
    if not isinstance(codes, list) or any(not isinstance(code, str) or not code for code in codes):
        raise ConformanceError(f"{case_id}: issue_codes must be strings")
    if codes != sorted(set(codes)):
        raise ConformanceError(f"{case_id}: issue_codes must be sorted and unique")
    if case["command"] == "validate":
        if set(expected) != {"exit_code", "valid", "issue_codes"}:
            raise ConformanceError(f"{case_id}: malformed validate expectation")
        valid = expected["valid"]
        if type(valid) is not bool or exit_code != (0 if valid else 1):
            raise ConformanceError(f"{case_id}: expected validity and exit code disagree")
        if valid != (not codes):
            raise ConformanceError(f"{case_id}: expected validity and issue codes disagree")
    else:
        if set(expected) != {"exit_code", "digest", "issue_codes"}:
            raise ConformanceError(f"{case_id}: malformed hash expectation")
        digest = expected["digest"]
        if digest is not None and (
            not isinstance(digest, str)
            or len(digest) != len(HASH_PREFIX) + 64
            or not digest.startswith(HASH_PREFIX)
            or any(char not in "0123456789abcdef" for char in digest[len(HASH_PREFIX):])
        ):
            raise ConformanceError(f"{case_id}: expected digest must be null or lowercase SHA-256")
        if (digest is not None) != (exit_code == 0) or (digest is not None) != (not codes):
            raise ConformanceError(f"{case_id}: expected digest, issues, and exit code disagree")


def _copy_tree(source: Path, destination: Path) -> None:
    if source.is_symlink() or not source.is_dir():
        raise ConformanceError(f"fixture directory is missing or unsafe: {source}")
    for item in sorted(source.rglob("*")):
        if item.is_symlink():
            raise ConformanceError(f"fixture contains symlink: {item}")
        target = destination / item.relative_to(source)
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif item.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item, target)
        else:
            raise ConformanceError(f"fixture contains non-regular entry: {item}")


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ConformanceError(f"Git fixture setup failed: {error}") from error
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ConformanceError(f"Git fixture setup failed ({result.returncode}): {detail}")
    return result.stdout.strip()


def _commit(root: Path, message: str) -> None:
    _git(
        root,
        "-c", "user.name=Conformance Fixture",
        "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false",
        "commit", "--quiet", "-m", message,
    )


def _bind_application(root: Path, application_path: str) -> None:
    application = _relative_path(application_path, "application_path")
    _git(root, "init", "--quiet")
    _git(root, "add", "--", application.as_posix())
    _commit(root, "conformance Application fixture")
    revision = _git(root, "rev-parse", f"HEAD:{application.as_posix()}")
    run_contexts = sorted((root / "vorgaenge").glob("*/CONTEXT.md"))
    if not run_contexts:
        raise ConformanceError("Git-bound fixture has no Run CONTEXT.md")
    for path in run_contexts:
        text = path.read_text(encoding="utf-8")
        if text.count(REVISION_TOKEN) != 1:
            raise ConformanceError(f"Run fixture needs one {REVISION_TOKEN} token: {path}")
        path.write_text(text.replace(REVISION_TOKEN, revision), encoding="utf-8")
    _git(root, "add", "--all")
    _commit(root, "conformance Run fixture")


def _prepare_workspace(case: dict[str, Any], manifest: dict[str, Any], root: Path) -> None:
    base_fixture = HERE / _relative_path(manifest["base_fixture"], "base_fixture")
    _copy_tree(base_fixture, root)
    if case.get("git_binding"):
        _copy_tree(RUN_ASSETS, root)
    fixture = case.get("fixture")
    if fixture is not None:
        _copy_tree(HERE / _relative_path(fixture, f"{case['id']}.fixture"), root)
    if case.get("git_binding"):
        _bind_application(root, manifest["application_path"])
        history_fixture = case.get("history_fixture")
        if history_fixture is not None:
            _copy_tree(HERE / _relative_path(history_fixture, f"{case['id']}.history_fixture"), root)
            application = _relative_path(manifest["application_path"], "application_path")
            _git(root, "add", "--", application.as_posix())
            _commit(root, "conformance current Application update")
        if _git(root, "status", "--porcelain"):
            raise ConformanceError(f"{case['id']}: fixture Git worktree is not clean")


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ConformanceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ConformanceError(f"non-standard JSON value: {value}")


def _parse_report(stdout: bytes) -> dict[str, Any]:
    try:
        text = stdout.decode("utf-8")
        report = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ConformanceError, RecursionError) as error:
        raise ConformanceError(f"stdout is not one strict JSON document: {error}") from error
    if not isinstance(report, dict):
        raise ConformanceError("JSON report must be an object")
    return report


def _check_report(report: dict[str, Any], case: dict[str, Any], root: Path, returncode: int) -> None:
    expected = case["expected"]
    command = case["command"]
    if command == "validate":
        required = {"report_version", "command", "tool", "root", "valid", "issues"}
    else:
        required = {"report_version", "command", "tool", "attempt", "surfaces", "digest", "issues"}
    if set(report) != required:
        raise ConformanceError(f"report fields must be exactly {sorted(required)}")
    if type(report["report_version"]) is not int or report["report_version"] != 1:
        raise ConformanceError("report_version must be integer 1")
    if report["command"] != command:
        raise ConformanceError("report command does not match invoked command")
    if command == "validate":
        if not isinstance(report["root"], str) or report["root"] != str(root):
            raise ConformanceError("report root does not match validate argument")
    else:
        expected_attempt = str(root / _relative_path(case["attempt"], f"{case['id']}.attempt"))
        if not isinstance(report["attempt"], str) or report["attempt"] != expected_attempt:
            raise ConformanceError("report attempt does not match hash argument")
        if report["surfaces"] != case["surfaces"] or not isinstance(report["surfaces"], list):
            raise ConformanceError("report surfaces do not match hash arguments")
    tool = report["tool"]
    if not isinstance(tool, dict) or set(tool) != {"name", "version", "version_source"}:
        raise ConformanceError("tool identity needs name, version, and version_source")
    if (
        not isinstance(tool["name"], str)
        or not tool["name"]
        or not isinstance(tool["version_source"], str)
        or not tool["version_source"]
        or (tool["version"] is not None and (not isinstance(tool["version"], str) or not tool["version"]))
    ):
        raise ConformanceError("tool name and version_source need strings; version needs string or null")
    issues = report["issues"]
    if not isinstance(issues, list):
        raise ConformanceError("issues must be an array")
    issue_codes: list[str] = []
    for issue in issues:
        if not isinstance(issue, dict) or set(issue) != {"code", "path", "message"}:
            raise ConformanceError("each issue needs exactly code, path, and message")
        if any(not isinstance(issue[field], str) or not issue[field] for field in ("code", "path", "message")):
            raise ConformanceError("issue code, path, and message must be non-empty strings")
        issue_codes.append(issue["code"])
    if sorted(issue_codes) != expected["issue_codes"]:
        raise ConformanceError(
            f"issue codes differ: expected {expected['issue_codes']}, got {sorted(issue_codes)}"
        )
    if returncode != expected["exit_code"]:
        raise ConformanceError(f"process exit {returncode}; expected {expected['exit_code']}")
    if command == "validate":
        valid = report["valid"]
        if type(valid) is not bool:
            raise ConformanceError("validate valid field must be boolean")
        if valid is not expected["valid"]:
            raise ConformanceError(f"valid={valid}; expected {expected['valid']}")
        if valid != (not issues) or returncode != (0 if valid else 1):
            raise ConformanceError("valid, issues, and process exit are inconsistent")
    else:
        digest = report["digest"]
        if digest is not None and (
            not isinstance(digest, str)
            or len(digest) != len(HASH_PREFIX) + 64
            or not digest.startswith(HASH_PREFIX)
            or any(char not in "0123456789abcdef" for char in digest[len(HASH_PREFIX):])
        ):
            raise ConformanceError("hash digest must be null or lowercase SHA-256")
        if digest != expected["digest"]:
            raise ConformanceError(f"digest {digest!r}; expected {expected['digest']!r}")
        if (digest is not None) != (not issues) or returncode != (0 if digest is not None else 1):
            raise ConformanceError("digest, issues, and process exit are inconsistent")


def _invoke(candidate: list[str], case: dict[str, Any], root: Path, timeout: float) -> dict[str, Any]:
    if case["command"] == "validate":
        arguments = ["validate", str(root), "--json"]
    else:
        attempt = root / _relative_path(case["attempt"], f"{case['id']}.attempt")
        surfaces = case["surfaces"]
        arguments = ["hash", str(attempt), *surfaces, "--json"]
    try:
        result = subprocess.run(
            [*candidate, *arguments],
            cwd=root,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise ConformanceError(f"candidate timed out after {timeout:g}s") from error
    except OSError as error:
        raise ConformanceError(f"candidate could not start: {error}") from error
    report = _parse_report(result.stdout)
    _check_report(report, case, root, result.returncode)
    return report


def run_cases(candidate: list[str], cases: list[dict[str, Any]], manifest: dict[str, Any], timeout: float) -> int:
    passed = 0
    for case in cases:
        try:
            with tempfile.TemporaryDirectory(prefix=f"impacts-conformance-{case['id']}-") as directory:
                root = Path(directory) / "workspace"
                root.mkdir()
                _prepare_workspace(case, manifest, root)
                reports = [
                    _invoke(candidate, case, root, timeout)
                    for _ in range(case.get("repeat", 1))
                ]
                if any(report != reports[0] for report in reports[1:]):
                    raise ConformanceError("fresh-process reports differ across repeats")
        except ConformanceError as error:
            print(f"FAIL {case['id']}: {error}", file=sys.stderr)
            return 1
        repeat_count = case.get("repeat", 1)
        suffix = f" ({repeat_count} fresh processes)" if repeat_count > 1 else ""
        print(f"PASS {case['id']}{suffix}")
        passed += 1
    print(f"Conformance passed: {passed}/{len(cases)} cases")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--command-json",
        default=json.dumps([sys.executable, "-m", "impacts_protocol.cli"]),
        help="candidate command as a JSON string array; no shell is used",
    )
    parser.add_argument("--case", help="run one case ID")
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout_seconds) or args.timeout_seconds <= 0:
        print("FAIL runner: timeout must be a positive finite number", file=sys.stderr)
        return 2
    try:
        candidate = json.loads(args.command_json)
    except json.JSONDecodeError as error:
        print(f"FAIL runner: --command-json is invalid JSON: {error}", file=sys.stderr)
        return 2
    if (
        not isinstance(candidate, list)
        or not candidate
        or any(not isinstance(part, str) or not part or "\x00" in part for part in candidate)
    ):
        print("FAIL runner: --command-json must be a non-empty array of non-empty strings", file=sys.stderr)
        return 2
    try:
        manifest, cases = _load_manifest()
        if args.case is not None:
            cases = [case for case in cases if case["id"] == args.case]
            if not cases:
                raise ConformanceError(f"unknown case ID: {args.case}")
    except ConformanceError as error:
        print(f"FAIL runner: {error}", file=sys.stderr)
        return 2
    return run_cases(candidate, cases, manifest, args.timeout_seconds)


if __name__ == "__main__":
    sys.exit(main())
