from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import impacts_protocol
from impacts_protocol.cli import main
from impacts_protocol.io import load_frontmatter


def _init_workspace(target: Path) -> Path:
    initializer = getattr(impacts_protocol, "init_workspace", None)
    if initializer is None:
        pytest.fail("public init_workspace is missing")
    return initializer(target)


def test_init_creates_only_minimal_workspace():
    with TemporaryDirectory() as directory:
        target = Path(directory) / "workspace"

        root = _init_workspace(target)

        assert sorted(path.name for path in root.iterdir()) == [
            "CONTEXT.md",
            "applications",
            "vorgaenge",
        ]
        assert load_frontmatter(root / "CONTEXT.md") == {"type": "workspace"}


def test_cli_init_needs_no_customer_argument():
    with TemporaryDirectory() as directory:
        target = Path(directory) / "workspace"

        assert main(["init", str(target)]) == 0
        assert target.is_dir()


def test_init_is_atomic_when_target_exists():
    with TemporaryDirectory() as directory:
        target = Path(directory) / "workspace"
        target.mkdir()
        marker = target / "keep"
        marker.write_text("keep", encoding="utf-8")

        with pytest.raises(FileExistsError):
            _init_workspace(target)

        assert marker.read_text(encoding="utf-8") == "keep"
        assert list(target.iterdir()) == [marker]


def test_init_router_body_states_the_operating_contract():
    with TemporaryDirectory() as directory:
        root = _init_workspace(Path(directory) / "workspace")

        body = (root / "CONTEXT.md").read_text(encoding="utf-8").split("---", 2)[2]

        for phrase in (
            "impacts template",
            "impacts hash",
            "impacts validate",
            "git rev-parse HEAD:applications/",
            "Git root",
            "No agent writes `human:<id>`",
            "02_protocol/ontology.md",
        ):
            assert phrase in body, f"router body lacks {phrase!r}"
