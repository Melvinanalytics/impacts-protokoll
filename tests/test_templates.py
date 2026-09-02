from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol.cli import main
from impacts_protocol.io import load_frontmatter_and_body
from impacts_protocol.generator import TEMPLATE_KINDS, template_text
from impacts_protocol.validator import SCHEMA_REGISTRY

TEMPLATES = ROOT / "02_protocol" / "templates"
SCHEMAS = ROOT / "02_protocol" / "schemas"
SCHEMA_KINDS = ("hauptprozess", "teilprozess", "arbeitsschritt", "vorgang")
SECTIONS = {
    "application": ("Markttopologie", "Wertfluss", "Zielgröße", "Touchpoints", "Automationsgrenze"),
    "hauptprozess": ("Weg zur Leistung", "Durchsatz", "Engpass"),
    "teilprozess": ("Beitrag", "Frühindikator"),
    "arbeitsschritt": (
        "Ein Job",
        "Eingaben",
        "Nicht laden",
        "Verarbeitung",
        "Ausgaben",
        "Prüfung",
        "Human Check",
    ),
    "vorgang": ("Betreff", "Stand"),
}


def test_template_kinds_are_the_five_core_objects():
    assert TEMPLATE_KINDS == ("application", "hauptprozess", "teilprozess", "arbeitsschritt", "vorgang")


@pytest.mark.parametrize("kind", SCHEMA_KINDS)
def test_template_frontmatter_names_every_schema_property(kind):
    metadata, _ = load_frontmatter_and_body(TEMPLATES / f"{kind}.md")
    schema = json.loads((SCHEMAS / f"{kind}.schema.json").read_text(encoding="utf-8"))

    assert set(metadata) == set(schema["properties"])


@pytest.mark.parametrize("kind", SCHEMA_KINDS)
def test_template_frontmatter_is_a_valid_schema_instance(kind):
    metadata, _ = load_frontmatter_and_body(TEMPLATES / f"{kind}.md")

    assert list(SCHEMA_REGISTRY.errors(kind, metadata)) == []


def test_application_template_router_carries_only_type():
    metadata, _ = load_frontmatter_and_body(TEMPLATES / "application.md")

    assert metadata == {"type": "application"}


@pytest.mark.parametrize("kind", sorted(SECTIONS))
def test_template_body_names_its_method_sections(kind):
    _, body = load_frontmatter_and_body(TEMPLATES / f"{kind}.md")

    for section in SECTIONS[kind]:
        assert section in body, f"{kind} template lacks section {section!r}"


def test_cli_template_prints_the_packaged_text():
    output = StringIO()

    with redirect_stdout(output):
        exit_code = main(["template", "arbeitsschritt"])

    assert exit_code == 0
    assert output.getvalue() == template_text("arbeitsschritt")
    assert output.getvalue() == (TEMPLATES / "arbeitsschritt.md").read_text(encoding="utf-8")


def test_cli_template_rejects_unknown_kind():
    with pytest.raises(SystemExit) as error:
        main(["template", "hauptprozesse"])

    assert error.value.code == 2
