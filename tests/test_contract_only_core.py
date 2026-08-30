from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol.cli import build_parser
from impacts_protocol.generator import generate_workspace
from impacts_protocol.validator import validate_workspace
from impacts_protocol.workspace_contract import WORKSPACE_FOLDERS


EXPECTED_WORKSPACE_FOLDERS = set(WORKSPACE_FOLDERS)


class ContractOnlyCoreTests(unittest.TestCase):
    def test_cli_exposes_only_init_and_validate(self):
        parser = build_parser()
        subparsers = next(
            action for action in parser._actions if action.dest == "command"
        )

        self.assertEqual({"init", "validate"}, set(subparsers.choices))

    def test_init_stamps_only_contract_workspace(self):
        with TemporaryDirectory() as directory:
            root = generate_workspace(Path(directory) / "kunde", "kunde-001")

            self.assertEqual(
                EXPECTED_WORKSPACE_FOLDERS,
                {path.name for path in root.iterdir() if path.is_dir()},
            )
            self.assertEqual([], list((root / "01_prozesse").iterdir()))
            self.assertEqual([], list((root / "05_aenderungsnachweise").iterdir()))
            self.assertEqual([], list((root / "06_vorgaenge").iterdir()))
            self.assertEqual([], list((root / "99_ansichten").iterdir()))

            generated_files = {
                path.relative_to(root).as_posix()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(
                {
                    "CONTEXT.md",
                    "00_steuerung/paketaktivierungen.yaml",
                    "02_grundlagen/datenautoritaet.yaml",
                },
                generated_files,
            )

    def test_init_defaults_to_local_record_authority(self):
        with TemporaryDirectory() as directory:
            root = generate_workspace(Path(directory) / "kunde", "kunde-001")

            authority = yaml.safe_load(
                (root / "02_grundlagen/datenautoritaet.yaml").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(
                {
                    "records": {
                        "default": {
                            "writes": "customer",
                            "kind": "file",
                            "path": "03_records",
                        }
                    }
                },
                authority,
            )
            self.assertTrue((root / "03_records").is_dir())

    def test_empty_contract_workspace_validates_without_run_evidence(self):
        with TemporaryDirectory() as directory:
            root = generate_workspace(Path(directory) / "kunde", "kunde-001")

            report = validate_workspace(root)

            self.assertTrue(report.valid, report.issues)

    def test_generated_view_cannot_be_record_write_authority(self):
        with TemporaryDirectory() as directory:
            root = generate_workspace(Path(directory) / "kunde", "kunde-001")
            authority_path = root / "02_grundlagen/datenautoritaet.yaml"
            authority = yaml.safe_load(authority_path.read_text(encoding="utf-8"))
            authority["records"]["default"]["path"] = "99_ansichten"
            authority_path.write_text(
                yaml.safe_dump(authority, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            report = validate_workspace(root)

            self.assertIn(
                "authority.generated_view_write",
                {issue.code for issue in report.issues},
            )

    def test_external_record_authority_requires_no_local_record_store(self):
        with TemporaryDirectory() as directory:
            root = generate_workspace(Path(directory) / "kunde", "kunde-001")
            authority_path = root / "02_grundlagen/datenautoritaet.yaml"
            authority = {
                "records": {
                    "default": {
                        "writes": "customer",
                        "kind": "external",
                        "authority_id": "crm:customer",
                    }
                }
            }
            authority_path.write_text(
                yaml.safe_dump(authority, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            report = validate_workspace(root)

            self.assertIn(
                "authority.duplicate_record_store",
                {issue.code for issue in report.issues},
            )

    def test_core_source_excludes_evidence_machine(self):
        module_names = {
            path.name for path in (ROOT / "src" / "impacts_protocol").glob("*.py")
        }

        self.assertNotIn("evidence.py", module_names)
        self.assertNotIn("evidence_validation.py", module_names)


if __name__ == "__main__":
    unittest.main()
