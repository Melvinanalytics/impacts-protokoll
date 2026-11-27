"""Focused tests for v0.9.0 capabilities: preview-pin, protocol-source, Arbeitsschritt size,
public vorgang_model/--json-stdout, and Human view upgrades."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote

import pytest

from impacts_protocol import validate
from impacts_protocol.cli import main
from impacts_protocol.view import site_model, vorgang_model, write
from tests.support import (
    committed_workspace, entry_active, entry_completed, entry_waiting, make_attempt,
    read_context, replace_context, write_context, write_hauptprozess, write_vorgang,
)
from tests.test_view import elements, embedded, render_page, text_content

ROOT = Path(__file__).resolve().parents[1]


# --- Item 1: --preview-pin ---

def test_preview_pin_judges_older_workspace_without_writing(tmp_path, capsys):
    root, revision = committed_workspace(tmp_path)
    replace_context(root / "CONTEXT.md", {"type": "workspace", "protocol": "v0.7.0"})
    (root / "loose.md").write_text("unlinked\n", encoding="utf-8")
    before = (root / "CONTEXT.md").read_bytes()

    unjudged = validate(root)
    assert unjudged.valid and not unjudged.workspace_judged and unjudged.pin == "v0.7.0"

    preview = validate(root, preview_pin=True)
    assert preview.workspace_judged and preview.preview_pin is True
    assert preview.pin == "v0.7.0"
    assert [(i.code, i.path) for i in preview.issues] == [("topology.link_missing", "loose.md")]
    assert (root / "CONTEXT.md").read_bytes() == before

    assert main(["validate", str(root), "--preview-pin"]) == 1
    out = capsys.readouterr().out
    assert "(preview)" in out and "topology.link_missing" in out

    # Combining --preview-pin and --require-judged is rejected so gates never accept a preview.
    with pytest.raises(SystemExit) as rejected:
        main(["validate", str(root), "--preview-pin", "--require-judged"])
    assert rejected.value.code == 2
    capsys.readouterr()

    (root / "loose.md").unlink()
    assert main(["validate", str(root), "--preview-pin", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True and payload["workspace_judged"] is True
    assert payload["pin"] == "v0.7.0" and payload["preview_pin"] is True

    assert main(["validate", str(root), "--json"]) == 0
    unjudged_payload = json.loads(capsys.readouterr().out)
    assert unjudged_payload["workspace_judged"] is False and unjudged_payload["preview_pin"] is False


# --- Item 8: --protocol-source ---

def test_protocol_source_checks_code_span_citations_and_anchors(tmp_path, capsys):
    root, _ = committed_workspace(tmp_path)
    with (root / "CONTEXT.md").open("a", encoding="utf-8") as handle:
        handle.write(
            "\nValid ref `02_protocol/binding.md#snapshot-and-provenance`.\n"
            "Valid line ref `02_protocol/capabilities.md:150` and `02_protocol/impacts-method.md:355-361`.\n"
            "Missing anchor `02_protocol/binding.md#does-not-exist`.\n"
            "Missing file `02_protocol/no-such-file.md`.\n"
            "Placeholder `02_protocol/<path>#<anchor>`.\n"
        )
    report = validate(root, protocol_source=ROOT)
    found = [(i.code, i.path, i.message) for i in report.issues]
    assert len(found) == 2
    assert all(code == "topology.link_broken" and path == "CONTEXT.md" for code, path, _ in found)
    assert any("does-not-exist" in msg for _, _, msg in found)
    assert any("no-such-file.md" in msg for _, _, msg in found)

    assert main(["validate", str(root), "--protocol-source", str(ROOT)]) == 1
    assert "does-not-exist" in capsys.readouterr().out

    # Invalid protocol source fails explicitly
    bad = validate(root, protocol_source=tmp_path / "missing-protocol")
    assert not bad.valid and bad.issues[0].code == "structure.level"


# --- Item 13: public vorgang_model & --json-stdout ---

def test_public_vorgang_model_and_cli_json_stdout(tmp_path, capsys):
    root, revision = committed_workspace(tmp_path)
    attempt = make_attempt(root / "vorgaenge" / "case-1", "start", 1, input_bytes="synthetic")
    vorgang_dir = write_vorgang(root, "case-1", revision, [entry_active("start", 1, attempt)])
    vorgang_file = vorgang_dir / "CONTEXT.md"

    model = vorgang_model(vorgang_file)
    assert model["kind"] == "vorgang" and model["issues"] == []
    assert model["view"]["status"] == "aktiv" and model["view"]["current"] == "arbeitsschritt:start"

    assert main(["view", str(vorgang_file), "--json-stdout"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    assert cli_payload["kind"] == "vorgang" and cli_payload["language"] == "en"
    assert cli_payload["view"] == model["view"]

    assert main(["view", str(root), "--json-stdout"]) == 0
    ws_payload = json.loads(capsys.readouterr().out)
    assert "index.html" in ws_payload and "v-case-1.html" in ws_payload

    with pytest.raises(ValueError):
        vorgang_model(tmp_path / "not-a-vorgang.md")


# --- Items 16–21: Human view upgrades ---

def test_view_supports_nested_analyse_bridge_multi_record_stufe_legacy_outputs_and_system_views(tmp_path):
    root, revision = committed_workspace(tmp_path)
    # 1) Second Record Library (bestand/) with German Stufe: and anchored table
    bestand = root / "bestand"
    bestand.mkdir()
    (bestand / "CONTEXT.md").write_text("# Bestand\n\n## Was laden\n\n## Übersicht\n\n[Fall A](fall-a.md)\n[Liste](liste.md)\n", encoding="utf-8")
    (bestand / "fall-a.md").write_text("# Fall A\n\nStufe: geprueft\n", encoding="utf-8")
    (bestand / "liste.md").write_text("| ID | Stufe |\n|---|---|\n| <a id=\"L1\"></a> L1 | beworben |\n", encoding="utf-8")

    # 2) Nested analyse/ist-prozesse/ + bridge.md
    analyse = root / "analyse"
    (analyse / "ist-prozesse").mkdir(parents=True)
    (analyse / "CONTEXT.md").write_text("# Analyse\n\n## Was laden\n\n## Übersicht\n\n[Ist](ist-prozesse/)\n[Bridge](offer-bridge.md)\n", encoding="utf-8")
    (analyse / "ist-prozesse" / "aufnahme.md").write_text(
        "---\ntype: ist-prozess\nname: Aufnahme Unterordner\n---\n\n# Aufnahme Unterordner\n", encoding="utf-8"
    )
    (analyse / "offer-bridge.md").write_text(
        "# Reality and Leistungsstückliste bridge: Demo\n\n## 1. Result boundary\n\n- Unit: synthetic\n", encoding="utf-8"
    )

    # 3) System/Market views (both HTML and Markdown) docked via View:
    grundlagen = root / "grundlagen"
    grundlagen.mkdir()
    (grundlagen / "CONTEXT.md").write_text("# Grundlagen\n\n## Was laden\n\n## Übersicht\n\n[Markt](markt.html)\n[Topologie](topologie.md)\n", encoding="utf-8")
    (grundlagen / "markt.html").write_text("<!doctype html><html><head><title>Markttopologie</title></head><body><h1>Markt</h1></body></html>\n", encoding="utf-8")
    (grundlagen / "topologie.md").write_text("# Marktbeziehungen\n\n## Teilnehmer\n\nKunde und Anbieter.\n", encoding="utf-8")

    with (root / "CONTEXT.md").open("a", encoding="utf-8") as handle:
        handle.write(
            "\nForm: bestand/ Record Library per Eintrag\n"
            "Form: analyse/ Context Map per Erfassung\n"
            "Form: grundlagen/ Knowledge Bundle per Thema\n"
            "[Bestand](bestand/CONTEXT.md)\n"
            "[Analyse](analyse/CONTEXT.md)\n"
            "[Grundlagen](grundlagen/CONTEXT.md)\n"
            "View: grundlagen/markt.html | Matching-Architektur\n"
            "View: grundlagen/topologie.md\n"
        )

    # 4) Judged Vorgang with completed output + open-attempt draft
    v_ok_dir = root / "vorgaenge" / "live-001"
    a1 = make_attempt(v_ok_dir, "start", 1, input_bytes="synthetic", output_bytes="# Ergebnis Start\nAlles belegt.\n")
    a2 = make_attempt(v_ok_dir, "pruefen", 1, input_bytes="synthetic")
    draft_dir = v_ok_dir / "pruefen" / "001" / "output"
    draft_dir.mkdir(parents=True, exist_ok=True)
    (draft_dir / "entscheidung-entwurf.md").write_text("# Entscheidung (Entwurf)\nOption A empfohlen.\n", encoding="utf-8")
    write_vorgang(
        root, "live-001", revision,
        [entry_completed("start", 1, a1, route="weiter"), entry_waiting("pruefen", 1, a2)],
    )

    # 5) Legacy (not_judged) Vorgang with readable history + subject link
    v_old_dir = root / "vorgaenge" / "legacy-001"
    v_old_dir.mkdir(parents=True)
    write_context(
        v_old_dir / "CONTEXT.md",
        {
            "type": "vorgang",
            "protocol": "v0.3.32",
            "id": "vorgang:legacy-001",
            "hauptprozess_revision": "legacy-tree",
            "laufpfad": [{"arbeitsschritt_ref": "arbeitsschritt:start", "nummer": 1, "status": "abgeschlossen", "gewaehlte_route": "ok"}],
        },
        "# Legacy Fall 001\n\n## Gegenstand\n\n[Fall A](../../bestand/fall-a.md)\n\n## Notiz\n\nAlte Aufzeichnung.\n",
    )

    out = tmp_path / "site-out"
    assert main(["view", str(root), "--out", str(out), "--json"]) == 0
    exported = json.loads((out / "model.json").read_text(encoding="utf-8"))

    # Check nested ist-prozess & bridge.md discovered
    assert "i-ist-prozesse-aufnahme.html" in exported
    assert "i-offer-bridge.html" in exported
    assert exported["i-offer-bridge.html"]["bridge"] is True

    # Check multi-Record-Library + German Stufe:
    stages = {row["stage"]: row["records"] for row in exported["index.html"]["funnel"]}
    assert stages["geprueft"] == ["bestand/fall-a.md"]
    assert stages["beworben"] == ["bestand/liste.md#L1"]

    # Check Level-0 System views docked and HTML copied verbatim
    sv = exported["index.html"]["system_views"]
    assert [v["title"] for v in sv] == ["Matching-Architektur", "Marktbeziehungen"]
    assert (out / "s-markt.html").read_text(encoding="utf-8").startswith("<!doctype html><html><head><title>Markttopologie</title>")
    assert (out / "s-topologie.html").is_file()

    # Check attempt output previews + open-attempt draft
    outputs = exported["v-live-001.html"]["attempt_outputs"]
    assert outputs[0][0]["draft"] is False and "Ergebnis Start" in outputs[0][0]["preview"]
    assert outputs[1][0]["draft"] is True and "Entscheidung (Entwurf)" in outputs[1][0]["preview"]

    # Check legacy read projection on not_judged Vorgang (without adding 'nodes')
    legacy_page = exported["v-legacy-001.html"]
    assert "nodes" not in legacy_page
    assert legacy_page["not_judged"]["protocol"] == "v0.3.32"
    assert legacy_page["legacy"]["title"] == "Legacy Fall 001"
    assert legacy_page["legacy"]["subject"] == {"record": "bestand/fall-a.md", "stage": "geprueft"}
    assert len(legacy_page["legacy"]["laufpfad"]) == 1

    # Render checks in node harness
    rendered_legacy = render_page(tmp_path, (out / "v-legacy-001.html").read_text(encoding="utf-8"))
    legacy_text = text_content(rendered_legacy["sheet"])
    assert "Legacy reading" in legacy_text and "Legacy Fall 001" in legacy_text and "bestand/fall-a.md" in legacy_text

    rendered_index = render_page(tmp_path, (out / "index.html").read_text(encoding="utf-8"))
    index_text = text_content(rendered_index["sheet"])
    assert "Matching-Architektur" in index_text and "Marktbeziehungen" in index_text
    hrefs = {el["attrs"].get("href") for el in elements(rendered_index["sheet"]) if el["tagName"] == "A"}
    assert {"s-markt.html", "s-topologie.html"} <= hrefs

    rendered_md_sv = render_page(tmp_path, (out / "s-topologie.html").read_text(encoding="utf-8"))
    assert "Kunde und Anbieter" in text_content(rendered_md_sv["sheet"])


def test_exported_map_svg_embeds_style_and_resolves_css_variables(tmp_path):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not installed")
    root, _ = committed_workspace(tmp_path)
    out = tmp_path / "site-svg"
    assert main(["view", str(root), "--out", str(out)]) == 0
    html = (out / "a-video.html").read_text(encoding="utf-8")
    code = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
    harness = r"""
class Element {
  constructor(tag) {
    this.tagName = tag.toUpperCase(); this.attrs = {}; this.children = []; this.hidden = false;
    this.listeners = {};
    this.classList = {add() {}, remove() {}, toggle() {}, contains() { return false; }};
  }
  get firstChild() { return this.children[0] || null; }
  set textContent(value) { this.children = [String(value)]; }
  get textContent() { return this.children.map(c => c instanceof Element ? c.textContent : String(c)).join(''); }
  setAttribute(key, value) { this.attrs[key] = String(value); }
  append(...children) { this.children.push(...children); }
  insertBefore(node, ref) {
    const idx = ref ? this.children.indexOf(ref) : -1;
    if (idx >= 0) this.children.splice(idx, 0, node);
    else this.children.unshift(node);
  }
  replaceChildren(...children) { this.children = children; }
  addEventListener(ev, fn) { (this.listeners[ev] ||= []).push(fn); }
  cloneNode(deep) {
    const copy = new Element(this.tagName.toLowerCase());
    copy.attrs = {...this.attrs};
    copy.children = deep ? this.children.map(c => c instanceof Element ? c.cloneNode(true) : c) : [];
    return copy;
  }
  click() {
    if (this.tagName === 'A' && this.href) { captured.push({href: this.href, download: this.download}); return; }
    for (const fn of this.listeners.click || []) fn();
  }
  focus() {}
  scrollIntoView() {}
  closest() { return null; }
  querySelectorAll() { return []; }
  getContext() { return {measureText: text => ({width: text.length * 7})}; }
}
class SVGElement extends Element {}
function serialize(node) {
  if (!(node instanceof Element)) return String(node);
  const tag = node.tagName.toLowerCase();
  const attrs = Object.entries(node.attrs).map(([k, v]) => ` ${k}="${String(v).replace(/"/g, '&quot;')}"`).join('');
  return `<${tag}${attrs}>${node.children.map(serialize).join('')}</${tag}>`;
}
class XMLSerializer { serializeToString(node) { return serialize(node); } }
const captured = [];
const elements = Object.fromEntries(['model', 'map-view', 'map-head', 'map', 'panel', 'sheet-view', 'sheet']
  .map(id => [id, new Element(id === 'map' ? 'svg' : 'div')]));
elements.model.textContent = JSON.stringify(INPUT);
const document = {
  documentElement: new Element('html'), body: new Element('body'), title: '',
  getElementById: id => elements[id] || null,
  createElement: tag => new Element(tag), createElementNS: (ns, tag) => new SVGElement(tag),
  querySelector: () => null, querySelectorAll: () => [], addEventListener() {},
};
const location = {hash: '', pathname: 'a-video.html'};
const history = {pushState() {}, replaceState() {}};
const window = {innerWidth: 1280, innerHeight: 900, addEventListener() {}, scrollTo() {}};
const matchMedia = () => ({matches: false});
const CSS = {escape: value => String(value)};
"""
    script = tmp_path / "export_svg.js"
    script.write_text(
        "const INPUT = " + json.dumps(embedded(html)) + ";\n" + harness + code + """
function findButton(node) {
  if (!(node instanceof Element)) return null;
  if (node.tagName === 'BUTTON' && node.textContent === W.export_svg) return node;
  for (const child of node.children) { const hit = findButton(child); if (hit) return hit; }
  return null;
}
const btn = findButton(elements['map-head']);
if (!btn) throw new Error('export button not found');
btn.click();
console.log(JSON.stringify(captured));
""",
        encoding="utf-8",
    )
    downloads = json.loads(subprocess.run([node, str(script)], capture_output=True, text=True, check=True).stdout)
    assert len(downloads) == 1
    assert downloads[0]["download"] == "video-map.svg"
    prefix = "data:image/svg+xml;charset=utf-8,"
    assert downloads[0]["href"].startswith(prefix)
    svg_text = unquote(downloads[0]["href"][len(prefix):])
    assert 'xmlns="http://www.w3.org/2000/svg"' in svg_text
    assert "<style>" in svg_text and ".edge{fill:none;stroke:#" in svg_text
    assert '<rect width="100%" height="100%" fill="#ffffff">' in svg_text
    assert "var(--" not in svg_text


def test_view_on_older_pinned_workspace_renders_legacy_projection_without_crashing(tmp_path):
    root, _ = committed_workspace(tmp_path)
    replace_context(root / "CONTEXT.md", {"type": "workspace", "protocol": "v0.8.2"})
    v_dir = root / "vorgaenge" / "old-run"
    v_dir.mkdir(parents=True)
    write_context(
        v_dir / "CONTEXT.md",
        {"type": "vorgang", "id": "vorgang:old-run", "laufpfad": [{"arbeitsschritt_ref": "arbeitsschritt:start", "nummer": 1, "status": "aktiv"}]},
        "# Old Run\n",
    )
    pages = site_model(root)
    assert pages["v-old-run.html"]["not_judged"]["protocol"] == "v0.8.2"
    assert pages["v-old-run.html"]["legacy"]["title"] == "Old Run"
    single = vorgang_model(v_dir / "CONTEXT.md")
    assert single["not_judged"]["protocol"] == "v0.8.2"
    assert single["legacy"]["title"] == "Old Run"
