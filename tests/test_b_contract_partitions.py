"""Owner B audit: malformed/edge partitions for the static contracts.

Expectations follow the authoritative sources, never validator output:
- 02_protocol/schemas/*.schema.json (patterns, required, additionalProperties)
- 02_protocol/invariants/complete-process-paths.md (graph rules + expected codes)
- 02_protocol/templates/application.md (layout rules: 3-digit attempts, folder==slug)
- 02_protocol/ontology.md ("laufpfad alone owns execution state"; relation separation)

These tests characterize malformed-input rejection and current contract
boundaries. Attempt and approval-timestamp acceptance lives in
test_b_repairs.py.

Run from a checkout root:  python -m pytest tests/test_b_contract_partitions.py
"""
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(os.environ.get("IMPACTS_AUDIT_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from impacts_protocol import init_workspace, surface_hash, validate
from impacts_protocol.io import DuplicateKeyError, load_frontmatter_and_body
from impacts_protocol.validator import SCHEMA_REGISTRY
from tests.support import (
    codes, git, read_context, replace_context, write_application, write_context,
    write_workstep,
)

H64 = "sha256:" + "b" * 64


# ---------------------------------------------------------------- io layer
@pytest.mark.parametrize("text", [
    "---\ntype: [\n---\n",                      # malformed YAML
    "---\ntype: vorgang\n",                     # no closing delimiter
    "---\n- a\n- b\n---\n",                     # frontmatter not a mapping
    "---\n1: x\n---\n",                         # non-string key
    "---\ntype: vorgang\n<<:\n  id: vorgang:x\n---\n",  # YAML merge key
])
def test_frontmatter_malformed_partitions_fail_closed(tmp_path, text):
    path = tmp_path / "CONTEXT.md"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        load_frontmatter_and_body(path, tmp_path)


def test_duplicate_keys_are_rejected_not_last_wins(tmp_path):
    path = tmp_path / "CONTEXT.md"
    path.write_text("---\ntype: vorgang\ntype: hauptprozess\n---\n", encoding="utf-8")
    with pytest.raises(DuplicateKeyError):
        load_frontmatter_and_body(path, tmp_path)


def test_non_utf8_context_fails_closed(tmp_path):
    path = tmp_path / "CONTEXT.md"
    path.write_bytes(b"---\ntype: vorgang\n---\n\nK\xf6rper\n")
    with pytest.raises(ValueError):
        load_frontmatter_and_body(path, tmp_path)


def test_utf8_bom_hides_frontmatter_and_validator_still_fails_closed(tmp_path):
    root = init_workspace(tmp_path / "kunde")
    (root / "CONTEXT.md").write_bytes(
        b"\xef\xbb\xbf---\ntype: workspace\n---\n\n# Body\n"
    )
    # BOM makes the router unreadable as frontmatter; validation must reject.
    assert "routing.type" in codes(root)


def test_block_scalar_with_bare_dashes_line_is_silently_truncated(tmp_path):
    """B-4 characterization: the line-based splitter closes frontmatter early.

    The truncation can only drop schema fields (fail closed) or shorten a
    free-text value without machine notice. This test pins the current
    behavior so any repair must update it deliberately.
    """
    path = tmp_path / "CONTEXT.md"
    path.write_text(
        "---\ntype: vorgang\nnote: >\n  line one\n---\n  line two\n---\n",
        encoding="utf-8",
    )
    metadata, body = load_frontmatter_and_body(path, tmp_path)
    assert metadata == {"type": "vorgang", "note": "line one"}
    assert "line two" in body


# ---------------------------------------------------------------- schema layer
def _vorgang(**over):
    doc = {
        "type": "vorgang", "id": "vorgang:x",
        "application_revision": "git-tree:" + "a" * 40,
        "laufpfad": [{"arbeitsschritt_ref": "arbeitsschritt:a", "versuch": 1,
                      "status": "aktiv", "eingabe_hash": H64}],
    }
    doc.update(over)
    return doc


def _schema_valid(kind: str, doc: dict) -> bool:
    return not list(SCHEMA_REGISTRY.errors(kind, doc))


@pytest.mark.parametrize("versuch,expected", [
    (1, True), (0, False), (-1, False), (True, False), ("1", False),
])
def test_versuch_boundaries(versuch, expected):
    doc = _vorgang()
    doc["laufpfad"][0]["versuch"] = versuch
    assert _schema_valid("vorgang", doc) is expected


def test_versuch_1000_is_rejected_by_schema_and_run_validation(tmp_path):
    """The run schema caps attempts at 999, matching templates/application.md."""
    doc = _vorgang()
    doc["laufpfad"][0]["versuch"] = 1000
    assert not _schema_valid("vorgang", doc)
    root = init_workspace(tmp_path / "kunde")
    write_application(root / "applications" / "video")
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "t@example.invalid")
    git(root, "config", "user.name", "T")
    git(root, "add", ".")
    git(root, "commit", "-m", "app")
    revision = git(root, "rev-parse", "HEAD:applications/video")
    attempt = root / "vorgaenge/video-x/start/1000"
    (attempt / "input").mkdir(parents=True)
    (attempt / "input/auftrag.md").write_text("E", encoding="utf-8")
    write_context(root / "vorgaenge/video-x/CONTEXT.md", {
        "type": "vorgang", "id": "vorgang:video-x",
        "application_revision": f"git-tree:{revision}",
        "laufpfad": [{"arbeitsschritt_ref": "arbeitsschritt:start", "versuch": 1000,
                      "status": "aktiv",
                      "eingabe_hash": surface_hash(attempt, ["input/auftrag.md"])}],
    })
    report = validate(root)
    assert not report.valid
    assert "schema.invalid" in {issue.code for issue in report.issues}


def test_freigabe_at_invalid_shape_is_rejected_by_schema_and_run_validation(tmp_path):
    """The pattern in schemas/vorgang.schema.json rejects this lexical shape.
    Calendar validation remains in validator._valid_human_approval."""
    doc = _vorgang()
    doc["laufpfad"][0].update(
        status="abgeschlossen", gewaehlte_route="freigegeben", ausgabe_hash=H64,
        freigabe={"by": "human:r", "at": "not-a-date"})
    assert not _schema_valid("vorgang", doc)

    root = init_workspace(tmp_path / "kunde")
    write_application(root / "applications" / "video")
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "t@example.invalid")
    git(root, "config", "user.name", "T")
    git(root, "add", ".")
    git(root, "commit", "-m", "app")
    revision = git(root, "rev-parse", "HEAD:applications/video")
    entries = []
    for index, (slug, route) in enumerate((("start", "weiter"), ("pruefen", "freigegeben")), 1):
        attempt = root / f"vorgaenge/video-x/{slug}/001"
        (attempt / "input").mkdir(parents=True)
        (attempt / "output").mkdir()
        (attempt / "input/auftrag.md").write_text(f"E{index}", encoding="utf-8")
        (attempt / "output/ergebnis.md").write_text(f"A{index}", encoding="utf-8")
        entry = {"arbeitsschritt_ref": f"arbeitsschritt:{slug}", "versuch": 1,
                 "status": "abgeschlossen",
                 "eingabe_hash": surface_hash(attempt, ["input/auftrag.md"]),
                 "gewaehlte_route": route,
                 "ausgabe_hash": surface_hash(attempt, ["output/ergebnis.md"])}
        if slug == "pruefen":
            entry["freigabe"] = {"by": "human:r", "at": "not-a-date"}
        entries.append(entry)
    write_context(root / "vorgaenge/video-x/CONTEXT.md", {
        "type": "vorgang", "id": "vorgang:video-x",
        "application_revision": f"git-tree:{revision}", "laufpfad": entries})
    report = validate(root)
    assert not report.valid
    assert "schema.invalid" in {issue.code for issue in report.issues}


# ------------------------------------------------------- graph partitions
@pytest.fixture
def app_root(tmp_path):
    root = init_workspace(tmp_path / "kunde")
    write_application(root / "applications" / "video")
    return root


def test_unreachable_step_rejected(app_root):
    write_workstep(app_root / "applications/video/produktion", "verwaist")
    assert "process.unreachable" in codes(app_root)


def test_loop_without_exit_rejected(app_root):
    path = app_root / "applications/video/produktion/pruefen/CONTEXT.md"
    metadata = read_context(path)
    metadata["routen"] = {"freigegeben": "arbeitsschritt:start",
                          "abgelehnt": "arbeitsschritt:start"}
    replace_context(path, metadata)
    assert "process.no_end" in codes(app_root)


def test_self_loop_with_exit_remains_valid(app_root):
    path = app_root / "applications/video/produktion/start/CONTEXT.md"
    metadata = read_context(path)
    metadata["routen"] = {"weiter": "arbeitsschritt:pruefen",
                          "warten": "arbeitsschritt:start"}
    replace_context(path, metadata)
    assert validate(app_root).valid


def test_cross_application_step_route_rejected(app_root):
    """Templates: independent Applications exchange results via separate runs,
    never cross-Application step routes."""
    write_application(app_root / "applications/andere")
    path = app_root / "applications/andere/CONTEXT.md"
    metadata = read_context(path)
    metadata["id"] = "hauptprozess:andere"
    replace_context(path, metadata)
    path = app_root / "applications/video/produktion/start/CONTEXT.md"
    metadata = read_context(path)
    metadata["routen"] = {"weiter": "arbeitsschritt:pruefen",
                          "extern": "arbeitsschritt:fremd"}
    replace_context(path, metadata)
    assert "reference.unresolved" in codes(app_root)


def test_human_gate_route_set_is_exact(app_root):
    path = app_root / "applications/video/produktion/pruefen/CONTEXT.md"
    metadata = read_context(path)
    metadata["routen"] = {"freigegeben": "end:fertig",
                          "abgelehnt": "arbeitsschritt:start",
                          "vielleicht": "end:unklar"}
    replace_context(path, metadata)
    assert "process.gate" in codes(app_root)


# ------------------------------------- ontology distinction counterexamples
def _schritt(routen, **over):
    doc = {"type": "arbeitsschritt", "id": "arbeitsschritt:a",
           "eingaben": ["input/a.md"], "ausgaben": ["output/b.md"],
           "pruefung": "x ist y", "routen": routen}
    doc.update(over)
    return doc


@pytest.mark.parametrize("routen", [
    {"siehe": "https://example.test/x"},   # knowledge navigation
    {"braucht": "input/a.md"},             # data dependency path
    {"gehoert": "teilprozess:x"},          # membership
])
def test_other_relation_kinds_cannot_masquerade_as_routes(routen):
    assert not _schema_valid("arbeitsschritt", _schritt(routen))


def test_route_syntax_cannot_masquerade_as_data_dependency():
    assert not _schema_valid("arbeitsschritt", _schritt(
        {"fertig": "end:fertig"}, eingaben=["arbeitsschritt:x"]))


def test_causal_vocabulary_as_route_key_is_structural_only(app_root):
    """B-3 counterexample: a causal claim worded as a route key passes the
    schema and is then traversed as an execution edge — it cannot hide
    silently, and Core deliberately does not interpret route semantics."""
    path = app_root / "applications/video/produktion/start/CONTEXT.md"
    metadata = read_context(path)
    metadata["routen"] = {"weiter": "arbeitsschritt:pruefen",
                          "weil-fehler": "arbeitsschritt:pruefen"}
    replace_context(path, metadata)
    assert validate(app_root).valid  # valid structure, semantics NOT endorsed


def test_continuation_ref_is_not_an_execution_route(tmp_path):
    """wiedereinstieg.continuation_ref accepts an event reference; the
    validator must not treat it as a transition even when it looks like one."""
    root = init_workspace(tmp_path / "kunde")
    write_application(root / "applications" / "video")
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "t@example.invalid")
    git(root, "config", "user.name", "T")
    git(root, "add", ".")
    git(root, "commit", "-m", "app")
    revision = git(root, "rev-parse", "HEAD:applications/video")
    attempt = root / "vorgaenge/video-x/start/001"
    (attempt / "input").mkdir(parents=True)
    (attempt / "input/auftrag.md").write_text("E", encoding="utf-8")
    write_context(root / "vorgaenge/video-x/CONTEXT.md", {
        "type": "vorgang", "id": "vorgang:video-x",
        "application_revision": f"git-tree:{revision}",
        "laufpfad": [{"arbeitsschritt_ref": "arbeitsschritt:start", "versuch": 1,
                      "status": "wartend",
                      "eingabe_hash": surface_hash(attempt, ["input/auftrag.md"]),
                      "wiedereinstieg": {"ausloeser": "Kundenanruf",
                                         "continuation_ref": "arbeitsschritt:pruefen"}}]})
    # The look-alike step reference stays an event reference: run is valid and
    # the current step remains 'start' (no transition semantics attached).
    assert validate(root).valid
