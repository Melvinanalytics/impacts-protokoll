from pathlib import Path
from collections import Counter
from io import BytesIO
import os
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

import pytest

ROOT = Path(__file__).resolve().parents[1]

from impacts_protocol import init_workspace, surface_hash, validate
import impacts_protocol.validator as validator
from tests.support import codes, git, read_context, replace_context, write_application, write_context


def _prepare_workspace(base: Path) -> tuple[Path, Path]:
    root = init_workspace(base / "kunde")
    write_application(root / "applications" / "video")
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    git(root, "add", ".")
    git(root, "commit", "-m", "application v1")
    revision = git(root, "rev-parse", "HEAD:applications/video")

    run = root / "vorgaenge" / "video-001"
    entries = []
    for index, (slug, route) in enumerate(
        (("start", "weiter"), ("pruefen", "freigegeben")), start=1
    ):
        attempt = run / slug / "001"
        (attempt / "input").mkdir(parents=True)
        (attempt / "output").mkdir()
        (attempt / "input" / "auftrag.md").write_text(
            f"Eingabe {index}", encoding="utf-8"
        )
        (attempt / "output" / "ergebnis.md").write_text(
            f"Ausgabe {index}", encoding="utf-8"
        )
        entry = {
            "arbeitsschritt_ref": f"arbeitsschritt:{slug}",
            "versuch": 1,
            "status": "abgeschlossen",
            "eingabe_hash": surface_hash(attempt, ["input/auftrag.md"]),
            "gewaehlte_route": route,
            "ausgabe_hash": surface_hash(attempt, ["output/ergebnis.md"]),
        }
        if slug == "pruefen":
            entry["freigabe"] = {
                "by": "human:reviewer",
                "at": "2026-08-30T10:00:00+02:00",
            }
        entries.append(entry)
    write_context(
        run / "CONTEXT.md",
        {
            "type": "vorgang",
            "id": "vorgang:video-001",
            "application_revision": f"git-tree:{revision}",
            "laufpfad": entries,
        },
        "# Video 001",
    )
    return root, run


def test_committed_revision_and_complete_run_are_valid():
    with TemporaryDirectory() as directory:
        root, _ = _prepare_workspace(Path(directory))

        report = validate(root)

        assert report.valid, report.issues


def test_unreachable_application_tree_is_rejected():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        metadata = read_context(run / "CONTEXT.md")
        metadata["application_revision"] = "git-tree:" + "a" * 40
        replace_context(run / "CONTEXT.md", metadata)

        assert "revision.invalid" in codes(root)


def test_invalid_historical_application_reports_bound_revision_and_field(tmp_path):
    root, run = _prepare_workspace(tmp_path)
    healthy = run.parent / "video-002"
    shutil.copytree(run, healthy)
    metadata = read_context(healthy / "CONTEXT.md")
    metadata["id"] = "vorgang:video-002"
    replace_context(healthy / "CONTEXT.md", metadata)

    path = root / "applications/video/produktion/pruefen/CONTEXT.md"
    original = path.read_bytes()
    metadata = read_context(path)
    metadata["pruefung"] = 42
    replace_context(path, metadata)
    git(root, "add", "applications")
    git(root, "commit", "-m", "invalid application fixture")
    revision = "git-tree:" + git(root, "rev-parse", "HEAD:applications/video")
    path.write_bytes(original)
    metadata = read_context(run / "CONTEXT.md")
    metadata["application_revision"] = revision
    replace_context(run / "CONTEXT.md", metadata)

    report = validate(root)

    assert len(report.issues) == 1, report.issues
    error = report.issues[0]
    assert error.code == "revision.invalid"
    assert error.path == "vorgaenge/video-001/CONTEXT.md"
    assert revision in error.message
    assert "produktion/pruefen/CONTEXT.md: schema.invalid: /pruefung:" in error.message
    assert "impacts-application-" not in error.message


def test_revision_history_is_reused_within_validation_but_rechecked_after_ref_changes(tmp_path, monkeypatch):
    root, run = _prepare_workspace(tmp_path)
    for index in (2, 3):
        duplicate = run.parent / f"video-{index:03}"
        shutil.copytree(run, duplicate)
        metadata = read_context(duplicate / "CONTEXT.md")
        metadata["id"] = f"vorgang:{duplicate.name}"
        replace_context(duplicate / "CONTEXT.md", metadata)

    commands = []
    original_git = validator._git
    def tracked_git(root, *args, **kwargs):
        commands.append(args)
        return original_git(root, *args, **kwargs)
    monkeypatch.setattr(validator, "_git", tracked_git)

    assert validate(root).valid
    assert commands.count(("rev-list", "--all", "--format=%T", "--no-commit-header")) == 1
    commit = git(root, "rev-parse", "HEAD")
    git(root, "update-ref", "-d", "refs/heads/main")
    report = validate(root)
    assert len(report.issues) == 3, report.issues
    assert all(issue.code == "revision.invalid" for issue in report.issues)
    assert commands.count(("rev-list", "--all", "--format=%T", "--no-commit-header")) == 2

    git(root, "update-ref", "refs/heads/main", commit)
    assert validate(root).valid
    assert commands.count(("rev-list", "--all", "--format=%T", "--no-commit-header")) == 3


def test_unrelated_reachable_commit_with_missing_root_tree_does_not_invalidate_bound_application(tmp_path):
    root, _ = _prepare_workspace(tmp_path)
    blob = subprocess.check_output(
        ["git", "-C", str(root), "hash-object", "-w", "--stdin"], input=b"unrelated\n",
    ).decode().strip()
    tree = subprocess.check_output(
        ["git", "-C", str(root), "mktree"],
        input=f"100644 blob {blob}\tunrelated.txt\n".encode(),
    ).decode().strip()
    commit = git(root, "commit-tree", tree, "-m", "unrelated reachable commit")
    git(root, "update-ref", "refs/heads/unrelated", commit)
    tree_object = root / ".git" / "objects" / tree[:2] / tree[2:]
    assert tree_object.is_file()
    tree_object.unlink()

    report = validate(root)
    assert report.valid, report.issues


@pytest.mark.parametrize("entry", [
    "100644 blob {oid}\t/absolute.txt",
    "100644 blob {oid}\t../outside.txt",
    "100644 blob {oid}\ta/../../outside.txt",
    "100644 blob {oid}\tCONTEXT.md ",
    "100644 blob {oid}\tCONTEXT.md.",
    "100644 blob {oid}\ta\\CONTEXT.md",
    "100644 blob {oid}\tCONTEXT.md:stream",
    "100644 blob {oid}\tNUL.txt",
    "100644 blob {oid}\tCON .txt",
    "100644 blob {oid}\tCOM¹",
    "100644 blob {oid}\tcontrol\x01.md",
    "120000 blob {oid}\tlink",
    "160000 commit {oid}\tsubmodule",
    "malformed",
])
def test_unsafe_git_tree_is_rejected_without_writing_outside_target(tmp_path, monkeypatch, entry):
    target = tmp_path / "extracted"
    target.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"preserve")
    listing = entry.format(oid="a" * 40) + "\0"
    monkeypatch.setattr(validator, "_git", lambda *args, **kwargs: listing)

    assert not validator._materialize_tree(tmp_path, "a" * 40, target)
    assert list(target.iterdir()) == []
    assert outside.read_bytes() == b"preserve"


@pytest.mark.parametrize("listing", [
    "100644 blob {oid}\tCONTEXT.md\0" * 2,
    "100644 blob {oid}\tparent\0" "100644 blob {oid}\tparent/child\0",
    "100644 blob {oid}\tsafe.txt\0" "120000 blob {oid}\tlink\0",
])
def test_conflicting_git_paths_are_rejected_before_materialization(tmp_path, monkeypatch, listing):
    monkeypatch.setattr(validator, "_git", lambda *args, **kwargs: listing.format(oid="a" * 40))
    assert not validator._materialize_tree(tmp_path, "a" * 40, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_reachable_application_with_duplicate_git_paths_is_rejected(tmp_path):
    root, run = _prepare_workspace(tmp_path)
    original = git(root, "rev-parse", "HEAD:applications/video")
    rows = git(root, "ls-tree", original).splitlines()
    context = next(row for row in rows if row.endswith("\tCONTEXT.md"))

    def make_tree(rows):
        return subprocess.check_output(
            ["git", "-C", str(root), "mktree"],
            input="\n".join(rows) + "\n", text=True,
        ).strip()

    duplicate = make_tree(rows + [context])
    applications = make_tree([f"040000 tree {duplicate}\tvideo"])
    root_rows = git(root, "ls-tree", "HEAD^{tree}").splitlines()
    root_rows = [row for row in root_rows if not row.endswith("\tapplications")]
    malformed_root = make_tree(root_rows + [f"040000 tree {applications}\tapplications"])
    commit = git(root, "commit-tree", malformed_root, "-p", "HEAD", "-m", "duplicate path fixture")
    git(root, "update-ref", "refs/heads/main", commit)
    metadata = read_context(run / "CONTEXT.md")
    metadata["application_revision"] = f"git-tree:{duplicate}"
    replace_context(run / "CONTEXT.md", metadata)

    assert git(root, "rev-parse", "HEAD:applications/video") == duplicate
    report = validate(root)
    assert not report.valid
    assert "revision.invalid" in {issue.code for issue in report.issues}


def test_bound_tree_ignores_archive_attributes_and_preserves_binary_bytes(tmp_path):
    root, _ = _prepare_workspace(tmp_path)
    application = root / "applications/video"
    payload = b"\x00\xffliteral $Format:%H$\n"
    (application / "payload.bin").write_bytes(payload)
    (application / ".gitattributes").write_text("payload.bin export-ignore\n*.md export-subst\n")
    git(root, "add", "applications")
    git(root, "commit", "-m", "archive attributes fixture")
    oid = git(root, "rev-parse", "HEAD:applications/video")
    target = tmp_path / "materialized"
    target.mkdir()

    assert validator._materialize_tree(root, oid, target)
    assert (target / "payload.bin").read_bytes() == payload
    assert (target / "produktion/pruefen/CONTEXT.md").read_bytes() == (application / "produktion/pruefen/CONTEXT.md").read_bytes()


def test_unreadable_git_tree_returns_failure_without_writing(tmp_path, monkeypatch):
    monkeypatch.setattr(validator, "_git", lambda *args, **kwargs: None)
    assert not validator._materialize_tree(tmp_path, "a" * 40, tmp_path)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("commits", [1, 31, 61])
def test_git_process_count_is_bounded_independently_of_commits(tmp_path, monkeypatch, commits):
    root, run = _prepare_workspace(tmp_path)
    marker = root / "applications/video/produktion/start/CONTEXT.md"
    for number in range(commits - 1):
        marker.write_text(marker.read_text() + f"\nSynthetic history {number}\n")
        git(root, "add", "applications")
        git(root, "commit", "-qm", f"synthetic history {number}")

    commands = Counter()
    original = subprocess.Popen
    def tracked(args, *positionals, **keywords):
        if args[0] == "git":
            commands[args[4]] += 1
        return original(args, *positionals, **keywords)
    monkeypatch.setattr(validator.subprocess, "Popen", tracked)
    report = validate(root)
    assert report.valid, report.issues
    assert commands["rev-list"] == 1
    assert sum(commands.values()) <= 8, commands


@pytest.mark.parametrize("blobs", [1, 81])
def test_materialization_batches_blobs_independent_of_blob_count(tmp_path, monkeypatch, blobs):
    root, _ = _prepare_workspace(tmp_path)
    application = root / "applications/video"
    for number in range(blobs):
        (application / f"payload-{number:03}.bin").write_bytes(b"\0raw\n" + bytes([number]))
    git(root, "add", "applications")
    git(root, "commit", "-qm", "synthetic blobs")
    oid = git(root, "rev-parse", "HEAD:applications/video")
    commands = Counter()
    original = subprocess.Popen
    def tracked(args, *positionals, **keywords):
        if args[0] == "git":
            commands[args[4]] += 1
        return original(args, *positionals, **keywords)
    monkeypatch.setattr(validator.subprocess, "Popen", tracked)
    target = tmp_path / "materialized"
    target.mkdir()
    assert validator._materialize_tree(root, oid, target)
    assert commands == Counter({"ls-tree": 1, "cat-file": 1})
    assert (target / f"payload-{blobs-1:03}.bin").read_bytes() == b"\0raw\n" + bytes([blobs-1])


def test_distinct_historical_revisions_share_one_reachability_scan(tmp_path, monkeypatch):
    root, run = _prepare_workspace(tmp_path)
    marker = root / "applications/video/produktion/start/CONTEXT.md"
    revisions = [git(root, "rev-parse", "HEAD:applications/video")]
    for number in range(9):
        marker.write_text(marker.read_text() + f"\nSynthetic revision {number}\n")
        git(root, "add", "applications")
        git(root, "commit", "-qm", f"revision {number}")
        revisions.append(git(root, "rev-parse", "HEAD:applications/video"))
    for number, oid in enumerate(revisions[1:], start=2):
        dest = run.parent / f"video-{number:03}"
        shutil.copytree(run, dest)
        metadata = read_context(dest / "CONTEXT.md")
        metadata["id"] = f"vorgang:{dest.name}"
        metadata["application_revision"] = f"git-tree:{oid}"
        replace_context(dest / "CONTEXT.md", metadata)

    commands = Counter()
    original = subprocess.Popen
    def tracked(args, *positionals, **keywords):
        if args[0] == "git":
            commands[args[4]] += 1
        return original(args, *positionals, **keywords)
    monkeypatch.setattr(validator.subprocess, "Popen", tracked)
    first = validate(root)
    assert first.valid, first.issues
    assert commands["rev-list"] == 1
    assert sum(commands.values()) <= 44, commands
    assert validate(root) == first
    assert commands["rev-list"] == 2


@pytest.mark.parametrize("response,exit_code,expected", [
    (b"a" * 40 + b" blob 4\n\0\xff\nX\n", 0, b"\0\xff\nX"),
    (b"a" * 40 + b" missing\n", 0, None),
    (b"a" * 40 + b" blob 4\nabc", 0, None),
    (b"a" * 40 + b" blob 4\nABCD\n", 1, None),
])
def test_git_batch_protocol_bytes_missing_truncation_and_exit(tmp_path, monkeypatch, response, exit_code, expected):
    class Process:
        stdin = BytesIO()
        stdout = BytesIO(response)
        def wait(self):
            return exit_code
        def kill(self):
            pass
    monkeypatch.setattr(validator.subprocess, "Popen", lambda *args, **kwargs: Process())
    batch = validator._GitBatch(tmp_path)
    result = batch.read("a" * 40)
    success = batch.close()
    assert (result[1] if result else None) == (b"ABCD" if exit_code else expected)
    assert success == ((response.endswith(b" missing\n") or expected is not None) and exit_code == 0)


def test_batch_reachability_skips_missing_object_but_rejects_broken_framing(tmp_path, monkeypatch):
    oid = "a" * 40
    response = b"a" * 40 + b" missing\n"
    class Process:
        def __init__(self):
            self.stdin = BytesIO()
            self.stdout = BytesIO(response)
        def wait(self):
            return 0
        def kill(self):
            pass
    monkeypatch.setattr(validator.subprocess, "Popen", lambda *args, **kwargs: Process())
    assert validator._batch_collect(tmp_path, {oid}, "tree", lambda *_: [], skip_unreadable=True) == set()
    response = b"a" * 40 + b" tree 4\nabc"
    assert validator._batch_collect(tmp_path, {oid}, "tree", lambda *_: [], skip_unreadable=True) is None


def test_identical_tree_oid_requires_reachability_in_each_repository(tmp_path):
    first, run = _prepare_workspace(tmp_path / "first")
    second = tmp_path / "second"
    git(tmp_path, "clone", "--quiet", str(first), str(second))
    shutil.copytree(run, second / "vorgaenge" / run.name)
    assert validate(first).valid
    assert validate(second).valid
    git(second, "update-ref", "-d", "refs/heads/main")
    git(second, "update-ref", "-d", "refs/remotes/origin/main")
    assert "revision.invalid" in {issue.code for issue in validate(second).issues}
    assert validate(first).valid


def test_tree_at_another_application_slug_does_not_authorize_a_run(tmp_path):
    root, _ = _prepare_workspace(tmp_path)
    git(root, "mv", "applications/video", "applications/other")
    git(root, "commit", "--amend", "-m", "wrong application location")
    assert "revision.invalid" in codes(root)


def test_replacement_tree_cannot_change_bound_application_bytes(tmp_path):
    root, run = _prepare_workspace(tmp_path)
    oid = read_context(run / "CONTEXT.md")["application_revision"].removeprefix("git-tree:")
    path = root / "applications/video/produktion/pruefen/CONTEXT.md"
    metadata = read_context(path)
    metadata["pruefung"] = 42
    replace_context(path, metadata)
    git(root, "add", "applications")
    git(root, "commit", "-m", "invalid replacement fixture")
    replacement = git(root, "rev-parse", "HEAD:applications/video")
    git(root, "checkout", "HEAD^", "--", "applications")
    git(root, "replace", oid, replacement)

    assert validate(root).valid


def test_laufpfad_must_start_at_application_entry():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        metadata = read_context(run / "CONTEXT.md")
        metadata["laufpfad"] = metadata["laufpfad"][1:]
        replace_context(run / "CONTEXT.md", metadata)

        assert "run.invalid" in codes(root)


def test_malformed_laufpfad_entry_fails_closed_without_exception():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        metadata = read_context(run / "CONTEXT.md")
        metadata["laufpfad"] = ["invalid"]
        replace_context(run / "CONTEXT.md", metadata)

        issue_codes = codes(root)

        assert "schema.invalid" in issue_codes
        assert "run.invalid" in issue_codes


def test_malformed_selected_route_fails_closed_without_exception():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        metadata = read_context(run / "CONTEXT.md")
        metadata["laufpfad"][0]["gewaehlte_route"] = ["weiter"]
        replace_context(run / "CONTEXT.md", metadata)

        issue_codes = codes(root)

        assert "schema.invalid" in issue_codes
        assert "run.invalid" in issue_codes


def test_changed_input_bytes_break_hash_binding():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        (run / "start/001/input/auftrag.md").write_text(
            "verändert", encoding="utf-8"
        )

        assert "hash.mismatch" in codes(root)


def test_changed_output_bytes_break_hash_binding():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        (run / "pruefen/001/output/ergebnis.md").write_text(
            "verändert", encoding="utf-8"
        )

        assert "hash.mismatch" in codes(root)


@pytest.mark.skipif(sys.platform != "linux", reason="Linux permits non-UTF-8 filename bytes")
def test_validate_rejects_actual_non_utf8_filename_on_linux(tmp_path):
    root, run = _prepare_workspace(tmp_path)
    attempt = run / "start/001"
    input_directory = attempt / "input/dokumente"
    input_directory.mkdir()
    (attempt / "input/auftrag.md").rename(input_directory / "auftrag.md")

    application_step = root / "applications/video/produktion/start/CONTEXT.md"
    step_metadata = read_context(application_step)
    step_metadata["eingaben"] = ["input/dokumente"]
    replace_context(application_step, step_metadata)
    git(root, "add", "applications/video")
    git(root, "commit", "-m", "bind input directory")
    run_metadata = read_context(run / "CONTEXT.md")
    run_metadata["application_revision"] = "git-tree:" + git(
        root, "rev-parse", "HEAD:applications/video"
    )
    run_metadata["laufpfad"][0]["eingabe_hash"] = surface_hash(
        attempt, ["input/dokumente"]
    )
    replace_context(run / "CONTEXT.md", run_metadata)

    raw_path = os.fsencode(input_directory) + b"/bad-\xff.md"
    descriptor = os.open(raw_path, os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        os.write(descriptor, b"synthetic")
    finally:
        os.close(descriptor)

    report = validate(root)

    assert any(
        issue.code == "hash.mismatch" and "not valid UTF-8" in issue.message
        for issue in report.issues
    )


def test_human_gate_rejects_agent_approval():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        metadata = read_context(run / "CONTEXT.md")
        metadata["laufpfad"][1]["freigabe"]["by"] = "agent:codex"
        replace_context(run / "CONTEXT.md", metadata)

        assert "trust.invalid" in codes(root)


def test_missing_attempt_directory_is_rejected():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        attempt = run / "start/001"
        for path in sorted(attempt.rglob("*"), reverse=True):
            path.unlink() if path.is_file() else path.rmdir()
        attempt.rmdir()

        assert "run.invalid" in codes(root)


def test_waiting_entry_needs_reentry_contract():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        metadata = read_context(run / "CONTEXT.md")
        waiting = metadata["laufpfad"][0]
        waiting["status"] = "wartend"
        waiting.pop("gewaehlte_route")
        waiting.pop("ausgabe_hash")
        metadata["laufpfad"] = [waiting]
        replace_context(run / "CONTEXT.md", metadata)

        assert "run.invalid" in codes(root)


def test_completed_entry_must_not_carry_reentry_contract():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        metadata = read_context(run / "CONTEXT.md")
        metadata["laufpfad"][0]["wiedereinstieg"] = {
            "ausloeser": "Termin",
            "continuation_ref": "calendar:1",
        }
        replace_context(run / "CONTEXT.md", metadata)

        assert "run.invalid" in codes(root)


def test_hash_surface_rejects_a_directory_symlink():
    with TemporaryDirectory() as directory:
        base = Path(directory)
        root, run = _prepare_workspace(base)
        application = root / "applications/video"
        for slug in ("start", "pruefen"):
            path = application / f"produktion/{slug}/CONTEXT.md"
            metadata = read_context(path)
            metadata["eingaben"] = ["input"]
            metadata["ausgaben"] = ["output"]
            replace_context(path, metadata)
        git(root, "add", "applications/video")
        git(root, "commit", "-m", "directory surfaces")

        metadata = read_context(run / "CONTEXT.md")
        metadata["application_revision"] = "git-tree:" + git(
            root, "rev-parse", "HEAD:applications/video"
        )
        for entry in metadata["laufpfad"]:
            slug = entry["arbeitsschritt_ref"].removeprefix("arbeitsschritt:")
            attempt = run / slug / "001"
            entry["eingabe_hash"] = surface_hash(attempt, ["input"])
            entry["ausgabe_hash"] = surface_hash(attempt, ["output"])
        replace_context(run / "CONTEXT.md", metadata)

        external = base / "external"
        external.mkdir()
        (external / "secret.txt").write_text("outside", encoding="utf-8")
        input_root = run / "start/001/input"
        (input_root / "auftrag.md").unlink()
        input_root.rmdir()
        input_root.symlink_to(external, target_is_directory=True)

        assert "structure.symlink" in codes(root)


@pytest.mark.parametrize("language", ["en", "de"])
@pytest.mark.parametrize("contents", ["empty", "application", "populated"])
def test_git_clone_preserves_workspace_validation(tmp_path, language, contents):
    if contents == "populated":
        root, _ = _prepare_workspace(tmp_path)
    else:
        root = init_workspace(tmp_path / "kunde", language=language)
        if contents == "application":
            write_application(root / "applications/video")
        git(root, "init", "-b", "main")
        git(root, "config", "user.email", "test@example.invalid")
        git(root, "config", "user.name", "Test")
    assert validate(root).valid
    git(root, "add", ".")
    git(root, "commit", "-m", "captured workspace")
    clone = tmp_path / "clone"
    git(tmp_path, "clone", "--quiet", str(root), str(clone))
    assert validate(clone).valid
    assert git(clone, "status", "--porcelain") == ""
    if contents == "empty":
        assert not (clone / "applications").exists()
    if contents != "populated":
        assert not (clone / "vorgaenge").exists()
    with pytest.raises(FileExistsError):
        init_workspace(clone)


@pytest.mark.parametrize("collection", ["applications", "vorgaenge"])
@pytest.mark.parametrize("kind,code", [("file", "structure.invalid"), ("symlink", "structure.symlink"), ("placeholder", "structure.invalid"), ("invalid-child", "routing.missing")])
def test_empty_collection_rule_preserves_invalid_entry_rejection(tmp_path, collection, kind, code):
    root = init_workspace(tmp_path / "kunde")
    path = root / collection
    if kind in {"file", "symlink"}:
        path.rmdir()
        if kind == "file":
            path.write_text("invalid collection")
        else:
            path.symlink_to(tmp_path / "missing", target_is_directory=True)
    elif kind == "placeholder":
        (path / ".gitkeep").write_text("")
    else:
        (path / "invalid").mkdir()
    assert code in codes(root)


def test_approval_timestamp_is_a_string_under_the_actual_loader(tmp_path):
    from impacts_protocol.io import load_frontmatter_and_body
    from impacts_protocol.generator import template_text
    path = tmp_path / "CONTEXT.md"
    path.write_text(template_text("vorgang"))
    document, _ = load_frontmatter_and_body(path)
    entry = document['laufpfad'][0]
    entry.update(status='abgeschlossen', gewaehlte_route='freigegeben', ausgabe_hash='sha256:' + 'b' * 64,
                 freigabe={'by': 'human:synthetic', 'at': '2026-08-30T10:00:00+02:00'})
    replace_context(path, document)
    loaded, _ = load_frontmatter_and_body(path)
    assert list(validator.SCHEMA_REGISTRY.errors("vorgang", loaded)) == []
    # PyYAML quotes timestamp-looking strings. Removing those quotes reproduces
    # the invalid YAML timestamp type without weakening the schema.
    text = path.read_text().replace("'2026-08-30T10:00:00+02:00'", '2026-08-30T10:00:00+02:00')
    assert text != path.read_text()
    path.write_text(text)
    loaded, _ = load_frontmatter_and_body(path)
    assert list(validator.SCHEMA_REGISTRY.errors("vorgang", loaded))


def test_definition_memo_keeps_snapshots_alive_and_checks_each_run(tmp_path, monkeypatch):
    root, run = _prepare_workspace(tmp_path)
    second = run.parent / 'video-002'
    shutil.copytree(run, second)
    metadata = read_context(second / 'CONTEXT.md')
    metadata['id'] = 'vorgang:video-002'
    replace_context(second / 'CONTEXT.md', metadata)
    (second / 'start/001/input/auftrag.md').write_text('corruption under a shared definition')
    targets = []
    original_materialize = validator._materialize_tree
    original_resolve = validator._resolve_application

    def materialize(workspace, oid, target):
        targets.append(target)
        return original_materialize(workspace, oid, target)

    def resolve(*args, **kwargs):
        application = original_resolve(*args, **kwargs)
        assert application.root.is_dir()
        assert all((path / 'CONTEXT.md').is_file() for path, _ in application.arbeitsschritte.values())
        return application

    monkeypatch.setattr(validator, '_materialize_tree', materialize)
    monkeypatch.setattr(validator, '_resolve_application', resolve)
    report = validate(root)
    assert len(targets) == 1
    assert all(not path.exists() for path in targets)
    assert any(issue.code == 'hash.mismatch' and 'video-002' in issue.path for issue in report.issues)
    assert all('video-001' not in issue.path for issue in report.issues)


def test_invalid_definition_memo_attributes_each_run(tmp_path, monkeypatch):
    root, run = _prepare_workspace(tmp_path)
    path = root / 'applications/video/produktion/start/CONTEXT.md'
    metadata = read_context(path)
    metadata['pruefung'] = 42
    replace_context(path, metadata)
    git(root, 'add', 'applications')
    git(root, 'commit', '-m', 'synthetic invalid definition')
    metadata = read_context(run / 'CONTEXT.md')
    metadata['application_revision'] = 'git-tree:' + git(root, 'rev-parse', 'HEAD:applications/video')
    replace_context(run / 'CONTEXT.md', metadata)
    second = run.parent / 'video-002'
    shutil.copytree(run, second)
    metadata['id'] = 'vorgang:video-002'
    replace_context(second / 'CONTEXT.md', metadata)
    from unittest.mock import patch
    with patch.object(validator, '_materialize_tree', wraps=validator._materialize_tree) as materialize:
        report = validate(root)
    assert materialize.call_count == 1
    errors = [issue for issue in report.issues if issue.code == 'revision.invalid']
    assert [issue.path for issue in errors] == ['vorgaenge/video-001/CONTEXT.md', 'vorgaenge/video-002/CONTEXT.md']
    assert errors[0].message == errors[1].message
    assert 'preserve existing historical bindings' in errors[0].message
    assert 'new Run' in errors[0].message
    assert 're-bind' not in errors[0].message
