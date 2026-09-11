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
    "application": ("Tree", "Rules", "Example"),
    "hauptprozess": (
        "Relevant environment",
        "Value flow",
        "Objective",
        "Touchpoints",
        "Automation boundary",
        "Path to the result",
        "Throughput",
        "Bottleneck",
    ),
    "teilprozess": ("Contribution", "Leading indicator"),
    "arbeitsschritt": (
        "One job",
        "Inputs",
        "Excluded context",
        "Processing",
        "Outputs",
        "Check",
        "Human check",
    ),
    "vorgang": ("Subject", "Progress"),
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


def test_application_template_is_the_tree_schablone():
    text = (TEMPLATES / "application.md").read_text(encoding="utf-8")

    assert not text.startswith("---")
    assert "applications/<hauptprozess>/" in text
    assert "<teilprozess>/" in text and "<arbeitsschritt>/" in text
    for kind in ("hauptprozess", "teilprozess", "arbeitsschritt", "vorgang"):
        assert f"impacts template {kind}" in text
    assert "hauptprozess/" not in text.replace("<hauptprozess>/", "")
    assert "teilprozesse/" not in text and "arbeitsschritte/" not in text


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


def test_workstep_template_exposes_only_the_local_capability_call():
    _, body = load_frontmatter_and_body(TEMPLATES / "arbeitsschritt.md")

    for field in (
        "Aufruf-ID",
        "Capability-Pfad",
        "Capability-Revision",
        "Operation",
        "erwartete Ausgabe",
        "Mindestprüfung",
    ):
        assert field in body
    assert "Parameterschema" not in body


def test_workstep_template_materializes_stable_inputs_with_provenance():
    _, body = load_frontmatter_and_body(TEMPLATES / "arbeitsschritt.md")

    inputs = body[body.index("## Inputs") : body.index("## Excluded context")]
    assert "harness materializes these bytes under `input/`" in inputs
    assert "*-herkunft.md" in inputs


def test_generated_workstep_routes_ontology_and_binds_document_blank():
    body = template_text("arbeitsschritt")
    assert "02_protocol/ontology.md" in body
    assert "document blanks outside the Application; their live links do not bind them" in body
    assert "Fill an output copy of the bound document blank" in body
    assert "Preserve current input bytes" in body
