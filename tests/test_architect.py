from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

from impacts_protocol.io import load_frontmatter_and_body

SKILL = ROOT / "02_protocol" / "impacts-architect"
SKILL_FILE = SKILL / "SKILL.md"
METHOD = ROOT / "02_protocol" / "impacts-method.md"
ONTOLOGY = ROOT / "02_protocol" / "ontology.md"
PROTOCOL_ROUTER = ROOT / "02_protocol" / "CONTEXT.md"
CAPABILITIES = ROOT / "02_protocol" / "capabilities.md"
FORM_SELECTION = SKILL / "references/formwahl.md"
GERMAN_GUIDE = ROOT / "02_protocol" / "translations" / "de.md"
LINK = re.compile(r"\]\(([^)]+)\)")


def _body() -> str:
    _, body = load_frontmatter_and_body(SKILL_FILE)
    return body


def _form_selection_text() -> str:
    return FORM_SELECTION.read_text(encoding="utf-8").lower()


def test_public_form_selection_is_the_operative_home_without_private_dependencies():
    text = FORM_SELECTION.read_text(encoding="utf-8")
    assert "## Select the form" in text
    assert "## Native topology and boundaries" in text
    assert all('docs/' not in target for target in LINK.findall(text))


def test_skill_routes_form_selection_to_its_public_authority():
    targets = LINK.findall(SKILL_FILE.read_text(encoding="utf-8"))
    reference = "references/formwahl.md"
    assert any(target.startswith(reference) for target in targets)
    assert (SKILL_FILE.parent / reference).resolve() == FORM_SELECTION
    text = FORM_SELECTION.read_text(encoding="utf-8")
    for heading in ("Work report before proposing a tree", "Composition", "Native topology and boundaries", "Tooling stop", "Knowledge Walk"):
        assert f"## {heading}\n" in text


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
    assert "materially redesigning work from an intended result" in description
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


def test_umbrella_routes_independent_pipelines_with_core_walks_when_selected():
    body = _body()
    topology = body[body.index("## Topology path") : body.index("## Build mode")]
    umbrella = next(line for line in topology.splitlines() if line.startswith("For an Umbrella"))

    assert "multiple independent Pipelines" in umbrella
    assert "selected Core Applications use their Process Walks" in umbrella
    assert "child forms" not in umbrella


def test_form_selection_reference_requires_native_topology_and_no_initial_tooling():
    text = FORM_SELECTION.read_text(encoding="utf-8")
    for phrase in (
        "Root router -> Domain router -> Fact home -> Source",
        "not empty categories",
        "require no new script",
        "three representative questions",
    ):
        assert phrase in text


def test_form_selection_reference_requires_work_report_before_tree_proposal():
    text = FORM_SELECTION.read_text(encoding="utf-8")
    assert text.index("## Work report before proposing a tree") < text.index("## Native topology and boundaries")
    report = text[text.index("## Work report before proposing a tree") : text.index("## Native topology and boundaries")]

    report = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", report)
    for field in (
        "Observed units that grow or repeat",
        "Selected existing forms and their rationale",
        "Explicitly deferred forms",
        "Smallest populated starting home",
    ):
        assert field in report
    assert "not a repository artifact" in report


def test_form_selection_reference_does_not_promote_composition_to_umbrella():
    text = FORM_SELECTION.read_text(encoding="utf-8")
    composition = text[text.index("## Composition") : text.index("## Native topology and boundaries")]

    assert "Record Library plus Knowledge Bundle alone is not an Umbrella" in composition
    assert "several independent Pipelines already exist" in composition
    assert "Other forms compose without one" in composition
    assert "When Core contracts are selected, only Pipelines become Applications" in composition
    assert "each selected Pipeline is exactly one Application" in composition
    assert "Nur eine Pipeline wird als Application gebaut" not in composition
    assert "Kindformen" not in composition


def test_form_selection_reference_requires_table_first_and_earned_splits():
    text = FORM_SELECTION.read_text(encoding="utf-8")
    topology = text[text.index("## Native topology and boundaries") : text.index("## Tooling stop")]

    assert "sharing a lifecycle" in topology
    assert "one fact file or table" in topology
    for criterion in ("independent query", "independent change", "its own evidence", "its own relationships"):
        assert criterion in topology
    assert "qualifying criterion for each split" in topology


def test_form_selection_reference_binds_reported_claims_to_source_artifacts():
    text = FORM_SELECTION.read_text(encoding="utf-8")
    topology = text[text.index("## Native topology and boundaries") : text.index("## Tooling stop")]

    assert "`reported`" in topology
    assert "preserved handover or source artifact" in topology
    assert "source register is a router or index" in topology
    assert "not a replacement for the actual artifact" in topology


def test_skill_routes_work_report_once_before_mode_selection():
    body = _body()
    selection = body[body.index("## Form selection") : body.index("## Choose a mode")]
    assert "work-report recipe" in selection
    assert "before proposing a tree" in selection.lower()
    assert "formwahl.md" in selection
    assert body.count("work-report recipe") == 1
    assert "observed growing/repeating units" not in body


def test_restructure_finds_all_icm_forms_not_only_applications():
    body = _body()
    restructure = body[body.index("## Restructure mode") : body.index("## Import mode")]
    assert "hidden forms" in restructure


def test_restructure_classifies_customer_instances_into_records():
    body = _body()
    restructure = body[body.index("## Restructure mode") : body.index("## Import mode")]
    assert "references/formwahl.md#native-topologie-und-schnitt" in restructure
    record_row = next(line for line in FORM_SELECTION.read_text().splitlines() if "Continuing business instances" in line)
    assert "Authoritative source system or maintained `records/`; runs bind excerpts" in record_row


def test_validate_scope_excludes_non_process_knowledge_topology():
    body = _body()
    invariants = body[body.index("## Invariants") : body.index("## Form selection")]

    assert "Applications and Vorgänge" in invariants
    assert "not non-process knowledge topology" in invariants


def test_knowledge_walk_is_limited_to_records_or_domain_foundations():
    body = _body()
    walk = body[body.index("## Walk test") : body.index("## Guardrails")]

    assert "only when the topology uses `records/` or domain `grundlagen/`" in walk


def test_build_mode_runs_the_seven_phases_in_order():
    body = _body()
    build = body[body.index("## Build mode") : body.index("## Restructure mode")]
    positions = [build.index(phase) for phase in ("Identify", "Minimize", "Perfect", "Augment", "Construct", "Test", "Scale")]

    assert positions == sorted(positions)


def test_method_scopes_process_phases_and_optional_core_procedures():
    text = METHOD.read_text(encoding="utf-8")
    before_identify = text[: text.index("## Identify")]

    assert "seven phases" in before_identify
    assert "guide selected process work" in before_identify
    assert "technical procedures apply when choosing Core Application/Run contracts" in before_identify
    assert "other non-process forms do not enter Identify" in before_identify


def test_result_first_setup_has_one_authoritative_method_home_and_preserves_boundaries():
    text = METHOD.read_text(encoding="utf-8")
    section = text[
        text.index("## Reverse-engineer a product or service") :
        text.index("## Compose an Arbeitsschritt")
    ]

    for phrase in (
        "before a form or executor is selected",
        "job boundary, order, handoff, wait, executor, acceptance or decision authority",
        "The observed process is evidence, not the default target",
        "Setup does not supply their authority",
        "next discriminating evidence action",
        "source existence, access, technical readiness and allowed use separate",
        "no structural change is warranted",
        "Complete the required backward trace under capture's completion condition",
        "preserve bound definitions and inputs",
    ):
        assert phrase in section
    for target in (
        "ontology.md#evidence-and-obligations",
        "#market-relationships",
        "ontology.md#author-or-change",
        "capabilities.md#data-governance",
        "#reviewed-correction",
    ):
        assert target in LINK.findall(section)
    assert text.count("Setup does not supply their authority") == 1


def test_capture_form_selection_skill_and_router_reach_result_first_setup_without_core():
    method = METHOD.read_text(encoding="utf-8")
    capture = method[method.index("## Capture business meaning") : method.index("## Market relationships")]
    form = FORM_SELECTION.read_text(encoding="utf-8")
    skill = _body()
    router = PROTOCOL_ROUTER.read_text(encoding="utf-8")

    assert "before selecting a form or executor" in capture
    assert "does not silently reopen the design" in capture
    assert "work is being set up or materially redesigned" in form
    assert "This derivation can precede an established repeatable result" in form
    report = form[form.index("## Work report before proposing a tree") : form.index("## Composition")]
    assert report.index("derive a provisional result boundary") < report.index("Selected existing forms")
    skill_selection = skill[skill.index("## Form selection") : skill.index("## Choose a mode")]
    assert "does not require an established Pipeline or Build mode" in skill_selection
    assert skill_selection.index("derive the intended result") < skill_selection.index("complete the work-report recipe")
    build = skill[skill.index("## Build mode") : skill.index("## Restructure mode")]
    assert "work being set up or materially redesigned from an intended result" in build
    route = next(line for line in router.splitlines() if "materially redesigned" in line)
    assert "Reverse-engineer a product or service" in route
    assert "Market relationships" in route
    assert "Author or change" in route


def test_german_guide_carries_result_first_meaning_and_scope_limits():
    text = GERMAN_GUIDE.read_text(encoding="utf-8")

    for phrase in (
        "### Arbeit vom Ergebnis her einrichten oder neu gestalten",
        "bevor eine Form oder ein Ausführender gewählt",
        "Der beobachtete Ablauf ist Evidenz und nicht automatisch der Zielablauf",
        "Die Einrichtung erteilt dafür keine Befugnis",
        "nächste unterscheidende Evidenzhandlung",
        "vorgesehenen Verwendungszweck",
        "keine strukturelle Änderung nötig",
        "erforderliche Rückwärtsableitung nach der Abschlussbedingung der Aufnahme vollständig",
        "gebundene Definitionen und Eingaben erhalten",
        "Reine Aufnahme bleibt Aufnahme",
    ):
        assert phrase in text


def test_result_first_setup_adds_no_oracle_or_morphological_routine():
    public_protocol = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (METHOD, PROTOCOL_ROUTER, SKILL_FILE, FORM_SELECTION, GERMAN_GUIDE)
    ).lower()

    assert "oracle" not in public_protocol
    assert "morpholog" not in public_protocol


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
    assert "[Capability contract](capabilities.md)" in method
    assert "[Capability contract](../capabilities.md)" in skill


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


def test_ontology_example_is_reachable_from_the_authoritative_instruction():
    ontology = ROOT / "02_protocol/ontology.md"
    example = SKILL / "references/datenbezug.md"
    target = "impacts-architect/references/datenbezug.md#vom-katalog-über-die-pipeline-zum-ausgefüllten-angebot"
    assert target in LINK.findall(ontology.read_text(encoding="utf-8"))
    assert (ontology.parent / target.split("#", 1)[0]).resolve() == example
    assert "## From catalog through pipeline to a filled offer" in example.read_text(encoding="utf-8")


def test_skill_names_the_core_commands():
    body = _body()

    for command in ("impacts template", "impacts validate", "impacts hash", "git rev-parse HEAD:applications/"):
        assert command in body, command


def test_build_mode_requires_role_specific_context_setup_completion():
    body = _body()
    build = body[body.index("## Build mode") : body.index("## Restructure mode")]

    assert "Build mode is incomplete until every Hauptprozess, Teilprozess and Arbeitsschritt" in build
    assert "localized setup-completion section" in build
    assert "../impacts-method.md#maintain-agent-instructions" in build
    assert "this review does not execute an Arbeitsschritt or establish readiness" in build
    assert "Test phase's responsible harness exercises" in build
    assert "Never require" not in build and "never exercise" not in build


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
    assert {"owner", "frequency", "touchpoint", "evidence_status"} <= set(metadata)
    assert "Current workflow" in body


def test_knowledge_walk_runs_each_question_in_a_fresh_session_without_cumulative_dialog():
    text = _form_selection_text()
    assert "each question" in text and "fresh session" in text
    assert "no cumulative dialogue" in text


def test_knowledge_walk_budget_is_per_question_payload_only_and_reports_measurement_limits():
    text = _form_selection_text()
    assert "per question" in text
    assert "8,000" in text
    assert "workspace/customer payload" in text
    assert "model, system, tool and harness tokens separately" in text
    assert "not topology payload" in text
    assert "payload tokenizer count cannot be isolated" in text
    assert "bytes/words" in text
    assert "do not claim an exact token pass" in text


def test_knowledge_walk_allows_exact_file_reads_but_blocks_shell_discovery():
    text = _form_selection_text()
    walk = text[text.index("## knowledge walk") :]

    for phrase in (
        "root router",
        "at most two further routers",
        "direct read-only access",
        "file tool",
        "output of an explicit path",
        "read content is never executed as a command",
        "revision,",
        "hash,",
        "byte and",
        "word checks",
        "separately as measurement-harness work",
    ):
        assert phrase in walk
    assert (
        "web, shell discovery, full scans, domain execution, graph scripts and internal mandate material "
        "remain excluded"
    ) in walk
    assert "bash" not in walk


def test_knowledge_walk_requires_question_scoped_start_links_and_hard_stop():
    text = _form_selection_text()
    assert "each question path names its start" in text
    assert "only the explicit links needed for that question" in text
    assert "a clear stop condition" in text


def test_knowledge_walk_does_not_load_optional_depth_or_exhaust_outgoing_links():
    text = _form_selection_text()
    assert "optional depth is not loaded by default" in text
    assert "do not exhaust outgoing links" in text


def test_empty_collections_use_an_authoritative_router_null_state_without_placeholders():
    text = _form_selection_text()
    assert "responsible router" in text
    assert "explicit authoritative empty state" in text
    assert "do not create an empty category" in text
    assert "merely to make absence clickable" in text


def test_router_replaces_empty_null_state_with_links_and_walk_can_stop_there():
    text = _form_selection_text()
    assert "once entries exist" in text
    assert "replace or extend" in text
    assert "empty state with direct links" in text
    assert "knowledge walk may stop at an explicit empty state" in text


def test_method_requires_direct_intent_routes_without_search_or_guessing():
    text = METHOD.read_text(encoding="utf-8")
    section = text[text.index("## Load context locally first") : text.index("## Where the context lives")]

    for phrase in (
        "states the selection condition",
        "directly links the next responsible router",
        "names or links the completion check",
        "surface actually used by the consumer",
        "no repository scan, filename guessing or model memory",
        "do not exhaust outgoing links",
    ):
        assert phrase in section
    assert "search and broader inventory are diagnosis" in section.lower()


def test_protocol_router_sends_context_delivery_and_efficiency_questions_directly_to_method():
    text = PROTOCOL_ROUTER.read_text(encoding="utf-8")
    row = next(
        line
        for line in text.splitlines()
        if line.startswith("|") and "#load-context-locally-first" in line
    )

    for target in (
        "impacts-method.md#load-context-locally-first",
        "ontology.md#use",
        "capabilities.md#snapshot-und-herkunftsnachweis",
        "../README.md#trust-and-security-boundaries",
        "impacts-method.md#test",
    ):
        assert f"]({target})" in row
    assert "only the conditional targets whose named condition applies" in text
    assert "read that bounded set together" in text


def test_ontology_use_owns_link_meanings_while_method_points_to_it():
    method = METHOD.read_text(encoding="utf-8")
    section = method[method.index("## Load context locally first") : method.index("## Where the context lives")]
    ontology = ONTOLOGY.read_text(encoding="utf-8")
    use = ontology[ontology.index("## Use") : ontology.index("## Domain definition pattern")]

    for meaning in (
        "Folder containment means membership",
        "`einstieg_ref` and `routen` mean execution order",
        "router link",
        "domain relationship",
        "domain key connects record instances",
        "declared input or handoff",
        "route governs execution",
        "source authority",
    ):
        assert meaning in use
        assert meaning not in section
    assert "establishes none of the other conditions" in use
    assert "ontology.md#use" in section
    assert "same representative questions and source state" in section
    assert "comparable model and harness conditions" in section


def test_protocol_router_partitions_maintenance_from_route_use_and_diagnosis():
    text = PROTOCOL_ROUTER.read_text(encoding="utf-8")
    maintenance = next(
        line
        for line in text.splitlines()
        if line.startswith("|") and "#maintain-agent-instructions" in line
    )
    route_use = next(line for line in text.splitlines() if "#load-context-locally-first" in line and line.startswith("|"))

    assert "Instruction maintenance starts at" in text
    assert "Existing route use or diagnosis starts at" in text
    assert "A mixed task maintains the instruction first, then exercises the route" in text
    for phrase in ("route wording", "instruction behavior"):
        assert phrase in maintenance
        assert phrase not in route_use
    for phrase in ("existing route", "projection", "missing linked or delivered material", "context-efficiency claim"):
        assert phrase in route_use
        assert phrase not in maintenance


def test_protocol_router_sends_setup_before_bounded_workstep_composition():
    text = PROTOCOL_ROUTER.read_text(encoding="utf-8")
    compose = next(
        line
        for line in text.splitlines()
        if line.startswith("| Workstep prompt")
        and "#compose-an-arbeitsschritt" in line
    )
    setup = next(
        line
        for line in text.splitlines()
        if line.startswith("|") and "#reverse-engineer-a-product-or-service" in line
    )

    assert "for an already-bounded workstep" in compose
    assert "before form or executor selection" in setup
    assert text.index(setup) < text.index(compose)


def test_market_route_sends_new_meaning_to_author_or_change():
    text = PROTOCOL_ROUTER.read_text(encoding="utf-8")
    market = next(
        line
        for line in text.splitlines()
        if line.startswith("| Market structure") and "#market-relationships" in line
    )

    assert "new or changed offering or relationship meaning" in market
    assert "](ontology.md#author-or-change)" in market


def test_context_selection_applies_inputs_and_exclusions_before_any_material_read():
    text = METHOD.read_text(encoding="utf-8")
    section = text[text.index("## Load context locally first") : text.index("## Where the context lives")]

    assert "before reading task material" in section.lower()
    assert "declared inputs, direct links and explicit exclusions" in section
    assert "Batch reads, searches and prior artifacts obey the same boundary" in section

    compose = text[text.index("## Compose an Arbeitsschritt") : text.index("## Work from prerequisites")]
    assert "](#load-context-locally-first)" in compose
    assert "batch reads, searches and prior artifacts" in compose


def test_form_selection_states_file_orchestration_applicability_boundary():
    text = FORM_SELECTION.read_text(encoding="utf-8")
    selection = text[text.index("## Select the form") : text.index("## Work report before proposing a tree")]

    assert "Human review belongs only at an identified" in selection
    assert "Core has one sequential `laufpfad`" in selection
    for unsupported_runtime in (
        "concurrent-user queues",
        "runtime state isolation",
        "real-time multi-agent messaging",
        "undeclared model-selected branching",
    ):
        assert unsupported_runtime in selection
