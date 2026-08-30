from contextlib import contextmanager
from pathlib import Path
import json
import sys
from tempfile import TemporaryDirectory
import unittest

from jsonschema import Draft202012Validator
import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol.generator import generate_workspace
from impacts_protocol.validator import validate_workspace


class PackageActivationInterfaceTests(unittest.TestCase):
    def test_core_activation_rejects_consumer_release_artifact(self):
        activation = {
            "customer_id": "customer:test",
            "packages": [
                {
                    "id": "external-capability",
                    "version": "1.0.0",
                    "activation": "active",
                    "evidence_status": "verified",
                    "artifact": {
                        "file": "vendor/external-capability-1.0.0.whl",
                        "sha256": "a" * 64,
                    },
                }
            ],
        }
        schema = json.loads(
            (ROOT / "02_protocol/schemas/paketaktivierungen.schema.json").read_text()
        )

        errors = list(Draft202012Validator(schema).iter_errors(activation))

        self.assertTrue(any("artifact" in error.message for error in errors))

    def test_external_package_metadata_validates_without_resolution(self):
        with generated_workspace() as root:
            path = root / "00_steuerung/paketaktivierungen.yaml"
            activation = load(path)
            activation["packages"] = [
                {
                    "id": "external-capability",
                    "version": "9.9.9",
                    "activation": "active",
                    "evidence_status": "reported",
                }
            ]
            dump(path, activation)

            report = validate_workspace(root)

        self.assertTrue(report.valid, report.issues)

    def test_duplicate_external_package_activation_is_rejected(self):
        with generated_workspace() as root:
            path = root / "00_steuerung/paketaktivierungen.yaml"
            activation = load(path)
            package = {
                "id": "external-capability",
                "version": "1.0.0",
                "activation": "active",
                "evidence_status": "reported",
            }
            activation["packages"] = [package, dict(package)]
            dump(path, activation)

            report = validate_workspace(root)

        self.assertIn("capability.duplicate_activation", codes(report))


class ViewProjectionTests(unittest.TestCase):
    def test_generated_view_cannot_source_itself_or_another_view(self):
        with generated_workspace() as root:
            first = root / "99_ansichten/first.yaml"
            second = root / "99_ansichten/second.yaml"
            dump(first, {"generated": True, "generated_from": ["99_ansichten/first.yaml"]})
            dump(second, {"generated": True, "generated_from": ["99_ansichten/first.yaml"]})

            report = validate_workspace(root)

        self.assertIn("view.non_authoritative_provenance", codes(report))

    def test_normalized_path_cannot_reenter_views(self):
        with generated_workspace() as root:
            source = root / "02_grundlagen/source.yaml"
            dump(source, {"id": "source:one"})
            dump(
                root / "99_ansichten/first.yaml",
                {"generated": True, "generated_from": ["02_grundlagen/source.yaml"]},
            )
            dump(
                root / "99_ansichten/second.yaml",
                {
                    "generated": True,
                    "generated_from": ["02_grundlagen/../99_ansichten/first.yaml"],
                },
            )

            report = validate_workspace(root)

        self.assertIn("view.non_authoritative_provenance", codes(report))


class DocumentationContractTests(unittest.TestCase):
    def test_superseded_design_is_absent_from_review_branch(self):
        self.assertFalse(
            (
                ROOT
                / "docs/superpowers/specs/2026-08-24-impacts-workspace-decomplected-design.md"
            ).exists()
        )
        self.assertTrue(
            (
                ROOT
                / "docs/superpowers/specs/2026-08-26-contract-only-core-design.md"
            ).is_file()
        )


def codes(report):
    return {issue.code for issue in report.issues}


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump(path: Path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


@contextmanager
def generated_workspace():
    with TemporaryDirectory() as directory:
        yield generate_workspace(Path(directory) / "workspace", "demo-kunde")


if __name__ == "__main__":
    unittest.main()
