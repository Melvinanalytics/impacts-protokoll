"""One machine vocabulary, paired readable views, explicit source revisions."""
import hashlib
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pytest

from impacts_protocol.cli import main
from impacts_protocol.generator import TEMPLATE_KINDS, init_workspace, template_text
from impacts_protocol.io import load_frontmatter_and_body
from impacts_protocol.validator import SCHEMA_REGISTRY, validate

PAIRS = [(f"02_protocol/templates/{kind}.md", f"02_protocol/templates/de/{kind}.md") for kind in (*TEMPLATE_KINDS, "workspace")]
PAIRS += [("02_protocol/language.md", "02_protocol/translations/de.md"),
          ("02_protocol/impacts-architect/templates/ist-prozess.md", "02_protocol/impacts-architect/templates/de/ist-prozess.md")]


def translation_matches(source: Path, translation: Path) -> bool:
    expected = f"<!-- Translation source: {source.relative_to(ROOT).as_posix()}; sha256: {hashlib.sha256(source.read_bytes()).hexdigest()} -->"
    return expected in translation.read_text()


@pytest.mark.parametrize("source,target", PAIRS)
def test_every_supported_translation_identifies_current_source_bytes(source, target):
    assert translation_matches(ROOT / source, ROOT / target)


def test_source_change_makes_translation_stale(tmp_path, monkeypatch):
    source_name, translation_name = PAIRS[0]
    original = (ROOT / source_name).read_bytes()
    translated = (ROOT / translation_name).read_text()
    source, translation = tmp_path / source_name, tmp_path / translation_name
    source.parent.mkdir(parents=True)
    translation.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(original)
    translation.write_text(translated)
    monkeypatch.setattr(sys.modules[__name__], "ROOT", tmp_path)
    assert translation_matches(source, translation)
    source.write_bytes(original + b"\nChanged requirement.\n")
    assert not translation_matches(source, translation)


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
    assert data == {"type": "workspace"} and validate(root).valid
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
        for match in re.finditer(r"impacts template (?:application|hauptprozess|teilprozess|arbeitsschritt|vorgang|<art>)", text):
            assert text[match.end():].startswith(" --language de"), target
