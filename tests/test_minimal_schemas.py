import json
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "02_protocol" / "schemas"


def _schemas() -> dict[str, dict]:
    return {
        path.name.removesuffix(".schema.json"): json.loads(
            path.read_text(encoding="utf-8")
        )
        for path in SCHEMAS.glob("*.schema.json")
    }


def schema_validator(name: str) -> Draft202012Validator:
    schemas = _schemas()
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema))
        for schema in schemas.values()
    )
    return Draft202012Validator(schemas[name], registry=registry)


def test_exactly_five_schemas_exist():
    assert set(_schemas()) == {
        "leistung",
        "hauptprozess",
        "teilprozess",
        "arbeitsschritt",
        "vorgang",
    }


def test_all_schemas_conform_to_the_draft_2020_12_meta_schema():
    for schema in _schemas().values():
        Draft202012Validator.check_schema(schema)


def test_hauptprozess_embeds_idless_leistung():
    document = {
        "type": "hauptprozess",
        "id": "hauptprozess:video",
        "leistung": {
            "ergebnis": "Veröffentlichtes Video",
            "kennzahl": "Durchlaufzeit",
            "abnahme": ["Video veröffentlicht"],
        },
        "einstieg_ref": "arbeitsschritt:thema",
    }

    assert list(schema_validator("hauptprozess").iter_errors(document)) == []


def test_embedded_leistung_rejects_identity():
    document = {
        "ergebnis": "Veröffentlichtes Video",
        "kennzahl": "Durchlaufzeit",
        "abnahme": ["Video veröffentlicht"],
        "id": "leistung:video",
    }

    assert list(schema_validator("leistung").iter_errors(document))


def test_workstep_contract_owns_routes():
    document = {
        "type": "arbeitsschritt",
        "id": "arbeitsschritt:thema",
        "eingaben": ["input/auftrag.md"],
        "ausgaben": ["output/thema.md"],
        "pruefung": "Thema ist freigegeben",
        "gate": "human",
        "routen": {
            "freigegeben": "arbeitsschritt:skript",
            "abgelehnt": "end:auftrag-abgelehnt",
        },
        "customer_touchpoint": "sacred",
    }

    assert list(schema_validator("arbeitsschritt").iter_errors(document)) == []


def test_workstep_paths_must_be_normalized_and_stay_in_their_surface():
    document = {
        "type": "arbeitsschritt",
        "id": "arbeitsschritt:thema",
        "eingaben": ["input/auftrag.md"],
        "ausgaben": ["output/thema.md"],
        "pruefung": "Thema ist vollständig",
        "routen": {"fertig": "end:fertig"},
    }
    validator = schema_validator("arbeitsschritt")

    for invalid in (
        "input/../auftrag.md",
        "input/./auftrag.md",
        "input//auftrag.md",
        "input/bad\nname.md",
    ):
        document["eingaben"] = [invalid]
        assert list(validator.iter_errors(document)), invalid


def test_vorgang_uses_only_revision_and_laufpfad_for_process_state():
    document = {
        "type": "vorgang", "protocol": "v0.4.0",
        "id": "vorgang:video-001",
        "hauptprozess_revision": "git-tree:" + "a" * 40,
        "laufpfad": [
            {
                "arbeitsschritt_ref": "arbeitsschritt:thema",
                "nummer": 1,
                "status": "aktiv",
                "gelesen": [{"ablage": "synthetic", "schluessel": "key", "sha256": "sha256:" + "b" * 64}],
            }
        ],
    }

    validator = schema_validator("vorgang")
    assert list(validator.iter_errors(document)) == []

    document["hauptprozess_ref"] = "hauptprozess:video"
    assert list(validator.iter_errors(document))


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
    """Calendar validity is the validator's job; the schema owns the lexical shape."""
    document = {
        "type": "vorgang", "protocol": "v0.4.0",
        "id": "vorgang:x",
        "hauptprozess_revision": "git-tree:" + "a" * 40,
        "laufpfad": [{
            "arbeitsschritt_ref": "arbeitsschritt:a", "nummer": 1,
            "status": "abgeschlossen", "gelesen": [{"ablage": "synthetic", "schluessel": "key", "sha256": "sha256:" + "b" * 64}],
            "gewaehlte_route": "freigegeben", "geschrieben": [{"pfad": "vorgaenge/x/a/001/output/result.md", "sha256": "sha256:" + "b" * 64}],
            "freigabe": {"by": "human:r", "at": at},
        }],
    }
    assert (not list(schema_validator("vorgang").iter_errors(document))) is expected


def _workstep(routen, **over):
    document = {"type": "arbeitsschritt", "id": "arbeitsschritt:a",
                "eingaben": ["input/a.md"], "ausgaben": ["output/b.md"],
                "pruefung": "x ist y", "routen": routen}
    document.update(over)
    return document


@pytest.mark.parametrize("routen", [
    {"siehe": "https://example.test/x"},   # knowledge navigation
    {"braucht": "input/a.md"},             # data dependency path
    {"gehoert": "teilprozess:x"},          # membership
])
def test_other_relation_kinds_cannot_masquerade_as_routes(routen):
    assert list(schema_validator("arbeitsschritt").iter_errors(_workstep(routen)))


def test_route_syntax_cannot_masquerade_as_data_dependency():
    document = _workstep({"fertig": "end:fertig"}, eingaben=["arbeitsschritt:x"])
    assert list(schema_validator("arbeitsschritt").iter_errors(document))
