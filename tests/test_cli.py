from contextlib import redirect_stderr, redirect_stdout
from importlib.metadata import PackageNotFoundError
from io import StringIO
from pathlib import Path
import json
import os
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol.cli import main


def _run_cli(cwd, *arguments):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "impacts_protocol.cli", *(str(arg) for arg in arguments)],
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _json_stdout(result):
    assert result.stdout.endswith("\n")
    assert result.stdout.count("\n") == 1
    return json.loads(result.stdout)


def _assert_tool_metadata(tool):
    assert set(tool) == {"name", "version", "version_source"}
    assert isinstance(tool["name"], str) and tool["name"]
    assert tool["version"] is None or isinstance(tool["version"], str)
    assert isinstance(tool["version_source"], str) and tool["version_source"]


def test_benchmark_yaml_fixtures_validate_and_select_expected_loader(tmp_path):
    from impacts_protocol import validate
    from impacts_protocol import io
    from tests.benchmark_cli import _yaml_fixture

    original_load = io.yaml.load
    for syntax in ("plain", "sensitive"):
        root, path = _yaml_fixture(tmp_path, syntax)
        selected = []

        def record_loader(source, *, Loader):
            selected.append(Loader)
            return original_load(source, Loader=Loader)

        with patch.object(io.yaml, "load", side_effect=record_loader):
            metadata = io.load_frontmatter(path)
        assert len(metadata["leistung"]["abnahme"]) == 2000
        assert validate(root).valid
        if hasattr(io, "_PythonStrictLoader"):
            expected = (io._StrictLoader if syntax == "plain" and io._C_SAFE_LOADER
                        else io._PythonStrictLoader)
            assert selected == [expected]


class CliTests(unittest.TestCase):
    def test_version_uses_installed_distribution_metadata(self):
        class Distribution:
            metadata = {"Name": "metadata-package"}
            version = "8.7.6"

        output = StringIO()
        with patch("importlib.metadata.distribution", return_value=Distribution()):
            with redirect_stdout(output), self.assertRaises(SystemExit) as raised:
                main(["--version"])

        self.assertEqual(0, raised.exception.code)
        self.assertEqual(
            "metadata-package 8.7.6 (installed distribution metadata)\n",
            output.getvalue(),
        )

    def test_version_marks_source_pyproject_fallback(self):
        with TemporaryDirectory() as directory:
            source_root = Path(directory)
            source_cli = source_root / "src" / "impacts_protocol" / "cli.py"
            source_cli.parent.mkdir(parents=True)
            (source_root / "pyproject.toml").write_text(
                '[project]\nname = "source-package"\nversion = "7.6.5"\n',
                encoding="utf-8",
            )
            output = StringIO()
            with (
                patch("impacts_protocol.cli.__file__", str(source_cli)),
                patch(
                    "importlib.metadata.distribution",
                    side_effect=PackageNotFoundError,
                ),
                redirect_stdout(output),
                self.assertRaises(SystemExit) as raised,
            ):
                main(["--version"])

        self.assertEqual(0, raised.exception.code)
        self.assertEqual(
            "source-package 7.6.5 (source pyproject.toml; source revision unknown)\n",
            output.getvalue(),
        )

    def test_validate_verbose_reports_package_identity_and_default_stays_quiet(self):
        class Distribution:
            metadata = {"Name": "metadata-package"}
            version = "8.7.6"

        with TemporaryDirectory() as directory:
            target = Path(directory) / "workspace"
            init_workspace_output = StringIO()
            with redirect_stdout(init_workspace_output):
                self.assertEqual(0, main(["init", str(target)]))

            default_stdout = StringIO()
            default_stderr = StringIO()
            verbose_stdout = StringIO()
            verbose_stderr = StringIO()
            with patch(
                "importlib.metadata.distribution",
                return_value=Distribution(),
            ):
                with redirect_stdout(default_stdout), redirect_stderr(default_stderr):
                    self.assertEqual(0, main(["validate", str(target)]))
                with redirect_stdout(verbose_stdout), redirect_stderr(verbose_stderr):
                    self.assertEqual(0, main(["validate", str(target), "--verbose"]))

        self.assertEqual("", default_stdout.getvalue())
        self.assertEqual("", default_stderr.getvalue())
        self.assertEqual("", verbose_stdout.getvalue())
        self.assertEqual(
            "Package metadata identity: metadata-package 8.7.6 (installed distribution metadata)\n",
            verbose_stderr.getvalue(),
        )

    def test_regular_commands_skip_distribution_metadata_lookup(self):
        output = StringIO()
        with patch("importlib.metadata.distribution", side_effect=AssertionError("unexpected lookup")):
            with redirect_stdout(output):
                self.assertEqual(0, main(["template", "arbeitsschritt"]))

        self.assertNotEqual("", output.getvalue())

    def test_non_validation_commands_leave_validator_unloaded(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            attempt = base / "attempt"
            attempt.mkdir()
            (attempt / "input.txt").write_text("synthetic", encoding="utf-8")
            cases = [
                ["--help"],
                ["--version"],
                ["init", str(base / "new")],
                ["template", "arbeitsschritt"],
                ["hash", str(attempt), "input.txt"],
                ["not-a-command"],
            ]
            for arguments in cases:
                with self.subTest(arguments=arguments):
                    code = (
                        "import json, sys; from impacts_protocol.cli import main; "
                        f"args = {arguments!r}; "
                        "\ntry:\n result = main(args)\nexcept SystemExit as error:\n result = error.code\n"
                        "print('MODULES=' + json.dumps(sorted(name for name in sys.modules "
                        "if name == 'impacts_protocol.validator' or "
                        "name == 'yaml' or "
                        "name.startswith(('yaml.', 'jsonschema', 'referencing')))))\n"
                        "sys.exit(result)"
                    )
                    result = subprocess.run(
                        [sys.executable, "-c", code], cwd=base, env=environment,
                        capture_output=True, text=True,
                    )
                    self.assertEqual(2 if arguments[0] == "not-a-command" else 0,
                                     result.returncode, result.stderr)
                    self.assertIn("MODULES=[]", result.stdout)

    def test_validation_command_loads_yaml(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "workspace"
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            code = (
                "import json, sys; from impacts_protocol.cli import main; "
                "result = main(['validate', sys.argv[1]]); "
                "print('MODULES=' + json.dumps(sorted(name for name in sys.modules "
                "if name in ('impacts_protocol.validator', 'yaml')))); "
                "sys.exit(result)"
            )
            self.assertEqual(0, main(["init", str(target)]))
            result = subprocess.run(
                [sys.executable, "-c", code, str(target)], cwd=base,
                env=environment, capture_output=True, text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn('MODULES=["impacts_protocol.validator", "yaml"]', result.stdout)

    def test_init_and_validate_generated_workspace(self):
        with TemporaryDirectory() as directory:
            target = Path(directory) / "demo"

            self.assertEqual(
                0, main(["init", str(target)])
            )
            self.assertEqual(0, main(["validate", str(target)]))

    def test_validate_accepts_utf8_bom_before_frontmatter(self):
        with TemporaryDirectory() as directory:
            target = Path(directory) / "demo"
            self.assertEqual(0, main(["init", str(target)]))
            router = target / "CONTEXT.md"
            router.write_bytes(b"\xef\xbb\xbf" + router.read_bytes())

            self.assertEqual(0, main(["validate", str(target)]))

    def test_init_rejects_existing_target_and_preserves_contents(self):
        with TemporaryDirectory() as directory:
            target = Path(directory) / "demo"
            target.mkdir()
            marker = target / "bestehend.txt"
            marker.write_text("bleibt erhalten", encoding="utf-8")

            error_output = StringIO()
            with redirect_stderr(error_output):
                exit_code = main(["init", str(target)])

            self.assertNotEqual(0, exit_code)
            self.assertIn("exists", error_output.getvalue())
            self.assertEqual([marker], list(target.iterdir()))
            self.assertEqual("bleibt erhalten", marker.read_text(encoding="utf-8"))


    def test_module_dispatches_and_propagates_exit_codes(self):
        with TemporaryDirectory() as directory:
            target = Path(directory) / "demo"
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            def run(*args):
                return subprocess.run(
                    [sys.executable, "-m", "impacts_protocol.cli", *args],
                    cwd=directory, env=environment, capture_output=True, text=True,
                )

            initialized = run("init", str(target))
            self.assertEqual(0, initialized.returncode, initialized.stderr)
            self.assertTrue((target / "CONTEXT.md").is_file(), initialized.stdout)
            self.assertEqual(0, run("validate", str(target)).returncode)
            duplicate = run("init", str(target))
            self.assertEqual(1, duplicate.returncode)
            self.assertIn("exists", duplicate.stderr)
            self.assertEqual(2, run("not-a-command").returncode)

            router = target / "CONTEXT.md"
            router.write_text("---\ntype: invalid\n---\n", encoding="utf-8")
            before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
            rejected = run("validate", str(target))
            self.assertEqual(1, rejected.returncode)
            self.assertIn("routing.type: CONTEXT.md: Root type must be workspace or hauptprozess", rejected.stdout)
            self.assertEqual("", rejected.stderr)
            self.assertEqual(before, {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()})


def test_validate_json_subprocess_reports_valid_and_invalid_without_text_leaks(tmp_path):
    from impacts_protocol import init_workspace

    root = init_workspace(tmp_path / "workspace")
    valid = _run_cli(tmp_path, "validate", root, "--json")

    assert valid.returncode == 0
    assert valid.stderr == ""
    valid_report = _json_stdout(valid)
    assert set(valid_report) == {
        "report_version", "command", "tool", "issues", "valid", "root"
    }
    assert valid_report["report_version"] == 1
    assert valid_report["command"] == "validate"
    _assert_tool_metadata(valid_report["tool"])
    assert valid_report["issues"] == []
    assert valid_report["valid"] is True
    assert valid_report["root"] == str(root)

    verbose = _run_cli(tmp_path, "validate", root, "--json", "--verbose")
    assert verbose.returncode == 0
    assert verbose.stderr.startswith("Package metadata identity: ")
    assert "Package metadata identity" not in verbose.stdout
    assert _json_stdout(verbose)["valid"] is True

    (root / "CONTEXT.md").write_text("---\ntype: invalid\n---\n", encoding="utf-8")
    invalid = _run_cli(tmp_path, "validate", root, "--json")

    assert invalid.returncode == 1
    assert invalid.stderr == ""
    invalid_report = _json_stdout(invalid)
    assert invalid_report["valid"] is False
    assert any(issue["code"] == "routing.type" for issue in invalid_report["issues"])
    assert all(set(issue) == {"code", "path", "message"} for issue in invalid_report["issues"])


def test_hash_json_subprocess_reports_digest_and_expected_failure(tmp_path):
    from impacts_protocol import surface_hash

    attempt = tmp_path / "attempt"
    (attempt / "input").mkdir(parents=True)
    source = attempt / "input" / "auftrag.md"
    source.write_bytes(b"Synthetic input\n")
    expected_digest = surface_hash(attempt, ["input/auftrag.md"])

    success = _run_cli(tmp_path, "hash", attempt, "input/auftrag.md", "--json")

    assert success.returncode == 0
    assert success.stderr == ""
    report = _json_stdout(success)
    assert set(report) == {
        "report_version", "command", "tool", "issues", "digest", "attempt", "surfaces"
    }
    assert report["report_version"] == 1
    assert report["command"] == "hash"
    _assert_tool_metadata(report["tool"])
    assert report["issues"] == []
    assert report["digest"] == expected_digest
    assert report["attempt"] == str(attempt)
    assert report["surfaces"] == ["input/auftrag.md"]

    failure = _run_cli(tmp_path, "hash", attempt, "input/missing.md", "--json")

    assert failure.returncode == 1
    assert failure.stderr == ""
    failed_report = _json_stdout(failure)
    assert failed_report["digest"] is None
    assert failed_report["attempt"] == str(attempt)
    assert failed_report["surfaces"] == ["input/missing.md"]
    assert failed_report["issues"][0]["code"] == "hash.mismatch"
    assert set(failed_report["issues"][0]) == {"code", "path", "message"}


def test_validate_json_subprocess_reports_tampered_attempt_hash(tmp_path):
    from tests.test_minimal_vorgang import _prepare_workspace

    root, run = _prepare_workspace(tmp_path)
    (run / "start" / "001" / "input" / "auftrag.md").write_text(
        "Tampered input\n", encoding="utf-8"
    )

    result = _run_cli(tmp_path, "validate", root, "--json")

    assert result.returncode == 1
    assert result.stderr == ""
    report = _json_stdout(result)
    assert report["valid"] is False
    assert any(
        issue["code"] == "hash.mismatch"
        and issue["path"] == "vorgaenge/video-001/start/001"
        for issue in report["issues"]
    )


def test_validate_json_subprocess_escapes_unicode_root_and_issue_paths(tmp_path):
    from impacts_protocol import init_workspace

    root = init_workspace(tmp_path / "workspace-ü")
    (root / "applications" / "café").mkdir()

    result = _run_cli(tmp_path, "validate", root, "--json")

    assert result.returncode == 1
    assert result.stdout.isascii()
    assert "\\u00fc" in result.stdout.lower()
    assert "\\u00e9" in result.stdout.lower()
    report = _json_stdout(result)
    assert report["root"] == str(root)
    assert any("café" in issue["path"] for issue in report["issues"])


def test_validate_json_subprocess_escapes_surrogateescape_root_on_posix(tmp_path):
    if os.name != "posix":
        raise unittest.SkipTest("surrogateescape paths require POSIX filesystem bytes")

    root_bytes = os.path.join(os.fsencode(tmp_path), b"workspace-\xff")
    root = os.fsdecode(root_bytes)
    code = """
import sys
from types import SimpleNamespace
from unittest.mock import patch
from impacts_protocol.cli import main

with patch(
    "impacts_protocol.validator.validate",
    return_value=SimpleNamespace(valid=True, issues=[]),
):
    raise SystemExit(main(["validate", sys.argv[1], "--json"]))
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", code, root],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.isascii()
    assert "\\udcff" in result.stdout.lower()
    report = _json_stdout(result)
    assert report["root"] == root


def test_json_usage_errors_remain_argparse_stderr_exit_two(tmp_path):
    missing_path = _run_cli(tmp_path, "validate", "--json")
    unsupported_command = _run_cli(tmp_path, "init", tmp_path / "new", "--json")

    for result in (missing_path, unsupported_command):
        assert result.returncode == 2
        assert result.stdout == ""
        assert "usage:" in result.stderr.lower()


def test_json_tool_version_is_null_when_metadata_and_source_version_are_unavailable(tmp_path):
    from impacts_protocol import init_workspace

    root = init_workspace(tmp_path / "workspace")
    code = """
import importlib.metadata
import sys
from unittest.mock import patch
from impacts_protocol.cli import main

with patch(
    "importlib.metadata.distribution",
    side_effect=importlib.metadata.PackageNotFoundError,
):
    with patch(
        "impacts_protocol.cli.__file__",
        "/missing/src/impacts_protocol/cli.py",
    ):
        raise SystemExit(main(["validate", sys.argv[1], "--json"]))
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", code, str(root)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    report = _json_stdout(result)
    assert report["tool"]["name"] == "impacts-protocol"
    assert report["tool"]["version"] is None
    assert report["tool"]["version_source"] == "metadata unavailable"


if __name__ == "__main__":
    unittest.main()
