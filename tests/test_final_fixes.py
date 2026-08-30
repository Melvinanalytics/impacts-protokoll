from pathlib import Path
import json
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol.generator import generate_workspace
from impacts_protocol.validator import validate_workspace


class FinalFixesTests(unittest.TestCase):
    def test_empty_customer_id_is_rejected_before_target_creation(self):
        for customer_id in ("", "   "):
            with self.subTest(customer_id=customer_id), TemporaryDirectory() as directory:
                target = Path(directory) / "demo"

                with self.assertRaises(ValueError):
                    generate_workspace(target, customer_id)

                self.assertFalse(target.exists())

    def test_partial_write_failure_leaves_no_target_or_staging_directory(self):
        with TemporaryDirectory() as directory:
            parent = Path(directory)
            target = parent / "demo"

            with patch(
                "impacts_protocol.generator.yaml.safe_dump",
                side_effect=OSError("synthetic write failure"),
            ):
                with self.assertRaises(OSError):
                    generate_workspace(target, "demo-kunde")

            self.assertFalse(target.exists())
            self.assertEqual([], list(parent.glob(".demo.*")))

    def test_staged_validation_failure_leaves_no_target(self):
        with TemporaryDirectory() as directory:
            parent = Path(directory)
            target = parent / "demo"

            with patch(
                "impacts_protocol.generator._validate_generated_workspace",
                side_effect=ValueError("synthetic validation failure"),
            ):
                with self.assertRaises(ValueError):
                    generate_workspace(target, "demo-kunde")

            self.assertFalse(target.exists())
            self.assertEqual([], list(parent.glob(".demo.*")))

    def test_wait_requires_owner_and_exactly_one_continuation(self):
        schema = json.loads(
            (ROOT / "02_protocol/schemas/hauptprozess.schema.json").read_text()
        )
        validator = Draft202012Validator(schema)
        document = {
            "id": "hauptprozess:wait",
            "leistung_ref": "leistung:wait",
            "entry": "wait",
            "nodes": [
                {"id": "wait", "type": "wait", "trigger": "reply", "next": ["end"]},
                {"id": "end", "type": "end", "event": "done", "next": []},
            ],
        }

        self.assertTrue(list(validator.iter_errors(document)))
        document["nodes"][0]["owner"] = "rolle:bearbeitung"
        document["nodes"][0]["next"] = ["end", "other"]
        self.assertTrue(list(validator.iter_errors(document)))

    def test_case_normalized_yaml_extension_gets_strict_duplicate_scan(self):
        with self.generated_workspace() as root:
            (root / "operator-notes.YmL").write_text(
                "meta:\n  id: one\n  id: two\n", encoding="utf-8"
            )

            report = validate_workspace(root)

        self.assertIn("format.invalid_yaml", {issue.code for issue in report.issues})

    def test_case_normalized_yaml_symlink_cannot_escape_workspace(self):
        with self.generated_workspace() as root:
            external = root.parent / "external.YAML"
            external.write_text("id: external\n", encoding="utf-8")
            (root / "operator-notes.YAML").symlink_to(external)

            report = validate_workspace(root)

        self.assertIn("structure.symlink", {issue.code for issue in report.issues})

    def test_generated_views_require_provenance(self):
        with self.generated_workspace() as root:
            (root / "99_ansichten/status.md").write_text(
                "# Status\n", encoding="utf-8"
            )

            report = validate_workspace(root)

        self.assertIn("view.missing_provenance", {issue.code for issue in report.issues})

    def test_generated_view_provenance_must_resolve(self):
        with self.generated_workspace() as root:
            self.dump(
                root / "99_ansichten/status.yaml",
                {"generated": True, "generated_from": ["02_grundlagen/fehlt.yaml"]},
            )

            report = validate_workspace(root)

        self.assertIn("view.unresolved_provenance", {issue.code for issue in report.issues})

    def test_repository_navigation_names_contract_only_core(self):
        for document in (ROOT / "README.md", ROOT / "CONTEXT.md"):
            text = document.read_text(encoding="utf-8")
            self.assertIn("src/impacts_protocol", text)
            self.assertIn("06_evaluations", text)
            self.assertNotIn("04_capabilities", text)

    @staticmethod
    def dump(path: Path, document):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def generated_workspace(self):
        temporary = TemporaryDirectory()
        root = generate_workspace(Path(temporary.name) / "workspace", "demo-kunde")

        class Context:
            def __enter__(self):
                return root

            def __exit__(self, *args):
                temporary.cleanup()

        return Context()


if __name__ == "__main__":
    unittest.main()
