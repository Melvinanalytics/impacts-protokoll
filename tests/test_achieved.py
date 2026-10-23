"""leistung.erreicht: the ends that achieve the Leistung, resolved by the validator and shown at a reached end."""
import pytest

from impacts_protocol import validate
from impacts_protocol.view import selection, write
from tests.test_stages import AT_PRUEFEN, ENDED, STAGES, _application, _vorgang
from tests.test_view import render_page, text_content


def test_listed_ends_that_routes_reach_are_valid(tmp_path):
    root = _application(tmp_path / "video", STAGES, ["end:video-veroeffentlicht"])
    assert validate(root).valid, validate(root).issues


def test_an_end_no_route_reaches_does_not_resolve(tmp_path):
    root = _application(tmp_path / "video", STAGES, ["end:video-veroeffentlicht", "end:gibt-es-nicht"])
    found = {(i.code, i.message) for i in validate(root).issues}
    assert found == {("reference.unresolved", "Achieving end does not resolve: end:gibt-es-nicht")}


@pytest.mark.parametrize("erreicht", [["end:gibt-es-nicht\n"], ["end:video-veroeffentlicht\n"]])
def test_a_trailing_newline_the_schema_admits_still_must_resolve(tmp_path, erreicht):
    root = _application(tmp_path / "video", STAGES, erreicht)
    assert {i.code for i in validate(root).issues} == {"reference.unresolved"}


@pytest.mark.parametrize("erreicht", [[], ["arbeitsschritt:start"], ["end:video-veroeffentlicht", "end:video-veroeffentlicht"], ["end:"]])
def test_malformed_lists_violate_the_schema_only(tmp_path, erreicht):
    root = _application(tmp_path / "video", STAGES, erreicht)
    assert {i.code for i in validate(root).issues} == {"schema.invalid"}


@pytest.mark.parametrize(("erreicht", "entries", "expected"), [
    (["end:video-veroeffentlicht"], ENDED, False),
    (["end:abgebrochen"], ENDED, True),
    (None, ENDED, "open"),
    (["end:video-veroeffentlicht"], AT_PRUEFEN, None),
])
def test_a_reached_end_says_whether_it_achieves_the_leistung(tmp_path, erreicht, entries, expected):
    model = selection.single_vorgang(_vorgang(tmp_path, STAGES, entries, erreicht))
    assert model["issues"] == []
    assert model["stand"]["erreicht"] == expected


def test_pages_show_the_outcome_only_at_a_reached_end(tmp_path):
    ended = selection.single_vorgang(_vorgang(tmp_path / "a", STAGES, ENDED, ["end:video-veroeffentlicht"]))
    ended["language"] = "de"
    assert "Leistung nicht erreicht" in text_content(render_page(tmp_path, write.page_html(ended))["head"])
    running = selection.single_vorgang(_vorgang(tmp_path / "b", STAGES, AT_PRUEFEN, ["end:video-veroeffentlicht"]))
    running["language"] = "en"
    assert "Process result" not in text_content(render_page(tmp_path, write.page_html(running))["head"])
    overview = selection.workspace_site(_vorgang(tmp_path / "c", STAGES, ENDED, ["end:abgebrochen"]).parents[2])["index.html"]
    overview["language"] = "en"
    assert "Process result achieved" in text_content(render_page(tmp_path, write.page_html(overview))["sheet"])
