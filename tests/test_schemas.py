from pathlib import Path
import json
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "02_protocol" / "schemas"
SCHEMA_FILES = {
    name: SCHEMA_DIR / f"{name}.schema.json"
    for name in {
        "leistung",
        "hauptprozess",
        "teilprozess",
        "arbeitsschritt",
        "vorgang",
        "wiedervorlage",
        "paketaktivierungen",
    }
}


RETIRED_EVIDENCE_SCHEMAS = {
    "receipt.schema.json",
    "delta.schema.json",
}


class SchemaTests(unittest.TestCase):
    def test_package_activation_cannot_claim_verified_without_human_binding(self):
        schema = json.loads(SCHEMA_FILES["paketaktivierungen"].read_text())
        validator = Draft202012Validator(schema)
        document = {
            "customer_id": "kunde",
            "packages": [
                {
                    "id": "application:demo",
                    "version": "1.0.0",
                    "activation": "active",
                    "evidence_status": "verified",
                }
            ],
        }

        self.assertTrue(list(validator.iter_errors(document)))

    def test_runtime_evidence_schemas_are_absent(self):
        self.assertEqual(
            set(),
            {
                path.name
                for path in SCHEMA_DIR.glob("*.json")
                if path.name in RETIRED_EVIDENCE_SCHEMAS
            },
        )

    def test_every_schema_is_valid_draft_2020_12(self):
        for path in SCHEMA_FILES.values():
            schema = json.loads(path.read_text())
            Draft202012Validator.check_schema(schema)

    def test_vorgang_requires_exactly_one_hauptprozess_reference(self):
        schema = json.loads(SCHEMA_FILES["vorgang"].read_text())
        validator = Draft202012Validator(schema)
        errors = list(validator.iter_errors({"id": "vorgang:demo"}))
        self.assertTrue(any("hauptprozess_ref" in error.message for error in errors))

    def test_vorgang_rejects_extra_root_property(self):
        schema = json.loads(SCHEMA_FILES["vorgang"].read_text())
        validator = Draft202012Validator(schema)
        errors = list(
            validator.iter_errors(
                {
                    "id": "vorgang:demo",
                    "hauptprozess_ref": "hauptprozess:demo",
                    "unexpected": True,
                }
            )
        )
        self.assertTrue(any("unexpected" in error.message for error in errors))

    def test_arbeitsschritt_requires_complete_stage_contract(self):
        validator = self._arbeitsschritt_validator()
        errors = list(
            validator.iter_errors(
                {
                    "id": "arbeitsschritt:demo",
                    "teilprozess_ref": "teilprozess:demo",
                }
            )
        )

        missing = {error.message for error in errors if error.validator == "required"}
        for field in ("inputs", "process", "outputs", "verify", "gate", "taetigkeiten"):
            self.assertIn(f"'{field}' is a required property", missing)

    def test_arbeitsschritt_accepts_complete_stage_contract(self):
        validator = self._arbeitsschritt_validator()
        errors = list(
            validator.iter_errors(
                {
                    "id": "arbeitsschritt:demo",
                    "teilprozess_ref": "teilprozess:demo",
                    "inputs": ["artefakt:eingabe"],
                    "process": "Eingabe bearbeiten",
                    "outputs": ["artefakt:ausgabe"],
                    "verify": "Ausgabe prüfen",
                    "gate": "Ausgabe freigeben",
                    "taetigkeiten": [{"id": "taetigkeit:bearbeiten"}],
                }
            )
        )

        self.assertEqual([], errors)

    def test_hauptprozess_rejects_wait_without_continuation_target(self):
        validator = self._hauptprozess_validator()
        errors = list(
            validator.iter_errors(
                {
                    "id": "hauptprozess:demo",
                    "leistung_ref": "leistung:demo",
                    "entry": "node:wait",
                    "nodes": [
                        {
                            "id": "node:wait",
                            "type": "wait",
                            "next": [],
                            "trigger": "customer_reply",
                        }
                    ],
                }
            )
        )
        self.assertTrue(any(error.validator == "minItems" for error in errors))

    def test_hauptprozess_rejects_end_with_continuation_target(self):
        validator = self._hauptprozess_validator()
        errors = list(
            validator.iter_errors(
                {
                    "id": "hauptprozess:demo",
                    "leistung_ref": "leistung:demo",
                    "entry": "node:end",
                    "nodes": [
                        {
                            "id": "node:end",
                            "type": "end",
                            "next": ["node:other"],
                            "event": "completed",
                        }
                    ],
                }
            )
        )
        self.assertTrue(any(error.validator == "maxItems" for error in errors))

    def test_hauptprozess_accepts_minimal_valid_graph(self):
        validator = self._hauptprozess_validator()
        errors = list(
            validator.iter_errors(
                {
                    "id": "hauptprozess:demo",
                    "leistung_ref": "leistung:demo",
                    "entry": "node:start",
                    "nodes": [
                        {
                            "id": "node:start",
                            "type": "task",
                            "next": ["node:end"],
                        },
                        {
                            "id": "node:end",
                            "type": "end",
                            "next": [],
                            "event": "completed",
                        },
                    ],
                }
            )
        )
        self.assertEqual([], errors)

    def test_hauptprozess_rejects_routes_on_non_gateway_nodes(self):
        validator = self._hauptprozess_validator()
        errors = list(
            validator.iter_errors(
                {
                    "id": "hauptprozess:demo",
                    "leistung_ref": "leistung:demo",
                    "entry": "node:start",
                    "nodes": [
                        {
                            "id": "node:start",
                            "type": "task",
                            "next": ["node:end"],
                            "routes": [
                                {"condition": "Umgehen", "target": "node:end"}
                            ],
                        },
                        {
                            "id": "node:end",
                            "type": "end",
                            "next": [],
                            "event": "completed",
                        },
                    ],
                }
            )
        )
        self.assertTrue(errors)

    @staticmethod
    def _hauptprozess_validator():
        schema = json.loads(SCHEMA_FILES["hauptprozess"].read_text())
        return Draft202012Validator(schema)

    @staticmethod
    def _arbeitsschritt_validator():
        schema = json.loads(SCHEMA_FILES["arbeitsschritt"].read_text())
        return Draft202012Validator(schema)
