"""The public in-process site model equals the export the CLI writes."""
import json

import pytest

from impacts_protocol.cli import main
from impacts_protocol.view import selection, site_model
from tests.test_stages import AT_PRUEFEN, ENDED, STAGES, _vorgang


def test_equals_the_exported_model_without_language(tmp_path):
    workspace = _vorgang(tmp_path, STAGES, AT_PRUEFEN).parents[2]
    ist = workspace / "grundlagen" / "ist-prozesse"
    ist.mkdir(parents=True)
    (ist / "angebot.md").write_text("---\ntype: ist-prozess\nname: Angebot\ndate: 2026-10-23\n---\n\n# Angebot\n", encoding="utf-8")
    out = tmp_path / "out"
    assert main(["view", str(workspace), "--out", str(out), "--json"]) == 0
    exported = json.loads((out / "model.json").read_text(encoding="utf-8"))
    assert {page.pop("language") for page in exported.values()} == {"en"}
    pages = site_model(workspace)
    assert pages == exported
    assert {page["format"] for page in pages.values()} == {"impacts-view/3"}
    assert pages["index.html"]["population"]["vorgaenge"] == 1
    assert '2026-10-23' in json.dumps(pages["i-angebot.html"])


def test_a_refused_vorgang_is_a_page_and_stops_no_other(tmp_path):
    workspace = _vorgang(tmp_path, STAGES, ENDED).parents[2]
    broken = workspace / "vorgaenge" / "video-002"
    broken.mkdir()
    (broken / "CONTEXT.md").write_text("---\ntype: vorgang\n---\n", encoding="utf-8")
    pages = site_model(workspace)
    vorgaenge = {name: page for name, page in pages.items() if page["kind"] == "vorgang"}
    assert sorted(bool(page["issues"]) for page in vorgaenge.values()) == [False, True]
    assert pages["index.html"]["population"]["vorgaenge_refused"] == 1


def test_a_folder_that_is_no_git_workspace_raises_value_error(tmp_path):
    with pytest.raises(ValueError, match="Git"):
        site_model(tmp_path)


def test_selected_vorgaenge_equal_their_pages_in_the_full_model(tmp_path):
    workspace = _vorgang(tmp_path, STAGES, ENDED).parents[2]
    second = workspace / "vorgaenge" / "video-002"
    second.mkdir()
    (second / "CONTEXT.md").write_text("---\ntype: vorgang\n---\n", encoding="utf-8")
    full = site_model(workspace)
    for selected in [{"video-001"}, {"video-002"}, {"video-001", "video-002"}, set()]:
        pages = site_model(workspace, vorgaenge=selected)
        assert {page["selection"]["vorgang"] for page in pages.values()} == {f"vorgaenge/{slug}" for slug in selected}
        assert pages == {name: full[name] for name in pages}


def test_only_selected_vorgang_folders_are_read(tmp_path, monkeypatch):
    workspace = _vorgang(tmp_path, STAGES, ENDED).parents[2]
    (workspace / "vorgaenge" / "video-002").mkdir()
    read = []
    original = selection.read_vorgang
    monkeypatch.setattr(selection, "read_vorgang", lambda path, *rest: read.append(path.parent.name) or original(path, *rest))
    site_model(workspace, vorgaenge=["video-001"])
    assert read == ["video-001"]


@pytest.mark.parametrize(("vorgaenge", "error"), [(["video-01"], ValueError), (["Video-001"], ValueError), ("video-001", TypeError)])
def test_a_slug_must_name_an_entry_exactly(tmp_path, vorgaenge, error):
    workspace = _vorgang(tmp_path, STAGES, ENDED).parents[2]
    with pytest.raises(error):
        site_model(workspace, vorgaenge=vorgaenge)
