"""Run-schema acceptance cases for attempt and approval timestamp constraints.

Sources:
- 02_protocol/templates/application.md: attempts use three-digit directories.
- 02_protocol/schemas/vorgang.schema.json: attempts are integers 1..999;
  freigabe.at has a mandatory offset, fixed lexical shape and numeric ranges.
- src/impacts_protocol/validator.py: _valid_human_approval parses the calendar
  date and requires a timezone. The schema pattern alone does not establish
  calendar validity or accept every ISO-8601 spelling.

These ten cases exercise the declared schema boundary. Human attribution
strings do not authenticate a decision.
"""
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(os.environ.get("IMPACTS_AUDIT_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol.validator import SCHEMA_REGISTRY

H64 = "sha256:" + "b" * 64


def _vorgang():
    return {
        "type": "vorgang", "id": "vorgang:x",
        "application_revision": "git-tree:" + "a" * 40,
        "laufpfad": [{"arbeitsschritt_ref": "arbeitsschritt:a", "versuch": 1,
                      "status": "aktiv", "eingabe_hash": H64}],
    }


def _valid(doc) -> bool:
    return not list(SCHEMA_REGISTRY.errors("vorgang", doc))


@pytest.mark.parametrize("versuch,expected", [(1, True), (999, True), (1000, False)])
def test_versuch_is_capped_by_three_digit_layout(versuch, expected):
    doc = _vorgang()
    doc["laufpfad"][0]["versuch"] = versuch
    assert _valid(doc) is expected


@pytest.mark.parametrize("at,expected", [
    ("2026-08-30T10:00:00+02:00", True),
    ("2026-08-30T10:00:00Z", True),
    ("2026-08-30T10:00:00.5Z", True),
    ("2026-08-30T10:00:00", False),   # lexical shape requires an offset
    ("not-a-date", False),
    ("2026-08-30", False),
    ("2026-13-45T99:99:99Z", False),  # lexical pattern rejects these numeric ranges
])
def test_freigabe_at_requires_declared_lexical_shape(at, expected):
    doc = _vorgang()
    doc["laufpfad"][0].update(
        status="abgeschlossen", gewaehlte_route="freigegeben", ausgabe_hash=H64,
        freigabe={"by": "human:r", "at": at})
    assert _valid(doc) is expected
