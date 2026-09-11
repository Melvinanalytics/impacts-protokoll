from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import os
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol.cli import main


class CliTests(unittest.TestCase):
    def test_init_and_validate_generated_workspace(self):
        with TemporaryDirectory() as directory:
            target = Path(directory) / "demo"

            self.assertEqual(
                0, main(["init", str(target)])
            )
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
