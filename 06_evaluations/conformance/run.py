#!/usr/bin/env python3
"""Run frozen CLI conformance cases against a command supplied as JSON argv."""

from __future__ import annotations

import argparse
import errno
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


HERE = Path(__file__).resolve().parent
MANIFEST_PATH = HERE / "cases.json"
VORGANG_ASSETS = HERE / "fixtures" / "common-run-assets"
REVISION_TOKEN = "@HAUPTPROZESS_REVISION@"
HASH_PREFIX = "sha256:"
FILESYSTEM_PROBES = {"case-sensitive", "path-component", "unicode-distinct"}


class ConformanceError(Exception):
    """A fixture, process, or candidate report failed the frozen contract."""


class UnsupportedCase(ConformanceError):
    """The host filesystem cannot represent one required fixture name."""


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


def _hex_bytes(value: Any, label: str) -> bytes:
    if (
        not isinstance(value, str)
        or len(value) % 2
        or any(char not in "0123456789abcdefABCDEF" for char in value)
    ):
        raise ConformanceError(f"{label} must be an even-length hexadecimal string")
    try:
        return bytes.fromhex(value)
    except ValueError as error:
        raise ConformanceError(f"{label} must be hexadecimal") from error


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
    _relative_path(manifest.get("hauptprozess_path"), "hauptprozess_path")
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
        if "symlink" in case:
            link = case["symlink"]
            if not isinstance(link, dict) or set(link) != {"path", "target"}:
                raise ConformanceError(f"{case_id}: symlink needs path and target")
            _relative_path(link["path"], "symlink.path")
            _relative_path(link["target"], "symlink.target")
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
        if "orphan_source_commit" in case:
            if type(case["orphan_source_commit"]) is not bool or not case.get("git_binding"):
                raise ConformanceError(f"{case_id}: orphan_source_commit needs a boolean and Git binding")
        if case.get("history_fixture") is not None:
            history_fixture = _relative_path(case["history_fixture"], f"{case_id}.history_fixture")
            if not (HERE / history_fixture).is_dir():
                raise ConformanceError(f"{case_id}: history fixture not found")
            if case.get("git_binding") is not True:
                raise ConformanceError(f"{case_id}: history fixture needs Git binding")
        invalid_utf8_file = case.get("invalid_utf8_file")
        if invalid_utf8_file is not None:
            if not isinstance(invalid_utf8_file, dict) or set(invalid_utf8_file) != {
                "parent", "name_hex", "content_hex"
            }:
                raise ConformanceError(f"{case_id}: invalid_utf8_file needs parent, name_hex, and content_hex")
            _relative_path(invalid_utf8_file["parent"], f"{case_id}.invalid_utf8_file.parent")
            name = _hex_bytes(invalid_utf8_file["name_hex"], f"{case_id}.invalid_utf8_file.name_hex")
            _hex_bytes(invalid_utf8_file["content_hex"], f"{case_id}.invalid_utf8_file.content_hex")
            if not name or name in (b".", b"..") or b"/" in name or b"\x00" in name:
                raise ConformanceError(f"{case_id}: invalid UTF-8 filename must be one basename")
            try:
                name.decode("utf-8")
            except UnicodeDecodeError:
                pass
            else:
                raise ConformanceError(f"{case_id}: invalid UTF-8 filename bytes decode as UTF-8")
        filesystem_probe = case.get("filesystem_probe")
        if filesystem_probe is not None:
            if not isinstance(filesystem_probe, dict):
                raise ConformanceError(f"{case_id}: filesystem_probe must be an object")
            kind = filesystem_probe.get("kind")
            if not isinstance(kind, str) or kind not in FILESYSTEM_PROBES:
                raise ConformanceError(f"{case_id}: unknown filesystem_probe kind")
            if kind == "path-component":
                length = filesystem_probe.get("length")
                if type(length) is not int or length < 256:
                    raise ConformanceError(
                        f"{case_id}: path-component probe length must be integer at least 256"
                    )
                if set(filesystem_probe) != {"kind", "length"}:
                    raise ConformanceError(f"{case_id}: malformed path-component probe")
            elif set(filesystem_probe) != {"kind"}:
                raise ConformanceError(f"{case_id}: malformed filesystem_probe")
        bad_folders = case.get("bad_folders", [])
        if (
            not isinstance(bad_folders, list)
            or any(
                not isinstance(name, str)
                or not name
                or name in (".", "..")
                or "/" in name
                or "\\" in name
                or "\x00" in name
                for name in bad_folders
            )
            or len(set(bad_folders)) != len(bad_folders)
        ):
            raise ConformanceError(f"{case_id}: bad_folders must be unique path basenames")
        bad_folder_length = case.get("bad_folder_length")
        if bad_folder_length is not None and (
            type(bad_folder_length) is not int or bad_folder_length < 256
        ):
            raise ConformanceError(f"{case_id}: bad_folder_length must be integer at least 256")
        if bad_folder_length is not None and bad_folders:
            raise ConformanceError(f"{case_id}: choose bad_folders or bad_folder_length")
        expected_issue_paths = case.get("expected_issue_paths")
        if expected_issue_paths is not None and (
            command != "validate"
            or not isinstance(expected_issue_paths, list)
            or any(not isinstance(path, str) or not path for path in expected_issue_paths)
        ):
            raise ConformanceError(f"{case_id}: expected_issue_paths must be non-empty strings")
        expected_messages = case.get("expected_issue_messages")
        if expected_messages is not None and (
            command != "validate"
            or not isinstance(expected_messages, list)
            or any(not isinstance(message, str) or not message for message in expected_messages)
        ):
            raise ConformanceError(f"{case_id}: expected_issue_messages must be non-empty strings")
        repeat = case.get("repeat", 1)
        if type(repeat) is not int or repeat < 1:
            raise ConformanceError(f"{case_id}: repeat must be positive integer")
        _validate_expected(case)
    return manifest, cases


def _validate_expected(case: dict[str, Any]) -> None:
    case_id = case["id"]
    expected = case.get("expected")
    if not isinstance(expected, dict):
        raise ConformanceError(f"{case_id}: expected result must be an object")
    exit_code = expected.get("exit_code")
    if type(exit_code) is not int or exit_code not in (0, 1):
        raise ConformanceError(f"{case_id}: expected exit_code must be 0 or 1")
    codes = expected.get("issue_codes")
    if not isinstance(codes, list) or any(not isinstance(code, str) or not code for code in codes):
        raise ConformanceError(f"{case_id}: issue_codes must be strings")
    if codes != sorted(codes):
        raise ConformanceError(f"{case_id}: issue_codes must be sorted")
    if case["command"] == "validate":
        if set(expected) - {"external_references_not_verified"} != {"exit_code", "valid", "issue_codes", "not_judged"}:
            raise ConformanceError(f"{case_id}: malformed validate expectation")
        count = expected.get("external_references_not_verified", 0)
        if type(count) is not int or count < 0:
            raise ConformanceError(f"{case_id}: external-store count must be a nonnegative integer")
        skipped = expected["not_judged"]
        if not isinstance(skipped, list) or any(
            not isinstance(item, dict) or set(item) not in ({"path", "protocol"}, {"path", "protocol", "reason"})
            or ("reason" in item and (not isinstance(item["reason"], str) or not item["reason"]))
            or not isinstance(item["path"], str) or not item["path"]
            or (item["protocol"] is not None and not isinstance(item["protocol"], str))
            for item in skipped
        ):
            raise ConformanceError(f"{case_id}: malformed not_judged expectation")
        valid = expected["valid"]
        if type(valid) is not bool or exit_code != (0 if valid else 1):
            raise ConformanceError(f"{case_id}: expected validity and exit code disagree")
        if valid != (not codes):
            raise ConformanceError(f"{case_id}: expected validity and issue codes disagree")
    else:
        if set(expected) != {"exit_code", "references", "issue_codes"}:
            raise ConformanceError(f"{case_id}: malformed hash expectation")
        references = expected["references"]
        _validate_references(references)
        if (references is not None) != (exit_code == 0) or (references is not None) != (not codes):
            raise ConformanceError(f"{case_id}: references, issues, and exit code disagree")


def _validate_references(references):
    if references is None:
        return
    if not isinstance(references, list):
        raise ConformanceError("references must be null or an array")
    for reference in references:
        if not isinstance(reference, dict) or set(reference) != {"pfad", "sha256"}:
            raise ConformanceError("reference needs pfad and sha256")
        _relative_path(reference["pfad"], "reference.pfad")
        digest = reference["sha256"]
        if not isinstance(digest, str) or len(digest) != 71 or not digest.startswith(HASH_PREFIX) or any(c not in "0123456789abcdef" for c in digest[7:]):
            raise ConformanceError("reference digest must be lowercase SHA-256")


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


def _create_invalid_utf8_file(root: Path, specification: dict[str, Any]) -> None:
    if os.name != "posix":
        raise UnsupportedCase("host is not POSIX; arbitrary filename bytes are unavailable")
    parent = root / _relative_path(specification["parent"], "invalid_utf8_file.parent")
    try:
        parent.mkdir(parents=True, exist_ok=True)
        if parent.is_symlink() or not parent.is_dir():
            raise ConformanceError(f"invalid UTF-8 fixture parent is not a directory: {parent}")
        parent_bytes = os.fsencode(parent)
    except ConformanceError:
        raise
    except (OSError, UnicodeError) as error:
        raise ConformanceError(f"cannot prepare invalid UTF-8 fixture directory: {error}") from error

    name = _hex_bytes(specification["name_hex"], "invalid_utf8_file.name_hex")
    content = _hex_bytes(specification["content_hex"], "invalid_utf8_file.content_hex")
    path = parent_bytes + os.fsencode(os.sep) + name
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as error:
        if error.errno in {errno.EINVAL, errno.EILSEQ}:
            raise UnsupportedCase(
                f"filesystem rejects non-UTF-8 filename ({error.strerror or error.errno})"
            ) from error
        raise ConformanceError(f"cannot create invalid UTF-8 fixture file: {error}") from error

    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(content)
    except (OSError, ValueError) as error:
        raise ConformanceError(f"cannot write invalid UTF-8 fixture file: {error}") from error


def _open_probe_file(
    path: Path, capability: str, unsupported_errnos: set[int]
) -> None:
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as error:
        if error.errno in unsupported_errnos:
            raise UnsupportedCase(
                f"filesystem lacks {capability} capability ({error.strerror or error.errno})"
            ) from error
        raise ConformanceError(f"cannot probe {capability} capability: {error}") from error
    try:
        os.close(descriptor)
    except OSError as error:
        raise ConformanceError(f"cannot finish {capability} capability probe: {error}") from error


def _path_component_probe_unsupported_errnos(platform: str) -> set[int]:
    unsupported = {errno.ENAMETOOLONG}
    if platform == "win32":
        # Windows reports its over-limit component response as EINVAL.
        unsupported.add(errno.EINVAL)
    return unsupported


def _probe_filesystem_capability(root: Path, specification: dict[str, Any]) -> None:
    """Verify only the host path property a fixture depends on."""
    kind = specification["kind"]
    try:
        with tempfile.TemporaryDirectory(prefix="filesystem-probe-", dir=root) as directory:
            probe_root = Path(directory)
            if kind == "case-sensitive":
                _open_probe_file(probe_root / "CaseProbe", "case-sensitive paths", set())
                _open_probe_file(
                    probe_root / "caseprobe", "case-sensitive paths", {errno.EEXIST}
                )
            elif kind == "path-component":
                length = specification["length"]
                _open_probe_file(
                    probe_root / ("p" * length),
                    f"{length}-byte path components",
                    _path_component_probe_unsupported_errnos(sys.platform),
                )
            elif kind == "unicode-distinct":
                composed = "caf\u00e9"
                decomposed = "cafe\u0301"
                _open_probe_file(
                    probe_root / composed,
                    "distinct Unicode spellings",
                    {errno.EINVAL, errno.EILSEQ},
                )
                _open_probe_file(
                    probe_root / decomposed,
                    "distinct Unicode spellings",
                    {errno.EEXIST, errno.EINVAL, errno.EILSEQ},
                )
            else:
                raise ConformanceError(f"unknown filesystem capability probe: {kind}")
    except UnsupportedCase:
        raise
    except ConformanceError:
        raise
    except OSError as error:
        raise ConformanceError(f"cannot prepare {kind} filesystem probe: {error}") from error


def _add_bad_folders(root: Path, manifest: dict[str, Any], case: dict[str, Any]) -> None:
    names = list(case.get("bad_folders", []))
    length = case.get("bad_folder_length")
    if length is not None:
        names.append("Bad_" + "x" * (length - len("Bad_")))
    if not names:
        return
    hauptprozess = root / _relative_path(manifest["hauptprozess_path"], "hauptprozess_path")
    context = (
        "---\n"
        "type: teilprozess\n"
        "id: teilprozess:filesystem-probe-{index}\n"
        "ergebnis: Folder spelling is preserved for structural validation\n"
        "---\n\n"
        "# Synthetic folder probe\n"
    )
    workstep_context = (
        "---\n"
        "type: arbeitsschritt\n"
        "id: arbeitsschritt:filesystem-probe-{index}\n"
        "eingaben:\n"
        "  - input/source.md\n"
        "ausgaben:\n"
        "  - output/result.md\n"
        "pruefung: Synthetic fixture file is listed\n"
        "routen:\n"
        "  fertig: end:fertig\n"
        "---\n\n"
        "# Synthetic folder workstep\n"
    )
    for index, name in enumerate(names, start=1):
        folder = hauptprozess / name
        try:
            folder.mkdir()
            (folder / "CONTEXT.md").write_text(context.format(index=index), encoding="utf-8")
            step = folder / f"filesystem-probe-{index}"
            step.mkdir()
            (step / "CONTEXT.md").write_text(
                workstep_context.format(index=index), encoding="utf-8"
            )
            actual_names = os.listdir(hauptprozess)
        except OSError as error:
            raise ConformanceError(f"cannot create bad-folder fixture {name!r}: {error}") from error
        if name not in actual_names:
            raise UnsupportedCase(
                f"filesystem cannot preserve requested folder spelling for bad-folder probe {index}"
            )


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
        "-c", "maintenance.auto=false",
        "commit", "--quiet", "-m", message,
    )


def _bind_hauptprozess(root: Path, hauptprozess_path: str, *, orphan_source_commit: bool = False) -> None:
    hauptprozess = _relative_path(hauptprozess_path, "hauptprozess_path")
    _git(root, "init", "--quiet")
    _git(root, "add", "--", hauptprozess.as_posix())
    for capture in sorted((root / "vorgaenge").glob("*/_quellen")):
        _git(root, "add", "--", capture.relative_to(root).as_posix())
    for home in ("records", "grundlagen"):
        if (root / home).is_dir():
            _git(root, "add", "--", home)
    _commit(root, "conformance Hauptprozess fixture")
    source_commit = _git(root, "rev-parse", "HEAD")
    orphan_commit = ""
    if orphan_source_commit:
        tree = _git(root, "rev-parse", "HEAD^{tree}")
        orphan_commit = _git(root, "-c", "user.name=Conformance Fixture",
                             "-c", "user.email=fixture@example.invalid",
                             "commit-tree", tree, "-m", "synthetic unreachable source")
    revision = _git(root, "rev-parse", f"HEAD:{hauptprozess.as_posix()}")
    vorgang_contexts = sorted((root / "vorgaenge").glob("*/CONTEXT.md"))
    if not vorgang_contexts:
        raise ConformanceError("Git-bound fixture has no Vorgang CONTEXT.md")
    for path in vorgang_contexts:
        text = path.read_text(encoding="utf-8")
        if text.count(REVISION_TOKEN) != 1:
            raise ConformanceError(f"Vorgang fixture needs one {REVISION_TOKEN} token: {path}")
        path.write_text(text.replace(REVISION_TOKEN, revision).replace("@SOURCE_COMMIT@", source_commit).replace("@ORPHAN_COMMIT@", orphan_commit), encoding="utf-8")
    _git(root, "add", "--all")
    _commit(root, "conformance Vorgang fixture")


def _prepare_workspace(case: dict[str, Any], manifest: dict[str, Any], root: Path) -> None:
    filesystem_probe = case.get("filesystem_probe")
    if filesystem_probe is not None:
        _probe_filesystem_capability(root, filesystem_probe)
    base_fixture = HERE / _relative_path(manifest["base_fixture"], "base_fixture")
    _copy_tree(base_fixture, root)
    if case.get("git_binding"):
        _copy_tree(VORGANG_ASSETS, root)
    fixture = case.get("fixture")
    if fixture is not None:
        _copy_tree(HERE / _relative_path(fixture, f"{case['id']}.fixture"), root)
    if "symlink" in case:
        link = case["symlink"]
        path = root / _relative_path(link["path"], "symlink.path")
        target = root / _relative_path(link["target"], "symlink.target")
        if not target.is_dir() or path.exists() or path.is_symlink():
            raise ConformanceError("symlink fixture needs a new path and existing target directory")
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.symlink_to(os.path.relpath(target, path.parent), target_is_directory=True)
        except OSError as error:
            if error.errno in {errno.ENOSYS, errno.EOPNOTSUPP} or getattr(error, "winerror", None) == 1314:
                raise UnsupportedCase("host cannot create fixture symlinks") from error
            raise ConformanceError(f"cannot create fixture symlink: {error}") from error
    _add_bad_folders(root, manifest, case)
    invalid_utf8_file = case.get("invalid_utf8_file")
    if invalid_utf8_file is not None:
        _create_invalid_utf8_file(root, invalid_utf8_file)
    if case.get("git_binding"):
        _bind_hauptprozess(root, manifest["hauptprozess_path"], orphan_source_commit=case.get("orphan_source_commit", False))
        history_fixture = case.get("history_fixture")
        if history_fixture is not None:
            _copy_tree(HERE / _relative_path(history_fixture, f"{case['id']}.history_fixture"), root)
            hauptprozess = _relative_path(manifest["hauptprozess_path"], "hauptprozess_path")
            _git(root, "add", "--", hauptprozess.as_posix())
            _commit(root, "conformance current Hauptprozess update")
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
        required = {"report_version", "command", "tool", "root", "valid", "issues", "not_judged", "external_references_not_verified", "release", "pin", "judged", "not_judged_counts", "superseded", "external_references"}
    else:
        required = {"report_version", "command", "tool", "attempt", "surfaces", "references", "issues"}
    if set(report) != required:
        raise ConformanceError(f"report fields must be exactly {sorted(required)}")
    if type(report["report_version"]) is not int or report["report_version"] != 3:
        raise ConformanceError("report_version must be integer 3")
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
        if not isinstance(issue, dict) or set(issue) != {"code", "path", "message", "rule"}:
            raise ConformanceError("each issue needs exactly code, path, message, and rule")
        if any(not isinstance(issue[field], str) or not issue[field] for field in ("code", "path", "message")):
            raise ConformanceError("issue code, path, and message must be non-empty strings")
        if not isinstance(issue["rule"], str) or not issue["rule"].split("#")[0].endswith(".md") or "#" not in issue["rule"] or not issue["rule"].split("#", 1)[1]:
            raise ConformanceError("issue rule must be a non-empty Markdown anchor")
        issue_codes.append(issue["code"])
    expected_paths = case.get("expected_issue_paths")
    if expected_paths is not None:
        actual_paths = sorted(issue["path"] for issue in issues)
        if actual_paths != sorted(expected_paths):
            raise ConformanceError(
                f"issue paths differ: expected {sorted(expected_paths)}, got {actual_paths}"
            )
    expected_messages = case.get("expected_issue_messages")
    if expected_messages is not None:
        actual_messages = sorted(issue["message"] for issue in issues)
        if len(actual_messages) != len(expected_messages) or any(
            expected not in actual
            for expected, actual in zip(sorted(expected_messages), actual_messages)
        ):
            raise ConformanceError("issue messages do not contain the frozen explanations")
    if sorted(issue_codes) != expected["issue_codes"]:
        raise ConformanceError(
            f"issue codes differ: expected {expected['issue_codes']}, got {sorted(issue_codes)}"
        )
    if returncode != expected["exit_code"]:
        raise ConformanceError(f"process exit {returncode}; expected {expected['exit_code']}")
    if command == "validate":
        if not isinstance(report["release"], str) or not report["release"]:
            raise ConformanceError("release must be a non-empty string")
        if report["pin"] is not None and not isinstance(report["pin"], str):
            raise ConformanceError("pin must be a string or null")
        judged = report["judged"]
        if (not isinstance(judged, dict) or set(judged) != {"hauptprozess", "teilprozess", "arbeitsschritt", "vorgang", "versuch"}
                or any(type(value) is not int or value < 0 for value in judged.values())):
            raise ConformanceError("judged must contain nonnegative counts for all five kinds")
        if not isinstance(report["superseded"], list) or any(not isinstance(path, str) or not path for path in report["superseded"]):
            raise ConformanceError("superseded must list Vorgang paths")
        external = report["external_references"]
        if not isinstance(external, list) or any(
            not isinstance(item, dict) or set(item) != {"vorgang", "pointer"}
            or not isinstance(item["vorgang"], str) or not item["vorgang"]
            or not isinstance(item["pointer"], str)
            or not re.fullmatch(r"/laufpfad/(0|[1-9][0-9]*)/(gelesen|geschrieben)/(0|[1-9][0-9]*)", item["pointer"])
            for item in external
        ):
            raise ConformanceError("external_references must list Vorgang paths and external pointers")
        count = report["external_references_not_verified"]
        if len(external) != count:
            raise ConformanceError("external-store list and count disagree")
        if type(count) is not int or count < 0 or count != expected.get("external_references_not_verified", 0):
            raise ConformanceError("external-store count does not match expected count")
        if report["not_judged"] != expected["not_judged"]:
            raise ConformanceError("not_judged does not match expected records")
        counts = report["not_judged_counts"]
        expected_counts = {
            "vorgang": sum(item["path"].startswith("vorgaenge/") and not item.get("reason") for item in report["not_judged"]),
            "definition_tree": sum(item.get("reason") == "definition tree outside hauptprozesse/, not bindable" for item in report["not_judged"]),
        }
        if (not isinstance(counts, dict) or counts != expected_counts
                or any(type(value) is not int for value in counts.values())):
            raise ConformanceError("not_judged_counts must match the skipped Vorgänge and definition trees")
        valid = report["valid"]
        if type(valid) is not bool:
            raise ConformanceError("validate valid field must be boolean")
        if valid is not expected["valid"]:
            raise ConformanceError(f"valid={valid}; expected {expected['valid']}")
        if valid != (not issues) or returncode != (0 if valid else 1):
            raise ConformanceError("valid, issues, and process exit are inconsistent")
    else:
        references = report["references"]
        _validate_references(references)
        if references != expected["references"]:
            raise ConformanceError(f"references {references!r}; expected {expected['references']!r}")
        if (references is not None) != (not issues) or returncode != (0 if references is not None else 1):
            raise ConformanceError("references, issues, and process exit are inconsistent")


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
    applicable = 0
    unsupported = 0
    failed = 0
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
        except UnsupportedCase as error:
            print(f"UNSUPPORTED {case['id']}: {error}")
            unsupported += 1
            continue
        except ConformanceError as error:
            print(f"FAIL {case['id']}: {error}", file=sys.stderr)
            applicable += 1
            failed += 1
            continue
        repeat_count = case.get("repeat", 1)
        suffix = f" ({repeat_count} fresh processes)" if repeat_count > 1 else ""
        print(f"PASS {case['id']}{suffix}")
        passed += 1
        applicable += 1
    print(
        "Conformance summary: "
        f"applicable={applicable} passed={passed} unsupported={unsupported} "
        f"failed={failed} total={len(cases)}"
    )
    if failed:
        return 1
    if applicable == 0:
        return 3
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
