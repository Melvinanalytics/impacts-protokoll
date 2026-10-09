from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from impacts_protocol.cli import main
from impacts_protocol.io import load_frontmatter_and_body
from impacts_protocol.generator import CLI_TEMPLATE_KINDS, TEMPLATE_KINDS, template_text
from impacts_protocol.validator import SCHEMA_REGISTRY

TEMPLATES = ROOT / "02_protocol" / "templates"
SCHEMAS = ROOT / "02_protocol" / "schemas"
SCHEMA_KINDS = ("hauptprozess", "teilprozess", "arbeitsschritt", "vorgang")
SECTIONS = {
    "application": ("Tree", "Rules", "Example"),
    "hauptprozess": (
        "Result and scope",
        "Relevant environment",
        "Value flow",
        "Objective",
        "Touchpoints",
        "Automation boundary",
        "Path to the result",
        "Throughput",
        "Bottleneck",
        "Setup completion",
    ),
    "teilprozess": (
        "Contribution to the result",
        "Inputs and boundaries",
        "Workstep composition",
        "Setup completion",
        "Leading indicator",
    ),
    "arbeitsschritt": (
        "One job",
        "Inputs",
        "Excluded context",
        "Processing",
        "Outputs and effects",
        "Check",
        "Authority",
        "Flow",
        "Setup completion",
    ),
    "vorgang": ("Subject", "Progress"),
}


def test_template_kinds_are_the_five_core_objects():
    assert TEMPLATE_KINDS == ("application", "hauptprozess", "teilprozess", "arbeitsschritt", "vorgang")
    assert CLI_TEMPLATE_KINDS == TEMPLATE_KINDS + ("herkunft",)


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


@pytest.mark.parametrize("kind", ("hauptprozess", "teilprozess", "arbeitsschritt"))
def test_generated_definition_orders_every_structural_setup_section(kind):
    body = template_text(kind)
    headings = [f"## {section}" for section in SECTIONS[kind]]

    positions = [body.index(heading) for heading in headings]
    assert positions == sorted(positions)
    assert "Definition setup is complete when" in body
    assert "not establish execution readiness" in body


def test_subprocess_setup_supports_internal_and_terminal_consumers_without_copying_handoffs():
    body = template_text("teilprozess")

    assert "For an internal handoff, reference the producer's declared handoff" in body
    assert "At a terminal boundary, name the final recipient, accepted result and applicable end" in body
    assert "producer-output → consumer-input" not in body
    assert "do not copy its content into this subprocess contract" in body


@pytest.mark.parametrize("kind", ("hauptprozess", "teilprozess", "arbeitsschritt"))
def test_definition_setup_separates_design_review_from_execution_evidence(kind):
    body = template_text(kind)

    assert "Before the candidate commit" in body
    assert "missing or conflicting prerequisite" in body
    assert "plausible forbidden" in body
    assert "After commit, the Test phase" in body


def test_workstep_setup_keeps_waiting_separate_from_completed_routes():
    body = template_text("arbeitsschritt")

    assert "every completed outcome selects a declared workstep or end route" in body
    assert "Flow names each wait's cause and resume trigger" in body


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


def test_cli_template_help_and_errors_list_supplemental_provenance_template(capsys):
    with pytest.raises(SystemExit) as help_error:
        main(["template", "--help"])
    assert help_error.value.code == 0
    assert "herkunft" in capsys.readouterr().out

    with pytest.raises(SystemExit) as unknown_error:
        main(["template", "unknown"])
    assert unknown_error.value.code == 2
    assert "herkunft" in capsys.readouterr().err


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


def test_both_workstep_templates_link_one_copyable_provenance_authority():
    capabilities = (ROOT / "02_protocol" / "capabilities.md").read_text(encoding="utf-8")
    anchor = capabilities.index('<a id="provenance-file-example"></a>')
    end = capabilities.find("\n## ", anchor)
    example = capabilities[anchor : end if end >= 0 else None]
    provenance = (TEMPLATES / "herkunft.md").read_text(encoding="utf-8")

    locator = "02_protocol/capabilities.md#provenance-file-example"
    for body in (
        template_text("arbeitsschritt"),
        template_text("arbeitsschritt", language="de"),
    ):
        assert locator in body
        assert "*-herkunft.md" in body
        assert '<a id="provenance-file-example"></a>' not in body
        assert "../capabilities.md#provenance-file-example" not in body

    for field in (
        "input/<name>-herkunft.md",
        "input/rezeptur.md",
        "input/messwerte.csv",
        "templates/herkunft.md",
        "impacts template herkunft",
        "impacts template herkunft --language de",
        "Replace all nine field values",
        "ordinary Markdown evidence",
        "not a Core schema",
    ):
        assert field in example

    for field in (
        "Origin / locator:",
        "Source state:",
        "Acquired by / provider:",
        "Acquired at:",
        "Selection:",
        "Content-Digest",
        "Required control:",
        "Actual control:",
    ):
        assert field in provenance
    assert len([line for line in provenance.splitlines() if line.startswith("- ")]) == 9
    assert "- Provenance file:" not in example
    assert "- Local input:" not in example


@pytest.mark.parametrize(
    "language,heading",
    [("en", "# Source provenance"), ("de", "# Herkunft der Quelle")],
)
def test_cli_provenance_template_prints_exact_localized_bytes(language, heading):
    output = StringIO()
    with redirect_stdout(output):
        exit_code = main(["template", "herkunft", "--language", language])

    assert exit_code == 0
    actual = output.getvalue().encode("utf-8")
    expected = (TEMPLATES / ("de/" if language == "de" else "") / "herkunft.md").read_bytes()
    assert heading.encode("utf-8") in actual
    assert actual == expected
    assert actual == template_text("herkunft", language=language).encode("utf-8")
    assert len([line for line in output.getvalue().splitlines() if line.startswith("- ")]) == 9
    assert "- Content-Digest:" in output.getvalue()


def test_generated_workstep_routes_ontology_and_binds_document_blank():
    body = template_text("arbeitsschritt")
    assert "02_protocol/ontology.md" in body
    assert "document blanks outside the Application; their live links do not bind them" in body
    assert "Fill an output copy of the bound document blank" in body
    assert "02_protocol/impacts-method.md#work-from-prerequisites" in body
