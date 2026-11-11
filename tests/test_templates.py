from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import re
from urllib.parse import unquote

import pytest

ROOT = Path(__file__).resolve().parents[1]

from impacts_protocol.cli import main
from impacts_protocol.io import load_frontmatter_and_body
from impacts_protocol.generator import CLI_TEMPLATE_KINDS, TEMPLATE_KINDS, template_text
from impacts_protocol.validator import SCHEMA_REGISTRY
from tests.test_public_release import anchors

TEMPLATES = ROOT / "02_protocol" / "templates"
SCHEMAS = ROOT / "02_protocol" / "schemas"
SKILL = ROOT / "02_protocol" / "impacts-architect"
SKILL_FILE = SKILL / "SKILL.md"
METHOD = ROOT / "02_protocol" / "impacts-method.md"
PROTOCOL_ROUTER = ROOT / "02_protocol" / "CONTEXT.md"
CAPABILITIES = ROOT / "02_protocol" / "capabilities.md"
FORM_SELECTION = SKILL / "references/formwahl.md"
LINK = re.compile(r"\]\(([^)]+)\)")
SCHEMA_KINDS = ("hauptprozess", "teilprozess", "arbeitsschritt", "vorgang")
SECTIONS = {
    "hauptprozess": (
        "Result and scope",
        "Relevant environment",
        "Value flow",
        "Objective",
        "Touchpoints",
        "Automation boundary",
        "Path to the result",
        "Setup completion",
    ),
    "teilprozess": (
        "Contribution to the result",
        "Inputs and boundaries",
        "Arbeitsschritt composition",
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


def test_template_kinds_are_the_four_core_routers():
    assert TEMPLATE_KINDS == ("hauptprozess", "teilprozess", "arbeitsschritt", "vorgang")
    assert CLI_TEMPLATE_KINDS == TEMPLATE_KINDS + ("herkunft",)


@pytest.mark.parametrize("kind", SCHEMA_KINDS)
def test_template_frontmatter_names_every_schema_property(kind):
    metadata, _ = load_frontmatter_and_body(TEMPLATES / f"{kind}.md")
    schema = json.loads((SCHEMAS / f"{kind}.schema.json").read_text(encoding="utf-8"))

    assert set(metadata) == set(schema["properties"]) - ({"vorgaenger"} if kind == "vorgang" else set())


@pytest.mark.parametrize("kind", SCHEMA_KINDS)
def test_template_frontmatter_is_a_valid_schema_instance(kind):
    metadata, _ = load_frontmatter_and_body(TEMPLATES / f"{kind}.md")

    assert list(SCHEMA_REGISTRY.errors(kind, metadata)) == []


def test_tree_rules_have_one_home_and_layout_kind_is_retired():
    text = (ROOT / "02_protocol/binding.md").read_text()
    assert "## Hauptprozess tree rules" in text
    assert "hauptprozesse/<hauptprozess>/" in text
    assert not (TEMPLATES / "application.md").exists()
    assert "application" not in CLI_TEMPLATE_KINDS
    with pytest.raises(ValueError):
        template_text("application")


@pytest.mark.parametrize("path", sorted((ROOT / "02_protocol").rglob("*.md")))
def test_protocol_examples_use_domain_folders_below_stage(path):
    text = path.read_text(encoding="utf-8")
    assert not re.search(
        r"(?<![a-z0-9_<-])(?:hauptprozess|teilprozess|arbeitsschritt|teilprozesse|arbeitsschritte)/",
        text,
    ), path.relative_to(ROOT)


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
    setup_home = METHOD.read_text(encoding="utf-8") if kind == "arbeitsschritt" else body
    assert "Definition setup is complete when" in setup_home
    method = METHOD.read_text(encoding="utf-8")
    setup = method[method.index("Core setup completion establishes") : method.index("Use this maintenance path:")]
    assert "not execution readiness or the business result" in setup


def test_subprocess_setup_supports_internal_and_terminal_consumers_without_copying_handoffs():
    body = template_text("teilprozess")

    assert "For an internal handoff, reference the producer's declared handoff" in body
    assert "At a terminal boundary, name the final recipient, Leistung and applicable end" in body
    assert "producer-output → consumer-input" not in body
    assert "do not copy its content into this Teilprozess contract" in body


@pytest.mark.parametrize("kind", ("hauptprozess", "teilprozess", "arbeitsschritt"))
def test_definition_setup_separates_design_review_from_execution_evidence(kind):
    body = template_text(kind)

    assert "Before the candidate commit" in body
    assert "missing or conflicting prerequisite" in body
    assert "plausible forbidden" in body
    assert "Link the review evidence under `02_protocol/impacts-method.md#maintain-agent-instructions`" in body
    method = METHOD.read_text(encoding="utf-8")
    setup = method[method.index("Core setup completion establishes") : method.index("Use this maintenance path:")]
    assert "records observed results against that exact revision" in setup
    assert "Keep the actual review and its gaps in the linked analysis file under `analyse/`" in setup
    assert "the definition retains its test premises and expected results" in setup


def test_workstep_setup_keeps_waiting_separate_from_completed_routes():
    body = template_text("arbeitsschritt")

    assert "every completed attempt selects a declared Arbeitsschritt or end route according to its check result" in METHOD.read_text(
        encoding="utf-8"
    )
    assert "Name each wait's cause, each applicable `ausloeser`" in body


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
    binding = (ROOT / "02_protocol" / "binding.md").read_text(encoding="utf-8")
    assert "The attempt holds only `output/`; `input/` is rejected." in binding
    assert "*-herkunft.md" in inputs


def test_both_workstep_templates_link_one_copyable_provenance_authority():
    capabilities = (ROOT / "02_protocol" / "binding.md").read_text(encoding="utf-8")
    anchor = capabilities.index("### Provenance file example")
    end = capabilities.find("\n## ", anchor)
    example = capabilities[anchor : end if end >= 0 else None]
    provenance = (TEMPLATES / "herkunft.md").read_text(encoding="utf-8")

    locator = "02_protocol/binding.md#provenance-file-example"
    for body in (
        template_text("arbeitsschritt"),
        template_text("arbeitsschritt", language="de"),
    ):
        assert locator in body
        assert "*-herkunft.md" in body
        assert '<a id="provenance-file-example"></a>' not in body
        assert "../binding.md#provenance-file-example" not in body

    for field in (
        "<name>-herkunft.md",
        "grundlagen/rezeptur.md",
        "records/messwerte.csv",
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
    assert "a link to their current copy does not bind them" in METHOD.read_text(encoding="utf-8")
    assert "Fill an output copy of the bound document blank" in METHOD.read_text(encoding="utf-8")
    assert "02_protocol/binding.md#work-from-prerequisites" in body


def test_skill_frontmatter_names_the_skill():
    metadata, _ = load_frontmatter_and_body(SKILL_FILE)

    assert metadata["name"] == "impacts-architect"
    assert len(metadata["description"]) > 80


def test_domain_entry_points_reach_the_single_ontology_instruction():
    ontology = ROOT / "02_protocol/ontology.md"
    entry_points = (
        ROOT / "AGENTS.md", ROOT / "CONTEXT.md", PROTOCOL_ROUTER,
        METHOD, SKILL_FILE, FORM_SELECTION, CAPABILITIES,
    )
    assert ontology.is_file()
    for document in entry_points:
        destinations = {
            (document.parent / target.split("#", 1)[0]).resolve()
            for target in LINK.findall(document.read_text(encoding="utf-8"))
            if not target.startswith(("http://", "https://", "#"))
        }
        assert ontology in destinations, f"No direct ontology route from {document}"


def assert_link_resolves(document, target):
    path, _, fragment = target.partition("#")
    destination = (document.parent / path).resolve() if path else document
    assert destination.is_file(), f"{document} -> {target}"
    if fragment:
        assert unquote(fragment) in anchors(destination.read_text(encoding="utf-8")), target
    return destination


def test_skill_routes_form_selection_to_its_public_authority():
    targets = [
        target for target in LINK.findall(SKILL_FILE.read_text(encoding="utf-8"))
        if target.split("#", 1)[0] == "references/formwahl.md"
    ]
    assert targets
    for target in targets:
        assert assert_link_resolves(SKILL_FILE, target) == FORM_SELECTION


def test_ontology_example_is_reachable_from_the_authoritative_instruction():
    ontology = ROOT / "02_protocol/ontology.md"
    target = "impacts-architect/references/datenbezug.md#from-catalog-through-pipeline-to-a-filled-offer"
    assert target in LINK.findall(ontology.read_text(encoding="utf-8"))
    assert assert_link_resolves(ontology, target) == SKILL / "references/datenbezug.md"


def test_result_first_setup_links_its_five_authority_targets():
    text = METHOD.read_text(encoding="utf-8")
    section = text[
        text.index("## Reverse-engineer a product or service") :
        text.index("## Compose an Arbeitsschritt")
    ]
    for target in (
        "ontology.md#evidence-and-obligations",
        "#market-relationships",
        "ontology.md#author-or-change",
        "impacts-architect/references/datenumgang.md#access-routes",
        "#reviewed-correction",
    ):
        assert target in LINK.findall(section)
        assert_link_resolves(METHOD, target)

    capture = text[
        text.index("## Capture business meaning") :
        text.index("### Guided interview")
    ]
    for target in (
        "impacts-architect/references/datenumgang.md#source-descriptions",
        "binding.md#source-inputs-for-core-hauptprozesse",
    ):
        assert target in LINK.findall(capture)
        assert_link_resolves(METHOD, target)


@pytest.mark.parametrize(
    "language,workflow,measurements",
    [
        ("en", "Current workflow", ("Throughput and lead time", "Bottleneck")),
        ("de", "Ablauf heute", ("Durchsatz und Durchlaufzeit", "Engpass")),
    ],
)
def test_as_is_capture_template_parses_with_its_capture_fields(language, workflow, measurements):
    capture = SKILL / "templates" / ("de/" if language == "de" else "") / "ist-prozess.md"
    metadata, body = load_frontmatter_and_body(capture)

    assert metadata["type"] == "ist-prozess"
    assert {"owner", "frequency", "touchpoint", "evidence_status"} <= set(metadata)
    assert workflow in body
    definition = template_text("hauptprozess", language=language)
    for heading in measurements:
        assert f"## {heading}" in body
        assert f"## {heading}" not in definition


@pytest.mark.parametrize("language", ("en", "de"))
@pytest.mark.parametrize("kind,destination", (
    ("teilprozess", "hauptprozesse/forecast/quantities/CONTEXT.md"),
    ("vorgang", "vorgaenge/forecast-november/CONTEXT.md"),
))
def test_generated_definition_protocol_references_resolve_at_recorded_source(tmp_path, language, kind, destination):
    workspace = tmp_path / "customer"
    workspace.mkdir()
    # The workspace selects this exact source; generated depth must not change it.
    (workspace / "CONTEXT.md").write_text(f"Protocol source: {ROOT}\nProtocol revision: synthetic-test\n")
    generated = workspace / destination
    generated.parent.mkdir(parents=True)
    generated.write_text(template_text(kind, language=language))
    body = generated.read_text()
    references = re.findall(r"`(02_protocol/[^` ]+\.md(?:#[^` ]+)?)`", body)
    assert references
    for reference in references:
        path, _, fragment = reference.partition("#")
        source = ROOT / path
        assert source.is_file(), (generated, reference)
        if fragment:
            assert fragment in anchors(source.read_text()), (generated, reference)
    assert not LINK.findall(body), "Protocol references must resolve through the recorded source"
    if kind == "vorgang":
        assert "02_protocol/binding.md#vorgang-progress" in references
        assert not re.search(r"^\|.*`aktiv`.*\|", body, re.M)


@pytest.mark.parametrize("language,mark,stop", [
    ("en", "synthetic test case", "ask the responsible customer and open nothing"),
    ("de", "synthetischer Testfall", "den verantwortlichen Kunden fragen und nichts öffnen"),
])
def test_workspace_clearance_routes_before_real_opening(language, mark, stop):
    from impacts_protocol.generator import _template_file
    body = _template_file("workspace", language)
    shape = "hauptprozess:<slug> cleared for real work: human:<id>, <YYYY-MM-DD>, git-tree:<oid>, tested by vorgang:<id>[, ...]"
    assert shape in body
    assert mark in body and stop in body
    execution = "02_protocol/binding.md#execution"
    contract = body[body.index("\n3. "):body.index("\n5. ")]
    assert body.index(stop) < body.index(execution, body.index("3. "))
    assert len(re.findall(r"^\d+\. ", contract, re.M)) == 2
    source, fragment = execution.split("#")
    assert fragment in anchors((ROOT / source).read_text())
    assert "source repository <repository>, commit <commit>, tree git-tree:<oid>, source protocol <Fachrepo protocol pin>" in body
    assert "templates/workspace.md#tree-clearance-and-imports" in SKILL_FILE.read_text()


def test_vorgang_templates_write_every_path_workspace_relative():
    for name in ("vorgang.md", "de/vorgang.md"):
        text = (ROOT / "02_protocol" / "templates" / name).read_text(encoding="utf-8")
        paths = re.findall(r"^\s*-?\s*(?:pfad|continuation_ref):\s*(\S+)", text, flags=re.M)
        assert paths, name
        for path in paths:
            assert path.startswith(("vorgaenge/", "records/", "grundlagen/")), (name, path)
