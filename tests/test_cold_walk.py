from contextlib import redirect_stdout
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol.generator import generate_workspace


CHECK_PATH = ROOT / "06_evaluations" / "cold-walk" / "check.py"


def load_check_module():
    spec = spec_from_file_location("impacts_cold_walk_check", CHECK_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load cold-walk checker from {CHECK_PATH}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ColdWalkTests(unittest.TestCase):
    def test_checker_accepts_contract_only_template(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            root = generate_workspace(Path(directory) / "workspace", "walk-demo")

            result = check.inspect_workspace(root)

        self.assertTrue(result.valid, result.issues)
        self.assertEqual(8, len(result.folders))
        self.assertEqual(3, len(result.files))

    def test_checker_rejects_missing_contract_file(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            root = generate_workspace(Path(directory) / "workspace", "walk-demo")
            (root / "02_grundlagen/datenautoritaet.yaml").unlink()

            result = check.inspect_workspace(root)

        self.assertFalse(result.valid)
        self.assertTrue(any("template.files" in issue for issue in result.issues))

    def test_checker_rejects_embedded_process_tree(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            root = generate_workspace(Path(directory) / "workspace", "walk-demo")
            path = root / "01_prozesse/eingebettet/hauptprozess.yaml"
            path.parent.mkdir()
            path.write_text("id: hauptprozess:falsch\n", encoding="utf-8")

            result = check.inspect_workspace(root)

        self.assertFalse(result.valid)
        self.assertTrue(any("template.files" in issue for issue in result.issues))

    def test_command_reports_contract_only_workspace(self):
        check = load_check_module()
        output = StringIO()

        with redirect_stdout(output):
            exit_code = check.main()

        self.assertEqual(0, exit_code)
        self.assertIn("PASS contract-only workspace", output.getvalue())
        self.assertNotIn("NEXT_ACTION", output.getvalue())


if __name__ == "__main__":
    unittest.main()
