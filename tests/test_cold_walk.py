from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
CHECK_PATH = ROOT / "06_evaluations" / "cold-walk" / "check.py"

from impacts_protocol import init_workspace


def _check_module():
    spec = spec_from_file_location("impacts_cold_walk", CHECK_PATH)
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_cold_walk_accepts_minimal_template():
    check = _check_module()
    with TemporaryDirectory() as directory:
        root = init_workspace(Path(directory) / "workspace")

        result = check.inspect_workspace(root)

        assert result.valid, result.issues
        assert result.folders == ("applications", "vorgaenge")
        assert result.files == ("CONTEXT.md",)


def test_cold_walk_rejects_missing_folder():
    check = _check_module()
    with TemporaryDirectory() as directory:
        root = init_workspace(Path(directory) / "workspace")
        (root / "vorgaenge").rmdir()

        result = check.inspect_workspace(root)

        assert not result.valid
        assert any("template.folders" in issue for issue in result.issues)
