import json
from pathlib import Path

from jsonschema import Draft202012Validator
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
        "type": "vorgang",
        "id": "vorgang:video-001",
        "application_revision": "git-tree:" + "a" * 40,
        "laufpfad": [
            {
                "arbeitsschritt_ref": "arbeitsschritt:thema",
                "versuch": 1,
                "status": "aktiv",
                "eingabe_hash": "sha256:" + "b" * 64,
            }
        ],
    }

    validator = schema_validator("vorgang")
    assert list(validator.iter_errors(document)) == []

    document["hauptprozess_ref"] = "hauptprozess:video"
    assert list(validator.iter_errors(document))
