import errno
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "06_evaluations" / "conformance" / "run.py"


def _runner_module():
    name = "conformance_runner_tests"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _candidate(tmp_path: Path, source: str) -> Path:
    script = tmp_path / "candidate with spaces.py"
    script.write_text(source, encoding="utf-8")
    return script


def _run(tmp_path: Path, source: str, *, case: str | None = None, timeout: float = 10.0):
    script = _candidate(tmp_path, source)
    command = [
        sys.executable,
        str(RUNNER),
        "--command-json",
        json.dumps([sys.executable, str(script)]),
        "--timeout-seconds",
        str(timeout),
    ]
    if case is not None:
        command.extend(["--case", case])
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=20)


def _emit_report(
    *,
    valid: bool,
    exit_code: int = 0,
    issue_codes: tuple[str, ...] = (),
    mutation: str = "",
) -> str:
    issues = [
        {"code": code, "path": "CONTEXT.md", "message": "synthetic candidate diagnostic"}
        for code in issue_codes
    ]
    return f"""import json
import sys
command = sys.argv[1]
report = {{
    "report_version": 1,
    "command": command,
    "tool": {{"name": "fake-candidate", "version": None, "version_source": "test stub"}},
    "issues": {issues!r},
}}
if command == "validate":
    report["root"] = sys.argv[2]
    report["valid"] = {valid!r}
else:
    report["attempt"] = sys.argv[2]
    report["surfaces"] = sys.argv[3:-1]
    report["digest"] = "sha256:e8fdf8b5a31291deb1c3fa4d982f85da0605a4e3dd5a2f340e2ad2ebf182b965"
payload = json.dumps(report, separators=(",", ":"))
{mutation}
sys.stdout.write(payload)
sys.exit({exit_code})
"""


def _emit_raw(stdout: str, exit_code: int = 0, delay: float = 0) -> str:
    return f"""import sys, time
time.sleep({delay!r})
sys.stdout.write({stdout!r})
sys.exit({exit_code})
"""


def test_runner_accepts_valid_reports_and_nullable_tool_version(tmp_path):
    result = _run(tmp_path, _emit_report(valid=True), case="application-valid")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS application-valid" in result.stdout


def test_runner_accepts_fixed_hash_vector_report(tmp_path):
    result = _run(tmp_path, _emit_report(valid=True), case="hash-fixed-vector")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS hash-fixed-vector" in result.stdout


def test_repeat_case_runs_candidate_in_fresh_processes(tmp_path):
    source = """import json
from pathlib import Path
import sys
counter = Path(__file__).with_suffix(".count")
count = int(counter.read_text()) if counter.exists() else 0
counter.write_text(str(count + 1))
report = {
    "report_version": 1,
    "command": sys.argv[1],
    "tool": {"name": "fake-candidate", "version": "test", "version_source": "test stub"},
    "root": sys.argv[2],
    "valid": True,
    "issues": [],
}
print(json.dumps(report, separators=(",", ":")))
"""
    result = _run(tmp_path, source, case="run-waiting")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "2 fresh processes" in result.stdout
    assert (tmp_path / "candidate with spaces.count").read_text(encoding="utf-8") == "2"


def test_always_valid_candidate_fails_invalid_case(tmp_path):
    result = _run(tmp_path, _emit_report(valid=True))

    assert result.returncode == 1
    assert "FAIL application-unresolved-route" in result.stderr


def test_always_invalid_candidate_fails_valid_case(tmp_path):
    result = _run(
        tmp_path,
        _emit_report(valid=False, exit_code=1, issue_codes=("fake.invalid",)),
    )

    assert result.returncode == 1
    assert "FAIL application-valid" in result.stderr


def test_runner_requires_exact_issue_codes(tmp_path):
    result = _run(
        tmp_path,
        _emit_report(valid=False, exit_code=1, issue_codes=("fake.invalid",)),
        case="application-unresolved-route",
    )

    assert result.returncode == 1
    assert "issue codes differ" in result.stderr


@pytest.mark.parametrize(
    ("mutation", "valid", "issue_codes", "diagnostic"),
    [
        ("payload = payload.replace('\"report_version\":1', '\"report_version\":1,\"report_version\":1', 1)", True, (), "duplicate JSON key"),
        ("payload = payload.replace('\"report_version\":1', '\"report_version\":NaN', 1)", True, (), "non-standard JSON value"),
        ('report["report_version"] = True\npayload = json.dumps(report, separators=(",", ":"))', True, (), "report_version must be integer 1"),
        ('report["issues"] = {}\npayload = json.dumps(report, separators=(",", ":"))', True, (), "issues must be an array"),
        ('report["issues"][0]["code"] = 1\npayload = json.dumps(report, separators=(",", ":"))', False, ("reference.unresolved",), "issue code, path, and message must be non-empty strings"),
        ('report["issues"][0]["path"] = 1\npayload = json.dumps(report, separators=(",", ":"))', False, ("reference.unresolved",), "issue code, path, and message must be non-empty strings"),
        ('report["issues"][0]["message"] = 1\npayload = json.dumps(report, separators=(",", ":"))', False, ("reference.unresolved",), "issue code, path, and message must be non-empty strings"),
    ],
)
def test_runner_fails_closed_on_malformed_reports(tmp_path, mutation, valid, issue_codes, diagnostic):
    case = "application-valid" if valid else "application-unresolved-route"
    source = _emit_report(
        valid=valid,
        exit_code=0 if valid else 1,
        issue_codes=issue_codes,
        mutation=mutation,
    )
    result = _run(tmp_path, source, case=case)

    assert result.returncode == 1
    assert f"FAIL {case}" in result.stderr
    assert diagnostic in result.stderr


def test_runner_fails_closed_on_inconsistent_exit_code(tmp_path):
    result = _run(tmp_path, _emit_report(valid=True, exit_code=1), case="application-valid")

    assert result.returncode == 1
    assert "process exit 1; expected 0" in result.stderr


def test_runner_fails_closed_on_timeout(tmp_path):
    result = _run(tmp_path, _emit_raw("{}", delay=2), case="application-valid", timeout=0.05)

    assert result.returncode == 1
    assert "timed out" in result.stderr


def test_runner_rejects_non_array_command_json(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--command-json",
            json.dumps({"executable": sys.executable}),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 2
    assert "non-empty array" in result.stderr


@pytest.mark.parametrize(
    "raw",
    [
        '{"corpus_version":1,"corpus_version":1}',
        '{"corpus_version":NaN}',
    ],
)
def test_manifest_loader_rejects_duplicate_keys_and_non_finite_values(tmp_path, raw):
    namespace = _runner_module()
    manifest_path = tmp_path / "cases.json"
    manifest_path.write_text(raw, encoding="utf-8")

    with pytest.raises(namespace.ConformanceError):
        namespace._load_manifest(manifest_path)


@pytest.mark.parametrize(
    ("error_number", "is_unsupported"),
    [
        (errno.EINVAL, True),
        (errno.EILSEQ, True),
        (errno.EACCES, False),
        (errno.ENOSPC, False),
    ],
)
def test_invalid_filename_setup_does_not_swallow_real_setup_errors(
    tmp_path, monkeypatch, error_number, is_unsupported
):
    runner = _runner_module()
    root = tmp_path / "workspace"
    root.mkdir()
    specification = {
        "parent": "attempt/input",
        "name_hex": "ff2e747874",
        "content_hex": "666978747572650a",
    }

    def fail_open(*_args, **_kwargs):
        raise OSError(error_number, "simulated filesystem result")

    monkeypatch.setattr(runner.os, "open", fail_open)
    if is_unsupported:
        with pytest.raises(runner.UnsupportedCase):
            runner._create_invalid_utf8_file(root, specification)
    else:
        with pytest.raises(runner.ConformanceError) as raised:
            runner._create_invalid_utf8_file(root, specification)
        assert not isinstance(raised.value, runner.UnsupportedCase)


def test_all_unsupported_selection_is_not_reported_as_pass(monkeypatch, capsys):
    runner = _runner_module()
    manifest, cases = runner._load_manifest()

    def unsupported(*_args, **_kwargs):
        raise runner.UnsupportedCase("synthetic filesystem capability limit")

    monkeypatch.setattr(runner, "_prepare_workspace", unsupported)
    exit_code = runner.run_cases(["unused"], cases[:1], manifest, timeout=1.0)

    assert exit_code == 3
    output = capsys.readouterr().out
    assert "UNSUPPORTED application-valid:" in output
    assert "applicable=0 passed=0 unsupported=1 failed=0 total=1" in output


def test_reference_cli_passes_full_frozen_corpus():
    env = os.environ.copy()
    source_path = str(ROOT / "src")
    env["PYTHONPATH"] = os.pathsep.join(
        part for part in (source_path, env.get("PYTHONPATH", "")) if part
    )
    result = subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    summary = next(
        line for line in result.stdout.splitlines() if line.startswith("Conformance summary: ")
    )
    match = re.fullmatch(
        r"Conformance summary: applicable=(\d+) passed=(\d+) unsupported=(\d+) failed=(\d+) total=(\d+)",
        summary,
    )
    assert match is not None
    applicable, passed, unsupported, failed, total = map(int, match.groups())
    assert passed == applicable
    assert failed == 0
    assert applicable + unsupported == total == 19
    assert 15 <= applicable
    assert unsupported <= 2
