"""One machine vocabulary, paired readable views, explicit source revisions."""
import hashlib
import importlib.util
from pathlib import Path
import re
import warnings

ROOT = Path(__file__).resolve().parents[1]

import pytest

from impacts_protocol.cli import main
from impacts_protocol.generator import CLI_TEMPLATE_KINDS, init_workspace, template_text
from impacts_protocol.io import load_frontmatter_and_body
from impacts_protocol.validator import SCHEMA_REGISTRY, validate

SPEC = importlib.util.spec_from_file_location("release_guard", ROOT / ".github/scripts/release_guard.py")
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)
PAIRS = guard.PAIRS


def test_translation_inventory_has_one_mirror_per_source_and_no_unpaired_files():
    sources, targets = zip(*PAIRS)
    assert {source for source in sources if source.startswith("02_protocol/templates/")} == {
        f"02_protocol/templates/{kind}.md" for kind in (*CLI_TEMPLATE_KINDS, "workspace")
    }
    assert {target for target in targets if target.startswith("02_protocol/translations/")} == {
        f"02_protocol/translations/{guide}.de.md"
        for guide in ("readme", "first-win", "language", "contributing")
    }
    assert len(sources) == len(set(sources))
    assert len(targets) == len(set(targets))
    marked = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "02_protocol").rglob("*.md")
        if "<!-- Translation source:" in path.read_text(encoding="utf-8")
    }
    guides = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "02_protocol/translations").rglob("*.md")
    }
    assert marked == set(targets)
    assert guides <= set(targets)


def check_translation(root: Path, source: str, target: str) -> None:
    if guard.translation_stale(root, source, target):
        warnings.warn(f"Stale translation: {target} (source: {source})", stacklevel=2)


@pytest.mark.parametrize("source,target", PAIRS)
def test_every_supported_translation_identifies_source_bytes(source, target):
    check_translation(ROOT, source, target)


def test_source_change_warns_in_suite_and_blocks_release(tmp_path, monkeypatch):
    source, target = "en.md", "de.md"
    (tmp_path / source).write_text("Current rule.\n")
    digest = hashlib.sha256((tmp_path / source).read_bytes()).hexdigest()
    (tmp_path / target).write_text(f"<!-- Translation source: {source}; sha256: {digest} -->\nMirror.\n")
    monkeypatch.setattr(guard, "PAIRS", [(source, target)])
    check_translation(tmp_path, source, target)
    guard.verify_translations(tmp_path)
    (tmp_path / source).write_text("Changed rule.\n")
    with pytest.warns(UserWarning, match="Stale translation: de.md"):
        check_translation(tmp_path, source, target)
    with pytest.raises(guard.ReleaseGuardError, match="Stale translations: de.md"):
        guard.verify_translations(tmp_path)


@pytest.mark.parametrize("marker", [None, "", "<!-- Translation source: en.md -->",
    "<!-- Translation source: en.md; sha256: invalid -->",
    f"<!-- Translation source: other.md; sha256: {'0' * 64} -->",
    f"<!-- Translation source: en.md; sha256: {'0' * 64} -->\n" * 2])
def test_invalid_or_missing_mirror_fails_suite_and_release(tmp_path, monkeypatch, marker):
    (tmp_path / "en.md").write_text("Rule.\n")
    if marker is not None:
        (tmp_path / "de.md").write_text(marker)
    monkeypatch.setattr(guard, "PAIRS", [("en.md", "de.md")])
    with pytest.raises(guard.ReleaseGuardError):
        check_translation(tmp_path, "en.md", "de.md")
    with pytest.raises(guard.ReleaseGuardError):
        guard.verify_translations(tmp_path)


@pytest.mark.parametrize("kind", ["hauptprozess", "teilprozess", "arbeitsschritt", "vorgang"])
def test_localized_templates_have_identical_machine_contracts(kind):
    en, _ = load_frontmatter_and_body(ROOT / f"02_protocol/templates/{kind}.md")
    de, _ = load_frontmatter_and_body(ROOT / f"02_protocol/templates/de/{kind}.md")
    assert list(SCHEMA_REGISTRY.errors(kind, en)) == []
    assert list(SCHEMA_REGISTRY.errors(kind, de)) == []
    assert set(en) == set(de)
    for key in set(en) - {"leistung", "ergebnis", "pruefung"}:
        assert en[key] == de[key], key
    if "leistung" in en:
        assert set(en["leistung"]) == set(de["leistung"])
        assert len(en["leistung"]["abnahme"]) == len(de["leistung"]["abnahme"])


@pytest.mark.parametrize("language,heading", [("en", "# Decide"), ("de", "# Entscheiden")])
def test_cli_language_selection_persists_and_prints_matching_template(tmp_path, capsys, language, heading):
    root = tmp_path / language
    assert main(["init", str(root), "--language", language]) == 0
    data, body = load_frontmatter_and_body(root / "CONTEXT.md")
    assert data == {"type": "workspace", "protocol": "v0.4.1"} and validate(root).valid
    assert f"Working language: {language}" in body
    init_output = capsys.readouterr().out
    assert "impacts validate" in init_output
    assert ("Nächster Schritt" if language == "de" else "Next:") in init_output
    assert main(["template", "arbeitsschritt", "--language", language]) == 0
    output = capsys.readouterr().out
    assert heading in output and "type: arbeitsschritt" in output
    assert output == template_text("arbeitsschritt", language=language)


def test_unknown_language_fails_before_creating_workspace(tmp_path):
    root = tmp_path / "unsupported"
    with pytest.raises(ValueError, match="unsupported working language"):
        init_workspace(root, language="fr")
    assert not root.exists()
    with pytest.raises(SystemExit) as error:
        main(["init", str(root), "--language", "fr"])
    assert error.value.code == 2 and not root.exists()


def test_german_template_commands_select_german_instead_of_default_english():
    for _, target in PAIRS:
        text = (ROOT / target).read_text()
        for match in re.finditer(r"impacts template (?:hauptprozess|teilprozess|arbeitsschritt|vorgang|herkunft|<art>)", text):
            assert text[match.end():].startswith(" --language de"), target


@pytest.mark.parametrize(
    "language,heading",
    [("en", "# Source provenance"), ("de", "# Herkunft der Quelle")],
)
def test_cli_selects_localized_provenance_template(language, heading, capsys):
    assert main(["template", "herkunft", "--language", language]) == 0
    assert capsys.readouterr().out == template_text("herkunft", language=language)
    assert heading in template_text("herkunft", language=language)


@pytest.mark.parametrize(
    "kind,headings",
    [
        (
            "hauptprozess",
            (
                "Ergebnis und Geltungsbereich",
                "Relevantes Umfeld",
                "Wertfluss",
                "Zielgröße und Leitplanken",
                "Kundenkontaktpunkte",
                "Automationsgrenze",
                "Weg zur Leistung",
                "Einrichtungsabschluss",
            ),
        ),
        ("teilprozess", ("Beitrag zur Leistung", "Eingaben und Grenzen", "Zusammenspiel der Arbeitsschritte", "Einrichtungsabschluss")),
        ("arbeitsschritt", ("Ein Job", "Eingaben", "Nicht laden", "Verarbeitung", "Ausgaben und Eingriffe", "Prüfung", "Befugnis", "Ablauf", "Einrichtungsabschluss")),
    ],
)
def test_german_generated_definitions_keep_role_specific_setup_sections(kind, headings):
    body = template_text(kind, language="de")
    positions = [body.index(f"## {heading}") for heading in headings]

    assert positions == sorted(positions)
    assert "Die Definitionseinrichtung ist abgeschlossen" in body
    assert "Vor dem Kandidaten-Commit" in body
    assert re.search(r"fehlend(?:e|er) oder widersprüchlich(?:e|er) Voraussetzung", body)
    assert re.search(r"plausibl(?:e|er) unzulässige", body)
    if kind != "teilprozess":
        assert "belegen weder Einsatzbereitschaft" in body or "belegen keine Einsatzbereitschaft" in body
        _assert_german_design_execution_boundary(body)


def _assert_german_design_execution_boundary(body):
    assert "Vor dem Kandidaten-Commit" in body
    assert re.search(r"fehlend(?:e|er) oder widersprüchlich(?:e|er) Voraussetzung", body)
    assert re.search(r"plausibl(?:e|er) unzulässige", body)
    assert "Nach dem Commit" in body
    assert "Harness" in body
    assert "diese Revision" in body


@pytest.mark.parametrize("kind", ("hauptprozess", "arbeitsschritt"))
def test_german_setup_boundary_rejects_missing_post_commit_harness_evidence(kind):
    body = template_text(kind, language="de")
    start = body.index("Nach dem Commit")
    broken = body[:start] + body[body.index(".", start) + 1 :]

    with pytest.raises(AssertionError):
        _assert_german_design_execution_boundary(broken)


def test_german_subprocess_preserves_terminal_and_negative_case_meaning():
    body = template_text("teilprozess", language="de")

    assert "Bei einer internen Übergabe auf die vom Producer deklarierte Übergabe" in body
    assert "An einer terminalen Grenze" in body
    assert "fehlender oder widersprüchlicher Voraussetzung" in body
    assert "plausibler unzulässiger Schlussfolgerung" in body
    assert "voraussetzungsarmen" not in body


def test_german_workstep_keeps_waiting_separate_from_completed_routes():
    body = template_text("arbeitsschritt", language="de")

    assert "jeder abgeschlossene Versuch anhand seines `pruefung`-Ergebnisses eine deklarierte Arbeitsschritt- oder Endroute wählt" in body
    assert "„Ablauf“ nennt für jedes Warten Ursache und Auslöser der Fortsetzung" in body


def test_gate_expiry_table_is_reachable_from_workstep_templates():
    """Both languages preserve gate expiry limits at the linked Waits home."""
    gate_transition = "| Human gate, check finds no decision | Apply declared escalation within its authority | Remain `wartend`, escalate and record the next `faellig`; expiry supplies no `freigabe` and selects neither `freigegeben` nor `abgelehnt` |"
    assert gate_transition in (ROOT / "02_protocol/binding.md").read_text(encoding="utf-8")
    for template in ("02_protocol/templates/arbeitsschritt.md", "02_protocol/templates/de/arbeitsschritt.md"):
        assert "`02_protocol/binding.md#waits`" in (ROOT / template).read_text(encoding="utf-8"), template
