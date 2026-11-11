"""The selected Linux install set pins every runtime dependency with a hash."""

from pathlib import Path
import re
import tomllib


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

