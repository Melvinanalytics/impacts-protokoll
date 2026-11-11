"""leistung.erreicht: the ends that achieve the Leistung, resolved by the validator and shown at a reached end."""
import pytest

from impacts_protocol import validate
from impacts_protocol.view import selection, write
from pathlib import Path
from impacts_protocol import init_workspace
from tests.support import fixture_path, fixture_references, git, write_context, write_workstep
from tests.test_view import render_page, text_content


def _hauptprozess(root: Path, erreicht: list | None = None) -> Path:
    metadata = {"type": "hauptprozess", "id": f"hauptprozess:{root.name}",
                "leistung": {"ergebnis": "Veröffentlichtes Video", "kennzahl": "Durchlaufzeit", "abnahme": ["Video veröffentlicht"]},
                "einstieg_ref": "arbeitsschritt:start"}
    if erreicht is not None:
        metadata["leistung"]["erreicht"] = erreicht
    write_context(root / "CONTEXT.md", metadata, "# Video-Produktion")
    part = root / "produktion"
    write_context(part / "CONTEXT.md", {"type": "teilprozess", "id": "teilprozess:produktion", "ergebnis": "Produziertes Video"}, "# Produktion")
    write_workstep(part, "start", routes={"weiter": "arbeitsschritt:pruefen", "abbruch": "end:abgebrochen"})
    write_workstep(part, "pruefen", routes={"freigegeben": "end:video-veroeffentlicht", "abgelehnt": "arbeitsschritt:start"}, gate="human")
    return root


def _vorgang(tmp_path: Path, entries: list, erreicht: list | None = None) -> Path:
    """A workspace with one Vorgang whose laufpfad visits (step, status, chosen route) in order."""
    root = init_workspace(tmp_path / "kunde")
    _hauptprozess(root / "hauptprozesse" / "video", erreicht)
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    git(root, "add", ".")
    git(root, "commit", "-m", "hauptprozess")
    revision = git(root, "rev-parse", "HEAD:hauptprozesse/video")
    folder, laufpfad = root / "vorgaenge" / "video-001", []
    for step, status, route in entries:
        attempt = folder / step / "001"
        (fixture_path(attempt, "input")).mkdir(parents=True)
        (attempt / "output").mkdir(parents=True, exist_ok=True)
        (fixture_path(attempt, "input") / "auftrag.md").write_text(step, encoding="utf-8")
        entry = {"arbeitsschritt_ref": f"arbeitsschritt:{step}", "nummer": 1, "status": status,
                 "gelesen": fixture_references(attempt, ["input/auftrag.md"])}
        if route is not None:
            (attempt / "output" / "ergebnis.md").write_text("fertig", encoding="utf-8")
            entry |= {"gewaehlte_route": route, "geschrieben": fixture_references(attempt, ["output/ergebnis.md"])}
        laufpfad.append(entry)
    write_context(folder / "CONTEXT.md", {"type": "vorgang", "protocol": "v0.4.0", "id": "vorgang:video-001",
                                          "hauptprozess_revision": f"git-tree:{revision}", "laufpfad": laufpfad}, "# Video 001")
    return folder / "CONTEXT.md"


AT_PRUEFEN = [("start", "abgeschlossen", "weiter"), ("pruefen", "aktiv", None)]
ENDED = [("start", "abgeschlossen", "abbruch")]


def test_listed_ends_that_routes_reach_are_valid(tmp_path):
    root = _hauptprozess(tmp_path / "video", ["end:video-veroeffentlicht"])
    assert validate(root).valid, validate(root).issues


def test_an_end_no_route_reaches_does_not_resolve(tmp_path):
    root = _hauptprozess(tmp_path / "video", ["end:video-veroeffentlicht", "end:gibt-es-nicht"])
    found = {(i.code, i.message) for i in validate(root).issues}
    assert found == {("reference.unresolved", "Achieving end does not resolve: end:gibt-es-nicht; name an end targeted by this Hauptprozess in leistung.erreicht")}


@pytest.mark.parametrize("erreicht", [["end:gibt-es-nicht\n"], ["end:video-veroeffentlicht\n"]])
def test_a_trailing_newline_the_schema_admits_still_must_resolve(tmp_path, erreicht):
    root = _hauptprozess(tmp_path / "video", erreicht)
    assert {i.code for i in validate(root).issues} == {"reference.unresolved"}


@pytest.mark.parametrize("erreicht", [[], ["arbeitsschritt:start"], ["end:video-veroeffentlicht", "end:video-veroeffentlicht"], ["end:"]])
def test_malformed_lists_violate_the_schema_only(tmp_path, erreicht):
    root = _hauptprozess(tmp_path / "video", erreicht)
    assert {i.code for i in validate(root).issues} == {"schema.invalid"}


@pytest.mark.parametrize(("erreicht", "entries", "expected"), [
    (["end:video-veroeffentlicht"], ENDED, False),
    (["end:abgebrochen"], ENDED, True),
    (None, ENDED, "open"),
    (["end:video-veroeffentlicht"], AT_PRUEFEN, None),
])
def test_a_reached_end_says_whether_it_achieves_the_leistung(tmp_path, erreicht, entries, expected):
    model = selection.single_vorgang(_vorgang(tmp_path, entries, erreicht))
    assert model["issues"] == []
    assert model["stand"]["erreicht"] == expected
    if entries == ENDED:
        assert model["view"]["status"] == "beendet"
        assert model["stand"]["kind"] == "ended"


def test_pages_show_leistung_achievement_only_at_a_reached_end(tmp_path):
    ended = selection.single_vorgang(_vorgang(tmp_path / "a", ENDED, ["end:video-veroeffentlicht"]))
    ended["language"] = "de"
    assert "Leistung nicht erreicht" in text_content(render_page(tmp_path, write.page_html(ended))["head"])
    running = selection.single_vorgang(_vorgang(tmp_path / "b", AT_PRUEFEN, ["end:video-veroeffentlicht"]))
    running["language"] = "en"
    assert "Process result" not in text_content(render_page(tmp_path, write.page_html(running))["head"])
    overview = selection.workspace_site(_vorgang(tmp_path / "c", ENDED, ["end:abgebrochen"]).parents[2])["index.html"]
    overview["language"] = "en"
    assert "Process result achieved" in text_content(render_page(tmp_path, write.page_html(overview))["sheet"])
