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
from datetime import date
from pathlib import Path
import random
import subprocess
import sys

import pytest
import yaml

ROOT = Path(os.environ.get("IMPACTS_AUDIT_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from impacts_protocol import init_workspace, surface_hash, validate
from impacts_protocol import io
from impacts_protocol.io import DuplicateKeyError, load_frontmatter_and_body
from impacts_protocol.validator import SCHEMA_REGISTRY
from tests.support import (
    codes, git, read_context, replace_context, write_application, write_context,
    write_workstep,
)

H64 = "sha256:" + "b" * 64


# ---------------------------------------------------------------- io layer
def test_default_loader_selects_fast_safe_parser_when_available():
    expected = yaml.CSafeLoader if hasattr(yaml, "CSafeLoader") else yaml.SafeLoader
    assert io._StrictLoader.__bases__ == (expected,)


@pytest.fixture(params=["python", "c"])
def strict_yaml_path(request, monkeypatch):
    if request.param == "c" and not hasattr(yaml, "CSafeLoader"):
        pytest.skip("PyYAML C extension unavailable")
    base = yaml.CSafeLoader if request.param == "c" else yaml.SafeLoader
    forced = io._strict_loader(base)
    monkeypatch.setattr(io, "_StrictLoader", forced)
    if request.param == "python":
        monkeypatch.setattr(io, "_PythonStrictLoader", forced)
    assert io._StrictLoader.__bases__ == (base,)
    return request.param


def _typed(value):
    if isinstance(value, dict):
        return (dict, tuple((key, _typed(child)) for key, child in value.items()))
    if isinstance(value, list):
        return (list, tuple(_typed(child) for child in value))
    return (type(value), value)


def test_safe_yaml_paths_preserve_scalar_types_aliases_and_body(tmp_path, strict_yaml_path):
    path = tmp_path / "CONTEXT.md"
    path.write_text(
        "---\n"
        "type: vorgang\n"
        "implicit:\n"
        "  truth: yes\n"
        "  falsehood: false\n"
        "  integer: 42\n"
        "  decimal: 3.5\n"
        "  date: 2026-09-25\n"
        "  empty: null\n"
        "nested: &nested\n"
        "  child: {name: text, count: 2}\n"
        "alias: *nested\n"
        "---\n# Body\n",
        encoding="utf-8",
    )
    metadata, body = load_frontmatter_and_body(path, tmp_path)
    reference = yaml.load(
        path.read_text().split("---")[1], Loader=io._strict_loader(yaml.SafeLoader)
    )
    assert _typed(metadata) == _typed(reference)
    assert metadata["implicit"] == {
        "truth": True,
        "falsehood": False,
        "integer": 42,
        "decimal": 3.5,
        "date": date(2026, 9, 25),
        "empty": None,
    }
    assert metadata["nested"] is metadata["alias"]
    assert body == "# Body"


@pytest.mark.parametrize("source,error", [
    ("type: a\ntype: b", DuplicateKeyError),
    ("type: a\nnested: {x: 1, x: 2}", DuplicateKeyError),
    ("type: a\nnested: {1: x}", ValueError),
    ("type: a\n<<: {x: 1}", ValueError),
    ("type: a\nnested: {<<: {x: 1}}", ValueError),
    ("type: !!python/object/apply:os.system ['true']", ValueError),
    ("type: [", ValueError),
])
def test_safe_yaml_paths_reject_bad_mappings_and_tags(
    tmp_path, strict_yaml_path, source, error
):
    path = tmp_path / "CONTEXT.md"
    path.write_text(f"---\n{source}\n---\n", encoding="utf-8")
    with pytest.raises(error) as caught:
        load_frontmatter_and_body(path, tmp_path)
    if error is DuplicateKeyError:
        assert caught.value.key in {"type", "x"}
    elif "<<:" in source or "!!python" in source or source.endswith("["):
        assert "invalid frontmatter YAML:" in str(caught.value)
    else:
        assert "frontmatter keys must be strings" in str(caught.value)


@pytest.mark.parametrize("source,error", [
    ("outer: {x: 1, x: 2}", DuplicateKeyError),
    ("outer: {1: x}", ValueError),
    ("outer: {<<: {x: 1}}", yaml.YAMLError),
])
def test_strict_mapping_constructor_runs_on_each_backend(
    strict_yaml_path, source, error
):
    with pytest.raises(error):
        yaml.load(source, Loader=io._StrictLoader)


def test_safe_yaml_paths_keep_validator_findings(tmp_path, strict_yaml_path):
    root = init_workspace(tmp_path / "kunde")
    path = root / "CONTEXT.md"
    path.write_text("---\ntype: workspace\ntype: other\n---\n", encoding="utf-8")
    report = validate(root)
    assert [(issue.code, issue.path) for issue in report.issues] == [
        ("format.invalid", "CONTEXT.md")
    ]


@pytest.mark.parametrize("source", [
    "extra: a\tb",                    # C accepts; Python rejects
    'extra: "\\uD800"',             # Python accepts; C rejects
    "extra: [a:]",                    # Python accepts; C rejects
    "extra: !",                       # both accept with different scalar values
    "extra: {a: 1?}",                 # C accepts; Python rejects
    "extra: {a: 1, b: true}",         # supported flow mapping
    "extra: &anchor [one, two]\ncopy: *anchor",
    "extra: 'quoted # text'",
    "extra: null",
    "extra: yes",
    "extra: 0x2a",
    "extra: 2026-09-25",
    "extra:\n  nested:\n    count: 3",
    "extra:\n  - one\n  - two",
    "extra: |\n  line one\n  line two",
    "extra: {a: 1, a: 2}",           # nested duplicate
    "extra: {1: value}",             # non-string key
    "extra: {<<: {a: 1}}",           # merge key rejected
    "extra: !!python/object/apply:os.system ['true']",
    "extra: [",
])
def test_loader_matches_python_contract_in_full_validate(tmp_path, source, monkeypatch):
    root = init_workspace(tmp_path / "kunde")
    (root / "CONTEXT.md").write_text(
        f"---\ntype: workspace\n{source}\n---\n", encoding="utf-8"
    )
    monkeypatch.setattr(io, "_StrictLoader", io._PythonStrictLoader)
    try:
        expected_metadata, expected_body = load_frontmatter_and_body(root / "CONTEXT.md", root)
    except ValueError as error:
        expected_error = (type(error), str(error))
    else:
        expected_error = None
    expected = validate(root)
    if not hasattr(yaml, "CSafeLoader"):
        pytest.skip("PyYAML C extension unavailable")
    monkeypatch.setattr(io, "_StrictLoader", io._strict_loader(yaml.CSafeLoader))
    if expected_error is None:
        metadata, body = load_frontmatter_and_body(root / "CONTEXT.md", root)
        assert _typed(metadata) == _typed(expected_metadata)
        assert body == expected_body
    else:
        with pytest.raises(expected_error[0]) as caught:
            load_frontmatter_and_body(root / "CONTEXT.md", root)
        assert str(caught.value) == expected_error[1]
    assert validate(root) == expected


def test_plain_block_fast_path_matches_python_on_seeded_corpus():
    if not hasattr(yaml, "CSafeLoader"):
        pytest.skip("PyYAML C extension unavailable")
    rng = random.Random(52)
    alphabet = "ab01: ,\n-./()_é"
    seeds = (
        "type: workspace",
        "root: a",
        "root:\n  a: 1",
        "root:\n  - a",
        "- a\n- b",
    )
    c_loader = io._strict_loader(yaml.CSafeLoader)

    def outcome(source, loader):
        try:
            return ("value", _typed(yaml.load(source, Loader=loader)))
        except DuplicateKeyError as error:
            return ("duplicate", error.key)
        except ValueError as error:
            return ("value_error", str(error))
        except yaml.YAMLError:
            return ("yaml_error",)

    for seed in seeds:
        for _ in range(120):
            source = seed
            for _ in range(rng.randint(1, 4)):
                position = rng.randrange(len(source) + 1)
                replacement = rng.choice(alphabet)
                delete = int(rng.random() < 0.4)
                source = source[:position] + replacement + source[position + delete:]
            assert outcome(source, c_loader) == outcome(source, io._PythonStrictLoader), source


def test_python_fallback_imports_without_c_extension(tmp_path):
    path = tmp_path / "CONTEXT.md"
    path.write_text("---\ntype: workspace\n---\n", encoding="utf-8")
    program = (
        "import sys, yaml; "
        "yaml.__dict__.pop('CSafeLoader', None); "
        "sys.path.insert(0, sys.argv[1]); "
        "from impacts_protocol import io; "
        "assert io._StrictLoader.__bases__ == (yaml.SafeLoader,); "
        "assert io.load_frontmatter(sys.argv[2]) == {'type': 'workspace'}"
    )
    check = subprocess.run(
        [sys.executable, "-c", program, str(ROOT / "src"), str(path)],
        capture_output=True, text=True,
    )
    assert check.returncode == 0, check.stderr


def test_c_rejection_retries_python_for_plain_frontmatter(tmp_path, monkeypatch):
    if not hasattr(yaml, "CSafeLoader"):
        pytest.skip("PyYAML C extension unavailable")
    path = tmp_path / "CONTEXT.md"
    path.write_text("---\ntype: workspace\n---\n", encoding="utf-8")
    original_load = yaml.load

    def reject_c(source, Loader):
        if Loader is io._StrictLoader:
            raise yaml.YAMLError("C parser rejected fixture")
        return original_load(source, Loader=Loader)

    monkeypatch.setattr(io.yaml, "load", reject_c)
    assert load_frontmatter_and_body(path, tmp_path) == ({"type": "workspace"}, "")


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
