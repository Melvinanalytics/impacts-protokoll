"""Stages: the optional `stufen` of a Hauptprozess, resolved by the validator and shown by the view."""
from pathlib import Path

import pytest

from impacts_protocol import init_workspace, surface_hash, validate
from impacts_protocol.view import selection, write
from tests.support import git, read_context, write_context, write_workstep
from tests.test_view import render_page, text_content

STAGES = {"stand:angefragt": 0, "arbeitsschritt:start": 10, "arbeitsschritt:pruefen": 60, "end:abgebrochen": 100}


def _application(root: Path, stages: dict | None) -> Path:
    metadata = {"type": "hauptprozess", "id": f"hauptprozess:{root.name}",
                "leistung": {"ergebnis": "Veröffentlichtes Video", "kennzahl": "Durchlaufzeit", "abnahme": ["Video veröffentlicht"]},
                "einstieg_ref": "arbeitsschritt:start"}
    if stages is not None:
        metadata["stufen"] = stages
    write_context(root / "CONTEXT.md", metadata, "# Video-Produktion")
    part = root / "produktion"
    write_context(part / "CONTEXT.md", {"type": "teilprozess", "id": "teilprozess:produktion", "ergebnis": "Produziertes Video"}, "# Produktion")
    write_workstep(part, "start", routes={"weiter": "arbeitsschritt:pruefen", "abbruch": "end:abgebrochen"})
    write_workstep(part, "pruefen", routes={"freigegeben": "end:video-veroeffentlicht", "abgelehnt": "arbeitsschritt:start"}, gate="human")
    return root


def _codes_and_messages(root: Path) -> set[tuple[str, str]]:
    return {(issue.code, issue.message) for issue in validate(root).issues}


def test_resolving_stages_are_valid(tmp_path):
    root = _application(tmp_path / "video", STAGES)
    assert validate(root).valid, validate(root).issues


@pytest.mark.parametrize("key", ["arbeitsschritt:fehlt", "end:fehlt"])
def test_a_stage_for_a_missing_step_or_end_does_not_resolve(tmp_path, key):
    root = _application(tmp_path / "video", {**STAGES, key: 50})
    assert ("reference.unresolved", f"Stage key does not resolve: {key}") in _codes_and_messages(root)


def test_record_states_need_no_step(tmp_path):
    root = _application(tmp_path / "video", {"stand:irgendwas": 5})
    assert validate(root).valid, validate(root).issues


@pytest.mark.parametrize("stages", [{}, {"vorgang:x": 5}, {"end:": 5}, {"arbeitsschritt:BAD": 5}, {"arbeitsschritt:start": 101},
                                    {"arbeitsschritt:start": -1}, {"arbeitsschritt:start": "zehn"}, {"arbeitsschritt:start": 1.5}])
def test_malformed_stages_violate_the_schema(tmp_path, stages):
    root = _application(tmp_path / "video", stages)
    assert {issue.code for issue in validate(root).issues} == {"schema.invalid"}


def _vorgang(tmp_path: Path, stages: dict | None, entries: list) -> Path:
    """A workspace with one Vorgang whose laufpfad visits (step, status, chosen route) in order."""
    root = init_workspace(tmp_path / "kunde")
    _application(root / "applications" / "video", stages)
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    git(root, "add", ".")
    git(root, "commit", "-m", "application")
    revision = git(root, "rev-parse", "HEAD:applications/video")
    folder, laufpfad = root / "vorgaenge" / "video-001", []
    for step, status, route in entries:
        attempt = folder / step / "001"
        (attempt / "input").mkdir(parents=True)
        (attempt / "output").mkdir()
        (attempt / "input" / "auftrag.md").write_text(step, encoding="utf-8")
        entry = {"arbeitsschritt_ref": f"arbeitsschritt:{step}", "versuch": 1, "status": status,
                 "eingabe_hash": surface_hash(attempt, ["input/auftrag.md"])}
        if route is not None:
            (attempt / "output" / "ergebnis.md").write_text("fertig", encoding="utf-8")
            entry |= {"gewaehlte_route": route, "ausgabe_hash": surface_hash(attempt, ["output/ergebnis.md"])}
        laufpfad.append(entry)
    write_context(folder / "CONTEXT.md", {"type": "vorgang", "id": "vorgang:video-001",
                                          "application_revision": f"git-tree:{revision}", "laufpfad": laufpfad}, "# Video 001")
    return folder / "CONTEXT.md"


AT_PRUEFEN = [("start", "abgeschlossen", "weiter"), ("pruefen", "aktiv", None)]
ENDED = [("start", "abgeschlossen", "abbruch")]


@pytest.mark.parametrize(("stages", "entries", "expected"), [
    (STAGES, AT_PRUEFEN, 60),
    (STAGES, ENDED, 100),
    ({"arbeitsschritt:start": 10}, AT_PRUEFEN, "open"),
    ({"arbeitsschritt:start": 10}, ENDED, "open"),
    (None, AT_PRUEFEN, None),
])
def test_the_stage_is_the_current_step_or_reached_end(tmp_path, stages, entries, expected):
    model = selection.single_vorgang(_vorgang(tmp_path, stages, entries))
    assert model["issues"] == []
    assert model["stand"]["stufe"] == expected


def test_the_stage_follows_the_bound_revision(tmp_path):
    context = _vorgang(tmp_path, STAGES, AT_PRUEFEN)
    hp = context.parents[2] / "applications" / "video" / "CONTEXT.md"
    metadata = read_context(hp)
    metadata["stufen"] = {**STAGES, "arbeitsschritt:pruefen": 70}
    write_context(hp, metadata, "# Video-Produktion")
    assert selection.single_vorgang(context)["stand"]["stufe"] == 60


def test_pages_show_the_stage_and_hide_it_without_stages(tmp_path):
    shown = selection.single_vorgang(_vorgang(tmp_path / "a", STAGES, AT_PRUEFEN))
    shown["language"] = "de"
    assert "Stufe 60" in text_content(render_page(tmp_path, write.page_html(shown))["head"])
    missing = selection.single_vorgang(_vorgang(tmp_path / "b", {"arbeitsschritt:start": 10}, AT_PRUEFEN))
    missing["language"] = "en"
    assert "Stage open" in text_content(render_page(tmp_path, write.page_html(missing))["head"])
    none = selection.single_vorgang(_vorgang(tmp_path / "c", None, AT_PRUEFEN))
    none["language"] = "de"
    assert "Stufe" not in text_content(render_page(tmp_path, write.page_html(none))["head"])


def test_overview_rows_show_the_stage(tmp_path):
    context = _vorgang(tmp_path, STAGES, ENDED)
    overview = selection.workspace_site(context.parents[2])["index.html"]
    assert overview["format"] == "impacts-view/3"
    row = overview["applications"][0]["vorgaenge"][0]
    assert row["stand"]["stufe"] == 100
    overview["language"] = "de"
    assert "Stufe 100" in text_content(render_page(tmp_path, write.page_html(overview))["sheet"])
