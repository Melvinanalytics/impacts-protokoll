"""Tests for `impacts view`, the read-only HTML view of IMPACTS files."""
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from impacts_protocol import init_workspace, surface_hash
from tests.support import git, read_context, replace_context, write_application, write_context

from impacts_protocol.cli import main
from impacts_protocol.view import blocks, choose_language, project, read, selection, working_language, write

HERE = Path(__file__).resolve().parent
PACKAGE = Path(write.__file__).parent

HOSTILE = "</script><script>alert(1)</script> __MODEL__ __POLICY__ [x](javascript:alert(1)) \u2028 & <b>"


def embedded(html: str) -> dict:
    return json.loads(re.search(r'<script type="application/json" id="model">(.*?)</script>', html, re.S).group(1))


def words(value) -> str:
    if isinstance(value, list):
        return " ".join(words(v) for v in value)
    if isinstance(value, dict):
        return " ".join(words(v) for v in value.values())
    return str(value)


def test_route_direction_distinguishes_dag_join_cycle_and_self_return():
    order = ["arbeitsschritt:a", "arbeitsschritt:b", "arbeitsschritt:c"]
    nodes = {
        "arbeitsschritt:a": {"routes": [["left", "arbeitsschritt:b"], ["right", "arbeitsschritt:c"]]},
        "arbeitsschritt:b": {"routes": [["done", "end:done"]]},
        "arbeitsschritt:c": {"routes": [["join", "arbeitsschritt:b"]]},
    }
    assert project.direction(nodes, order, "arbeitsschritt:c", "arbeitsschritt:b") == "forward"
    nodes["arbeitsschritt:b"]["routes"].append(["again", "arbeitsschritt:c"])
    assert project.direction(nodes, order, "arbeitsschritt:c", "arbeitsschritt:b") == "back"
    assert project.direction(nodes, order, "arbeitsschritt:c", "arbeitsschritt:c") == "back"
    assert project.direction(nodes, order, "arbeitsschritt:b", "end:done") == "end"


def word_tables(page: str) -> dict:
    return json.loads(re.search(r"const WORDS = (.*?);\nconst W =", page, re.S).group(1))


def render_page(tmp_path: Path, html: str, fragment: str = "") -> dict:
    """Run the actual page script with a DOM adapter, without browser geometry or events."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not installed")
    adapter = r"""
class Element {
  constructor(tag) {
    this.tagName = tag.toUpperCase(); this.attrs = {}; this.children = []; this.hidden = false;
    this.classList = {add() {}, remove() {}, toggle() {}, contains() { return false; }};
  }
  set textContent(value) { this.children = [String(value)]; }
  get textContent() { return this.children.map(c => c instanceof Element ? c.textContent : String(c)).join(''); }
  setAttribute(key, value) { this.attrs[key] = String(value); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  addEventListener() {}
  focus() {}
  scrollIntoView() {}
  closest() { return null; }
  querySelectorAll() { return []; }
  getContext() { return {measureText: text => ({width: text.length * 7})}; }
}
class SVGElement extends Element {}
const elements = Object.fromEntries(['model', 'map-view', 'map-head', 'map', 'panel', 'sheet-view', 'sheet']
  .map(id => [id, new Element('div')]));
elements.model.textContent = JSON.stringify(INPUT);
const document = {
  documentElement: new Element('html'), body: new Element('body'), title: '',
  getElementById: id => elements[id] || null,
  createElement: tag => new Element(tag), createElementNS: (ns, tag) => new SVGElement(tag),
  querySelector: () => null, querySelectorAll: () => [], addEventListener() {},
};
const location = {hash: FRAGMENT, pathname: 'index.html'};
const history = {pushState() {}, replaceState() {}};
const window = {innerWidth: 1280, innerHeight: 900, addEventListener() {}, scrollTo() {}};
const matchMedia = () => ({matches: false});
const CSS = {escape: value => String(value)};
"""
    code = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
    script = tmp_path / "render.js"
    script.write_text("const INPUT = " + json.dumps(embedded(html)) + ";\nconst FRAGMENT = " + json.dumps(fragment)
                      + ";\n" + adapter + code + """
console.log(JSON.stringify({language: document.documentElement.lang,
  words: W === WORDS.en ? 'en' : W === WORDS.de ? 'de' : null,
  title: document.title, error: document.body.textContent,
  sheet: elements.sheet, head: elements['map-head'], map: elements.map}));
""", encoding="utf-8")
    return json.loads(subprocess.run([node, str(script)], capture_output=True, text=True, check=True).stdout)


def elements(tree):
    if isinstance(tree, dict):
        if "tagName" in tree:
            yield tree
        yield from elements(tree.get("children", []))
    elif isinstance(tree, list):
        for child in tree:
            yield from elements(child)


def text_content(tree):
    if isinstance(tree, dict):
        return "".join(text_content(c) for c in tree.get("children", []))
    if isinstance(tree, list):
        return "".join(text_content(c) for c in tree)
    return str(tree)


def run_cli(source, *argv) -> int:
    """Synthetic sources without a workspace setting are shown in German, the view's first language."""
    return main(["view", str(source), *[str(a) for a in argv]])


# ---------- blocks: the only Markdown reader ----------

ODD = [
    "```text\nKEEP\n```DO NOT APPROVE\nAFTER\n```\nTAIL",
    "```text\nKEEP\n```\ufeff\nINSIDE\n```\nTAIL",
    "```text\nKEEP\n```\x85\nINSIDE\n```\nTAIL",
    "| X | A\\| B |\n| --- | --- |\n| eins | zwei |",
    "| X | A\\\\| Y |",
    "- a\n  - b\n    - c\n      - d\n        - e\n      - f",
    "7. sieben\n8. acht\nweiter ohne Marker",
    "- Parent\n\n  - Required child\n\n- Sibling",
    "Text\n\n    if a:\n        approve()\n    else:\n        refuse()\n\nDanach",
    "Absatz mit `code` und **fett** und [Label](javascript:alert(1)) und ~~~",
]


def test_sections_keep_title_preamble_fences_and_lines():
    body = "\n# Titel\n\nVorab `open`: Frage\n\n## Eins\n\n```md\n## kein Abschnitt\n```\n\n## Zwei\nText\n"
    title, parts = blocks.sections(body, 5)
    assert title == "Titel"
    assert [p["heading"] for p in parts] == [None, "Eins", "Zwei"]
    assert parts[0]["text"] == "Vorab `open`: Frage"
    assert "## kein Abschnitt" in parts[1]["text"]
    assert [p["line"] for p in parts] == [5, 10, 16]


def test_blocks_keep_every_word():
    for text in ODD:
        rendered = words(blocks.blocks(text))
        for word in re.findall(r"\w+", text):
            assert word in rendered, (text, word)


def test_unsupported_shapes_stay_verbatim():
    assert blocks.blocks(ODD[4])[0] == {"type": "text", "text": ODD[4], "line": 1}
    assert blocks.blocks(ODD[5])[0] == {"type": "text", "text": ODD[5], "line": 1}
    for text in ODD[1:3]:
        code = blocks.blocks(text)[0]
        assert code["type"] == "code" and "INSIDE" in code["text"]
    assert [i["marker"] for i in blocks.blocks(ODD[6])[0]["items"]] == ["7.", "8."]
    assert blocks.blocks(ODD[7])[1] == {"type": "text", "text": "  - Required child", "line": 3}
    assert blocks.blocks(ODD[8])[1] == {"type": "text", "text": "    if a:\n        approve()\n    else:\n        refuse()", "line": 3}


def test_real_fixture_sections_keep_every_word():
    model = selection.application_page(HERE / "view_source" / "applications" / "invoice-entry")
    assert model["issues"] == []
    for node in model["nodes"]:
        for part in node["sections"]:
            rendered = words(part["blocks"])
            for word in re.findall(r"\w+", part["text"]):
                assert word in rendered, (node["path"], part["heading"], word)


# ---------- reading one Application ----------

def test_invalid_application_is_refused_with_validator_issues(tmp_path):
    root = write_application(tmp_path / "video")
    shutil.copytree(root / "produktion" / "start", root / "produktion" / "kopie")
    model = selection.application_page(root)
    assert "nodes" not in model and "reference.duplicate" in {i["code"] for i in model["issues"]}


def test_unknown_files_refuse_before_copying(tmp_path):
    root = write_application(tmp_path / "video")
    (root / "produktion" / "notes.bin").write_bytes(b"x" * 10)
    assert selection.application_page(root)["issues"] == [
        {"code": "structure.invalid", "path": "produktion/notes.bin", "message": "Unknown Application entry"}]


@pytest.mark.parametrize("damage", ["closing", "opening"])
def test_line_separator_in_frontmatter_is_refused(tmp_path, damage):
    root = write_application(tmp_path / "video")
    step = root / "produktion" / "start" / "CONTEXT.md"
    text = step.read_text(encoding="utf-8")
    if damage == "closing":
        head, _, body = text.partition("\n---\n")
        step.write_text(head + "\u2028---\n" + body, encoding="utf-8")
    else:
        step.write_text("---\u2028" + text[4:], encoding="utf-8")
    model = selection.application_page(root)
    assert "nodes" not in model and model["issues"][0]["code"] == "view.unreadable"


def test_route_order_survives_integer_like_labels(tmp_path):
    root = write_application(tmp_path / "video")
    step = root / "produktion" / "start" / "CONTEXT.md"
    step.write_text(step.read_text(encoding="utf-8").replace(
        "  weiter: arbeitsschritt:pruefen", "  '10': arbeitsschritt:pruefen\n  '2': end:abgebrochen"), encoding="utf-8")
    model = selection.application_page(root)
    assert model["issues"] == []
    start = next(n for n in model["nodes"] if n["id"] == "arbeitsschritt:start")
    assert [row[0] for row in start["routes"]] == ["10", "2"]
    map_routes = [c["route"] for c in model["map"]["children"][0]["children"][0]["children"]]
    assert map_routes == ["10", "2"]


# ---------- the writer ----------

def test_hostile_source_text_stays_data(tmp_path):
    root = write_application(tmp_path / "video")
    step = root / "produktion" / "start" / "CONTEXT.md"
    step.write_text(step.read_text(encoding="utf-8") + f"\n## Böse\n\n{HOSTILE}\n", encoding="utf-8")
    model = selection.application_page(root)
    html = write.page_html(model)
    assert html.count("</script>") == 2
    assert "innerHTML" not in html and "javascript:" not in html.split("__MODEL__")[0]
    assert embedded(html) == json.loads(json.dumps(model, default=str))
    found = [s for n in model["nodes"] for s in n["sections"] if s["heading"] == "Böse"]
    assert found[0]["text"] == HOSTILE


def test_policy_hashes_match_the_inline_code(tmp_path):
    html = write.page_html(selection.application_page(write_application(tmp_path / "video")))
    policy = re.search(r'Content-Security-Policy" content="([^"]+)"', html).group(1)
    for tag in ("script", "style"):
        code = re.search(rf"<{tag}>(.*?)</{tag}>", html, re.S).group(1)
        assert f"'sha256-{base64.b64encode(hashlib.sha256(code.encode()).digest()).decode()}'" in policy
    assert policy.startswith("default-src 'none'")


def test_page_script_is_valid_javascript(tmp_path):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not installed")
    html = write.page_html(selection.application_page(write_application(tmp_path / "video")))
    script = tmp_path / "page.js"
    script.write_text(re.search(r"<script>(.*?)</script>", html, re.S).group(1), encoding="utf-8")
    assert subprocess.run([node, "--check", str(script)], capture_output=True).returncode == 0


def test_same_files_give_same_bytes(tmp_path):
    root = write_application(tmp_path / "video")
    first = write.page_html(selection.application_page(root))
    assert write.page_html(selection.application_page(root)) == first


def test_output_folder_rules(tmp_path):
    root = write_application(tmp_path / "video")
    for out in (root / "view", tmp_path):
        with pytest.raises(SystemExit):
            run_cli(root, "--out", out)
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "keep.txt").write_text("x")
    linked = tmp_path / "linked"
    linked.symlink_to(foreign)
    for out in (foreign, linked):
        with pytest.raises(SystemExit):
            run_cli(root, "--out", out)
    assert [p.name for p in foreign.iterdir()] == ["keep.txt"]
    out = tmp_path / "view"
    assert run_cli(root, "--out", out, "--json") == 0
    assert {p.name for p in out.iterdir()} == {"index.html", "model.json"}
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    with pytest.raises(SystemExit):  # an earlier view is never replaced or deleted
        run_cli(root, "--out", out)
    assert {p.name: p.read_bytes() for p in out.iterdir()} == before


def test_swapped_parent_cannot_redirect_writes(tmp_path, monkeypatch):
    """The writer holds the checked folder; renaming its path to the source changes nothing."""
    root = write_application(tmp_path / "video")
    source = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    parent = tmp_path / "views"
    parent.mkdir()
    real_mkdir = os.mkdir

    def swap_then_mkdir(name, mode=0o777, *, dir_fd=None):
        if dir_fd is not None:  # only the writer's own call, after its check
            parent.rename(tmp_path / "moved")
            parent.symlink_to(root)
        return real_mkdir(name, mode, dir_fd=dir_fd)

    monkeypatch.setattr(write.os, "mkdir", swap_then_mkdir)
    assert run_cli(root, "--out", parent / "view") == 0
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == source
    assert (tmp_path / "moved" / "view" / "index.html").is_file()


def test_failed_generation_is_reported_and_nothing_is_deleted(tmp_path, monkeypatch):
    root = write_application(tmp_path / "video")
    real_fdopen = os.fdopen

    def fail(*args, **kwargs):
        stream = real_fdopen(*args, **kwargs)
        stream.close()
        raise OSError("disk full")

    monkeypatch.setattr(write.os, "fdopen", fail)
    with pytest.raises(OSError, match="disk full"):
        run_cli(root, "--out", tmp_path / "view")
    # The folder stays, incomplete; only a successful exit marks a finished view.
    assert (tmp_path / "view" / "index.html").read_bytes() == b""


def test_hard_link_at_output_name_is_refused(tmp_path):
    root = write_application(tmp_path / "video")
    elsewhere = tmp_path / "elsewhere.txt"
    elsewhere.write_text("unchanged")
    os.link(elsewhere, tmp_path / "view")
    with pytest.raises(SystemExit):
        run_cli(root, "--out", tmp_path / "view")
    assert elsewhere.read_text() == "unchanged"


def test_whole_line_html_comment_is_its_own_block():
    found = blocks.blocks("<!-- Quelle: x;\nsha256: abc -->\n\nText danach", 5)
    assert found == [{"type": "comment", "text": "<!-- Quelle: x;\nsha256: abc -->", "line": 5},
                     {"type": "para", "spans": [["t", "Text danach", ""]], "line": 8}]
    assert [b["type"] for b in blocks.blocks("<!-- a --> und Text")] == ["para"]
    assert [b["type"] for b in blocks.blocks("<!-- offen ohne Ende\nText")] == ["para"]
    _, parts = blocks.sections(TEMPLATE_DE.read_text(encoding="utf-8").split("---\n", 2)[2], 18)
    assert parts[0]["blocks"][0]["type"] == "comment" and "sha256" in parts[0]["blocks"][0]["text"]


def test_list_with_indented_code_stays_verbatim():
    text = "- Regel:\n      if authorized:\n          approve()\n      else:\n          refuse()"
    assert blocks.blocks(text) == [{"type": "text", "text": text, "line": 1}]


# ---------- runs and workspaces ----------

def _workspace(base: Path, applications=("video",), runs=(("video-001", "video"),)) -> Path:
    root = init_workspace(base / "kunde")
    for name in applications:
        write_application(root / "applications" / name)
        hp = root / "applications" / name / "CONTEXT.md"
        hp.write_text(hp.read_text(encoding="utf-8").replace("hauptprozess:video", f"hauptprozess:{name}"), encoding="utf-8")
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    git(root, "add", ".")
    git(root, "commit", "-m", "applications v1")
    for slug, application in runs:
        revision = git(root, "rev-parse", f"HEAD:applications/{application}")
        run, entries = root / "vorgaenge" / slug, []
        # pruefen is a human gate. Its open decision is wartend under the current rule; an aktiv gate entry
        # stays valid for runs recorded earlier, so this fixture keeps that older shape on purpose.
        for step, status in (("start", "abgeschlossen"), ("pruefen", "aktiv")):
            attempt = run / step / "001"
            (attempt / "input").mkdir(parents=True)
            (attempt / "output").mkdir()
            (attempt / "input" / "auftrag.md").write_text(step, encoding="utf-8")
            entry = {"arbeitsschritt_ref": f"arbeitsschritt:{step}", "versuch": 1, "status": status,
                     "eingabe_hash": surface_hash(attempt, ["input/auftrag.md"])}
            if status == "abgeschlossen":
                (attempt / "output" / "ergebnis.md").write_text("fertig", encoding="utf-8")
                entry |= {"gewaehlte_route": "weiter", "ausgabe_hash": surface_hash(attempt, ["output/ergebnis.md"])}
            entries.append(entry)
        write_context(run / "CONTEXT.md", {"type": "vorgang", "id": f"vorgang:{slug}",
                                           "application_revision": f"git-tree:{revision}", "laufpfad": entries}, f"# {slug}")
    return root


def test_vorgang_shows_the_bound_revision_not_the_working_tree(tmp_path):
    root = _workspace(tmp_path)
    step = root / "applications" / "video" / "produktion" / "start" / "CONTEXT.md"
    step.write_text(step.read_text(encoding="utf-8").replace("Erzeuge", "GEÄNDERT"), encoding="utf-8")
    model = selection.single_vorgang(root / "vorgaenge" / "video-001" / "CONTEXT.md")
    assert model["issues"] == []
    text = json.dumps(model, ensure_ascii=False)
    assert "Erzeuge das deklarierte Ergebnis" in text and "GEÄNDERT" not in text
    assert model["view"] == {"phase": {"arbeitsschritt:start": "done", "arbeitsschritt:pruefen": "current"},
                             "current": "arbeitsschritt:pruefen", "ended": None}


def test_invalid_run_is_refused(tmp_path):
    root = _workspace(tmp_path)
    (root / "vorgaenge" / "video-001" / "start" / "001" / "input" / "auftrag.md").write_text("verändert", encoding="utf-8")
    model = selection.single_vorgang(root / "vorgaenge" / "video-001" / "CONTEXT.md")
    assert "nodes" not in model and {i["code"] for i in model["issues"]} == {"hash.mismatch"}


def test_vorgang_outside_vorgaenge_is_refused(tmp_path):
    root = _workspace(tmp_path)
    copy = root / "scratch" / "video-001"
    shutil.copytree(root / "vorgaenge" / "video-001", copy)
    with pytest.raises(SystemExit):
        selection.single_vorgang(copy / "CONTEXT.md")


def test_broken_workspace_router_blocks_the_run(tmp_path):
    root = _workspace(tmp_path)
    router = root / "CONTEXT.md"
    router.write_text(router.read_text(encoding="utf-8").replace("type: workspace", "type: kaputt"), encoding="utf-8")
    model = selection.single_vorgang(root / "vorgaenge" / "video-001" / "CONTEXT.md")
    assert "nodes" not in model and model["issues"]


def test_output_never_inside_the_workspace_of_a_run(tmp_path):
    root = _workspace(tmp_path)
    with pytest.raises(SystemExit):
        run_cli(root / "vorgaenge" / "video-001" / "CONTEXT.md", "--out", root / "ansicht")


def test_phases_follow_rework_waiting_and_end():
    nodes = [{"id": "hauptprozess:h", "kind": "hauptprozess", "parent": None},
             {"id": "teilprozess:t", "kind": "teilprozess", "parent": "hauptprozess:h"},
             {"id": "arbeitsschritt:a", "kind": "arbeitsschritt", "parent": "teilprozess:t", "meta": {"routen": {"weiter": "arbeitsschritt:b"}}},
             {"id": "arbeitsschritt:b", "kind": "arbeitsschritt", "parent": "teilprozess:t",
              "meta": {"routen": {"gut": "end:fertig", "zurueck": "arbeitsschritt:a"}}}]
    done = {"status": "abgeschlossen"}
    rework = [{"arbeitsschritt_ref": "arbeitsschritt:a", **done, "gewaehlte_route": "weiter"},
              {"arbeitsschritt_ref": "arbeitsschritt:b", **done, "gewaehlte_route": "zurueck"},
              {"arbeitsschritt_ref": "arbeitsschritt:a", "status": "wartend"}]
    view = project.phases(nodes, rework)
    # b's attempt closed, but its back route reopened a: a closed attempt is not shown as done.
    assert view["phase"] == {"arbeitsschritt:a": "waiting", "arbeitsschritt:b": "looped"}
    assert view["current"] == "arbeitsschritt:a" and view["ended"] is None
    # The forward route after rework is no return: a's rework result counts as done again.
    redone = project.phases(nodes, rework[:2] + [{"arbeitsschritt_ref": "arbeitsschritt:a", **done, "gewaehlte_route": "weiter"},
                                                 {"arbeitsschritt_ref": "arbeitsschritt:b", "status": "aktiv"}])
    assert redone["phase"] == {"arbeitsschritt:a": "done", "arbeitsschritt:b": "current"}
    ended = project.phases(nodes, rework[:1] + [{"arbeitsschritt_ref": "arbeitsschritt:b", **done, "gewaehlte_route": "gut"}])
    assert ended["ended"] == "end:fertig" and ended["current"] is None
    handed = project.phases(nodes, rework[:1])
    assert handed["phase"]["arbeitsschritt:b"] == "next" and handed["current"] == "arbeitsschritt:b"


def test_back_route_marks_every_step_closed_since_the_reopened_attempt():
    step = lambda name, routes: {"id": f"arbeitsschritt:{name}", "kind": "arbeitsschritt", "parent": "teilprozess:t",
                                 "meta": {"routen": routes}}
    nodes = [{"id": "hauptprozess:h", "kind": "hauptprozess", "parent": None},
             {"id": "teilprozess:t", "kind": "teilprozess", "parent": "hauptprozess:h"},
             step("a", {"weiter": "arbeitsschritt:x"}), step("x", {"weiter": "arbeitsschritt:b"}),
             step("b", {"gut": "end:fertig", "zurueck": "arbeitsschritt:a"})]
    closed = lambda name, route: {"arbeitsschritt_ref": f"arbeitsschritt:{name}", "status": "abgeschlossen", "gewaehlte_route": route}
    view = project.phases(nodes, [closed("a", "weiter"), closed("x", "weiter"), closed("b", "zurueck"),
                                  {"arbeitsschritt_ref": "arbeitsschritt:a", "status": "aktiv"}])
    assert view["phase"] == {"arbeitsschritt:a": "current", "arbeitsschritt:x": "looped", "arbeitsschritt:b": "looped"}


def test_looped_follows_the_laufpfad_not_the_display_order():
    # Route order puts c before b in the display, yet c -> b is the return and b -> c the forward step.
    step = lambda name, routes: {"id": f"arbeitsschritt:{name}", "kind": "arbeitsschritt", "parent": "teilprozess:t",
                                 "meta": {"routen": routes}}
    nodes = [{"id": "hauptprozess:h", "kind": "hauptprozess", "parent": None},
             {"id": "teilprozess:t", "kind": "teilprozess", "parent": "hauptprozess:h"},
             step("a", {"skip": "arbeitsschritt:c", "normal": "arbeitsschritt:b"}),
             step("c", {"nacharbeit": "arbeitsschritt:b", "gut": "end:fertig"}), step("b", {"weiter": "arbeitsschritt:c"})]
    closed = lambda name, route: {"arbeitsschritt_ref": f"arbeitsschritt:{name}", "status": "abgeschlossen", "gewaehlte_route": route}
    history = [closed("a", "normal"), closed("b", "weiter"), closed("c", "nacharbeit")]
    returned = project.phases(nodes, history + [{"arbeitsschritt_ref": "arbeitsschritt:b", "status": "aktiv"}])
    assert returned["phase"] == {"arbeitsschritt:a": "done", "arbeitsschritt:b": "current", "arbeitsschritt:c": "looped"}
    finished = project.phases(nodes, history + [closed("b", "weiter"), closed("c", "gut")])
    assert finished["phase"] == {"arbeitsschritt:a": "done", "arbeitsschritt:b": "done", "arbeitsschritt:c": "done"}
    assert finished["ended"] == "end:fertig"


def _waiting_run(root: Path, **entry) -> Path:
    context = root / "vorgaenge" / "video-001" / "CONTEXT.md"
    metadata = read_context(context)
    metadata["laufpfad"][-1] |= {"status": "wartend", "wiedereinstieg": {"ausloeser": "Lieferschein", "continuation_ref": "mail:lieferschein"}}
    metadata["laufpfad"][-1] |= entry
    replace_context(context, metadata)
    return context


def test_waiting_run_shows_status_start_and_next_check_verbatim_without_judging_lateness(tmp_path):
    root = _workspace(tmp_path)
    context = _waiting_run(root, status_seit="2026-10-20T09:00:00+02:00",
                           wiedereinstieg={"ausloeser": "Lieferschein", "continuation_ref": "mail:lieferschein",
                                           "faellig": "2026-11-02T17:00:00+01:00"})
    model = selection.single_vorgang(context)
    assert model["issues"] == []
    stand = model["stand"]
    assert (stand["kind"], stand["status_seit"], stand["faellig"]) == ("waiting", "2026-10-20T09:00:00+02:00", "2026-11-02T17:00:00+01:00")
    model["language"] = "de"
    result = render_page(tmp_path, write.page_html(model))
    text = text_content(result["head"]) + text_content(result["sheet"])
    assert "Status seit: 2026-10-20T09:00:00+02:00" in text
    assert "Nächste Prüfung: 2026-11-02T17:00:00+01:00" in text
    assert "überfällig" not in text.lower()


def test_overview_names_the_human_decision_of_a_waiting_gate(tmp_path):
    root = _workspace(tmp_path)
    _waiting_run(root)
    overview = selection.workspace_site(root)["index.html"]
    overview["language"] = "de"
    text = text_content(render_page(tmp_path, write.page_html(overview))["sheet"])
    assert "Mensch entscheidet: freigegeben · abgelehnt" in text and "Wartet auf: Lieferschein" in text


def test_missing_time_fields_stay_unknown(tmp_path):
    root = _workspace(tmp_path)
    current = selection.single_vorgang(root / "vorgaenge" / "video-001" / "CONTEXT.md")
    assert current["stand"]["status_seit"] is None and current["stand"]["faellig"] is None
    current["language"] = "de"
    text = text_content(render_page(tmp_path, write.page_html(current))["head"])
    assert "Status seit: unbekannt" in text and "Nächste Prüfung" not in text
    waiting = selection.single_vorgang(_waiting_run(root))
    waiting["language"] = "en"
    text = text_content(render_page(tmp_path, write.page_html(waiting))["head"])
    assert "Status since: unknown" in text and "No next check stated in history" in text


def test_workspace_site_lists_every_application_and_run(tmp_path):
    root = _workspace(tmp_path, applications=("video", "schnitt"),
                      runs=(("video-001", "video"), ("video-002", "video"), ("schnitt-001", "schnitt")))
    (root / "vorgaenge" / "video-002" / "start" / "001" / "input" / "auftrag.md").write_text("kaputt", encoding="utf-8")
    pages = selection.workspace_site(root)
    assert set(pages) == {"index.html", "a-schnitt.html", "a-video.html",
                          "v-schnitt-001.html", "v-video-001.html", "v-video-002.html"}
    overview = pages["index.html"]
    assert overview["population"] == {"applications": 2, "applications_refused": 0, "historic": 0, "runs": 3, "runs_refused": 1, "ist": 0}
    assert overview["ist"] is None
    by_folder = {a["folder"]: a for a in overview["applications"]}
    assert [r["page"] for r in by_folder["video"]["runs"]] == ["v-video-001.html"]
    assert [r["page"] for r in by_folder["schnitt"]["runs"]] == ["v-schnitt-001.html"]
    assert [r["page"] for r in overview["unassigned"]] == ["v-video-002.html"]
    assert overview["unassigned"][0]["issues"]
    assert all(r["matches_head"] for a in overview["applications"] for r in a["runs"])
    assert all(m["site"]["index"] == "index.html" for m in pages.values())


def test_workspace_marks_runs_bound_to_an_older_definition(tmp_path):
    root = _workspace(tmp_path)
    step = root / "applications" / "video" / "produktion" / "start" / "CONTEXT.md"
    step.write_text(step.read_text(encoding="utf-8").replace("Erzeuge", "Erstelle"), encoding="utf-8")
    git(root, "commit", "-qam", "application v2")
    overview = selection.workspace_site(root)["index.html"]
    run = overview["applications"][0]["runs"][0]
    assert run["matches_head"] is False and run["stand"]["kind"] == "current"


def test_workspace_inventory_keeps_files_and_links(tmp_path):
    root = _workspace(tmp_path)
    (root / "vorgaenge" / "notiz.md").write_text("x")
    (root / "applications" / "alias").symlink_to(root / "applications" / "video")
    pages = selection.workspace_site(root)
    overview = pages["index.html"]
    assert overview["population"]["runs_refused"] == 1 and overview["population"]["applications_refused"] == 1
    assert {r["id"] for r in overview["unassigned"]} == {"vorgaenge/notiz.md"}


def test_workspace_change_during_generation_writes_nothing(tmp_path, monkeypatch):
    root = _workspace(tmp_path)
    real = selection.validate

    def validate_and_add(path):
        report = real(path)
        (root / "vorgaenge" / "neu").mkdir()
        return report

    monkeypatch.setattr(selection, "validate", validate_and_add)
    with pytest.raises(SystemExit):
        selection.workspace_site(root)


def test_unreadable_run_is_listed_not_fatal(tmp_path):
    root = _workspace(tmp_path, runs=(("video-001", "video"), ("video-002", "video")))
    locked = root / "vorgaenge" / "video-002" / "CONTEXT.md"
    locked.chmod(0)
    try:
        overview = selection.workspace_site(root)["index.html"]
    finally:
        locked.chmod(0o644)
    assert overview["population"]["runs"] == 2 and overview["population"]["runs_refused"] == 1


def test_run_whose_application_left_the_working_files_keeps_its_leistung(tmp_path):
    root = _workspace(tmp_path)
    shutil.rmtree(root / "applications" / "video")
    git(root, "commit", "-qam", "remove application")
    overview = selection.workspace_site(root)["index.html"]
    historic = [a for a in overview["applications"] if not a["current"]]
    assert len(historic) == 1 and historic[0]["id"] == "hauptprozess:video"
    assert historic[0]["runs"][0]["page"] == "v-video-001.html" and not overview["unassigned"]


def test_waiting_and_reached_ends_are_not_progress():
    nodes = [{"id": "hauptprozess:h", "kind": "hauptprozess", "parent": None, "children": ["teilprozess:t"]},
             {"id": "teilprozess:t", "kind": "teilprozess", "parent": "hauptprozess:h", "children": ["arbeitsschritt:a"]},
             {"id": "arbeitsschritt:a", "kind": "arbeitsschritt", "parent": "teilprozess:t", "children": [],
              "meta": {"routen": {"stop": "end:abgebrochen"}}, "routes": [["stop", "end:abgebrochen"]]}]
    waiting = [{"arbeitsschritt_ref": "arbeitsschritt:a", "versuch": 1, "status": "wartend"}]
    run = {"id": "vorgang:r", "meta": {"laufpfad": waiting}}
    tree = project.map_tree(nodes, run, project.phases(nodes, waiting))
    assert tree["children"][0]["children"][0]["phase"] == "waiting"
    ended = [{"arbeitsschritt_ref": "arbeitsschritt:a", "versuch": 1, "status": "abgeschlossen", "gewaehlte_route": "stop"}]
    run = {"id": "vorgang:r", "meta": {"laufpfad": ended}}
    tree = project.map_tree(nodes, run, project.phases(nodes, ended))
    route = tree["children"][0]["children"][0]["children"][0]
    assert route["phase"] == "reached" and route["dir"] == "end" and tree["phase"] == "reached"
    assert tree["children"][0]["phase"] == ""  # a container never takes done or a lime colour


def test_workspace_cli_writes_one_folder(tmp_path):
    root = _workspace(tmp_path)
    out = tmp_path / "ansicht"
    assert run_cli(root, "--out", out, "--json") == 0
    names = {p.name for p in out.iterdir()}
    assert names == {"index.html", "a-video.html", "v-video-001.html", "model.json"}
    assert embedded((out / "index.html").read_text(encoding="utf-8"))["kind"] == "overview"


def test_waiting_attempt_is_not_active():
    nodes = [{"id": "hauptprozess:h", "kind": "hauptprozess", "parent": None, "children": ["teilprozess:t"]},
             {"id": "teilprozess:t", "kind": "teilprozess", "parent": "hauptprozess:h", "children": ["arbeitsschritt:a"]},
             {"id": "arbeitsschritt:a", "kind": "arbeitsschritt", "parent": "teilprozess:t", "children": [],
              "meta": {"routen": {"stop": "end:abgebrochen"}}, "routes": [["stop", "end:abgebrochen"]]}]
    waiting = [{"arbeitsschritt_ref": "arbeitsschritt:a", "versuch": 1, "status": "wartend"}]
    tree = project.map_tree(nodes, {"id": "vorgang:r", "meta": {"laufpfad": waiting}}, project.phases(nodes, waiting))
    assert tree["children"][0]["children"][0]["children"][0]["phase"] == "waiting"


def test_vanished_application_keeps_each_bound_leistung(tmp_path):
    root = _workspace(tmp_path)
    hp = root / "applications" / "video" / "CONTEXT.md"
    hp.write_text(hp.read_text(encoding="utf-8").replace("Veröffentlichtes Video", "Zweite Leistung"), encoding="utf-8")
    git(root, "commit", "-qam", "applications v2")
    second = root / "vorgaenge" / "video-002"
    shutil.copytree(root / "vorgaenge" / "video-001", second)
    run = second / "CONTEXT.md"
    v1, v2 = (git(root, "rev-parse", ref) for ref in ("HEAD~1:applications/video", "HEAD:applications/video"))
    run.write_text(run.read_text(encoding="utf-8").replace(v1, v2).replace("vorgang:video-001", "vorgang:video-002"),
                   encoding="utf-8")
    shutil.rmtree(root / "applications" / "video")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "remove application")
    overview = selection.workspace_site(root)["index.html"]
    historic = [a for a in overview["applications"] if not a["current"]]
    assert sorted(a["leistung"]["ergebnis"] for a in historic) == ["Veröffentlichtes Video", "Zweite Leistung"]
    assert all(len(a["runs"]) == 1 for a in historic) and overview["population"]["historic"] == 2


def test_run_evidence_changed_after_validation_is_refused(tmp_path, monkeypatch):
    root = _workspace(tmp_path)
    real = selection.validate

    def validate_then_change(path):
        report = real(path)
        (root / "vorgaenge" / "video-001" / "start" / "001" / "input" / "auftrag.md").write_text("später", encoding="utf-8")
        return report

    monkeypatch.setattr(selection, "validate", validate_then_change)
    run = selection.workspace_site(root)["v-video-001.html"]
    assert "nodes" not in run and run["issues"][0]["code"] == "view.unreadable"


def test_head_moved_and_restored_cannot_relabel_the_definition(tmp_path, monkeypatch):
    root = _workspace(tmp_path)
    first = git(root, "rev-parse", "HEAD")
    application_page, vorgang_page = selection.application_page, selection.vorgang_page

    def advance(*args):
        page = application_page(*args)
        hp = root / "applications" / "video" / "CONTEXT.md"
        hp.write_text(hp.read_text(encoding="utf-8") + "\nNachtrag\n", encoding="utf-8")
        git(root, "commit", "-qam", "later")
        return page

    def restore(*args):
        git(root, "reset", "-q", "--hard", first)
        return vorgang_page(*args)

    monkeypatch.setattr(selection, "application_page", advance)
    monkeypatch.setattr(selection, "vorgang_page", restore)
    overview = selection.workspace_site(root)["index.html"]
    assert overview["applications"][0]["head"] == git(root, "rev-parse", f"{first}:applications/video")


def test_fifo_in_a_run_is_recorded_not_read(tmp_path):
    root = _workspace(tmp_path)
    os.mkfifo(root / "vorgaenge" / "video-001" / "pruefen" / "001" / "extra-fifo")
    state = selection.capture(root / "vorgaenge" / "video-001")
    assert state["pruefen/001/extra-fifo"].startswith("special:")


def test_overlong_slug_gets_a_short_page_name():
    used = {"index.html"}
    assert re.fullmatch(r"a-[0-9a-f]{12}\.html", selection.page_name("a", "x" * 250, used))


# ---------- Ist-Prozess files and the Notwendigkeit table ----------

REPO = HERE.parent
TEMPLATE_DE = REPO / "02_protocol" / "impacts-architect" / "templates" / "de" / "ist-prozess.md"
TEMPLATE_EN = REPO / "02_protocol" / "impacts-architect" / "templates" / "ist-prozess.md"


def ist_node(path: Path) -> dict:
    return {"id": path.name, "kind": "ist-prozess", "parent": None, "children": [], **read.read_file(path, path.name)}


def ist_text(path: Path, change=None) -> Path:
    text = TEMPLATE_DE.read_text(encoding="utf-8")
    path.write_text(change(text) if change else text, encoding="utf-8")
    return path


def test_cell_mapping_reads_the_leading_word_and_keeps_the_answer(tmp_path):
    rows = project.necessity(ist_node(ist_text(tmp_path / "antrag.md")))["rows"]
    coordination = rows[0]["answers"][1]
    assert (coordination["mark"], coordination["labels"], coordination["solid"]) == ("yes", ["hypothesis"], False)
    assert "getrennt nur durch E-Mail-Kanal" in project.plain(coordination["spans"])
    assert (rows[1]["answers"][0]["mark"], rows[1]["answers"][0]["solid"]) == ("yes", False)
    assert rows[5]["answers"][1]["mark"] == "no"
    assert rows[9]["answers"][0]["mark"] == "yes"
    cell = lambda text: project.answer(blocks.spans(text))
    assert cell("Yes (`verified`)")["solid"] is True
    assert cell("`open`")["mark"] == "open" and cell("offen, Katalog fehlt")["mark"] == "open"
    assert (cell("Teilweise")["mark"], cell("Teilweise")["word"]) == ("other", "Teilweise")
    assert cell("Ja (`verified`, `hypothesis`)")["solid"] is False


def test_analysis_rows_carry_their_file_lines(tmp_path):
    found = project.necessity(ist_node(ist_text(tmp_path / "antrag.md")))
    assert found["status"] == "table" and found["heading_line"] == 59
    node = ist_node(tmp_path / "antrag.md")
    section, index = found["at"]
    assert node["sections"][section]["blocks"][index]["line"] == 61
    assert (found["rows"][0]["line"], found["rows"][11]["line"]) == (63, 74)
    assert found["conditions"]["C1"]["line"] == 35 and found["activities"]["3"]["line"] == 48


def test_conditions_resolve_from_the_file(tmp_path):
    found = project.necessity(ist_node(ist_text(tmp_path / "antrag.md", lambda t: t.replace(
        "| 4 | Fehlende Eingabe für C2 |", "| 4 | Fehlende Eingabe für C2 und C9 |"))))
    rows = found["rows"]
    assert rows[1]["serves"]["ids"] == ["C2"] and rows[0]["serves"]["ids"] == []
    assert rows[5]["serves"]["ids"] == ["C1"] and "Entscheidungsbefunde" in project.plain(rows[5]["serves"]["spans"])
    assert rows[3]["serves"] == {"spans": rows[3]["serves"]["spans"], "ids": ["C2"], "unknown": ["C9"]}
    assert "open" in found["conditions"]["C2"]["labels"]
    english = project.necessity(ist_node(TEMPLATE_EN))
    german = project.necessity(ist_node(TEMPLATE_DE))
    assert english["status"] == "table" and len(english["rows"]) == 12
    assert [r["serves"]["ids"] for r in english["rows"]] == [r["serves"]["ids"] for r in german["rows"]]


@pytest.mark.parametrize("change, reason", [
    (lambda t: t.replace("| Nr. | Dient | Ergebnisarbeit?", "| Nr. | Zweck | Ergebnisarbeit?"), "shape"),
    (lambda t: t.replace("| 9 | C1 | Ja (`reported`)", "| 9 | C1 \\ C4 | Ja (`reported`)"), "unreadable"),
    (lambda t: t.replace("| 8 | C1 | Ja (`reported`) | Nein |", "| 8 | C1 | Ja (`reported`) |"), "unreadable"),
    (lambda t: t.replace("\n## Wo wird angehalten", "\n### Analyse\n\n| Nr. | Dient |\n|---|---|\n| 1 | C1 |\n\n## Wo wird angehalten"), "several"),
])
def test_unsupported_analysis_stays_verbatim(tmp_path, change, reason):
    node = ist_node(ist_text(tmp_path / "antrag.md", change))
    found = project.necessity(node)
    assert (found["status"], found["reason"], found["rows"]) == ("unsupported", reason, [])
    text = (tmp_path / "antrag.md").read_text(encoding="utf-8")
    start = text.index("### Analyse")
    table = text[start:text.index("\n\n", text.index("| 12 |", start))]
    rendered = words([p["blocks"] for p in node["sections"]])
    for word in re.findall(r"\w+", table):
        assert word in rendered, word


def test_ist_prozess_without_analysis_keeps_every_section(tmp_path):
    path = tmp_path / "angebot.md"
    path.write_text("---\ntype: ist-prozess\nname: Angebot\nevidence_status: reported\n---\n\n# Angebot\n\nVorab.\n\n"
                    "## Ablauf heute\n\n1. Entwurf\n2. Einreichung (`verified`)\n\n## Quellen\n\nAkte.\n", encoding="utf-8")
    node = ist_node(path)
    found = project.necessity(node)
    assert found["status"] == "none" and found["rows"] == [] and found["conditions"] is None
    assert [p["heading"] for p in node["sections"]] == [None, "Ablauf heute", "Quellen"]
    assert node["meta_lines"] == [2, 4] and node["path_in_revision"] == "angebot.md"


def _ist_workspace(tmp_path, files: dict) -> Path:
    root = _workspace(tmp_path)
    folder = root / "grundlagen" / "ist-prozesse"
    folder.mkdir(parents=True)
    for name, text in files.items():
        (folder / name).write_text(text, encoding="utf-8")
    return root


def test_hostile_ist_prozess_text_stays_data(tmp_path):
    hostile = "<img src=x onerror=alert(1)> </script> javascript:alert(1)  "
    text = TEMPLATE_DE.read_text(encoding="utf-8").replace("name: Antrag prüfen und entscheiden", f"name: \"{hostile}\"") \
        .replace("| C2 | Eine Entscheidung", f"| C2{hostile} | Eine Entscheidung").replace("| 2 | C2 | Ja", f"| 2 | C2 {hostile} | Ja")
    root = _ist_workspace(tmp_path, {"antrag.md": text, "Böse <x>.md": text})
    pages = selection.workspace_site(root)
    names = [n for n in pages if n.startswith("i-")]
    assert "i-antrag.html" in names and len(names) == 2 and all(write.NAME.fullmatch(n) for n in names)
    for name in names:
        html = write.page_html(pages[name])
        assert html.count("</script>") == 2 and " " not in html
        assert embedded(html) == json.loads(json.dumps(pages[name], default=str))
    template = write.TEMPLATE.read_text(encoding="utf-8")
    for api in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", 'setAttribute("style"'):
        assert api not in template
    assert write.NAME.fullmatch("i-x.html") and not write.NAME.fullmatch("i-../x.html")


def test_links_reject_unsafe_fragments(tmp_path):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not installed")
    template = write.TEMPLATE.read_text(encoding="utf-8")
    code = "\n".join(re.search(rf"^const {name} = .*?;$", template, re.M | re.S).group(0) for name in ("PAGE", "safeHref"))
    script = tmp_path / "links.js"
    script.write_text(code + "\nconsole.log(JSON.stringify([safeHref('v-a.html', 'arbeitsschritt:x'), safeHref('v-a.html', 'a\"b'),"
                      " safeHref('v-a.html', '#javascript:'), safeHref('../x.html', 'a'), safeHref('javascript:alert(1)', null),"
                      " safeHref('i-x.html', null), safeHref('i-x.html', 'n-1/1 (b)')]));\n", encoding="utf-8")
    out = json.loads(subprocess.run([node, str(script)], capture_output=True, text=True, check=True).stdout)
    assert out == ["v-a.html#arbeitsschritt%3Ax", "v-a.html#a%22b", "v-a.html#%23javascript%3A", None, None, "i-x.html",
                   "i-x.html#n-1%2F1%20%28b%29"]


def test_ist_inventory_lists_what_it_does_not_read(tmp_path):
    root = _ist_workspace(tmp_path, {"antrag.md": TEMPLATE_DE.read_text(encoding="utf-8"), "notiz.txt": "x",
                                     "router.md": "---\ntype: workspace\n---\n# R\n"})
    (root / "grundlagen" / "ist-prozesse" / "alias.md").symlink_to(root / "grundlagen" / "ist-prozesse" / "antrag.md")
    (root / "grundlagen" / "ist-prozesse" / "teil").mkdir()
    pages = selection.workspace_site(root)
    ist = pages["index.html"]["ist"]
    assert [p["page"] for p in ist["pages"]] == ["i-antrag.html"] and ist["pages"][0]["analysis"] == "table"
    assert {s["file"].rsplit("/", 1)[-1]: s["reason"] for s in ist["skipped"]} == {
        "alias.md": "link", "notiz.txt": "not-markdown", "router.md": "wrong-type", "teil": "dir"}
    assert pages["index.html"]["population"]["ist"] == 1


def test_ist_change_during_generation_writes_nothing(tmp_path, monkeypatch):
    root = _ist_workspace(tmp_path, {"antrag.md": TEMPLATE_DE.read_text(encoding="utf-8")})
    real = selection.validate

    def validate_and_edit(path):
        report = real(path)
        (root / "grundlagen" / "ist-prozesse" / "antrag.md").write_text("geändert", encoding="utf-8")
        return report

    monkeypatch.setattr(selection, "validate", validate_and_edit)
    out = tmp_path / "ansicht"
    with pytest.raises(SystemExit):
        run_cli(root, "--out", out)
    assert not out.exists()


def test_unreadable_ist_prozess_is_refused_not_skipped(tmp_path):
    root = _ist_workspace(tmp_path, {"kaputt.md": "---\ntype: [ist-prozess\n---\n"})
    pages = selection.workspace_site(root)
    assert pages["i-kaputt.html"]["issues"][0]["code"] == "view.unreadable"
    assert pages["index.html"]["ist"]["pages"][0]["issues"]


# ---------- phases, map and Stand ----------

def _nodes(gate=None):
    step = lambda name, routes, **meta: {"id": f"arbeitsschritt:{name}", "kind": "arbeitsschritt", "parent": "teilprozess:t", "children": [],
                                         "title": name.title(), "sections": [], "meta": {"routen": routes, **meta}, "routes": list(routes.items())}
    nodes = [{"id": "hauptprozess:h", "kind": "hauptprozess", "parent": None, "children": ["teilprozess:t"], "title": "H", "sections": [], "meta": {}},
             {"id": "teilprozess:t", "kind": "teilprozess", "parent": "hauptprozess:h", "title": "T", "sections": [], "meta": {},
              "children": ["arbeitsschritt:a", "arbeitsschritt:b", "arbeitsschritt:c"]},
             step("a", {"weiter": "arbeitsschritt:b"}),
             step("b", {"freigegeben": "arbeitsschritt:c", "abgelehnt": "arbeitsschritt:a"}, gate=gate),
             step("c", {"fertig": "end:fertig", "stopp": "end:abgebrochen"})]
    project.annotate(nodes)
    return nodes


def _boxes(tree):
    yield tree
    for child in tree["children"]:
        yield from _boxes(child)


def _run(entries):
    return {"id": "vorgang:r", "title": None, "meta": {"laufpfad": entries}}


DONE_A = {"arbeitsschritt_ref": "arbeitsschritt:a", "versuch": 1, "status": "abgeschlossen", "gewaehlte_route": "weiter"}


def test_phases_keep_green_for_the_position_only():
    nodes = _nodes(gate="human")
    cases = {
        "current": [DONE_A, {"arbeitsschritt_ref": "arbeitsschritt:b", "versuch": 1, "status": "aktiv"}],
        "next": [DONE_A],
        "waiting": [DONE_A, {"arbeitsschritt_ref": "arbeitsschritt:b", "versuch": 1, "status": "wartend"}],
        "ended": [DONE_A, {"arbeitsschritt_ref": "arbeitsschritt:b", "versuch": 1, "status": "abgeschlossen", "gewaehlte_route": "abgelehnt"},
                  {"arbeitsschritt_ref": "arbeitsschritt:a", "versuch": 2, "status": "abgeschlossen", "gewaehlte_route": "weiter"},
                  {"arbeitsschritt_ref": "arbeitsschritt:b", "versuch": 2, "status": "abgeschlossen", "gewaehlte_route": "freigegeben"},
                  {"arbeitsschritt_ref": "arbeitsschritt:c", "versuch": 1, "status": "abgeschlossen", "gewaehlte_route": "stopp"}],
    }
    for kind, entries in cases.items():
        view = project.phases(nodes, entries)
        tree = project.map_tree(nodes, _run(entries), view)
        boxes = list(_boxes(tree))
        assert not any(b["phase"] == "done" for b in boxes if b["kind"] in ("hp", "tp")), kind
        b = next(x for x in boxes if x.get("ref") == "arbeitsschritt:b")
        if kind == "waiting":
            assert b["phase"] == "waiting" and view["current"] == "arbeitsschritt:b"
            assert {r["route"]: r["phase"] for r in b["children"] if r["kind"] == "route"} == {"freigegeben": "possible", "abgelehnt": "possible"}
            assert view["phase"]["arbeitsschritt:c"] == "possible"
        if kind == "current":
            assert b["phase"] == "current" and {r["phase"] for r in b["children"] if r["kind"] == "route"} == {"option"}
        if kind == "ended":
            assert tree["phase"] == "reached" and tree["children"][0]["phase"] == ""
            assert {r["route"]: r["phase"] for r in boxes if r.get("ref") is None and r["kind"] == "route" and r["target"].startswith("end:")} \
                == {"fertig": "past", "stopp": "reached"}
    routes = {r[0]: r[3] for r in next(n for n in nodes if n["id"] == "arbeitsschritt:b")["routes"]}
    assert routes == {"freigegeben": "forward", "abgelehnt": "back"}
    assert {r[0]: r[3] for r in nodes[4]["routes"]} == {"fertig": "end", "stopp": "end"}


def test_stand_has_one_case_per_kind():
    # The aktiv entry at gate b is the older, still valid shape; the viewer must keep showing it.
    nodes = _nodes(gate="human")
    stand = lambda entries: project.stand(nodes, _run(entries), project.phases(nodes, entries))
    current = stand([DONE_A, {"arbeitsschritt_ref": "arbeitsschritt:b", "versuch": 1, "status": "aktiv"}])
    assert (current["kind"], current["step_title"], current["part_title"], current["gate"], current["versuch"]) == ("current", "B", "T", "human", 1)
    assert [r[0] for r in current["routes"]] == ["freigegeben", "abgelehnt"]
    following = stand([DONE_A])
    assert (following["kind"], following["step"], following["from_title"], following["route"], following["entry"]) == ("next", "arbeitsschritt:b", "A", "weiter", 1)
    resume = {"ausloeser": "Unterlagen <b>da</b>", "continuation_ref": "records/x.md"}
    waiting = stand([DONE_A, {"arbeitsschritt_ref": "arbeitsschritt:b", "versuch": 1, "status": "wartend", "wiedereinstieg": resume}])
    assert (waiting["kind"], waiting["ausloeser"], waiting["continuation_ref"]) == ("waiting", "Unterlagen <b>da</b>", "records/x.md")
    bare = stand([DONE_A, {"arbeitsschritt_ref": "arbeitsschritt:b", "versuch": 1, "status": "wartend"}])
    assert (bare["kind"], bare["ausloeser"]) == ("waiting", None)
    ended = stand([DONE_A, {"arbeitsschritt_ref": "arbeitsschritt:b", "versuch": 1, "status": "abgeschlossen", "gewaehlte_route": "freigegeben"},
                   {"arbeitsschritt_ref": "arbeitsschritt:c", "versuch": 1, "status": "abgeschlossen", "gewaehlte_route": "fertig"}])
    assert (ended["kind"], ended["end"], ended["route"], ended["from_title"], ended["entry"], ended["entries"]) == ("ended", "fertig", "fertig", "C", 3, 3)
    assert project.stand(nodes, None, None) == {"kind": "definition"}


def test_run_summary_copies_the_wait_verbatim(tmp_path):
    root = _workspace(tmp_path)
    run = root / "vorgaenge" / "video-001" / "CONTEXT.md"
    run.write_text(run.read_text(encoding="utf-8").replace("status: aktiv", "status: wartend\n  wiedereinstieg:\n"
                   "    ausloeser: Freigabe liegt vor\n    continuation_ref: records/video.md"), encoding="utf-8")
    overview = selection.workspace_site(root)["index.html"]
    summary = overview["applications"][0]["runs"][0]
    assert summary["issues"] == [], summary["issues"]
    assert (summary["stand"]["kind"], summary["stand"]["ausloeser"], summary["statuses"]) == ("waiting", "Freigabe liegt vor", ["abgeschlossen", "wartend"])


def test_step_refs_say_nothing_the_file_does_not(tmp_path):
    model = selection.application_page(write_application(tmp_path / "video"))
    steps = [n for n in model["nodes"] if n["kind"] == "arbeitsschritt"]
    for step in steps:
        assert set(step) >= {"job", "authority", "flow", "path_in_revision", "meta_lines"}
        assert step["meta_lines"][0] == 2 and step["path_in_revision"] == step["path"]
    no_sections = {"id": "arbeitsschritt:x", "kind": "arbeitsschritt", "sections": []}
    assert project.step_refs(no_sections) == {"job": None, "authority": None, "flow": None, "execution": []}
    said = [["t", "Nur die bevollmächtigte Vertretung schreibt ", ""], ["code", "freigabe", ""]]
    gated = {"sections": [{"heading": "Human Check", "line": 37, "blocks": [{"type": "list", "items": [], "line": 38},
                                                                         {"type": "para", "spans": said, "line": 40}]}]}
    assert project.step_refs(gated)["authority"] == {"heading": "Human Check", "line": 37, "spans": said}
    bare = {"sections": [{"heading": "Befugnis", "line": 9, "blocks": []}]}
    assert project.step_refs(bare)["authority"] == {"heading": "Befugnis", "line": 9, "spans": None}
    template = write.TEMPLATE.read_text(encoding="utf-8")
    assert "Steht nicht in den Dateien." in template  # the one fallback for an empty triad slot


# ---------- copy honesty and removed parts ----------

def test_copy_is_quoted_from_the_protocol():
    templates = "\n".join(p.read_text(encoding="utf-8") for p in (REPO / "02_protocol").rglob("*.md") if "templates" in p.parts)
    for table in project.SUBTITLE.values():
        for sentence in table.values():
            assert sentence in templates, sentence
    page = write.TEMPLATE.read_text(encoding="utf-8")
    translation = (REPO / "02_protocol" / "translations" / "de.md").read_text(encoding="utf-8")
    tables = word_tables(page)
    question_keys = re.findall(r"W\.(\w+)", re.search(r"const QUESTIONS = \[(.*?)\];", page, re.S).group(1))
    found = [tables["de"][key] for key in question_keys]
    assert len(found) == 5 and all(q in translation for q in found)
    yes_key = re.search(r"const YES_NOTE = W\.(\w+);", page).group(1)
    assert tables["de"][yes_key] in TEMPLATE_DE.read_text(encoding="utf-8")



def test_removed_parts_stay_removed():
    package = "\n".join(p.read_text(encoding="utf-8") for p in PACKAGE.iterdir() if p.suffix in (".py", ".html"))
    for gone in ("view.path", "function facts", "dblclick", "prefers-color-scheme: light", "prefers-color-scheme:light", "MAP_PHASE", "STATUS = {\"abgeschlossen\": \"erledigt\"",
                 "Begründung anzeigen", "Leistung dieser Fassung", 'kv("Steht bei"', "scrollIntoView({block: \"nearest\", inline: \"center\""):
        assert gone not in package, gone
    page = write.TEMPLATE.read_text(encoding="utf-8")
    # replaceChildren(null) renders the text "null"; only the filtering helper may call it.
    assert page.count("replaceChildren(") == 1 and "const fill = (element, ...children) => element.replaceChildren(" in page


# ---------- fix round 2 ----------

def test_answer_marks_a_caveat_behind_the_word(tmp_path):
    rows = project.necessity(ist_node(ist_text(tmp_path / "antrag.md")))["rows"]
    assert rows[0]["answers"][2]["more"] is True  # "Nein; erster Durchlauf"
    assert rows[7]["answers"][1]["more"] is False  # "Nein"
    assert rows[5]["answers"][1]["more"] is True and rows[4]["answers"][3]["more"] is True
    cell = lambda text: project.answer(blocks.spans(text))["more"]
    assert not cell("Ja (`reported`)") and not cell("Ja (`verified`, `hypothesis`)") and not cell("`open`")
    assert cell("offen, Katalog fehlt") and cell("Ja, nur für eine eigene Regel (`reported`)")


def test_linked_grundlagen_is_listed_not_followed(tmp_path):
    root = _workspace(tmp_path)
    outside = tmp_path / "draussen" / "ist-prozesse"
    outside.mkdir(parents=True)
    (outside / "x.md").write_text("---\ntype: ist-prozess\nname: Geheim ausserhalb\n---\n# X\n", encoding="utf-8")
    (root / "grundlagen").symlink_to(tmp_path / "draussen")
    pages = selection.workspace_site(root)
    assert not [n for n in pages if n.startswith("i-")]
    assert pages["index.html"]["ist"] == {"pages": [], "skipped": [{"file": "grundlagen", "reason": "link"}]}
    assert "Geheim" not in json.dumps(pages, default=str)


def test_readable_copy_keeps_the_field_name_in_sources_only():
    page = write.TEMPLATE.read_text(encoding="utf-8")
    script = re.search(r"<script>(.*?)</script>", page, re.S).group(1)
    text_values = re.findall(r'"([^"\n]*laufpfad[^"\n]*)"', script.split("const W =", 1)[1])
    text_values += [text for table in word_tables(page).values() for text in table.values() if "laufpfad" in text]
    for text in text_values:
        assert re.search(r"laufpfad-Eintr|Liste laufpfad|laufpfad entr|laufpfad list|^ · laufpfad$|^laufpfad$", text), text
    assert "aktiv laut Verlauf" in page
    for gone in ("function sectionLabel", "written.has(", "const chips ="):
        assert gone not in page, gone


def test_execution_kinds_come_only_from_labelled_processing_items():
    found = lambda text: [e["kind"] for e in project.execution({"blocks": blocks.blocks(text)})]
    assert found("- Deterministisches System: `rechenweg:frist`\n- Klassifikator: vollständig ja/nein/offen\n"
                 "- Agent: Begründung\n- Mensch: Zusage") == ["deterministic", "classifier", "agent", "human"]
    assert found("- Classifier: complete?\n- Human: sign") == ["classifier", "human"]
    # Prose, nested items and unknown words name no kind; the view does not guess.
    assert found("Der Agent schreibt den Text.\n\n- Physisch: Montage\n- Liste\n  - Agent: tief") == []
    assert project.execution(None) == []


def test_move_cell_names_targets_and_removal():
    cell = lambda text: blocks.spans(text)
    parse = lambda text: (project._unique(project.TARGET.findall(project.plain(cell(text)))),
                          any(k == "code" and x == project.REMOVED for k, x, _ in cell(text)))
    assert parse("Behalten (`reported`); arbeitsschritt:entscheiden, arbeitsschritt:bescheid-entwerfen") == (["entscheiden", "bescheid-entwerfen"], False)
    assert parse("Streichen (`hypothesis`); `entfaellt`") == ([], True)
    assert parse("x-arbeitsschritt:nein und hauptprozess:arbeitsschritt:nein und entfaellt") == ([], False)
    assert project.necessity(ist_node(TEMPLATE_DE))["rows"][0]["move"]["resolved"] is None


def test_ist_targets_resolve_only_within_this_view(tmp_path):
    text = ist_text(tmp_path / "antrag.md", lambda t: t
        .replace("soweit C1 trägt (`reported`); arbeitsschritt:entscheiden |\n| 9 |",
                 "soweit C1 trägt (`reported`); arbeitsschritt:pruefen arbeitsschritt:fehlt |\n| 9 |", 1)
        .replace("Dieselbe Korrektur wie bei 3 |\n| 5 |", "Dieselbe Korrektur wie bei 3; `entfaellt` |\n| 5 |", 1)).read_text(encoding="utf-8")
    root = _ist_workspace(tmp_path, {"antrag.md": text})
    git(root, "add", ".")
    git(root, "commit", "-qm", "ist")
    pages = selection.workspace_site(root)
    rows = {r["nr"]: r for r in pages["i-antrag.html"]["necessity"]["rows"]}
    found, gap = rows["8"]["move"]["resolved"]
    assert (found["status"], found["page"], found["gate"], gap["status"]) == ("found", "a-video.html", True, "missing")
    assert rows["4"]["move"]["removed"] is True and rows["4"]["move"]["resolved"] == []
    step = next(n for n in pages["a-video.html"]["nodes"] if n["id"] == "arbeitsschritt:pruefen")
    assert len(step["ist"]) == 1
    backlink = step["ist"][0]
    assert {k: backlink[k] for k in ("page", "nr", "file", "activity")} == {
        "page": "i-antrag.html", "nr": "8", "file": "grundlagen/ist-prozesse/antrag.md", "activity": "Entscheiden"}
    assert backlink["row"] == rows["8"] and backlink["index"] == 7
    assert backlink["heading"] == "Analyse"
    # A Vorgang draws its bound revision, another snapshot: it gets no back links.
    assert all("ist" not in n for m in pages.values() if m["kind"] == "vorgang" for n in m.get("nodes", []))


def test_a_step_in_two_applications_is_a_gap_not_a_choice(tmp_path):
    root = _workspace(tmp_path, applications=("video", "schnitt"), runs=())
    folder = root / "grundlagen" / "ist-prozesse"
    folder.mkdir(parents=True)
    ist_text(folder / "antrag.md", lambda t: t.replace("Trennung aufheben: Eingang legt die Fallakte direkt an (`hypothesis`)",
                                                      "Trennung aufheben (`hypothesis`); arbeitsschritt:start"))
    git(root, "add", ".")
    git(root, "commit", "-qm", "ist")
    pages = selection.workspace_site(root)
    assert pages["i-antrag.html"]["necessity"]["rows"][0]["move"]["resolved"] == [{"ref": "arbeitsschritt:start", "status": "ambiguous"}]


@pytest.mark.parametrize("text, expected", [
    ("arbeitsschritt:start_extra", []), ("arbeitsschritt:start--extra", []),
    ("arbeitsschritt:startABC", []), ("arbeitsschritt:start:extra", []),
    ("`arbeitsschritt:start-2`", ["start-2"]),
    ("arbeitsschritt:start, arbeitsschritt:other.", ["start", "other"]),
])
def test_target_references_preserve_complete_identity(text, expected):
    assert project.TARGET.findall(text) == expected


def test_all_processing_sections_preserve_contributions_and_source_lines():
    body = "## Processing\n- Agent: Draft\n  continuation\n- Human: Decide\n\n## Other\n- Agent: ignored\n\n## Verarbeitung\n- Deterministisches System: Check\n- Klassifikator: Classify"
    _, sections = blocks.sections(body, 11)
    contributions = project.step_refs({"sections": sections})["execution"]
    assert [e["kind"] for e in contributions] == ["agent", "human", "deterministic", "classifier"]
    assert [e["line"] for e in contributions] == [12, 14, 20, 21]
    assert [e["heading_line"] for e in contributions] == [11, 11, 19, 19]
    assert project.plain(contributions[0]["spans"]) == "Agent: Draft\ncontinuation"


def test_duplicate_conditions_retain_every_declaration_without_a_winner(tmp_path):
    node = ist_node(ist_text(tmp_path / "antrag.md", lambda t: t.replace("| C2 |", "| C1 |", 1)))
    condition = project.necessity(node)["conditions"]["C1"]
    assert condition["status"] == "ambiguous"
    assert condition["cells"] == [] and condition["labels"] == []
    assert [d["line"] for d in condition["declarations"]] == [35, 36]
    assert "open" in condition["declarations"][1]["labels"]
    assert project.plain(condition["declarations"][0]["cells"][0]) != project.plain(condition["declarations"][1]["cells"][0])


def test_activity_inventory_survives_missing_duplicate_and_orphan_analysis(tmp_path):
    text = TEMPLATE_DE.read_text(encoding="utf-8")
    first = "Trennung aufheben: Eingang legt die Fallakte direkt an (`hypothesis`)"
    text = text.replace(first, first + "; arbeitsschritt:start")
    analysis_start = text.index("### Analyse")
    prefix, analysis = text[:analysis_start], text[analysis_start:]
    lines = analysis.splitlines()
    row1 = next(line for line in lines if line.startswith("| 1 |"))
    row2 = next(line for line in lines if line.startswith("| 2 |"))
    analysis = analysis.replace(row1, row1 + "\n" + row1).replace(row2 + "\n", "")
    analysis = analysis.replace(row1 + "\n", row1 + "\n" + row1.replace("| 1 |", "| 99 |", 1) + "\n", 1)
    root = _ist_workspace(tmp_path, {"antrag.md": prefix + analysis})
    pages = selection.workspace_site(root)
    nec = pages["i-antrag.html"]["necessity"]
    mapping = {entry["nr"]: entry for entry in nec["mapping"]}
    assert len(nec["mapping"]) == 13 and len(nec["rows"]) == 13
    assert mapping["1"]["status"] == "ambiguous-analysis" and len(mapping["1"]["analysis_rows"]) == 2
    assert mapping["2"]["status"] == "missing-analysis" and mapping["2"]["activity"]["name"] == "Vollständigkeit prüfen"
    assert mapping["99"]["status"] == "orphan-analysis" and mapping["99"]["activity"] is None
    assert all(r["move"]["resolved"] == [] for r in nec["rows"] if r["nr"] in ("1", "99"))
    start = next(n for n in pages["a-video.html"]["nodes"] if n["id"] == "arbeitsschritt:start")
    assert "ist" not in start


def test_duplicate_activity_numbers_do_not_assign_an_analysis_to_the_first(tmp_path):
    text = TEMPLATE_DE.read_text(encoding="utf-8").replace("| 2 | Vollständigkeit prüfen |", "| 1 | Vollständigkeit prüfen |", 1)
    root = _ist_workspace(tmp_path, {"antrag.md": text})
    nec = selection.workspace_site(root)["i-antrag.html"]["necessity"]
    duplicates = [entry for entry in nec["mapping"] if entry["nr"] == "1"]
    assert len(duplicates) == 2 and all(e["status"] == "ambiguous-activity" for e in duplicates)
    assert len({e["activity"]["name"] for e in duplicates}) == 2
    assert next(r for r in nec["rows"] if r["nr"] == "1")["activity"] is None
    assert next(r for r in nec["rows"] if r["nr"] == "1")["move"]["resolved"] == []


def test_repeated_capture_sections_contribute_all_conditions_and_activities(tmp_path):
    extra = """### Geforderte Bedingungen

| ID | Bedingung | Urheber und Grundlage | Evidenz |
|---|---|---|---|
| C1 | Contradiction in another section | Other basis | `open` |
| C5 | Another condition | Declared basis | `reported` |

### Tätigkeiten in Ablaufreihenfolge

| Nr. | Tätigkeit |
|---|---|
| 13 | Extra captured activity |

"""
    path = ist_text(tmp_path / "antrag.md", lambda t: t.replace("### Analyse", extra + "### Analyse"))
    node = ist_node(path)
    nec = project.necessity(node)
    assert nec["conditions"]["C1"]["status"] == "ambiguous" and len(nec["conditions"]["C1"]["declarations"]) == 2
    assert len(nec["mapping"]) == 13
    extra_activity = next(item for item in nec["mapping"] if item["nr"] == "13")
    assert extra_activity["activity"]["name"] == "Extra captured activity" and extra_activity["status"] == "missing-analysis"
    assert len(nec["conditions_tables"]) == len(nec["activities_tables"]) == 2
    assert nec["conditions_at"] == nec["conditions_tables"][0] and nec["activities_at"] == nec["activities_tables"][0]
    condition_table = node["sections"][nec["conditions_tables"][1][0]]["blocks"][nec["conditions_tables"][1][1]]
    activity_table = node["sections"][nec["activities_tables"][1][0]]["blocks"][nec["activities_tables"][1][1]]
    assert [project.plain(r[0]) for r in condition_table["rows"]] == ["C1", "C5"]
    assert [project.plain(r[0]) for r in activity_table["rows"]] == ["13"]
    source = path.read_text(encoding="utf-8").splitlines()
    for ref in ("C1", "C5"):
        for declaration in nec["conditions"][ref]["declarations"]:
            assert source[declaration["line"] - 1].startswith("| " + ref + " | " + project.plain(declaration["cells"][0]) + " |")
    assert source[extra_activity["activity"]["line"] - 1] == "| 13 | Extra captured activity |"


def test_capture_table_coordinates_exclude_unclassified_source_tables(tmp_path):
    extra = """### Unrelated notes

| ID | Bedingung | Urheber und Grundlage | Evidenz |
|---|---|---|---|
| C9 | No declared condition scope | Notes | `open` |

### Tätigkeiten in Ablaufreihenfolge

| Nr. | Different meaning |
|---|---|
| 99 | Unsupported shape |

"""
    node = ist_node(ist_text(tmp_path / "antrag.md", lambda t: t.replace("### Analyse", extra + "### Analyse")))
    nec = project.necessity(node)
    assert len(nec["conditions_tables"]) == len(nec["activities_tables"]) == 1
    assert "C9" not in nec["conditions"] and "99" not in nec["activities"]


def test_condition_ids_match_whole_declared_names_only():
    known = {"C1", "C1-extra", "C2"}
    assert project.condition_refs("C1-extra", known) == (["C1-extra"], [])
    assert project.condition_refs("C2 und C1; dazu C9", known) == (["C2", "C1"], ["C9"])
    assert project.condition_refs("C1-extra, C1", known) == (["C1-extra", "C1"], [])


@pytest.mark.parametrize("long_id", ["C1.extra", "C1:other", "C1/part", "C1/C9", "scope:C1", "C1 (extra)"])
def test_overlapping_declared_condition_ids_preserve_the_complete_reference(long_id):
    known = {"C1", long_id, "C2"}
    assert project.condition_refs(long_id, known) == ([long_id], [])
    assert project.condition_refs("C2; " + long_id + "; C1, C9", known) == (["C2", long_id, "C1"], ["C9"])
    assert project.condition_refs(long_id + "; " + long_id, known) == ([long_id], [])


@pytest.mark.parametrize("reference", ["C1.extra", "C1:other", "C1/part", "C1/C9", "scope:C1", "urn:scope:C1"])
def test_unknown_composite_condition_identity_is_one_gap_not_a_shorter_reference(reference):
    assert project.condition_refs(reference, {"C1", "C9"}) == ([], [reference])
    assert project.condition_refs("C1, " + reference + "; C2", {"C1", "C9", "C2"}) == (["C1", "C2"], [reference])


def test_condition_reference_punctuation_preserves_prose_and_separate_references():
    known = {"C1", "C2"}
    assert project.condition_refs("C1.", known) == (["C1"], [])
    assert project.condition_refs("C1. Next sentence; C2: explanation.", known) == (["C1", "C2"], [])
    assert project.condition_refs("C1,C2 C9", known) == (["C1", "C2"], ["C9"])
    assert project.condition_refs("C1.extra.more", {"C1", "C1.extra"}) == ([], ["C1.extra.more"])


def test_analysis_retains_unknown_composite_identity_without_a_condition_link(tmp_path):
    node = ist_node(ist_text(tmp_path / "antrag.md", lambda t: t.replace("| 2 | C2 |", "| 2 | C1.extra |", 1)))
    row = next(r for r in project.necessity(node)["rows"] if r["nr"] == "2")
    assert row["serves"]["ids"] == [] and row["serves"]["unknown"] == ["C1.extra"]
    assert project.plain(row["serves"]["spans"]) == "C1.extra"


def test_analysis_links_only_the_complete_declared_condition_identity(tmp_path):
    node = ist_node(ist_text(tmp_path / "antrag.md", lambda t: t.replace("| C2 |", "| C1.extra |", 1)
                            .replace("| 2 | C2 |", "| 2 | C1.extra |", 1)))
    nec = project.necessity(node)
    row = next(r for r in nec["rows"] if r["nr"] == "2")
    assert row["serves"]["ids"] == ["C1.extra"] and row["serves"]["unknown"] == []
    assert project.plain(row["serves"]["spans"]) == "C1.extra"


def test_comparison_preserves_free_prose_and_partial_target_metadata(tmp_path):
    """Exercise the actual comparison renderer; element-tree adapter omits browser geometry/events."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not installed")
    text = TEMPLATE_DE.read_text(encoding="utf-8").replace(
        "Trennung aufheben: Eingang legt die Fallakte direkt an (`hypothesis`)",
        "Vorschlag; arbeitsschritt:start arbeitsschritt:fehlt")
    root = _ist_workspace(tmp_path, {"antrag.md": text})
    source = root / "applications" / "video" / "produktion" / "start" / "CONTEXT.md"
    source.write_text(source.read_text(encoding="utf-8") + "\n## Processing\n- Agent: Draft\n", encoding="utf-8")
    pages = selection.workspace_site(root)
    nec = pages["i-antrag.html"]["necessity"]
    first = nec["rows"][0]
    assert [t["status"] for t in first["move"]["resolved"]] == ["found", "missing"]
    assert first["serves"]["ids"] == first["serves"]["unknown"] == []
    model = pages["i-antrag.html"]
    model["language"] = "de"
    result = render_page(tmp_path, write.page_html(model))
    sheet = result["sheet"]
    table = next(e for e in elements(sheet) if e["attrs"].get("class") == "t nt")
    row = next(e for e in elements(table) if e["attrs"].get("id") == "n-1")
    assert project.plain(first["serves"]["spans"]) in text_content(row)
    assert "AS fehlt" in text_content(row)
    assert "arbeitsschritt:fehlt" in row["children"][-1]["attrs"]["title"]
    assert "in keiner Leistung dieser Ansicht" in text_content(row)
    assert any(e["attrs"].get("href") == "a-video.html#arbeitsschritt%3Astart" for e in elements(row))
    assert "zsteps" not in {e["attrs"].get("class") for e in elements(sheet)}
    assert "Ist und Ziel" not in text_content(sheet)
    step_model = pages["a-video.html"]
    step_model["language"] = "de"
    step_sheet = render_page(tmp_path, write.page_html(step_model), "#arbeitsschritt:start")["sheet"]
    assert "Agent: Draft" in text_content(step_sheet)


def test_unmapped_analysis_rows_have_their_own_anchor_namespace():
    """`n-<Nr>` belongs to a uniquely mapped activity; an Nr like `1-0` must never collide with another row's anchor."""
    page = write.TEMPLATE.read_text(encoding="utf-8")
    assert '"n-" + r.nr + "-"' not in page and '"n-" + m.nr + "-"' not in page
    assert '"na-" + nec.rows.indexOf(r)' in page


# ---------- bilingual page words and explicit language boundary ----------


def test_word_tables_have_identical_keys():
    page = write.TEMPLATE.read_text(encoding="utf-8")
    tables = word_tables(page)
    assert set(tables) == {"de", "en"}
    assert tables["de"].keys() == tables["en"].keys()
    used = set(re.findall(r"\bW\.(\w+)", page))
    assert used == set(tables["de"])
    assert all("—" not in text for text in tables["en"].values())


@pytest.mark.parametrize("language", [None, "", "fr", "constructor", "__proto__"])
def test_missing_or_unknown_page_language_is_a_plain_error(tmp_path, language):
    model = {"kind": "application", "issues": []}
    if language is not None:
        model["language"] = language
    result = render_page(tmp_path, write.page_html(model))
    assert result["words"] is None
    assert result["error"] == "Error: missing or unsupported page language."
    assert result["title"] == result["error"]
    assert "language" not in result
    assert result["sheet"]["children"] == result["head"]["children"] == result["map"]["children"] == []
    assert "Prozessansicht" not in result["error"]


def test_english_workspace_renders_english_words_and_model(tmp_path):
    root = init_workspace(tmp_path / "english", language="en")
    application = write_application(root / "applications" / "video")
    readable = {
        "Veröffentlichtes Video": "Published video", "Durchlaufzeit": "Time to finish",
        "Video veröffentlicht": "Video published", "Video-Produktion": "Video production",
        "Produziertes Video": "Produced video", "# Produktion": "# Production",
        "Ergebnis ist vollständig": "Result is complete", "## Bearbeitung": "## Processing",
        "Erzeuge das deklarierte Ergebnis.": "Produce the declared result.",
    }
    for context in application.rglob("CONTEXT.md"):
        text = context.read_text(encoding="utf-8")
        for german, english in readable.items():
            text = text.replace(german, english)
        context.write_text(text, encoding="utf-8")
    step = application / "produktion" / "start" / "CONTEXT.md"
    template = (REPO / "02_protocol" / "templates" / "arbeitsschritt.md").read_text(encoding="utf-8")
    body = template.split("---\n", 2)[2]
    _, frontmatter, _ = step.read_text(encoding="utf-8").split("---\n", 2)
    step.write_text("---\n" + frontmatter + "---\n" + body
                    + "\n## Processing\n- Deterministic system: Calculate\n- Classifier: Choose a category\n"
                    "- Agent: Draft\n- Human: Decide\n\n## Source quotation\n"
                    "German source: unverändert `open` `hypothesis` `reported` `verified` `entfaellt`\n",
                    encoding="utf-8")
    folder = root / "grundlagen" / "ist-prozesse"
    folder.mkdir(parents=True)
    (folder / "request.md").write_text(TEMPLATE_EN.read_text(encoding="utf-8"), encoding="utf-8")
    (folder / "note.txt").write_text("Do not read", encoding="utf-8")
    (folder / "no-type.md").write_text("# No type", encoding="utf-8")
    (folder / "wrong-type.md").write_text("---\ntype: workspace\n---\n", encoding="utf-8")
    git(root, "init", "-b", "main")
    out = tmp_path / "english-view"
    assert run_cli(root, "--out", out) == 0
    assert {p.name for p in out.iterdir()} == {"index.html", "a-video.html", "i-request.html"}
    for filename in ("index.html", "a-video.html", "i-request.html"):
        html = (out / filename).read_text(encoding="utf-8")
        model = embedded(html)
        assert model["language"] == "en"
        result = render_page(tmp_path, html, "#arbeitsschritt:start" if filename == "a-video.html" else "")
        assert result["words"] == result["language"] == "en"
        shown = words(result)
        assert "Read-only view." in shown
        assert "Nur Ansicht." not in shown
        if filename == "a-video.html":
            assert "Processing" in shown and "Outcome" in shown
            for label in ("Deterministic system", "Classifier", "Agent", "Human"):
                assert label in shown
            assert "German source: unverändert" in shown and "entfaellt" in shown
            assert model["selection"]["revision"].startswith("sha256:")
            assert not model["selection"]["revision"].startswith("Arbeitsstand")
            start = next(n for n in model["nodes"] if n["id"] == "arbeitsschritt:start")
            subtitles = {p["heading"]: p["subtitle"] for p in start["sections"]}
            assert subtitles["One job"] == "One sentence: the result this job produces, its recipient and permitted use."
            assert subtitles["Inputs"] is None
        if filename == "i-request.html":
            assert "Current and target" not in shown and "Necessity" in shown
            assert "E Result work" in shown and "Record, not checked by Core" in shown
        if filename == "index.html":
            assert "Not read:" in shown and "not a .md file" in shown
            assert "type: missing" in shown and "type: workspace" in shown


@pytest.mark.parametrize("language", ["de", "en"])
def test_template_subtitles_match_the_heading_language(language):
    folder = REPO / "02_protocol" / "templates"
    if language == "de":
        folder /= "de"
    for kind, subtitles in project.SUBTITLE.items():
        template = (folder / f"{kind}.md").read_text(encoding="utf-8")
        _, sections = blocks.sections(template.split("---\n", 2)[2], 1)
        for section in sections:
            heading = project.heading_key(section)
            if heading in subtitles:
                assert subtitles[heading] in template
        own_headings = {project.heading_key(p) for p in sections}
        assert len(own_headings & subtitles.keys()) == (4 if kind == "arbeitsschritt" else 1)



def test_english_waiting_history_preserves_status_token(tmp_path):
    root = _workspace(tmp_path)
    path = root / "vorgaenge" / "video-001" / "CONTEXT.md"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "status: aktiv", "status: wartend\n  wiedereinstieg:\n"
        "    ausloeser: Freigabe liegt vor\n    continuation_ref: records/video.md"), encoding="utf-8")
    model = selection.workspace_site(root)["v-video-001.html"]
    model["language"] = "en"
    result = render_page(tmp_path, write.page_html(model), "#vorgang:video-001")
    assert model["run"]["meta"]["laufpfad"][-1]["status"] == "wartend"
    assert "Continue when: Freigabe liegt vor" in words(result["sheet"])
    assert "Continue in: records/video.md" in words(result["sheet"])
    assert "waiting" in words(result["sheet"])


def test_default_language_is_german_without_a_recorded_setting(tmp_path):
    root = write_application(tmp_path / "video")
    assert working_language(root) is None and choose_language(root, None) == "de"
    out = tmp_path / "view"
    assert main(["view", str(root), "--out", str(out)]) == 0
    html = (out / "index.html").read_text(encoding="utf-8")
    assert embedded(html)["language"] == "de"
    assert render_page(tmp_path, html, "#arbeitsschritt:start")["language"] == "de"
    assert choose_language(root, "en") == "en"


@pytest.mark.parametrize("language", ["de", "en"])
def test_recorded_language_wins_and_conflicting_option_is_refused(tmp_path, language):
    root = init_workspace(tmp_path / "workspace", language=language)
    assert choose_language(root, None) == language
    assert choose_language(root, language) == language
    with pytest.raises(SystemExit, match="cannot override"):
        choose_language(root, "en" if language == "de" else "de")


def test_necessity_08_only_appears_on_the_named_target_and_links_every_source(tmp_path):
    text = TEMPLATE_DE.read_text(encoding="utf-8").replace(
        "Trennung aufheben: Eingang legt die Fallakte direkt an (`hypothesis`)",
        "Vorschlag (`hypothesis`); arbeitsschritt:start")
    root = _ist_workspace(tmp_path, {"first.md": text, "second.md": text})
    pages = selection.workspace_site(root)
    model = {**pages["a-video.html"], "language": "de"}
    html = write.page_html(model)
    target = render_page(tmp_path, html, "#arbeitsschritt:start")["sheet"]
    section = next(e for e in elements(target) if e["attrs"].get("id") == "s-necessity")
    assert text_content(section).startswith("08Notwendigkeit")
    headings = [text_content(e) for e in elements(section) if e["tagName"] == "TH"]
    assert headings == ["Tätigkeit", "dient", "E", "K", "F", "D", "Ü", "Erste Zeile oder nächster Schritt"]
    assert {e["attrs"].get("href") for e in elements(section) if e["tagName"] == "A"} == {"i-first.html#n-1", "i-second.html#n-1"}
    assert "E Ergebnisarbeit · K Koordination · F Fehlerfolge · D Doppelung · Ü Überschuss" in text_content(section)
    other = render_page(tmp_path, html, "#arbeitsschritt:pruefen")["sheet"]
    assert not any(e["attrs"].get("id") == "s-necessity" for e in elements(other))
    for tree in (target, other):
        ids = [e["attrs"]["id"] for e in elements(tree) if "id" in e["attrs"]]
        assert len(ids) == len(set(ids))


def test_open_ist_move_keeps_jump_control_separate_from_source_controls(tmp_path):
    text = TEMPLATE_DE.read_text(encoding="utf-8").replace(
        "Trennung aufheben: Eingang legt die Fallakte direkt an (`hypothesis`)",
        "[Quelle](basis.md) (`open`, `reported`, `verified`); arbeitsschritt:start")
    root = _ist_workspace(tmp_path, {"antrag.md": text})
    pages = selection.workspace_site(root)
    sheet = render_page(tmp_path, write.page_html({**pages["a-video.html"], "language": "de"}),
                        "#arbeitsschritt:start")["sheet"]
    collection = next(e for e in elements(sheet) if e["attrs"].get("id") == "s-open")
    assert "Quelle" in text_content(collection)
    controls = [e for e in elements(collection) if e["tagName"] == "BUTTON"]
    assert controls
    assert all(not any(child["tagName"] == "BUTTON" for child in list(elements(control))[1:])
               for control in controls)
    ist = render_page(tmp_path, write.page_html({**pages["i-antrag.html"], "language": "de"}))["sheet"]
    header = next(e for e in elements(ist) if e["tagName"] == "HEADER")
    assert "berichtet" in text_content(header)
    assert not any(e["attrs"].get("class") == "stated source-label" for e in elements(ist))


def test_legend_maps_labels_without_inventing_evidence(tmp_path):
    root = write_application(tmp_path / "video")
    path = root / "produktion" / "start" / "CONTEXT.md"
    path.write_text(path.read_text(encoding="utf-8") + "\n## One job\n\nResult. Another sentence.\n"
                    "\n## Inputs\n\nStated `reported`. Checked `verified`. Plain.\n"
                    "\n## Authority\n\nProposed `hypothesis`. Missing `open`.\n", encoding="utf-8")
    model = {**selection.application_page(root), "language": "de"}
    sheet = render_page(tmp_path, write.page_html(model), "#arbeitsschritt:start")["sheet"]
    legend = next(e for e in elements(sheet) if e["attrs"].get("class") == "evidence-legend")
    assert text_content(legend) == "ohne Markierung: aus der Dateiabgeleitetoffen"
    marked = [e for e in elements(sheet) if e["attrs"].get("class", "").startswith("ev ")]
    assert {e["attrs"]["class"] for e in marked} == {"ev ev-hypothesis", "ev ev-open"}
    assert all(text_content(e) == ("abgeleitet" if "hypothesis" in e["attrs"]["class"] else "offen") for e in marked)
    assert all(any(label in e["attrs"].get("title", "") for e in elements(sheet)) for label in ("reported", "verified", "hypothesis", "open"))
    header = next(e for e in elements(sheet) if e["tagName"] == "HEADER")
    assert "Result." in text_content(header) and "Another sentence." not in text_content(header)
    assert "Verantwortlich" not in text_content(header)
    assert "Definition, kein Ausführungsstand" in text_content(header)
    assert not any(e["attrs"].get("class") == "triad" for e in elements(sheet))
    opened = next(e for e in elements(sheet) if e["attrs"].get("id") == "s-open")
    assert "Missing" in text_content(opened)


def test_sheet_uses_template_order_and_separate_handgrips_without_dropping_source(tmp_path):
    root = write_application(tmp_path / "video")
    path = root / "produktion" / "start" / "CONTEXT.md"
    path.write_text(path.read_text(encoding="utf-8") + "\n## Flow\n\nStart on arrival.\n"
                    "\n## Check\n\nCompare result.\n## Processing\n- Human: Compare\n- Agent: Draft\n"
                    "### Tools\n\nTool X.\n### Handgriffe\n\n| Nr. | Handgriff |\n| --- | --- |\n| 1 | Read input |\n"
                    "### Capability call\n\nRetain this after handgrips.\n"
                    "\n## Excluded context\n\nDo not load Y.\n\n## Inputs\n\nLoad X.\n"
                    "\n## Authority\n\nHolder decides.\n\n## Outputs and effects\n\nPacket written.\n"
                    "\n## One job\n\nDeliver packet.\n", encoding="utf-8")
    model = {**selection.application_page(root), "language": "de"}
    sheet = render_page(tmp_path, write.page_html(model), "#arbeitsschritt:start")["sheet"]
    numbered = [e for e in elements(sheet) if e["tagName"] == "SECTION" and e["attrs"].get("id", "").startswith("s-")]
    assert [e["attrs"]["id"] for e in numbered] == ["s-job", "s-inputs", "s-processing", "s-handgrips", "s-outputs", "s-check", "s-authority", "s-flow"]
    processing = next(e for e in numbered if e["attrs"]["id"] == "s-processing")
    assert "Tool X." in text_content(processing) and "Retain this after handgrips." in text_content(processing)
    inputs = next(e for e in numbered if e["attrs"]["id"] == "s-inputs")
    assert "Nicht laden" in text_content(inputs) and "Do not load Y." in text_content(inputs)
    assert "Arbeitsschritt · Verarbeitung › Handgriffe · Zeile " in text_content(sheet)
    assert any("Processing › Handgriffe" in e["attrs"].get("title", "") for e in elements(sheet))
    assert "03Handgriffe" in text_content(sheet)
    ids = [e["attrs"]["id"] for e in elements(sheet) if "id" in e["attrs"]]
    assert len(ids) == len(set(ids))
    assert not any(e["attrs"].get("id") in ("s-open", "s-necessity") for e in elements(sheet))


def test_unmapped_and_conflicting_conditions_render_closed_and_keep_unique_anchors(tmp_path):
    text = TEMPLATE_DE.read_text(encoding="utf-8")
    text = text.replace("| 2 | C2 | Ja", "| 99 | C2 | Ja", 1).replace(
        "| C2 | Eine Entscheidung", "| C1 | Eine Entscheidung", 1)
    root = _ist_workspace(tmp_path, {"antrag.md": text})
    model = {**selection.workspace_site(root)["i-antrag.html"], "language": "de"}
    sheet = render_page(tmp_path, write.page_html(model))["sheet"]
    assert "mehrfach erklärt" in text_content(sheet)
    assert "keine eindeutige analysezeile" in text_content(sheet).lower()
    assert "Nr. 99" in text_content(sheet)
    ids = [e["attrs"]["id"] for e in elements(sheet) if "id" in e["attrs"]]
    assert len(ids) == len(set(ids))
    assert "na-1" in ids and "n-99" not in ids
    details = [e for e in elements(sheet) if e["tagName"] == "DETAILS"]
    assert all(not e.get("open") and "open" not in e["attrs"] for e in details)
    assert text_content(sheet).count("Ein Zielschritt ist ein Vorschlag; er belegt weder Abdeckung noch Umsetzung.") == 1


def test_ist_without_analysis_renders_source_sections_verbatim(tmp_path):
    path = tmp_path / "note.md"
    path.write_text("---\ntype: ist-prozess\nname: Angebot\nowner: Team\n---\n\n# Angebot\n\n"
                    "## Ablauf heute\n\n1. Entwurf\n2. Einreichung (`verified`)\n\n## Quellen\n\nAkte.\n", encoding="utf-8")
    model = {**selection.ist_page(path, "note.md"), "language": "de"}
    sheet = render_page(tmp_path, write.page_html(model))["sheet"]
    assert "Ablauf heute" in text_content(sheet) and "Entwurf" in text_content(sheet)
    assert "Einreichung" in text_content(sheet) and "Akte." in text_content(sheet)
    assert "Team" in text_content(sheet)
    assert not any(e["attrs"].get("class") == "t nt" for e in elements(sheet))


def test_owner_is_shown_only_from_an_explicit_source_label(tmp_path):
    root = write_application(tmp_path / "video")
    path = root / "produktion" / "start" / "CONTEXT.md"
    original = path.read_text(encoding="utf-8")
    path.write_text(original + "\n## Processing\n\n- Human: Clerk processes the packet.\n", encoding="utf-8")
    model = {**selection.application_page(root), "language": "de"}
    sheet = render_page(tmp_path, write.page_html(model), "#arbeitsschritt:start")["sheet"]
    header = next(e for e in elements(sheet) if e["tagName"] == "HEADER")
    assert "Verantwortlich" not in text_content(header)
    path.write_text(original + "\n## Authority\n\n- **Role**: Office Coordinator (`reported`)\n", encoding="utf-8")
    model = {**selection.application_page(root), "language": "de"}
    step = next(n for n in model["nodes"] if n["id"] == "arbeitsschritt:start")
    assert project.plain(step["owners"][0]["spans"]) == "Office Coordinator (reported)"
    assert path.read_text().splitlines()[step["owners"][0]["line"] - 1].startswith("- **Role**:")
    sheet = render_page(tmp_path, write.page_html(model), "#arbeitsschritt:start")["sheet"]
    header = next(e for e in elements(sheet) if e["tagName"] == "HEADER")
    assert "VerantwortlichOffice Coordinator" in text_content(header)
    assert "Role:" not in text_content(header) and "()" not in text_content(header)


def test_open_collection_links_each_marked_item_and_omits_unmarked_siblings(tmp_path):
    root = write_application(tmp_path / "video")
    path = root / "produktion" / "start" / "CONTEXT.md"
    path.write_text(path.read_text() + "\n## Inputs\n\n- First question `open`\n- Known sibling `reported`\n"
                    "- Second question `open`\n", encoding="utf-8")
    model = {**selection.application_page(root), "language": "de"}
    sheet = render_page(tmp_path, write.page_html(model), "#arbeitsschritt:start")["sheet"]
    collection = next(e for e in elements(sheet) if e["attrs"].get("id") == "s-open")
    rows = [e for e in elements(collection) if e["tagName"] == "LI"]
    assert len(rows) == 2
    assert "First question" in text_content(rows[0]) and "Second question" in text_content(rows[1])
    assert "Known sibling" not in text_content(collection)
    assert len([e for e in elements(collection) if e["tagName"] == "BUTTON"]) == 2


def test_title_and_metadata_source_lines_are_exact_even_with_fenced_headings(tmp_path):
    path = tmp_path / "CONTEXT.md"
    path.write_text('---\ntype: ist-prozess\nname: Packet\n---\n\n```md\n# Decoy\n```\n\n# Packet\n\n## Check\n\nKnown.\n', encoding="utf-8")
    node = read.read_file(path, "CONTEXT.md")
    assert node["title"] == "Packet" and node["title_line"] == 10
    assert node["meta_field_lines"] == {"type": 2, "name": 3}


def test_missing_name_job_and_owner_are_omitted_from_the_header(tmp_path):
    root = write_application(tmp_path / "video")
    path = root / "produktion" / "start" / "CONTEXT.md"
    path.write_text(re.sub(r"^# .*$", "", path.read_text(), flags=re.M), encoding="utf-8")
    model = {**selection.application_page(root), "language": "de"}
    sheet = render_page(tmp_path, write.page_html(model), "#arbeitsschritt:start")["sheet"]
    header = next(e for e in elements(sheet) if e["tagName"] == "HEADER")
    labels = [text_content(e["children"][0]) for e in elements(header) if e["attrs"].get("class") == "kv"]
    assert "Name" not in labels and "Auftrag" not in labels and "Verantwortlich" not in labels
    assert "Gehört zu" in labels and "Stand" in labels and "Schicht" in labels


@pytest.mark.parametrize("language,more", [("de", "mehr anzeigen"), ("en", "show more")])
def test_long_blocks_start_collapsed_and_short_blocks_stay_open(tmp_path, language, more):
    root = write_application(tmp_path / "video")
    path = root / "produktion" / "start" / "CONTEXT.md"
    long = "Ein belegter Satz mit vollständigem Quelltext. " * 9
    path.write_text(path.read_text() + "\n## Inputs\n\nKurz.\n\n" + long + "\n\n"
                    + "\n".join(f"- Punkt {i}" for i in range(7)) + "\n\nZwischen.\n\n"
                    + "\n".join(f"- Eintrag {i}" for i in range(10)) + "\n\n"
                    + "| Name | Aussage |\n| --- | --- |\n"
                    + "\n".join(f"| {i} | {long} |" for i in range(2)) + "\n\n"
                    + "| Nr. | Kurz |\n| --- | --- |\n"
                    + "\n".join(f"| {i} | x |" for i in range(5)) + "\n", encoding="utf-8")
    model = {**selection.application_page(root), "language": language}
    sheet = render_page(tmp_path, write.page_html(model), "#arbeitsschritt:start")["sheet"]
    inputs = next(e for e in elements(sheet) if e["attrs"].get("id") == "s-inputs")
    previews = [e for e in elements(inputs) if e["attrs"].get("class") == "expandable"]
    # Prose and lists over eight items fold; tables and short lists stay whole, as in the approved sheet.
    assert len(previews) == 2  # long paragraph, ten-item list
    assert any(e["tagName"] == "P" and text_content(e) == "Kurz." for e in elements(inputs))
    for preview in previews:
        button = next(e for e in elements(preview) if e["attrs"].get("class") == "collapse-toggle")
        assert button["attrs"]["aria-expanded"] == "false" and text_content(button) == more
        assert not any("style" in e["attrs"] for e in elements(preview))
    assert long.strip() in text_content(inputs) and "Punkt 6" in text_content(inputs)
    css = re.search(r"<style>(.*?)</style>", write.TEMPLATE.read_text(), re.S).group(1)
    assert "@media print" in css and "max-height:none!important" in css


def test_sections_have_one_source_line_with_all_sources_reachable(tmp_path):
    root = write_application(tmp_path / "video")
    path = root / "produktion" / "start" / "CONTEXT.md"
    path.write_text(path.read_text() + "\n## Inputs\n\nFirst.\n\n## Inputs\n\nSecond `open`.\n"
                    "\n## Nicht laden\n\nExcluded.\n", encoding="utf-8")
    model = {**selection.application_page(root), "language": "de"}
    sheet = render_page(tmp_path, write.page_html(model), "#arbeitsschritt:start")["sheet"]
    for section in (e for e in elements(sheet) if e["tagName"] == "SECTION"):
        origins = [e for e in elements(section) if e["attrs"].get("class") == "origin"]
        assert len(origins) == 1
        assert text_content(origins[0]).count("Quelle: ") == 1
    inputs = next(e for e in elements(sheet) if e["attrs"].get("id") == "s-inputs")
    sources = [e for e in elements(inputs) if e["attrs"].get("class") == "source-ref"]
    assert len(sources) == 4  # two body sections, excluded context, declared input
    assert all(path.name in e["attrs"]["title"] and "Zeile" in e["attrs"]["title"] for e in sources)
    details = next(e for e in elements(inputs) if e["attrs"].get("class") == "more-sources")
    assert text_content(details["children"][0]) == "+3" and not details.get("open")


@pytest.mark.parametrize("outputs,authority", [("Ausgaben", "Human Check"), ("Outputs", "Menschliche Prüfung"),
                                               ("Outputs and effects", "Authority")])
def test_sections_map_before_08_and_only_09_follows(tmp_path, outputs, authority):
    text = TEMPLATE_DE.read_text().replace(
        "Trennung aufheben: Eingang legt die Fallakte direkt an (`hypothesis`)", "Vorschlag; arbeitsschritt:start")
    root = _ist_workspace(tmp_path, {"antrag.md": text})
    path = root / "applications" / "video" / "produktion" / "start" / "CONTEXT.md"
    path.write_text(path.read_text().replace("routen:", "gate: human\nrouten:").replace(
        "  weiter: arbeitsschritt:pruefen", "  freigegeben: arbeitsschritt:pruefen\n  abgelehnt: arbeitsschritt:start")
                    + f"\n## {outputs}\n\nDeclared output.\n\n## {authority}\n\nHolder `open`.\n"
                    "\n## Weitere Hinweise\n\nRetain extra source.\n", encoding="utf-8")
    model = {**selection.workspace_site(root)["a-video.html"], "language": "de"}
    sheet = render_page(tmp_path, write.page_html(model), "#arbeitsschritt:start")["sheet"]
    sections = [e for e in elements(sheet) if e["tagName"] == "SECTION"]
    numbers = [text_content(e["children"][0]["children"][0]) for e in sections
               if e["children"][0]["children"][0]["attrs"].get("class") == "no"]
    assert numbers == sorted(numbers) and numbers[-2:] == ["08", "09"]
    index = next(i for i, e in enumerate(sections) if e["attrs"].get("id") == "s-necessity")
    assert [e["attrs"].get("id") for e in sections[index + 1:]] == ["s-open"]
    output = next(e for e in sections if e["attrs"].get("id") == "s-outputs")
    assert "04Ausgaben und Wirkungen" in text_content(output) and "Declared output." in text_content(output)
    authority_section = next(e for e in sections if e["attrs"].get("id") == "s-authority")
    assert text_content(authority_section["children"][-1]).startswith("Gate: Mensch entscheidet")
    assert "Holder" in text_content(authority_section) and "Human Check" not in text_content(authority_section)


def test_necessity_prose_hides_machine_markers_but_titles_keep_raw_cells(tmp_path):
    text = TEMPLATE_DE.read_text().replace(
        "Trennung aufheben: Eingang legt die Fallakte direkt an (`hypothesis`)",
        "Behalten (`hypothesis`); `arbeitsschritt:start`; arbeitsschritt:fehlt")
    root = _ist_workspace(tmp_path, {"antrag.md": text})
    pages = selection.workspace_site(root)
    ist = render_page(tmp_path, write.page_html({**pages["i-antrag.html"], "language": "de"}))["sheet"]
    rows = [e for e in elements(ist) if e["attrs"].get("class") == "nrow"]
    cell = rows[0]["children"][-1]
    assert "Behalten" in text_content(cell) and "→ AS start" in text_content(cell)
    assert "arbeitsschritt:" not in text_content(cell)
    assert "arbeitsschritt:start" in cell["attrs"]["title"] and "arbeitsschritt:fehlt" in cell["attrs"]["title"]
    removed = next(e["children"][-1] for e in rows if "entfaellt" in e["children"][-1]["attrs"]["title"])
    assert "entfaellt" not in text_content(removed) and "entfällt (Vorschlag)" in text_content(removed)
    step = render_page(tmp_path, write.page_html({**pages["a-video.html"], "language": "de"}), "#arbeitsschritt:start")["sheet"]
    own = next(e for e in elements(step) if e["attrs"].get("id") == "s-necessity")
    own_cell = next(e for e in elements(own) if e["attrs"].get("class") == "nrow")["children"][-1]
    assert "arbeitsschritt:" not in text_content(own_cell) and "→ AS start" not in text_content(own_cell)
    assert "arbeitsschritt:start" in own_cell["attrs"]["title"]


def test_ist_guidance_collapses_below_header_and_main_necessity(tmp_path):
    model = {**selection.ist_page(ist_text(tmp_path / "antrag.md"), "antrag.md"), "language": "de"}
    sheet = render_page(tmp_path, write.page_html(model))["sheet"]
    header = next(e for e in elements(sheet) if e["tagName"] == "HEADER")
    assert len([e for e in header["children"] if e["attrs"].get("class") == "meta"]) == 2
    stand = next(e for e in elements(header) if e["attrs"].get("class") == "file-stand")
    assert "antrag.md" in text_content(stand) and "Prüfsumme" in text_content(stand)
    sections = [e for e in elements(sheet) if e["tagName"] == "SECTION"]
    assert sections[0]["attrs"]["id"] == "notwendigkeit"
    for name in ("Ablauf heute", "Beobachtungen und Belege", "Berechnungen und Entscheidungen", "Quellen und Aktualität"):
        section = next(e for e in sections if text_content(e["children"][0]) == name)
        toggle = next(e for e in elements(section) if e["attrs"].get("class") == "collapse-toggle")
        assert toggle["attrs"]["aria-expanded"] == "false"
        assert len([e for e in elements(section) if e["attrs"].get("class") == "origin"]) == 1


def test_execution_labels_are_bold_and_contribution_uses_two_paragraphs(tmp_path):
    root = write_application(tmp_path / "video")
    path = root / "produktion" / "start" / "CONTEXT.md"
    path.write_text(path.read_text() + "\n## Verarbeitung\n\n- **Mensch**: Prüft.\n"
                    "- Deterministisches System: Rechnet.\n", encoding="utf-8")
    model = {**selection.application_page(root), "language": "de"}
    sheet = render_page(tmp_path, write.page_html(model), "#arbeitsschritt:start")["sheet"]
    processing = next(e for e in elements(sheet) if e["attrs"].get("id") == "s-processing")
    labels = [text_content(e) for e in elements(processing) if e["tagName"] == "STRONG"]
    assert labels == ["Mensch:", "Deterministisches System:"]
    assert text_content(processing).count("Mensch") == 1
    job = next(e for e in elements(sheet) if e["attrs"].get("id") == "s-job")
    paragraphs = [text_content(e) for e in elements(job) if e["tagName"] == "P"]
    assert "Produziertes Video" in paragraphs
    assert any(p.startswith("Leistung: ") for p in paragraphs)
