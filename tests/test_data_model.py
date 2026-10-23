"""The overview's data model card: the packaged schemas, read and never restated."""
from impacts_protocol.validator import SCHEMA_REGISTRY
from impacts_protocol.view import project, selection, write
from tests.test_stages import AT_PRUEFEN, STAGES, _vorgang
from tests.test_view import render_page, text_content

COUNTS = dict.fromkeys(("hauptprozess", "leistung", "teilprozess", "arbeitsschritt", "vorgang", "laufpfadeintrag"), 0)


def test_rows_follow_the_packaged_schemas():
    schemas = SCHEMA_REGISTRY.schemas()
    rows = {r["name"]: r for r in project.data_model(schemas, COUNTS)}
    assert list(rows) == ["hauptprozess", "leistung", "teilprozess", "arbeitsschritt", "vorgang", "laufpfadeintrag"]
    for name, schema in [*schemas.items(), ("laufpfadeintrag", schemas["vorgang"]["$defs"]["laufpfadeintrag"])]:
        assert rows[name]["required"] == schema["required"]
        assert rows[name]["optional"] == [f for f in schema["properties"] if f not in schema["required"]]
    assert rows["hauptprozess"]["refers"] == [["leistung", "leistung"], ["einstieg_ref", "arbeitsschritt"],
                                              ["stufen", "arbeitsschritt"], ["stufen", "end"], ["stufen", "stand"]]
    assert rows["arbeitsschritt"]["refers"] == [["routen", "arbeitsschritt"], ["routen", "end"]]
    assert rows["vorgang"]["refers"] == [["application_revision", "git-tree"], ["laufpfad", "laufpfadeintrag"]]
    assert rows["laufpfadeintrag"]["refers"] == [["arbeitsschritt_ref", "arbeitsschritt"]]


def test_a_schema_change_reaches_the_card_without_code():
    schemas = SCHEMA_REGISTRY.schemas()
    schemas["teilprozess"]["properties"]["vorgaenger_ref"] = {"type": "string", "pattern": "^teilprozess:[a-z]+$"}
    row = next(r for r in project.data_model(schemas, COUNTS) if r["name"] == "teilprozess")
    assert row["optional"] == ["vorgaenger_ref"] and row["refers"] == [["vorgaenger_ref", "teilprozess"]]
    assert "vorgaenger_ref" not in SCHEMA_REGISTRY.schemas()["teilprozess"]["properties"]


def test_overview_counts_and_shows_the_data_model_and_stage_coverage(tmp_path):
    context = _vorgang(tmp_path, STAGES, AT_PRUEFEN)
    overview = selection.workspace_site(context.parents[2])["index.html"]
    counts = {r["name"]: r["count"] for r in overview["data_model"]}
    assert counts == {"hauptprozess": 1, "leistung": 1, "teilprozess": 1, "arbeitsschritt": 2, "vorgang": 1, "laufpfadeintrag": 2}
    # start, pruefen and end:abgebrochen carry stages; end:video-veroeffentlicht does not.
    assert overview["applications"][0]["stufen"] == {"assigned": 3, "of": 4}
    overview["language"] = "de"
    text = text_content(render_page(tmp_path, write.page_html(overview))["sheet"])
    assert "Datenmodell" in text and "Pflichtfelder" in text and "einstieg_ref" in text
    assert "Laufpfad-Eintrag (Versuch)" in text and "application_revision → Application-Fassung (Git-Baum)" in text
    assert "Stufen vergeben für 3 von 4 Schritten und Enden" in text


def test_without_stages_no_coverage_is_shown(tmp_path):
    context = _vorgang(tmp_path, None, AT_PRUEFEN)
    overview = selection.workspace_site(context.parents[2])["index.html"]
    assert overview["applications"][0]["stufen"] is None
    overview["language"] = "en"
    text = text_content(render_page(tmp_path, write.page_html(overview))["sheet"])
    assert "Data model" in text and "Stages assigned" not in text
