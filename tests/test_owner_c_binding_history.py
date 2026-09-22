"""Owner C audit — binding integrity, history, writeback, transport (O3, O5, O6).

Authoritative meaning: impacts-method.md §Scale ("Existing Vorgänge remain bound to
their historical revision"; move path via git archive; "an OID ... authenticates
neither origin nor approval"), capabilities.md §Record writeback ("Bound definitions
and historical run bytes remain unchanged"; "Core provides no write service").
"""

from hashlib import sha256
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]

from impacts_protocol import init_workspace, surface_hash, validate
from tests.c_owner_support import (
    HUMAN,
    codes,
    committed_workspace,
    entry_completed,
    git,
    issues_for,
    make_attempt,
    write_run,
)
from tests.support import read_context, replace_context

CAPABILITIES = ROOT / "02_protocol" / "capabilities.md"
METHOD = ROOT / "02_protocol" / "impacts-method.md"


def _completed_run(root: Path, revision: str, name: str = "video-001") -> Path:
    run = root / "vorgaenge" / name
    a1 = make_attempt(run, "start", 1, input_bytes="eins", output_bytes="a1")
    p1 = make_attempt(run, "pruefen", 1, input_bytes="zwei", output_bytes="p1")
    entries = [
        entry_completed("start", 1, a1, "weiter"),
        entry_completed("pruefen", 1, p1, "freigegeben", freigabe=HUMAN),
    ]
    write_run(root, name, revision, entries)
    return run


def _tree_digest(root: Path) -> str:
    entries = []
    for path in sorted(
        item for item in root.rglob("*") if item.is_file() and ".git" not in item.parts
    ):
        entries.append(
            (path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest())
        )
    return sha256(json.dumps(entries, separators=(",", ":")).encode()).hexdigest()


# --- O3: history --------------------------------------------------------------


def test_current_application_change_does_not_rebind_old_run(tmp_path):
    root, revision = committed_workspace(tmp_path)
    _completed_run(root, revision)
    assert validate(root).valid

    # Change TODAY's definition: different routes and input declaration.
    step = root / "applications/video/produktion/pruefen/CONTEXT.md"
    metadata = read_context(step)
    metadata["routen"] = {"freigegeben": "end:video-veroeffentlicht"}  # gate now broken
    metadata["eingaben"] = ["input/neu.md"]
    replace_context(step, metadata)
    git(root, "add", "applications")
    git(root, "commit", "-m", "current definition changed after the run")

    report = validate(root)
    # The current application is invalid on its own (gate route set) ...
    assert any(issue.code == "process.gate" for issue in report.issues)
    # ... but the historical run is still judged against the OLD bound definition.
    assert issues_for(root, "vorgaenge/") == []


def test_deleted_current_application_leaves_historical_run_valid(tmp_path):
    root, revision = committed_workspace(tmp_path)
    _completed_run(root, revision)
    assert validate(root).valid

    git(root, "rm", "-r", "-q", "applications/video")
    git(root, "commit", "-m", "application removed from current worktree")

    report = validate(root)
    assert report.valid, report.issues
    assert issues_for(root, "vorgaenge/") == []


def test_same_tree_under_fabricated_commit_is_only_content_identity(tmp_path):
    """A digest cannot detect coordinated rewriting without trusted history (O3.4).

    Expected: validation still passes — and the docs must keep disclaiming exactly
    this. If validation failed, history binding would be over-strict; if the docs
    claimed authentication, that claim would be false.
    """
    root, revision = committed_workspace(tmp_path)
    _completed_run(root, revision)
    assert validate(root).valid

    # Fabricate provenance: identical tree, different author/message/parent chain.
    tree = git(root, "rev-parse", "HEAD^{tree}")
    fabricated = git(
        root,
        "-c", "user.name=Angreifer",
        "-c", "user.email=angreifer@example.invalid",
        "commit-tree", tree, "-m", "gefälschte Herkunft",
    )
    git(root, "update-ref", "refs/heads/main", fabricated)

    report = validate(root)
    assert report.valid, report.issues

    capabilities = CAPABILITIES.read_text(encoding="utf-8")
    method = METHOD.read_text(encoding="utf-8")
    assert "identity, not trustworthiness" in capabilities
    assert "authenticates neither origin nor approval" in method


def test_wrong_revision_shape_is_rejected(tmp_path):
    root, revision = committed_workspace(tmp_path)
    run = _completed_run(root, revision)

    # Bind the run to the repository ROOT tree instead of the application tree.
    metadata = read_context(run / "CONTEXT.md")
    metadata["application_revision"] = "git-tree:" + git(root, "rev-parse", "HEAD^{tree}")
    replace_context(run / "CONTEXT.md", metadata)

    assert "revision.invalid" in codes(root)


# --- O5: writeback vs immutable run evidence -----------------------------------


def test_writeback_to_continuing_record_preserves_run_evidence(tmp_path):
    """Permitted writeback: result lands in a business record outside the run (O5.1)."""
    root, revision = committed_workspace(tmp_path)
    run = _completed_run(root, revision)
    assert validate(root).valid
    before = read_context(run / "CONTEXT.md")

    record = root / "records" / "kunde.md"
    record.parent.mkdir(parents=True)
    output = (run / "pruefen/001/output/ergebnis.md").read_text(encoding="utf-8")
    record.write_text(
        f"# Kunde\n\nLetztes Prüfergebnis (aus vorgang:video-001):\n{output}",
        encoding="utf-8",
    )

    report = validate(root)
    assert report.valid, report.issues
    assert read_context(run / "CONTEXT.md") == before
    attempt = run / "pruefen/001"
    assert surface_hash(attempt, ["output/ergebnis.md"]) == before["laufpfad"][1]["ausgabe_hash"]


def test_writeback_into_completed_attempt_breaks_binding(tmp_path):
    """Run evidence is immutable: using a bound output as writeback target fails (O5.2)."""
    root, revision = committed_workspace(tmp_path)
    run = _completed_run(root, revision)
    assert validate(root).valid

    (run / "pruefen/001/output/ergebnis.md").write_text(
        "nachträglich überschrieben", encoding="utf-8"
    )

    mismatches = [
        issue for issue in validate(root).issues if issue.code == "hash.mismatch"
    ]
    assert mismatches
    assert all("pruefen/001" in issue.path for issue in mismatches)


def test_validate_is_read_only_and_idempotent(tmp_path):
    """Core provides no write service: validation never changes the workspace (O5.3/O5.4)."""
    root, revision = committed_workspace(tmp_path)
    run = _completed_run(root, revision)
    # Introduce detectable damage: the checker must SEE it, not fix or worsen it.
    (run / "start/001/input/auftrag.md").write_text("manipuliert", encoding="utf-8")

    before_digest = _tree_digest(root)
    before_objects = git(root, "count-objects")
    before_status = git(root, "status", "--porcelain")

    first = validate(root)
    second = validate(root)

    assert not first.valid  # damage is detected ...
    assert (first.issues == second.issues)  # ... idempotently ...
    assert _tree_digest(root) == before_digest  # ... and nothing was written.
    assert git(root, "count-objects") == before_objects
    assert git(root, "status", "--porcelain") == before_status


# --- O6: transport ---------------------------------------------------------------


def _build_run_in(root: Path) -> tuple[str, Path]:
    revision = git(root, "rev-parse", "HEAD:applications/video")
    run = _completed_run(root, revision)
    # Runs are evidence: commit them so clone/transport preserves old attempts.
    git(root, "add", "vorgaenge")
    git(root, "commit", "-m", "record run evidence")
    return revision, run


def test_documented_transport_preserves_tree_oid_and_old_runs(tmp_path):
    """impacts-method.md §Scale move path: byte copy keeps OID; old attempts survive (O6.1)."""
    source, _ = committed_workspace(tmp_path / "src_repo")
    revision, run = _build_run_in(source)
    assert validate(source).valid

    # Documented path: archive the application tree into a second repository.
    kunde = init_workspace(tmp_path / "ziel" / "kunde")
    target = kunde / "applications" / "video"
    target.mkdir()
    archive = subprocess.check_output(
        ["git", "-C", str(source), "archive", "--format=tar", f"HEAD:applications/video"]
    )
    subprocess.run(["tar", "-x", "-C", str(target)], input=archive, check=True)
    git(kunde, "init", "-b", "main")
    git(kunde, "config", "user.email", "audit-c@example.invalid")
    git(kunde, "config", "user.name", "Audit C")
    git(kunde, "add", ".")
    git(kunde, "commit", "-m", f"import applications/video (tree {revision})")

    imported = git(kunde, "rev-parse", "HEAD:applications/video")
    assert imported == revision  # content identity preserved through transport
    assert validate(kunde).valid

    # Old attempts are preserved by clone and still verify in the clone.
    clone = tmp_path / "klon"
    subprocess.run(
        ["git", "clone", "--quiet", str(source), str(clone)], check=True
    )
    report = validate(clone)
    assert report.valid, report.issues
    assert (clone / "vorgaenge/video-001/start/001/input/auftrag.md").read_bytes() == (
        run / "start/001/input/auftrag.md"
    ).read_bytes()


def test_export_attributes_inside_application_tree_fail_closed(tmp_path):
    """git archive honors in-tree export attributes — but such a tree is unbindable (O6.2).

    This fixture checks that archiving the Application subtree honors its
    export-ignore attribute. The layout in 02_protocol/templates/application.md
    forbids these extra files, so binding a run to this tree is rejected with
    revision.invalid.
    """
    source, _ = committed_workspace(tmp_path / "src_repo")
    app = source / "applications/video"
    (app / "intern.md").write_text("interne Notiz\n", encoding="utf-8")
    (app / ".gitattributes").write_text("intern.md export-ignore\n", encoding="utf-8")
    git(source, "add", "applications")
    git(source, "commit", "-m", "fixture with in-tree export-ignore")
    revision = git(source, "rev-parse", "HEAD:applications/video")

    # The hazard is real: the documented archive path silently drops the file.
    archive = subprocess.check_output(
        ["git", "-C", str(source), "archive", "--format=tar", f"HEAD:applications/video"]
    )
    target = tmp_path / "export"
    target.mkdir()
    subprocess.run(["tar", "-x", "-C", str(target)], input=archive, check=True)
    assert not (target / "intern.md").exists()

    # ... but no run can ever be bound to that poisoned tree.
    _completed_run(source, revision)
    report = validate(source)
    assert not report.valid
    assert "revision.invalid" in {issue.code for issue in report.issues}

    # The method mandates the OID comparison that keeps transport detectable.
    assert "Matching tree OIDs establish content identity" in METHOD.read_text(
        encoding="utf-8"
    )
