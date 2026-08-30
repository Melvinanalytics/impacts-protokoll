from pathlib import Path
import json
import sys
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

RETIRED_TERM = "ab" + "lauf"
SKIPPED_PARTS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}


class CanonicalProcessModelTests(unittest.TestCase):
    def test_retired_term_is_absent_from_repository_paths_and_text(self):
        findings = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or any(part in SKIPPED_PARTS for part in path.parts):
                continue
            relative = path.relative_to(ROOT).as_posix()
            if RETIRED_TERM in relative.casefold():
                findings.append(relative)
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if RETIRED_TERM in text.casefold():
                findings.append(relative)

        self.assertEqual([], findings)

    def test_hauptprozess_owns_process_graph(self):
        validator = self.schema_validator("hauptprozess")
        document = {
            "id": "hauptprozess:demo",
            "leistung_ref": "leistung:demo",
            "entry": "arbeitsschritt:start",
            "nodes": [
                {
                    "id": "arbeitsschritt:start",
                    "type": "task",
                    "next": ["ereignis:fertig"],
                },
                {
                    "id": "ereignis:fertig",
                    "type": "end",
                    "next": [],
                    "event": "Leistung erbracht",
                },
            ],
        }

        self.assertEqual([], list(validator.iter_errors(document)))

    def test_vorgang_references_exactly_one_hauptprozess(self):
        validator = self.schema_validator("vorgang")
        document = {
            "id": "vorgang:demo",
            "hauptprozess_ref": "hauptprozess:demo",
            "status": "angelegt",
            "run_id": "run:demo",
            "receipt_refs": ["receipt:demo"],
        }

        self.assertEqual([], list(validator.iter_errors(document)))

    def test_wiedervorlage_uses_vorgang_process_context(self):
        validator = self.schema_validator("wiedervorlage")
        document = {
            "id": "wiedervorlage:demo",
            "vorgang_ref": "vorgang:demo",
            "run_id": "run:demo",
            "owner": "rolle:bearbeitung",
            "trigger": "antwort_eingegangen",
            "continuation": "arbeitsschritt:pruefen",
            "status": "wartend",
            "receipt_refs": ["receipt:demo"],
        }

        self.assertEqual([], list(validator.iter_errors(document)))

    @staticmethod
    def schema_validator(name: str) -> Draft202012Validator:
        path = ROOT / "02_protocol/schemas" / f"{name}.schema.json"
        return Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
