import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _install(temporary_root: Path) -> tuple[Path, Path, dict[str, str]]:
    target = temporary_root / "site"
    run_directory = temporary_root / "unrelated"
    source = temporary_root / "source"
    run_directory.mkdir()
    shutil.copytree(
        ROOT,
        source,
        ignore=shutil.ignore_patterns(".git", "build", "*.egg-info", "__pycache__"),
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
    assert install.returncode == 0, install.stderr
    environment = os.environ.copy()
    environment["PATH"] = f"{target / 'bin'}{os.pathsep}{environment['PATH']}"
    environment["PYTHONPATH"] = str(target)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return target, run_directory, environment


@pytest.mark.skipif(
    subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True,
    ).returncode
    != 0,
    reason="packaging test requires pip",
)
def test_non_editable_install_exposes_minimal_cli_from_unrelated_cwd():
    with TemporaryDirectory() as directory:
        temporary_root = Path(directory)
        _, run_directory, environment = _install(temporary_root)
        workspace = temporary_root / "workspace"

        initialized = subprocess.run(
            ["impacts", "init", str(workspace)],
            cwd=run_directory,
            env=environment,
            capture_output=True,
            text=True,
        )
        checked = subprocess.run(
            ["impacts", "validate", str(workspace)],
            cwd=run_directory,
            env=environment,
            capture_output=True,
            text=True,
        )

        assert initialized.returncode == 0, initialized.stderr
        assert checked.returncode == 0, checked.stdout + checked.stderr


def test_non_editable_install_contains_only_five_schemas_and_minimal_api():
    with TemporaryDirectory() as directory:
        temporary_root = Path(directory)
        _, run_directory, environment = _install(temporary_root)
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import impacts_protocol; "
                    "from importlib import metadata, resources; "
                    "files=resources.files('impacts_protocol.schemas'); "
                    "names=sorted(p.name for p in files.iterdir() if p.name.endswith('.json')); "
                    "assert set(impacts_protocol.__all__)=={'Issue','ValidationReport','init_workspace','validate'}; "
                    "assert metadata.version('impacts-protocol')=='0.2.0'; "
                    "assert names==['arbeitsschritt.schema.json','hauptprozess.schema.json','leistung.schema.json','teilprozess.schema.json','vorgang.schema.json'], names"
                ),
            ],
            cwd=run_directory,
            env=environment,
            capture_output=True,
            text=True,
        )

        assert probe.returncode == 0, probe.stdout + probe.stderr


def test_distribution_declares_and_contains_apache_license():
    with TemporaryDirectory() as directory:
        temporary_root = Path(directory)
        _, run_directory, environment = _install(temporary_root)
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from importlib import metadata; "
                    "distribution=metadata.distribution('impacts-protocol'); "
                    "assert distribution.metadata['License-Expression']=='Apache-2.0'; "
                    "names={str(path) for path in distribution.files}; "
                    "assert 'impacts_protocol-0.2.0.dist-info/licenses/LICENSE' in names, names"
                ),
            ],
            cwd=run_directory,
            env=environment,
            capture_output=True,
            text=True,
        )

        assert probe.returncode == 0, probe.stdout + probe.stderr
