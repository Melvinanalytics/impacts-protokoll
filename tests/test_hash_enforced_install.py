"""The selected Linux install set is fully pinned and rejects changed wheel bytes."""

import base64
import csv
import hashlib
from io import StringIO
from pathlib import Path
import re
import subprocess
import sys
import tomllib
import venv
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / ".github/runtime-linux-cp311-x86_64.txt"
REQUIREMENT = re.compile(
    r"^([A-Za-z0-9_.-]+)==([^\s]+) --hash=sha256:([0-9a-f]{64})$"
)


def test_install_lock_pins_direct_runtime_and_transitive_dependencies():
    parsed = []
    for line in LOCK.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        match = REQUIREMENT.fullmatch(line)
        assert match, f"unhashed or unpinned requirement: {line}"
        parsed.append(match.groups())
    normalized = {name.lower().replace("_", "-").replace(".", "-") for name, _, _ in parsed}
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    direct = {
        re.match(r"([A-Za-z0-9_.-]+)", requirement).group(1).lower().replace("_", "-").replace(".", "-")
        for requirement in project["project"]["dependencies"]
    }
    assert direct <= normalized
    assert "setuptools" in normalized  # pinned build backend for the editable source install
    assert len(normalized) == len(parsed)


def _wheel(path: Path) -> None:
    files = {
        "tiny_dependency.py": b"VALUE = 1\n",
        "tiny_dependency-1.0.dist-info/METADATA": (
            b"Metadata-Version: 2.1\nName: tiny-dependency\nVersion: 1.0\n"
        ),
        "tiny_dependency-1.0.dist-info/WHEEL": (
            b"Wheel-Version: 1.0\nGenerator: evidence-test\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
        ),
    }
    rows = []
    for name, content in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip("=")
        rows.append((name, f"sha256={digest}", str(len(content))))
    rows.append(("tiny_dependency-1.0.dist-info/RECORD", "", ""))
    record = StringIO(newline="")
    csv.writer(record, lineterminator="\n").writerows(rows)
    files["tiny_dependency-1.0.dist-info/RECORD"] = record.getvalue().encode()
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


def test_pip_rejects_modified_dependency_wheel_under_hash_checking(tmp_path):
    wheels = tmp_path / "wheels"
    wheels.mkdir()
    artifact = wheels / "tiny_dependency-1.0-py3-none-any.whl"
    _wheel(artifact)
    approved_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
    with artifact.open("ab") as changed:
        changed.write(b"changed after its approved digest")
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        f"tiny-dependency==1.0 --hash=sha256:{approved_hash}\n", encoding="utf-8"
    )

    environment = tmp_path / "venv"
    venv.create(environment, with_pip=True)
    python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    result = subprocess.run(
        [
            str(python), "-m", "pip", "install", "--disable-pip-version-check",
            "--no-index", "--find-links", str(wheels), "--require-hashes",
            "--no-deps", "-r", str(requirements), "--target", str(tmp_path / "target"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "do not match the hashes" in (result.stdout + result.stderr).lower()
