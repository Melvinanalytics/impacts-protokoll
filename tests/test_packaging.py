import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
class PackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pip_probe = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
        )
        if pip_probe.returncode != 0:
            raise unittest.SkipTest(
                f"packaging tests require pip for {sys.executable}: {pip_probe.stderr.strip()}"
            )

    def test_non_editable_install_can_load_canonical_schemas(self):
        with TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            target = temporary_root / "site"
            run_directory = temporary_root / "run"
            source = temporary_root / "source"
            run_directory.mkdir()
            shutil.copytree(
                ROOT,
                source,
                ignore=shutil.ignore_patterns(
                    ".git", "build", "*.egg-info", "__pycache__"
                ),
            )
            install = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-cache-dir",
                    "--no-build-isolation",
                    "--no-deps",
                    "--target",
                    str(target),
                    str(source),
                ],
                cwd=run_directory,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, install.returncode, install.stderr)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(target)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            fixture = temporary_root / "fixture"
            generated = subprocess.run(
                [
                    str(target / "bin" / "impacts"),
                    "init",
                    str(fixture),
                    "--customer",
                    "packaging-smoke",
                ],
                cwd=run_directory,
                env=environment,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, generated.returncode, generated.stderr)
            smoke = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from pathlib import Path; "
                        "from impacts_protocol.validator import validate_workspace; "
                        "report = validate_workspace(Path(__import__('sys').argv[1])); "
                        "assert report.valid, report.issues"
                    ),
                    str(fixture),
                ],
                cwd=run_directory,
                env=environment,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, smoke.returncode, smoke.stderr)

    def test_non_editable_install_exposes_console_entry_from_unrelated_cwd(self):
        with TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            target = temporary_root / "site"
            run_directory = temporary_root / "unrelated"
            source = temporary_root / "source"
            workspace = temporary_root / "workspace"
            run_directory.mkdir()
            shutil.copytree(
                ROOT,
                source,
                ignore=shutil.ignore_patterns(
                    ".git", "build", "*.egg-info", "__pycache__"
                ),
            )
            install = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-cache-dir",
                    "--no-build-isolation",
                    "--no-deps",
                    "--target",
                    str(target),
                    str(source),
                ],
                cwd=run_directory,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, install.returncode, install.stderr)
            environment = os.environ.copy()
            environment["PATH"] = f"{target / 'bin'}{os.pathsep}{environment['PATH']}"
            environment["PYTHONPATH"] = str(target)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            init = subprocess.run(
                [
                    "impacts",
                    "init",
                    str(workspace),
                    "--customer",
                    "demo-kunde",
                ],
                cwd=run_directory,
                env=environment,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, init.returncode, init.stderr)
            validate = subprocess.run(
                ["impacts", "validate", str(workspace)],
                cwd=run_directory,
                env=environment,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, validate.returncode, validate.stderr)

            for name in ("duplicate",):
                invalid_workspace = temporary_root / f"workspace-{name}"
                init = subprocess.run(
                    [
                        "impacts",
                        "init",
                        str(invalid_workspace),
                        "--customer",
                        "demo-kunde",
                    ],
                    cwd=run_directory,
                    env=environment,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, init.returncode, init.stderr)
                activation_path = (
                    invalid_workspace / "00_steuerung/paketaktivierungen.yaml"
                )
                activation = yaml.safe_load(
                    activation_path.read_text(encoding="utf-8")
                )
                package = {
                    "id": "external-capability",
                    "version": "1.0.0",
                    "activation": "active",
                    "evidence_status": "reported",
                }
                activation["packages"] = [package, dict(package)]
                activation_path.write_text(
                    yaml.safe_dump(activation, allow_unicode=True, sort_keys=False),
                    encoding="utf-8",
                )
                invalid = subprocess.run(
                    ["impacts", "validate", str(invalid_workspace)],
                    cwd=run_directory,
                    env=environment,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(1, invalid.returncode)
                self.assertIn("capability.duplicate_activation", invalid.stdout)


if __name__ == "__main__":
    unittest.main()
