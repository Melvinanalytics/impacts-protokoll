from contextlib import redirect_stderr
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


if __name__ == "__main__":
    unittest.main()
