"""Owner C audit — attempt lifecycle and canonical hashing (oracles O1, O2, O7).

Lifecycle expectations follow 02_protocol/invariants/complete-process-paths.md.
The fixed hash vector checks the serialization contract documented in
src/impacts_protocol/hashing.py.
"""

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]

from impacts_protocol import surface_hash, validate
from tests.c_owner_support import (
    FROZEN_SURFACE_HASH,
    HUMAN,
    codes,
    committed_workspace,
    entry_active,
    entry_completed,
    entry_waiting,
    issues_for,
    make_attempt,
    rewrite_run,
    write_run,
)
from tests.support import read_context


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --- O2: canonical hashing -------------------------------------------------


def test_surface_hash_matches_frozen_independent_oracle(tmp_path):
    attempt = tmp_path / "001"
    _write(attempt / "input" / "a.md", "a")
    _write(attempt / "input" / "zwei.md", "b")
    _write(attempt / "input" / "ä.md", "umlaut")

    assert surface_hash(attempt, ["input"]) == FROZEN_SURFACE_HASH


def test_content_and_identity_are_bound_separately(tmp_path):
    attempt = tmp_path / "001"
    _write(attempt / "input" / "a.md", "gleich")
    _write(attempt / "input" / "b.md", "andere")
    original = surface_hash(attempt, ["input"])

    # Identity mutation only: same bytes under a new name.
    (attempt / "input" / "a.md").rename(attempt / "input" / "umbenannt.md")
    renamed = surface_hash(attempt, ["input"])
    assert renamed != original

    # Content mutation only: original name, changed bytes.
    (attempt / "input" / "umbenannt.md").rename(attempt / "input" / "a.md")
    _write(attempt / "input" / "a.md", "verändert")
    mutated = surface_hash(attempt, ["input"])
    assert mutated != original
    assert mutated != renamed


def test_declaration_and_creation_order_do_not_change_hash(tmp_path):
    first = tmp_path / "a" / "001"
    _write(first / "input" / "a.md", "a")
    _write(first / "input" / "zwei.md", "b")
    forward = surface_hash(first, ["input/a.md", "input/zwei.md"])
    backward = surface_hash(first, ["input/zwei.md", "input/a.md"])
    assert forward == backward

    second = tmp_path / "b" / "001"
    _write(second / "input" / "zwei.md", "b")
    _write(second / "input" / "a.md", "a")
    assert surface_hash(second, ["input"]) == forward

    # Overlapping declarations include each path exactly once.
    assert surface_hash(first, ["input", "input/a.md"]) == forward


# --- O1: lifecycle states ---------------------------------------------------


def test_active_entry_must_be_last(tmp_path):
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    first = make_attempt(run, "start", 1, input_bytes="eins")
    second = make_attempt(run, "pruefen", 1, input_bytes="zwei")
    entries = [entry_active("start", 1, first), entry_active("pruefen", 1, second)]
    write_run(root, "video-001", revision, entries)

    assert "run.invalid" in codes(root)


@pytest.mark.parametrize(
    "field,value",
    [
        ("gewaehlte_route", "weiter"),
        ("ausgabe_hash", "sha256:" + "0" * 64),
        ("wiedereinstieg", {"ausloeser": "x", "continuation_ref": "y"}),
        ("freigabe", HUMAN),
    ],
)
def test_active_entry_carries_no_decision_fields(tmp_path, field, value):
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    attempt = make_attempt(run, "start", 1, input_bytes="eins")
    entry = entry_active("start", 1, attempt)
    entry[field] = value
    write_run(root, "video-001", revision, [entry])

    assert "run.invalid" in codes(root)


@pytest.mark.parametrize(
    "field,value",
    [
        ("gewaehlte_route", "weiter"),
        ("ausgabe_hash", "sha256:" + "0" * 64),
        ("freigabe", HUMAN),
    ],
)
def test_waiting_entry_carries_only_its_reentry_contract(tmp_path, field, value):
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    attempt = make_attempt(run, "start", 1, input_bytes="eins")
    entry = entry_waiting("start", 1, attempt)
    entry[field] = value
    write_run(root, "video-001", revision, [entry])

    assert "run.invalid" in codes(root)


def test_waiting_entry_must_be_last(tmp_path):
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    first = make_attempt(run, "start", 1, input_bytes="eins", output_bytes="a1")
    second = make_attempt(run, "pruefen", 1, input_bytes="zwei")
    entries = [
        entry_completed("start", 1, first, "weiter"),
        entry_waiting("pruefen", 1, second),
    ]
    write_run(root, "video-001", revision, entries)
    assert validate(root).valid, list(validate(root).issues)

    # A later entry after the waiting one violates the single-current-step rule.
    third = make_attempt(run, "pruefen", 2, input_bytes="drei")
    entries.append(entry_active("pruefen", 2, third))
    rewrite_run(root, run, entries)

    assert "run.invalid" in codes(root)


@pytest.mark.parametrize(
    "mutation",
    [
        "no_route",
        "undeclared_route",
        "no_output_hash",
        "reentry_present",
    ],
)
def test_completed_entry_contract(tmp_path, mutation):
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    attempt = make_attempt(run, "start", 1, input_bytes="eins", output_bytes="a1")
    entry = entry_completed("start", 1, attempt, "weiter")
    if mutation == "no_route":
        del entry["gewaehlte_route"]
    elif mutation == "undeclared_route":
        entry["gewaehlte_route"] = "erfunden"
    elif mutation == "no_output_hash":
        del entry["ausgabe_hash"]
    elif mutation == "reentry_present":
        entry["wiedereinstieg"] = {"ausloeser": "x", "continuation_ref": "y"}
    write_run(root, "video-001", revision, [entry])

    assert "run.invalid" in codes(root)


def test_successor_must_follow_selected_route(tmp_path):
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    first = make_attempt(run, "start", 1, input_bytes="eins", output_bytes="a1")
    second = make_attempt(run, "start", 2, input_bytes="zwei")
    entries = [
        entry_completed("start", 1, first, "weiter"),  # route targets pruefen
        entry_active("start", 2, second),  # but the run continues at start
    ]
    write_run(root, "video-001", revision, entries)

    assert "run.invalid" in codes(root)


def test_laufpfad_must_not_continue_after_end_route(tmp_path):
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    first = make_attempt(run, "start", 1, input_bytes="eins", output_bytes="a1")
    second = make_attempt(run, "pruefen", 1, input_bytes="zwei", output_bytes="a2")
    third = make_attempt(run, "start", 2, input_bytes="drei")
    entries = [
        entry_completed("start", 1, first, "weiter"),
        entry_completed("pruefen", 1, second, "freigegeben", freigabe=HUMAN),
        entry_active("start", 2, third),
    ]
    write_run(root, "video-001", revision, entries)

    assert "run.invalid" in codes(root)


def test_rejection_loop_retry_is_valid(tmp_path):
    """Negative end -> new attempt of the earlier step (O1.5)."""
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    a1 = make_attempt(run, "start", 1, input_bytes="eins", output_bytes="a1")
    p1 = make_attempt(run, "pruefen", 1, input_bytes="zwei", output_bytes="p1")
    a2 = make_attempt(run, "start", 2, input_bytes="drei", output_bytes="a2")
    p2 = make_attempt(run, "pruefen", 2, input_bytes="vier", output_bytes="p2")
    entries = [
        entry_completed("start", 1, a1, "weiter"),
        entry_completed("pruefen", 1, p1, "abgelehnt", freigabe=HUMAN),
        entry_completed("start", 2, a2, "weiter"),
        entry_completed("pruefen", 2, p2, "freigegeben", freigabe=HUMAN),
    ]
    write_run(root, "video-001", revision, entries)

    report = validate(root)
    assert report.valid, report.issues


def test_resumption_after_context_loss(tmp_path):
    """A fresh validator process sees the waiting state; resume preserves bytes."""
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    first = make_attempt(run, "start", 1, input_bytes="eins", output_bytes="a1")
    second = make_attempt(run, "pruefen", 1, input_bytes="zwei", output_bytes="p2")
    entries = [
        entry_completed("start", 1, first, "weiter"),
        entry_waiting("pruefen", 1, second),
    ]
    write_run(root, "video-001", revision, entries)
    bound_input = (second / "input" / "auftrag.md").read_bytes()

    # Context loss: a separate OS process re-reads only the files on disk.
    import subprocess

    check = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from impacts_protocol.cli import main; "
            "sys.exit(main(['validate', sys.argv[1]]))",
            str(root),
        ],
        capture_output=True,
        text=True,
    )
    assert check.returncode == 0, check.stdout + check.stderr

    # Resume: complete the waiting step via its declared route.
    entries[1] = entry_completed("pruefen", 1, second, "freigegeben", freigabe=HUMAN)
    rewrite_run(root, run, entries)

    report = validate(root)
    assert report.valid, report.issues
    assert (second / "input" / "auftrag.md").read_bytes() == bound_input


def test_permitted_draft_while_active_preserves_binding(tmp_path):
    """Independent preparation: undeclared draft under output/ of an active attempt."""
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    attempt = make_attempt(run, "start", 1, input_bytes="eins")
    entry = entry_active("start", 1, attempt)
    write_run(root, "video-001", revision, [entry])
    assert validate(root).valid

    _write(attempt / "output" / "entwurf.md", "ungebundener Entwurf")

    report = validate(root)
    assert report.valid, report.issues
    metadata = read_context(run / "CONTEXT.md")
    assert metadata["laufpfad"][0]["eingabe_hash"] == entry["eingabe_hash"]


def test_attempt_numbering_accepts_999_and_rejects_1000(tmp_path):
    """The run schema and templates/application.md bound attempts at 999.
    Preserve the valid 999 fixture; a 1000 attempt fails schema validation."""
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    attempt = make_attempt(run, "start", 999, input_bytes="eins")
    write_run(root, "video-001", revision, [entry_active("start", 999, attempt)])
    assert validate(root).valid

    attempt1000 = run / "start" / "1000"
    (attempt1000 / "input").mkdir(parents=True)
    (attempt1000 / "input" / "auftrag.md").write_text("eins", encoding="utf-8")
    entry = {
        "arbeitsschritt_ref": "arbeitsschritt:start",
        "versuch": 1000,
        "status": "aktiv",
        "eingabe_hash": surface_hash(attempt1000, ["input/auftrag.md"]),
    }
    write_run(root, "video-001", revision, [entry])
    report = validate(root)
    assert not report.valid
    assert "schema.invalid" in {issue.code for issue in report.issues}


def test_duplicate_attempt_in_laufpfad_is_rejected(tmp_path):
    """The same (step, versuch) pair may not appear twice (reference.duplicate)."""
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    attempt = make_attempt(run, "start", 1, input_bytes="eins")
    entry = entry_active("start", 1, attempt)
    write_run(root, "video-001", revision, [entry, dict(entry)])

    assert "reference.duplicate" in codes(root)


@pytest.mark.parametrize("versuch", [0, -1, True, "1"])
def test_versuch_must_be_a_positive_integer(tmp_path, versuch):
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    attempt = make_attempt(run, "start", 1, input_bytes="eins")
    entry = entry_active("start", 1, attempt)
    entry["versuch"] = versuch
    write_run(root, "video-001", revision, [entry])

    report = validate(root)  # must fail closed, not raise
    assert not report.valid
    assert {"schema.invalid", "run.invalid"} & {issue.code for issue in report.issues}


# --- O7: failure / recovery (checker detects damage) -------------------------


def test_orphan_attempt_directory_is_detected(tmp_path):
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    attempt = make_attempt(run, "start", 1, input_bytes="eins")
    write_run(root, "video-001", revision, [entry_active("start", 1, attempt)])
    assert validate(root).valid

    make_attempt(run, "start", 2, input_bytes="ungebunden")

    assert "run.invalid" in codes(root)


def test_torn_run_router_fails_closed_without_exception(tmp_path):
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    attempt = make_attempt(run, "start", 1, input_bytes="eins")
    write_run(root, "video-001", revision, [entry_active("start", 1, attempt)])
    assert validate(root).valid

    # Simulate an interrupted write: frontmatter truncated, no closing delimiter.
    text = (run / "CONTEXT.md").read_text(encoding="utf-8")
    (run / "CONTEXT.md").write_text(text[: len(text) // 3], encoding="utf-8")

    report = validate(root)
    assert not report.valid
    assert "format.invalid" in {issue.code for issue in report.issues}


def test_duplicate_frontmatter_key_fails_closed(tmp_path):
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    attempt = make_attempt(run, "start", 1, input_bytes="eins")
    write_run(root, "video-001", revision, [entry_active("start", 1, attempt)])

    path = run / "CONTEXT.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("---\n", "---\ntype: vorgang\n", 1), encoding="utf-8")

    assert "format.invalid" in codes(root)


def test_half_created_attempt_reports_hash_mismatch_not_crash(tmp_path):
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    attempt = make_attempt(run, "start", 1, input_bytes="eins")
    write_run(root, "video-001", revision, [entry_active("start", 1, attempt)])

    # Interruption left the declared input missing.
    (attempt / "input" / "auftrag.md").unlink()

    report = validate(root)
    assert not report.valid
    assert "hash.mismatch" in {issue.code for issue in report.issues}


# --- O2.4 / O2.5: binding scope ----------------------------------------------


def test_input_mutation_invalidates_only_the_affected_binding(tmp_path):
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    a1 = make_attempt(run, "start", 1, input_bytes="eins", output_bytes="a1")
    p1 = make_attempt(run, "pruefen", 1, input_bytes="zwei")
    entries = [
        entry_completed("start", 1, a1, "weiter"),
        entry_active("pruefen", 1, p1),
    ]
    write_run(root, "video-001", revision, entries)
    assert validate(root).valid

    (a1 / "input" / "auftrag.md").write_text("manipuliert", encoding="utf-8")

    report = validate(root)
    mismatches = [issue for issue in report.issues if issue.code == "hash.mismatch"]
    assert mismatches, report.issues
    assert all("start/001" in issue.path for issue in mismatches)
    assert not issues_for(root, "vorgaenge/video-001/pruefen")


def test_unrelated_extra_content_changes_no_binding(tmp_path):
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    attempt = make_attempt(run, "start", 1, input_bytes="eins", output_bytes="a1")
    entry = entry_completed("start", 1, attempt, "weiter")
    p1 = make_attempt(run, "pruefen", 1, input_bytes="zwei")
    write_run(root, "video-001", revision, [entry, entry_active("pruefen", 1, p1)])
    assert validate(root).valid

    # Content outside every declared surface authorizes nothing and breaks nothing.
    _write(attempt / "output" / "notiz.md", "nicht deklariert")
    _write(attempt / "roh.txt", "nicht deklariert")

    report = validate(root)
    assert report.valid, report.issues
    metadata = read_context(run / "CONTEXT.md")
    assert metadata["laufpfad"][0]["ausgabe_hash"] == entry["ausgabe_hash"]
