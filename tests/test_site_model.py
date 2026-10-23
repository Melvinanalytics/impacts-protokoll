"""The public in-process site model equals the export the CLI writes."""
import json

import pytest

from impacts_protocol.cli import main
from impacts_protocol.view import site_model
from tests.test_stages import AT_PRUEFEN, ENDED, STAGES, _vorgang


def test_equals_the_exported_model_without_language(tmp_path):
    workspace = _vorgang(tmp_path, STAGES, AT_PRUEFEN).parents[2]
    out = tmp_path / "out"
    assert main(["view", str(workspace), "--out", str(out), "--json"]) == 0
    exported = json.loads((out / "model.json").read_text(encoding="utf-8"))
    assert {page.pop("language") for page in exported.values()} == {"en"}
    pages = site_model(workspace)
    assert pages == exported
    assert {page["format"] for page in pages.values()} == {"impacts-view/3"}
    assert pages["index.html"]["population"]["vorgaenge"] == 1


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
