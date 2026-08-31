from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
