import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(
    subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True,
    ).returncode
    != 0,
    reason="packaging tests require pip",
)


@pytest.fixture(scope="module")
def installed_environment(tmp_path_factory) -> dict[str, str]:
    temporary_root = tmp_path_factory.mktemp("installed-package")
    target = temporary_root / "site"
    source = temporary_root / "source"
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
        cwd=temporary_root,
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, install.stderr
    environment = os.environ.copy()
    environment["PATH"] = f"{target / 'bin'}{os.pathsep}{environment['PATH']}"
    environment["PYTHONPATH"] = str(target)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


@pytest.mark.parametrize("language", ["en", "de"])
def test_non_editable_install_exposes_minimal_cli_from_unrelated_cwd(
    installed_environment, tmp_path, language
):
    workspace = tmp_path / "workspace"

    initialized = subprocess.run(
        ["impacts", "init", str(workspace), "--language", language],
        cwd=tmp_path,
        env=installed_environment,
        capture_output=True,
        text=True,
    )
    checked = subprocess.run(
        ["impacts", "validate", str(workspace)],
        cwd=tmp_path,
        env=installed_environment,
        capture_output=True,
        text=True,
    )

    assert initialized.returncode == 0, initialized.stderr
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert f"Working language: {language}" in (workspace / "CONTEXT.md").read_text()


@pytest.mark.parametrize("language,heading", [("en", "# Decide"), ("de", "# Entscheiden")])
def test_non_editable_install_exposes_template_and_hash_from_unrelated_cwd(
    installed_environment, tmp_path, language, heading
):
    attempt = tmp_path / "001"
    (attempt / "input").mkdir(parents=True)
    (attempt / "input" / "auftrag.md").write_text("Auftrag", encoding="utf-8")

    template = subprocess.run(
        ["impacts", "template", "arbeitsschritt", "--language", language],
        cwd=tmp_path,
        env=installed_environment,
        capture_output=True,
        text=True,
    )
    digest = subprocess.run(
        ["impacts", "hash", str(attempt), "input/auftrag.md"],
        cwd=tmp_path,
        env=installed_environment,
        capture_output=True,
        text=True,
    )

    assert template.returncode == 0, template.stderr
    assert template.stdout.startswith("---\ntype: arbeitsschritt\n")
    assert heading in template.stdout
    assert digest.returncode == 0, digest.stderr
    assert digest.stdout.startswith("sha256:") and len(digest.stdout.strip()) == 71


def test_non_editable_install_contains_only_five_schemas_and_minimal_api(
    installed_environment, tmp_path
):
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import impacts_protocol; "
                "from importlib import metadata, resources; "
                "files=resources.files('impacts_protocol.schemas'); "
                "names=sorted(p.name for p in files.iterdir() if p.name.endswith('.json')); "
                "assert set(impacts_protocol.__all__)=={'HashSurfaceError','Issue','ValidationReport','init_workspace','surface_hash','validate'}; "
                "assert metadata.version('impacts-protocol')=='0.3.0'; "
                "assert 'referencing>=0.28.4' in metadata.requires('impacts-protocol'); "
                "assert names==['arbeitsschritt.schema.json','hauptprozess.schema.json','leistung.schema.json','teilprozess.schema.json','vorgang.schema.json'], names"
            ),
        ],
        cwd=tmp_path,
        env=installed_environment,
        capture_output=True,
        text=True,
    )

    assert probe.returncode == 0, probe.stdout + probe.stderr


def test_distribution_declares_and_contains_apache_license(installed_environment, tmp_path):
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from importlib import metadata; "
                "distribution=metadata.distribution('impacts-protocol'); "
                "assert distribution.metadata['License-Expression']=='Apache-2.0'; "
                "names={str(path) for path in distribution.files}; "
                "assert 'impacts_protocol-0.3.0.dist-info/licenses/LICENSE' in names, names"
            ),
        ],
        cwd=tmp_path,
        env=installed_environment,
        capture_output=True,
        text=True,
    )

    assert probe.returncode == 0, probe.stdout + probe.stderr
