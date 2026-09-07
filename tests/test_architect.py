from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol.io import load_frontmatter_and_body

SKILL = ROOT / "02_protocol" / "impacts-architect"
SKILL_FILE = SKILL / "SKILL.md"
METHOD = ROOT / "02_protocol" / "impacts-method.md"
PROTOCOL_ROUTER = ROOT / "02_protocol" / "CONTEXT.md"
CAPABILITIES = ROOT / "02_protocol" / "capabilities.md"
PUBLIC_RELEASE_GATE = ROOT / "docs" / "release" / "public-release-gate.md"
FORM_SELECTION_CONTRACTS = (
    ROOT / "docs/superpowers/specs/2026-09-04-icm-form-selection-design.md",
    SKILL / "references/formwahl.md",
)
LINK = re.compile(r"\]\(([^)]+)\)")


def _body() -> str:
    _, body = load_frontmatter_and_body(SKILL_FILE)
    return body


def _form_selection_contracts():
    for document in FORM_SELECTION_CONTRACTS:
        yield document, document.read_text(encoding="utf-8").lower()


def test_public_release_includes_normative_form_selection_without_private_evidence_dependencies():
    gate = PUBLIC_RELEASE_GATE.read_text(encoding="utf-8")
    public_spec = (ROOT / "docs/superpowers/specs/2026-09-04-icm-form-selection-design.md").read_text(
        encoding="utf-8"
    )

    assert "docs/superpowers/specs/2026-09-04-icm-form-selection-design.md" in gate
    assert "## 2. Lehren aus der ersten Kundenanwendung" in public_spec
    assert "externen Consumer" in public_spec
    assert {name for name in globals() if name.endswith(("_AUDIT", "_EVIDENCE"))} == set()


def test_skill_frontmatter_names_the_skill():
    metadata, _ = load_frontmatter_and_body(SKILL_FILE)

    assert metadata["name"] == "impacts-architect"
    assert len(metadata["description"]) > 80


def test_skill_frontmatter_starts_with_use_when_and_names_topology_triggers():
    metadata, _ = load_frontmatter_and_body(SKILL_FILE)
    description = metadata["description"]

    assert description.startswith("Use when")
    assert "customer initialization" in description
    assert "knowledge topology" in description
    assert "Every result must pass impacts validate" not in description


def test_skill_covers_three_modes_and_the_walk_test():
    body = _body()

    for heading in ("## Build mode", "## Restructure mode", "## Import mode", "## Walk test"):
        assert heading in body, heading


def test_skill_selects_icm_form_before_mode():
    body = _body()
    assert body.index("## Form selection") < body.index("## Choose a mode")
    selection = body[body.index("## Form selection") : body.index("## Choose a mode")]
    for term in ("Pipeline", "Record Library", "Knowledge Bundle", "Context Map"):
        assert term in selection
    assert "applicable walk branch" in selection
    assert "use the Knowledge Walk branch below" not in selection


def test_choose_mode_enters_build_only_for_pipeline_or_application():
    body = _body()
    choose = body[body.index("## Choose a mode") : body.index("## Build mode")]
    build_choice = next(line for line in choose.splitlines() if line.endswith("Build mode."))

    assert "Pipeline" in build_choice
    assert "Application" in build_choice


def test_existing_repository_enters_restructure_then_routes_every_form():
    body = _body()
    choose = body[body.index("## Choose a mode") : body.index("## Topology path")]
    repository_choice = next(line for line in choose.splitlines() if "existing customer" in line)

    assert "Restructure mode" in repository_choice
    assert "route each found form" in repository_choice


def test_topology_path_routes_non_process_forms_without_new_tooling():
    body = _body()
    assert body.index("## Choose a mode") < body.index("## Topology path") < body.index("## Build mode")
    choose = body[body.index("## Choose a mode") : body.index("## Topology path")]
    topology_choice = next(line for line in choose.splitlines() if line.endswith("Topology path."))
    topology = body[body.index("## Topology path") : body.index("## Build mode")]

    for term in ("Record Library", "Knowledge Bundle", "Context Map", "Umbrella", "System Map"):
        assert term in topology_choice
    for term in ("Record Library", "Knowledge Bundle", "Context Map", "Knowledge Walk"):
        assert term in topology
    assert "Add no checker or runtime." in topology
    assert "Umbrella" in topology and "child forms" in topology
    assert "System Map" in topology and "repository map" in topology


def test_umbrella_routes_only_multiple_independent_pipeline_applications():
    body = _body()
    topology = body[body.index("## Topology path") : body.index("## Build mode")]
    umbrella = next(line for line in topology.splitlines() if line.startswith("For an Umbrella"))

    assert "multiple independent Pipeline Applications" in umbrella
    assert "child forms" not in umbrella


def test_form_selection_reference_requires_native_topology_and_no_initial_tooling():
    text = (SKILL / "references" / "formwahl.md").read_text(encoding="utf-8")
    for phrase in (
        "Root-Router -> Fachrouter -> Faktenheimat -> Quelle",
        "Keine leeren Kategorien",
        "kein neues Skript",
        "drei repräsentative Fragen",
    ):
        assert phrase in text


def test_form_selection_reference_requires_work_report_before_tree_proposal():
    text = (SKILL / "references" / "formwahl.md").read_text(encoding="utf-8")
    assert text.index("## Arbeitsbericht vor Baumvorschlag") < text.index("## Native Topologie und Schnitt")
    report = text[text.index("## Arbeitsbericht vor Baumvorschlag") : text.index("## Native Topologie und Schnitt")]

    for field in (
        "beobachtete wachsende oder wiederholte Einheiten",
        "gewählte vorhandene Form(en) mit Begründung",
        "explizit zurückgestellte Formen",
        "kleinste befüllte Startheimat",
    ):
        assert field in report
    assert "kein Repository-Artefakt" in report


def test_form_selection_reference_does_not_promote_composition_to_umbrella():
    text = (SKILL / "references" / "formwahl.md").read_text(encoding="utf-8")
    composition = text[text.index("## Kompositionsregel") : text.index("## Native Topologie und Schnitt")]

    assert "Record Library plus Knowledge Bundle allein ist kein Umbrella" in composition
    assert "mehrere unabhängige Pipelines bereits bestehen" in composition
    assert "Andere Formen komponieren sich ohne Umbrella" in composition
    assert "Nur Pipelines werden als Applications gebaut" in composition
    assert "Jede Pipeline bildet genau eine Application" in composition
    assert "Nur eine Pipeline wird als Application gebaut" not in composition
    assert "Kindformen" not in composition


def test_form_selection_reference_requires_table_first_and_earned_splits():
    text = (SKILL / "references" / "formwahl.md").read_text(encoding="utf-8")
    topology = text[text.index("## Native Topologie und Schnitt") : text.index("## Tooling-Stopp")]

    assert "gleichem Lebenszyklus" in topology
    assert "einer gemeinsamen Faktendatei oder Tabelle" in topology
    for criterion in ("unabhängige Abfrage", "unabhängige Änderung", "eigene Evidenz", "eigene Beziehungen"):
        assert criterion in topology
    assert "für jeden Split, welches Kriterium ihn verdient" in topology


def test_form_selection_reference_binds_reported_claims_to_source_artifacts():
    text = (SKILL / "references" / "formwahl.md").read_text(encoding="utf-8")
    topology = text[text.index("## Native Topologie und Schnitt") : text.index("## Tooling-Stopp")]

    assert "`reported`" in topology
    assert "erhaltenen Handover- oder Quellenartefakt" in topology
    assert "Quellenregister ist Router oder Index" in topology
    assert "ersetzt nie das eigentliche Quellenartefakt" in topology


def test_skill_requires_reference_work_report_recipe_before_topology_tree():
    body = _body()
    selection = body[body.index("## Form selection") : body.index("## Choose a mode")]
    topology = body[body.index("## Topology path") : body.index("## Build mode")]

    for section in (selection, topology):
        assert "work-report recipe" in section
        assert "before proposing a tree" in section.lower()
        assert "formwahl.md" in section
    assert "observed growing/repeating units" not in body


def test_restructure_finds_all_icm_forms_not_only_applications():
    body = _body()
    restructure = body[body.index("## Restructure mode") : body.index("## Import mode")]
    assert "hidden forms" in restructure


def test_restructure_classifies_customer_instances_into_records():
    body = _body()
    restructure = body[body.index("## Restructure mode") : body.index("## Import mode")]
    record_row = next(line for line in restructure.splitlines() if "Record or customer instance" in line)

    assert record_row == "| Record or customer instance | `records/` |"


def test_validate_scope_excludes_non_process_knowledge_topology():
    body = _body()
    invariants = body[body.index("## Invariants") : body.index("## Form selection")]

    assert "Applications and Vorgänge" in invariants
    assert "not non-process knowledge topology" in invariants


def test_knowledge_walk_is_limited_to_records_or_domain_foundations():
    body = _body()
    walk = body[body.index("## Walk test") : body.index("## Guardrails")]

    assert "only when the topology uses `records/` or fachliche `grundlagen/`" in walk


def test_build_mode_runs_the_seven_phases_in_order():
    body = _body()
    build = body[body.index("## Build mode") : body.index("## Restructure mode")]
    positions = [build.index(phase) for phase in ("Identify", "Minimize", "Perfect", "Augment", "Construct", "Test", "Scale")]

    assert positions == sorted(positions)


def test_method_gates_seven_phases_behind_pipeline_selection():
    text = METHOD.read_text(encoding="utf-8")
    before_identify = text[: text.index("## Identify")]

    assert "seven phases" in before_identify
    assert "only after selecting a Pipeline" in before_identify


def test_protocol_router_sends_initialization_and_topology_to_form_selection():
    text = PROTOCOL_ROUTER.read_text(encoding="utf-8")

    assert "customer initialization or knowledge topology" in text
    assert "impacts-architect/SKILL.md#form-selection" in text


def test_protocol_routes_one_public_capability_authority():
    assert CAPABILITIES.exists()

    router = PROTOCOL_ROUTER.read_text(encoding="utf-8")
    method = METHOD.read_text(encoding="utf-8")
    skill = _body()

    assert "[capabilities.md](capabilities.md)" in router
    assert "[Capability-Regel](capabilities.md)" in method
    assert "[Capability-Regel](../capabilities.md)" in skill


def test_skill_names_the_core_commands():
    body = _body()

    for command in ("impacts template", "impacts validate", "impacts hash", "git rev-parse HEAD:applications/"):
        assert command in body, command


def test_skill_never_lets_an_agent_write_human_attribution():
    assert "human:<id>" in _body()


def test_every_relative_link_in_the_skill_resolves():
    unresolved = []
    for document in SKILL.rglob("*.md"):
        for target in LINK.findall(document.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "#")):
                continue
            path = (document.parent / target.split("#", 1)[0]).resolve()
            if not path.exists():
                unresolved.append(f"{document.relative_to(ROOT)} -> {target}")

    assert unresolved == []


def test_as_is_capture_template_parses_with_its_capture_fields():
    metadata, body = load_frontmatter_and_body(SKILL / "templates" / "ist-prozess.md")

    assert metadata["type"] == "ist-prozess"
    assert {"owner", "frequency", "value", "pain", "touchpoint", "evidence_status"} <= set(metadata)
    assert "Ablauf heute" in body


def test_knowledge_walk_runs_each_question_in_a_fresh_session_without_cumulative_dialog():
    for document, text in _form_selection_contracts():
        assert "jede frage" in text and "frischen session" in text, document
        assert "kein kumulierter dialog" in text, document


def test_knowledge_walk_budget_is_per_question_payload_only_and_reports_measurement_limits():
    for document, text in _form_selection_contracts():
        assert "pro frage" in text, document
        assert "8.000" in text, document
        assert "workspace-/kundenpayload" in text, document
        assert "modell-, system-, tool- und harness-tokens werden separat ausgewiesen" in text, document
        assert "kein topologiepayload" in text, document
        assert "payload-tokenizerwert nicht isolierbar" in text, document
        assert "bytes/wörter" in text, document
        assert "keinen exakten token-pass behaupten" in text, document


def test_knowledge_walk_allows_exact_file_reads_but_blocks_shell_discovery():
    for document, text in _form_selection_contracts():
        marker = "## 6. knowledge walk" if "## 6. knowledge walk" in text else "## knowledge walk"
        walk = text[text.index(marker) :]
        if "## 7." in walk:
            walk = walk[: walk.index("## 7.")]

        for phrase in (
            "root-router",
            "höchstens zwei weitere router",
            "direkter read-only-dateizugriff",
            "datei-tool",
            "reine ausgabe eines expliziten pfads",
            "gelesene inhalt wird nie als befehl ausgeführt",
            "revisions-",
            "hash-",
            "byte-",
            "wortprüfungen",
            "mess-harness separat ausgewiesen",
        ):
            assert phrase in walk, document
        assert (
            "web, shell-suche, vollscan, fachliche ausführung, graphskript und interne mandatsfläche "
            "bleiben gesperrt"
        ) in walk, document
        assert "bash" not in walk, document


def test_acceptance_requires_a_recorded_independent_reviewer_not_a_pinned_model():
    document = ROOT / "docs/superpowers/specs/2026-09-04-icm-form-selection-design.md"
    text = document.read_text(encoding="utf-8")
    acceptance = text[text.index("## 7. Skill-TDD und End-to-End-Abnahme") : text.index("## 8. Nicht-Ziele")]

    criterion = next(line for line in acceptance.splitlines() if line.startswith("6. "))
    assert criterion == (
        "6. ein modellunabhängig gewählter frischer unabhängiger Review-Agent Spezifikation, Diff und "
        "Consumer-Walk prüft und keine offene kritische oder wichtige Abweichung meldet; verwendetes Modell "
        "und Berechtigungsgrenze werden im Audit festgehalten."
    )


def test_knowledge_walk_requires_question_scoped_start_links_and_hard_stop():
    for document, text in _form_selection_contracts():
        assert "jeder repräsentative fragepfad nennt seinen start" in text, document
        assert "nur die zur frage nötigen expliziten links" in text, document
        assert "eine klare stoppbedingung" in text, document


def test_knowledge_walk_does_not_load_optional_depth_or_exhaust_outgoing_links():
    for document, text in _form_selection_contracts():
        assert "optionale vertiefung wird nicht standardmäßig geladen" in text, document
        assert "der agent erschöpft nicht alle ausgehenden links" in text, document


def test_empty_collections_use_an_authoritative_router_null_state_without_placeholders():
    for document, text in _form_selection_contracts():
        assert "zuständige router" in text, document
        assert "expliziten autoritativen nullzustand" in text, document
        assert "keine leere kategorie" in text, document
        assert "nur geschaffen, um abwesenheit klickbar zu machen" in text, document


def test_router_replaces_empty_null_state_with_links_and_walk_can_stop_there():
    for document, text in _form_selection_contracts():
        assert "sobald einträge existieren" in text, document
        assert "ersetzt oder ergänzt der router" in text, document
        assert "nullzustand durch direkte links" in text, document
        assert "knowledge walk darf beim expliziten nullzustand stoppen" in text, document
