from tests.support import fixture_path, fixture_references
from pathlib import Path
from collections import Counter
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from io import BytesIO
import os
import json
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

import pytest

ROOT = Path(__file__).resolve().parents[1]

from impacts_protocol import init_workspace, validate
import impacts_protocol.validator as validator
from tests.support import (
    HUMAN, codes, committed_workspace, entry_active, entry_completed, entry_waiting, git,
    issues_for, make_attempt, read_context, replace_context, rewrite_vorgang, write_hauptprozess,
    write_context, write_vorgang,
)


@pytest.mark.parametrize("as_json", [False, True])
def test_vorgang_yaml_diagnostic_keeps_location_and_first_use_repair_hint(tmp_path, as_json):
    root, vorgang = _prepare_workspace(tmp_path)
    (vorgang / "CONTEXT.md").write_text(
        "---\ntype: vorgang\nid: vorgang:bad: value\n---\n"
    )
    args = [sys.executable, "-B", "-m", "impacts_protocol.cli", "validate", str(root)]
    if as_json:
        args.append("--json")
    result = subprocess.run(args, text=True, capture_output=True)
    assert result.returncode == 1
    assert "format.invalid" in result.stdout
    assert "line 3, column" in result.stdout
    assert "mapping values are not allowed here" in result.stdout
    assert "quote ambiguous scalar text such as values containing ': '" in result.stdout
    if as_json:
        assert json.loads(result.stdout)["valid"] is False


@pytest.mark.parametrize("as_json", [False, True])
def test_invalid_approval_diagnostic_keeps_found_value_and_independent_error(tmp_path, as_json):
    root, vorgang = _prepare_workspace(tmp_path)
    metadata = read_context(vorgang / "CONTEXT.md")
    metadata["laufpfad"][-1]["freigabe"] = {
        "by": "agent:diagnostic-example",
        "at": "2040-04-07T09:17:32+00:00",
    }
    replace_context(vorgang / "CONTEXT.md", metadata)
    (vorgang / "start/001/output/ergebnis.md").write_text("changed independent output")
    args = [sys.executable, "-B", "-m", "impacts_protocol.cli", "validate", str(root)]
    if as_json:
        args.append("--json")
    result = subprocess.run(args, text=True, capture_output=True)
    assert result.returncode == 1
    assert "freigabe.by must be human:<id>; found 'agent:diagnostic-example'" in result.stdout
    assert "schema.invalid" in result.stdout
    assert "trust.invalid" in result.stdout
    assert "binding.reference_digest" in result.stdout
    if as_json:
        assert json.loads(result.stdout)["valid"] is False


@pytest.mark.parametrize("backend", ["python", "c"])
@pytest.mark.parametrize("tag", ["int", "float", "bool", "timestamp"])
@pytest.mark.parametrize("token", ["''", "'_'", "CANARY_NUMBER", "eins"])
def test_invalid_native_scalar_constructor_keeps_value_cause_and_source_mark_on_each_backend(backend, tag, token):
    import yaml
    from impacts_protocol import io
    if backend == "c" and io._C_SAFE_LOADER is None:
        pytest.skip("PyYAML C extension unavailable")
    loader = io._PythonStrictLoader if backend == "python" else io._strict_loader(io._C_SAFE_LOADER)
    with pytest.raises(yaml.YAMLError) as caught:
        yaml.load(f"probe: !!{tag} {token}\n", Loader=loader)
    value = token.strip("'")
    assert caught.value.problem.startswith(f"invalid YAML {tag} scalar {value!r}:")
    assert str(caught.value.__cause__) in caught.value.problem
    assert caught.value.problem_mark.line == 0
    assert caught.value.problem_mark.column == 7
    with pytest.raises(yaml.YAMLError) as normalized:
        io.load_yaml_strict(f"probe: !!{tag} {token}\n")
    assert caught.value.problem in str(normalized.value)


@pytest.mark.parametrize("as_json", [False, True])
def test_native_scalar_diagnostic_keeps_offending_value_and_original_cause(tmp_path, as_json):
    root, vorgang = _prepare_workspace(tmp_path)
    path = vorgang / "CONTEXT.md"
    path.write_text(path.read_text().replace("type: vorgang", "type: vorgang\nprobe: !!int eins", 1))
    args = [sys.executable, "-B", "-m", "impacts_protocol.cli", "validate", str(root)]
    if as_json:
        args.append("--json")
    result = subprocess.run(args, text=True, capture_output=True)
    assert result.returncode == 1
    assert "format.invalid" in result.stdout
    assert "line 3, column 8" in result.stdout
    assert "invalid YAML int scalar 'eins': invalid literal for int() with base 10: 'eins'" in result.stdout
    if as_json:
        assert json.loads(result.stdout)["valid"] is False


@pytest.mark.parametrize("failure", [RuntimeError, KeyError])
def test_numeric_scalar_normalization_preserves_unexpected_constructor_failures(failure):
    import yaml
    from impacts_protocol import io

    class BrokenLoader(yaml.SafeLoader):
        pass

    def broken_constructor(loader, node):
        raise failure("unexpected constructor invariant")

    BrokenLoader.add_constructor("tag:yaml.org,2002:int", broken_constructor)
    with pytest.raises(failure, match="unexpected constructor invariant"):
        yaml.load("probe: !!int 42\n", Loader=io._strict_loader(BrokenLoader))


def _prepare_workspace(base: Path) -> tuple[Path, Path]:
    root = init_workspace(base / "kunde")
    write_hauptprozess(root / "hauptprozesse" / "video")
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    git(root, "add", ".")
    git(root, "commit", "-m", "hauptprozess v1")
    revision = git(root, "rev-parse", "HEAD:hauptprozesse/video")

    vorgang = root / "vorgaenge" / "video-001"
    # Bind both stable records before the one fixture binding commit.
    for index, slug in enumerate(("start", "pruefen"), start=1):
        source = fixture_path(vorgang / slug / "001", "input/auftrag.md")
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f"Eingabe {index}", encoding="utf-8")
    git(root, "add", "records", "CONTEXT.md")
    git(root, "commit", "--amend", "--no-edit")
    entries = []
    for index, (slug, route) in enumerate(
        (("start", "weiter"), ("pruefen", "freigegeben")), start=1
    ):
        attempt = vorgang / slug / "001"
        (fixture_path(attempt, "input")).mkdir(parents=True, exist_ok=True)
        (attempt / "output").mkdir(parents=True, exist_ok=True)
        (fixture_path(attempt, "input") / "auftrag.md").write_text(
            f"Eingabe {index}", encoding="utf-8"
        )
        (attempt / "output" / "ergebnis.md").write_text(
            f"Ausgabe {index}", encoding="utf-8"
        )
        entry = {
            "arbeitsschritt_ref": f"arbeitsschritt:{slug}",
            "nummer": 1,
            "status": "abgeschlossen",
            "gelesen": fixture_references(attempt, ["input/auftrag.md"]),
            "gewaehlte_route": route,
            "geschrieben": fixture_references(attempt, ["output/ergebnis.md"]),
        }
        if slug == "pruefen":
            entry["freigabe"] = {
                "by": "human:reviewer",
                "at": "2026-08-30T10:00:00+02:00",
            }
        entries.append(entry)
    write_context(
        vorgang / "CONTEXT.md",
        {
            "type": "vorgang", "protocol": "v0.5.0",
            "id": "vorgang:video-001",
            "hauptprozess_revision": f"git-tree:{revision}",
            "laufpfad": entries,
        },
        "# Video 001",
    )
    return root, vorgang


def test_committed_revision_and_complete_vorgang_are_valid():
    with TemporaryDirectory() as directory:
        root, _ = _prepare_workspace(Path(directory))

        report = validate(root)

        assert report.valid, report.issues


def test_missing_vorgang_id_reports_schema_repair_without_folder_mismatch(tmp_path):
    root, vorgang = _prepare_workspace(tmp_path)
    metadata = read_context(vorgang / "CONTEXT.md")
    metadata.pop("id")
    replace_context(vorgang / "CONTEXT.md", metadata)

    issues = validate(root).issues

    assert len(issues) == 1
    assert issues[0].code == "schema.invalid"
    assert issues[0].path == "vorgaenge/video-001/CONTEXT.md"
    assert issues[0].message == (
        "'id' is a required property; add `id` to this frontmatter mapping"
    )


def test_present_wrong_vorgang_id_still_reports_folder_mismatch(tmp_path):
    root, vorgang = _prepare_workspace(tmp_path)
    metadata = read_context(vorgang / "CONTEXT.md")
    metadata["id"] = "vorgang:other-run"
    replace_context(vorgang / "CONTEXT.md", metadata)

    issues = validate(root).issues

    assert len(issues) == 1
    assert issues[0].code == "structure.level"
    assert issues[0].message == "Vorgang ID must match folder slug: found 'vorgang:other-run', expected vorgang:video-001"


def test_current_head_path_does_not_break_hauptprozess_reachability(tmp_path):
    root, _ = _prepare_workspace(tmp_path)
    assert validate(root).valid
    head = git(root, "rev-parse", "HEAD")
    (root / head).write_text("Synthetic filename sharing the current commit object ID.\n")
    assert validate(root).valid


def test_unreachable_hauptprozess_tree_is_rejected():
    with TemporaryDirectory() as directory:
        root, vorgang = _prepare_workspace(Path(directory))
        metadata = read_context(vorgang / "CONTEXT.md")
        metadata["hauptprozess_revision"] = "git-tree:" + "a" * 40
        replace_context(vorgang / "CONTEXT.md", metadata)

        assert "binding.revision" in codes(root)


def test_invalid_historical_hauptprozess_reports_bound_revision_and_field(tmp_path):
    root, vorgang = _prepare_workspace(tmp_path)
    healthy = vorgang.parent / "video-002"
    shutil.copytree(vorgang, healthy)
    metadata = read_context(healthy / "CONTEXT.md")
    metadata["id"] = "vorgang:video-002"
    replace_context(healthy / "CONTEXT.md", metadata)

    path = root / "hauptprozesse/video/produktion/pruefen/CONTEXT.md"
    original = path.read_bytes()
    metadata = read_context(path)
    metadata["pruefung"] = 42
    replace_context(path, metadata)
    git(root, "add", "hauptprozesse")
    git(root, "commit", "-m", "invalid hauptprozess fixture")
    revision = "git-tree:" + git(root, "rev-parse", "HEAD:hauptprozesse/video")
    path.write_bytes(original)
    metadata = read_context(vorgang / "CONTEXT.md")
    metadata["hauptprozess_revision"] = revision
    replace_context(vorgang / "CONTEXT.md", metadata)

    report = validate(root)

    assert len(report.issues) == 1, report.issues
    error = report.issues[0]
    assert error.code == "binding.revision"
    assert error.path == "vorgaenge/video-001/CONTEXT.md"
    assert revision in error.message
    assert "produktion/pruefen/CONTEXT.md: schema.invalid: /pruefung:" in error.message
    assert "impacts-hauptprozess-" not in error.message


def test_revision_history_is_reused_within_validation_but_rechecked_after_ref_changes(tmp_path, monkeypatch):
    root, vorgang = _prepare_workspace(tmp_path)
    for index in (2, 3):
        duplicate = vorgang.parent / f"video-{index:03}"
        shutil.copytree(vorgang, duplicate)
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
    assert sum(args[0] == "rev-list" for args in commands) == 1
    commit = git(root, "rev-parse", "HEAD")
    git(root, "update-ref", "-d", "refs/heads/main")
    report = validate(root)
    assert len(report.issues) == 3, report.issues
    assert all(issue.code == "binding.revision" for issue in report.issues)
    assert sum(args[0] == "rev-list" for args in commands) == 2

    git(root, "update-ref", "refs/heads/main", commit)
    assert validate(root).valid
    assert sum(args[0] == "rev-list" for args in commands) == 3


def test_unrelated_reachable_commit_with_missing_root_tree_does_not_invalidate_bound_hauptprozess(tmp_path):
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


def test_reachable_hauptprozess_with_duplicate_git_paths_is_rejected(tmp_path):
    root, vorgang = _prepare_workspace(tmp_path)
    original = git(root, "rev-parse", "HEAD:hauptprozesse/video")
    rows = git(root, "ls-tree", original).splitlines()
    context = next(row for row in rows if row.endswith("\tCONTEXT.md"))

    def make_tree(rows):
        return subprocess.check_output(
            ["git", "-C", str(root), "mktree"],
            input="\n".join(rows) + "\n", text=True,
        ).strip()

    duplicate = make_tree(rows + [context])
    hauptprozesse = make_tree([f"040000 tree {duplicate}\tvideo"])
    root_rows = git(root, "ls-tree", "HEAD^{tree}").splitlines()
    root_rows = [row for row in root_rows if not row.endswith("\thauptprozesse")]
    malformed_root = make_tree(root_rows + [f"040000 tree {hauptprozesse}\thauptprozesse"])
    commit = git(root, "commit-tree", malformed_root, "-p", "HEAD", "-m", "duplicate path fixture")
    git(root, "update-ref", "refs/heads/main", commit)
    metadata = read_context(vorgang / "CONTEXT.md")
    metadata["hauptprozess_revision"] = f"git-tree:{duplicate}"
    replace_context(vorgang / "CONTEXT.md", metadata)

    assert git(root, "rev-parse", "HEAD:hauptprozesse/video") == duplicate
    report = validate(root)
    assert not report.valid
    assert "binding.revision" in {issue.code for issue in report.issues}


def test_bound_tree_ignores_archive_attributes_and_preserves_binary_bytes(tmp_path):
    root, _ = _prepare_workspace(tmp_path)
    hauptprozess = root / "hauptprozesse/video"
    payload = b"\x00\xffliteral $Format:%H$\n"
    (hauptprozess / "payload.bin").write_bytes(payload)
    (hauptprozess / ".gitattributes").write_text("payload.bin export-ignore\n*.md export-subst\n")
    git(root, "add", "hauptprozesse")
    git(root, "commit", "-m", "archive attributes fixture")
    oid = git(root, "rev-parse", "HEAD:hauptprozesse/video")
    target = tmp_path / "materialized"
    target.mkdir()

    assert validator._materialize_tree(root, oid, target)
    assert (target / "payload.bin").read_bytes() == payload
    assert (target / "produktion/pruefen/CONTEXT.md").read_bytes() == (hauptprozess / "produktion/pruefen/CONTEXT.md").read_bytes()


def test_unreadable_git_tree_returns_failure_without_writing(tmp_path, monkeypatch):
    monkeypatch.setattr(validator, "_git", lambda *args, **kwargs: None)
    assert not validator._materialize_tree(tmp_path, "a" * 40, tmp_path)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("commits", [1, 31, 61])
def test_git_process_count_is_bounded_independently_of_commits(tmp_path, monkeypatch, commits):
    root, vorgang = _prepare_workspace(tmp_path)
    marker = root / "hauptprozesse/video/produktion/start/CONTEXT.md"
    for number in range(commits - 1):
        marker.write_text(marker.read_text() + f"\nSynthetic history {number}\n")
        git(root, "add", "hauptprozesse")
        git(root, "commit", "-qm", f"synthetic history {number}")

    commands = Counter()
    original = subprocess.Popen
    def tracked(args, *positionals, **keywords):
        if args[0] == "git":
            commands[args[args.index("-C") + 2]] += 1
        return original(args, *positionals, **keywords)
    monkeypatch.setattr(validator.subprocess, "Popen", tracked)
    report = validate(root)
    assert report.valid, report.issues
    assert commands["rev-list"] == 1
    assert commands["ls-files"] == 1  # X4 adds one ignored-entry census per validation.
    assert sum(commands.values()) - commands["ls-files"] <= 14, commands


@pytest.mark.parametrize("blobs", [1, 81])
def test_materialization_batches_blobs_independent_of_blob_count(tmp_path, monkeypatch, blobs):
    root, _ = _prepare_workspace(tmp_path)
    hauptprozess = root / "hauptprozesse/video"
    for number in range(blobs):
        (hauptprozess / f"payload-{number:03}.bin").write_bytes(b"\0raw\n" + bytes([number]))
    git(root, "add", "hauptprozesse")
    git(root, "commit", "-qm", "synthetic blobs")
    oid = git(root, "rev-parse", "HEAD:hauptprozesse/video")
    commands = Counter()
    original = subprocess.Popen
    def tracked(args, *positionals, **keywords):
        if args[0] == "git":
            commands[args[args.index("-C") + 2]] += 1
        return original(args, *positionals, **keywords)
    monkeypatch.setattr(validator.subprocess, "Popen", tracked)
    target = tmp_path / "materialized"
    target.mkdir()
    assert validator._materialize_tree(root, oid, target)
    assert commands == Counter({"ls-tree": 1, "cat-file": 1})
    assert (target / f"payload-{blobs-1:03}.bin").read_bytes() == b"\0raw\n" + bytes([blobs-1])


def test_distinct_historical_revisions_share_one_reachability_scan(tmp_path, monkeypatch):
    root, vorgang = _prepare_workspace(tmp_path)
    marker = root / "hauptprozesse/video/produktion/start/CONTEXT.md"
    revisions = [git(root, "rev-parse", "HEAD:hauptprozesse/video")]
    for number in range(9):
        marker.write_text(marker.read_text() + f"\nSynthetic revision {number}\n")
        git(root, "add", "hauptprozesse")
        git(root, "commit", "-qm", f"revision {number}")
        revisions.append(git(root, "rev-parse", "HEAD:hauptprozesse/video"))
    for number, oid in enumerate(revisions[1:], start=2):
        dest = vorgang.parent / f"video-{number:03}"
        shutil.copytree(vorgang, dest)
        metadata = read_context(dest / "CONTEXT.md")
        metadata["id"] = f"vorgang:{dest.name}"
        metadata["hauptprozess_revision"] = f"git-tree:{oid}"
        replace_context(dest / "CONTEXT.md", metadata)

    commands = Counter()
    original = subprocess.Popen
    def tracked(args, *positionals, **keywords):
        if args[0] == "git":
            commands[args[args.index("-C") + 2]] += 1
        return original(args, *positionals, **keywords)
    monkeypatch.setattr(validator.subprocess, "Popen", tracked)
    first = validate(root)
    assert first.valid, first.issues
    assert commands["rev-list"] == 1
    assert commands["ls-files"] == 1
    assert sum(commands.values()) - commands["ls-files"] <= 104, commands
    assert validate(root) == first
    assert commands["rev-list"] == 2
    assert commands["ls-files"] == 2


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
    first, vorgang = _prepare_workspace(tmp_path / "first")
    second = tmp_path / "second"
    git(tmp_path, "clone", "--quiet", str(first), str(second))
    shutil.copytree(vorgang, second / "vorgaenge" / vorgang.name, dirs_exist_ok=True)
    assert validate(first).valid
    assert validate(second).valid
    git(second, "update-ref", "-d", "refs/heads/main")
    git(second, "update-ref", "-d", "refs/remotes/origin/main")
    assert "binding.revision" in {issue.code for issue in validate(second).issues}
    assert validate(first).valid


def test_tree_at_another_hauptprozess_slug_does_not_authorize_a_vorgang(tmp_path):
    root, _ = _prepare_workspace(tmp_path)
    git(root, "mv", "hauptprozesse/video", "hauptprozesse/other")
    git(root, "commit", "--amend", "-m", "wrong hauptprozess location")
    assert "binding.revision" in codes(root)


def test_replacement_tree_cannot_change_bound_hauptprozess_bytes(tmp_path):
    root, vorgang = _prepare_workspace(tmp_path)
    oid = read_context(vorgang / "CONTEXT.md")["hauptprozess_revision"].removeprefix("git-tree:")
    path = root / "hauptprozesse/video/produktion/pruefen/CONTEXT.md"
    metadata = read_context(path)
    metadata["pruefung"] = 42
    replace_context(path, metadata)
    git(root, "add", "hauptprozesse")
    git(root, "commit", "-m", "invalid replacement fixture")
    replacement = git(root, "rev-parse", "HEAD:hauptprozesse/video")
    git(root, "checkout", "HEAD^", "--", "hauptprozesse")
    git(root, "replace", oid, replacement)

    assert validate(root).valid


def test_laufpfad_must_start_at_hauptprozess_entry():
    with TemporaryDirectory() as directory:
        root, vorgang = _prepare_workspace(Path(directory))
        metadata = read_context(vorgang / "CONTEXT.md")
        metadata["laufpfad"] = metadata["laufpfad"][1:]
        replace_context(vorgang / "CONTEXT.md", metadata)

        assert "execution.attempt" in codes(root)


def test_malformed_laufpfad_entry_fails_closed_without_exception():
    with TemporaryDirectory() as directory:
        root, vorgang = _prepare_workspace(Path(directory))
        metadata = read_context(vorgang / "CONTEXT.md")
        metadata["laufpfad"] = ["invalid"]
        replace_context(vorgang / "CONTEXT.md", metadata)

        issue_codes = codes(root)

        assert "schema.invalid" in issue_codes
        assert "execution.attempt" in issue_codes


def test_malformed_selected_route_fails_closed_without_exception():
    with TemporaryDirectory() as directory:
        root, vorgang = _prepare_workspace(Path(directory))
        metadata = read_context(vorgang / "CONTEXT.md")
        metadata["laufpfad"][0]["gewaehlte_route"] = ["weiter"]
        replace_context(vorgang / "CONTEXT.md", metadata)

        issue_codes = codes(root)

        assert "schema.invalid" in issue_codes
        assert "execution.attempt" in issue_codes


def test_changed_output_bytes_break_hash_binding():
    with TemporaryDirectory() as directory:
        root, vorgang = _prepare_workspace(Path(directory))
        (vorgang / "pruefen/001/output/ergebnis.md").write_text(
            "verändert", encoding="utf-8"
        )

        assert "binding.reference_digest" in codes(root)


@pytest.mark.skipif(sys.platform != "linux", reason="Linux permits non-UTF-8 filename bytes")
def test_validate_rejects_actual_non_utf8_filename_on_linux(tmp_path):
    # Sources bind by Git commit, so only a working-tree output inventory can meet such a name.
    root, vorgang = _prepare_workspace(tmp_path)
    raw_path = os.fsencode(vorgang / "start/001/output") + b"/bad-\xff.md"
    descriptor = os.open(raw_path, os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        os.write(descriptor, b"synthetic")
    finally:
        os.close(descriptor)

    report = validate(root)

    assert any(
        issue.code == "binding.reference_missing" and "not valid UTF-8" in issue.message
        for issue in report.issues
    )


def test_human_gate_rejects_agent_approval():
    with TemporaryDirectory() as directory:
        root, vorgang = _prepare_workspace(Path(directory))
        metadata = read_context(vorgang / "CONTEXT.md")
        metadata["laufpfad"][1]["freigabe"]["by"] = "agent:codex"
        replace_context(vorgang / "CONTEXT.md", metadata)

        assert "trust.invalid" in codes(root)


def test_missing_attempt_directory_is_rejected():
    with TemporaryDirectory() as directory:
        root, vorgang = _prepare_workspace(Path(directory))
        attempt = vorgang / "start/001"
        for path in sorted(attempt.rglob("*"), reverse=True):
            path.unlink() if path.is_file() else path.rmdir()
        attempt.rmdir()

        assert "execution.attempt" in codes(root)


def test_waiting_entry_needs_reentry_contract():
    with TemporaryDirectory() as directory:
        root, vorgang = _prepare_workspace(Path(directory))
        metadata = read_context(vorgang / "CONTEXT.md")
        waiting = metadata["laufpfad"][0]
        waiting["status"] = "wartend"
        waiting.pop("gewaehlte_route")
        waiting.pop("geschrieben")
        metadata["laufpfad"] = [waiting]
        replace_context(vorgang / "CONTEXT.md", metadata)

        assert "execution.attempt" in codes(root)


def test_completed_entry_must_not_carry_reentry_contract():
    with TemporaryDirectory() as directory:
        root, vorgang = _prepare_workspace(Path(directory))
        metadata = read_context(vorgang / "CONTEXT.md")
        metadata["laufpfad"][0]["wiedereinstieg"] = {
            "ausloeser": "Termin",
            "continuation_ref": "calendar:1",
        }
        replace_context(vorgang / "CONTEXT.md", metadata)

        assert "execution.attempt" in codes(root)


def _wait_at_gate(root: Path, vorgang: Path, **fields) -> None:
    metadata = read_context(vorgang / "CONTEXT.md")
    gate = metadata["laufpfad"][1]
    for key in ("gewaehlte_route", "geschrieben", "freigabe"):
        gate.pop(key)
    gate |= {"status": "wartend", "wiedereinstieg": {"ausloeser": "Entscheidung der Prüferin", "continuation_ref": "vorgaenge/video-001/pruefen/001/output/ergebnis.md"}}
    gate |= fields
    replace_context(vorgang / "CONTEXT.md", metadata)


def test_status_start_and_next_check_are_optional_offset_timestamps(tmp_path):
    root, vorgang = _prepare_workspace(tmp_path)
    metadata = read_context(vorgang / "CONTEXT.md")
    metadata["laufpfad"][0]["status_seit"] = "2026-10-19T16:30:00+02:00"
    replace_context(vorgang / "CONTEXT.md", metadata)
    # A next check before the status start is no contradiction: the promised time may already have passed.
    _wait_at_gate(root, vorgang, status_seit="2026-10-20T09:00:00+02:00",
                  wiedereinstieg={"ausloeser": "Entscheidung der Prüferin", "continuation_ref": "vorgaenge/video-001/pruefen/001/output/ergebnis.md",
                                  "faellig": "2026-10-18T12:00:00Z"})
    report = validate(root)
    assert report.valid, report.issues


@pytest.mark.parametrize("field, value", [("status_seit", "2026-10-20T09:00:00"), ("status_seit", "2026-10-20"),
                                          ("faellig", "2026-11-02"), ("faellig", "2026-11-02T17:00:00")])
def test_time_fields_without_offset_are_schema_errors(tmp_path, field, value):
    root, vorgang = _prepare_workspace(tmp_path)
    resume = {"ausloeser": "Entscheidung der Prüferin", "continuation_ref": "vorgaenge/video-001/pruefen/001/output/ergebnis.md"}
    if field == "faellig":
        _wait_at_gate(root, vorgang, wiedereinstieg=resume | {"faellig": value})
    else:
        _wait_at_gate(root, vorgang, status_seit=value)
    assert "schema.invalid" in codes(root)


@pytest.mark.parametrize("field", ["status_seit", "faellig"])
def test_time_fields_reject_impossible_calendar_dates(tmp_path, field):
    root, vorgang = _prepare_workspace(tmp_path)
    impossible = "2026-02-31T09:00:00+01:00"
    resume = {"ausloeser": "Entscheidung der Prüferin", "continuation_ref": "vorgaenge/video-001/pruefen/001/output/ergebnis.md"}
    if field == "faellig":
        _wait_at_gate(root, vorgang, wiedereinstieg=resume | {"faellig": impossible})
    else:
        _wait_at_gate(root, vorgang, status_seit=impossible)
    report = validate(root)
    assert any(issue.code == "execution.attempt" and "real calendar timestamp" in issue.message for issue in report.issues)


def test_next_check_cannot_appear_on_an_active_entry(tmp_path):
    root, vorgang = _prepare_workspace(tmp_path)
    _wait_at_gate(root, vorgang, status="aktiv",
                  wiedereinstieg={"ausloeser": "x", "continuation_ref": "y", "faellig": "2026-11-02T17:00:00+01:00"})
    assert "execution.attempt" in codes(root)


def test_output_reference_rejects_a_directory_symlink():
    with TemporaryDirectory() as directory:
        base = Path(directory)
        root, vorgang = _prepare_workspace(base)
        external = base / "external"
        external.mkdir()
        (external / "ergebnis.md").write_text("outside", encoding="utf-8")
        output_root = vorgang / "start/001/output"
        (output_root / "ergebnis.md").unlink()
        output_root.rmdir()
        output_root.symlink_to(external, target_is_directory=True)

        assert "structure.symlink" in codes(root)


@pytest.mark.parametrize("language", ["en", "de"])
@pytest.mark.parametrize("contents", ["empty", "hauptprozess", "populated"])
def test_git_clone_preserves_workspace_validation(tmp_path, language, contents):
    if contents == "populated":
        root, _ = _prepare_workspace(tmp_path)
    else:
        root = init_workspace(tmp_path / "kunde", language=language)
        if contents == "hauptprozess":
            write_hauptprozess(root / "hauptprozesse/video")
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
        assert not (clone / "hauptprozesse").exists()
    if contents != "populated":
        assert not (clone / "vorgaenge").exists()
    with pytest.raises(FileExistsError):
        init_workspace(clone)


@pytest.mark.parametrize("collection", ["hauptprozesse", "vorgaenge"])
@pytest.mark.parametrize("kind,code", [("file", "structure.level"), ("symlink", "structure.symlink"), ("placeholder", "structure.level"), ("invalid-child", "routing.missing")])
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
    entry.update(status='abgeschlossen', gewaehlte_route='freigegeben', geschrieben=[],
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


def test_definition_memo_keeps_snapshots_alive_and_checks_each_vorgang(tmp_path, monkeypatch):
    root, vorgang = _prepare_workspace(tmp_path)
    second = vorgang.parent / 'video-002'
    shutil.copytree(vorgang, second)
    metadata = read_context(second / 'CONTEXT.md')
    metadata['id'] = 'vorgang:video-002'
    replace_context(second / 'CONTEXT.md', metadata)
    (second / 'start/001/output/ergebnis.md').write_text('corruption under a shared definition')
    targets = []
    original_materialize = validator._materialize_tree
    original_resolve = validator._resolve_hauptprozess

    def materialize(workspace, oid, target):
        targets.append(target)
        return original_materialize(workspace, oid, target)

    def resolve(*args, **kwargs):
        hauptprozess = original_resolve(*args, **kwargs)
        assert hauptprozess.root.is_dir()
        assert all((path / 'CONTEXT.md').is_file() for path, _ in hauptprozess.arbeitsschritte.values())
        return hauptprozess

    monkeypatch.setattr(validator, '_materialize_tree', materialize)
    monkeypatch.setattr(validator, '_resolve_hauptprozess', resolve)
    report = validate(root)
    assert len(targets) == 1
    assert all(not path.exists() for path in targets)
    assert any(issue.code == 'binding.reference_digest' and 'video-002' in issue.path for issue in report.issues)
    assert all('video-001' not in issue.path for issue in report.issues)


def test_invalid_definition_memo_attributes_each_vorgang(tmp_path, monkeypatch):
    root, vorgang = _prepare_workspace(tmp_path)
    path = root / 'hauptprozesse/video/produktion/start/CONTEXT.md'
    metadata = read_context(path)
    metadata['pruefung'] = 42
    replace_context(path, metadata)
    git(root, 'add', 'hauptprozesse')
    git(root, 'commit', '-m', 'synthetic invalid definition')
    metadata = read_context(vorgang / 'CONTEXT.md')
    metadata['hauptprozess_revision'] = 'git-tree:' + git(root, 'rev-parse', 'HEAD:hauptprozesse/video')
    replace_context(vorgang / 'CONTEXT.md', metadata)
    second = vorgang.parent / 'video-002'
    shutil.copytree(vorgang, second)
    metadata['id'] = 'vorgang:video-002'
    replace_context(second / 'CONTEXT.md', metadata)
    from unittest.mock import patch
    with patch.object(validator, '_materialize_tree', wraps=validator._materialize_tree) as materialize:
        report = validate(root)
    assert materialize.call_count == 1
    errors = [issue for issue in report.issues if issue.code == 'binding.revision']
    assert [issue.path for issue in errors] == ['vorgaenge/video-001/CONTEXT.md', 'vorgaenge/video-002/CONTEXT.md']
    assert errors[0].message == errors[1].message
    assert 'preserve existing historical bindings' in errors[0].message
    assert 'new Vorgang' in errors[0].message
    assert 're-bind' not in errors[0].message


@pytest.mark.parametrize('case,expected_codes,fragments', [
    ('V1', ['execution.attempt'], ["/laufpfad/0 (arbeitsschritt:start, nummer 1)", "'weitr'", 'actual pruefung result', "['weiter']"]),
    ('V2', ['execution.attempt'], ['/laufpfad/1', "'genehmigt'", "responsible human's decision"]),
    ('V3', ['execution.attempt'], ['/laufpfad/0', 'geschrieben missing', 'every output file']),
    ('V4a', [], []),
    ('V4b', ['execution.attempt'], ['/laufpfad/0', 'next entry is arbeitsschritt:start']),
    ('V5', ['trust.invalid'], ['/laufpfad/0', 'allowed only on a gate: human Arbeitsschritt', 'arbeitsschritt:start declares no gate']),
    ('V6', ['trust.invalid'], ['/laufpfad/1', 'freigabe missing', "responsible human's decision", 'dependent transition unresolved']),
    ('V7', ['execution.attempt'], ['/laufpfad/1', 'aktiv entry must not carry freigabe', 'leave a human-written freigabe unchanged']),
    ('V8', ['schema.invalid', 'trust.invalid'], ['/laufpfad/1', "freigabe.by must be human:<id>; found 'agent:x'", 'preserve decision evidence']),
    ('V9', ['schema.invalid'], ['/laufpfad/1/freigabe/at', '2026-08-30T10:00:00+02:00', 'read this value as datetime', 'quote plain scalar text', "responsible human's decision"]),
    ('V10', ['execution.attempt', 'execution.attempt'], ['aktiv entry must not carry gewaehlte_route', 'aktiv entry must not carry geschrieben']),
    ('V11', ['execution.attempt'], ['/laufpfad/0', 'Attempt directory is missing or unsafe']),
])
def test_entry_diagnostics_identify_the_actual_condition(tmp_path, case, expected_codes, fragments):
    root, vorgang = _prepare_workspace(tmp_path)
    path = vorgang / 'CONTEXT.md'
    metadata = read_context(path)
    entries = metadata['laufpfad']
    if case == 'V1':
        entries[0]['gewaehlte_route'] = 'weitr'
    elif case == 'V2':
        entries[1]['gewaehlte_route'] = 'genehmigt'
    elif case == 'V3':
        entries[0].pop('geschrieben')
    elif case == 'V4a':
        entries.pop()
        shutil.rmtree(vorgang / 'pruefen')
    elif case == 'V4b':
        entries[1] = dict(entries[0], nummer=2)
        entries[1]["geschrieben"] = [{**ref, "pfad": ref["pfad"].replace("/start/001/", "/start/002/")} for ref in entries[0]["geschrieben"]]
        shutil.copytree(vorgang / 'start/001', vorgang / 'start/002')
        shutil.rmtree(vorgang / 'pruefen')
    elif case == 'V5':
        entries[0]['freigabe'] = dict(entries[1]['freigabe'])
    elif case == 'V6':
        entries[1].pop('freigabe')
    elif case == 'V7':
        entries[1]['status'] = 'aktiv'
        entries[1].pop('gewaehlte_route')
        entries[1].pop('geschrieben')
    elif case == 'V8':
        entries[1]['freigabe']['by'] = 'agent:x'
    elif case == 'V10':
        entries[1]['status'] = 'aktiv'
        entries[1].pop('freigabe')
    elif case == 'V11':
        shutil.rmtree(vorgang / 'start')
    replace_context(path, metadata)
    if case == 'V9':
        original = path.read_text()
        changed = original.replace("'2026-08-30T10:00:00+02:00'", '2026-08-30T10:00:00+02:00')
        assert changed != original
        path.write_text(changed)

    issues = validate(root).issues

    assert sorted(issue.code for issue in issues) == sorted(expected_codes), issues
    messages = '\n'.join(issue.message for issue in issues)
    for fragment in fragments:
        assert fragment in messages
    if case in {'V2', 'V6', 'V7', 'V8', 'V9'}:
        assert 'remove freigabe' not in messages and 'reopen' not in messages
        assert 'keep the entry uncompleted' not in messages
    if case == 'V2':
        assert 'freigegeben' not in messages
    assert '02_protocol/' not in messages


@pytest.mark.parametrize('recorded', [None, 42])
def test_missing_or_nonstring_output_hash_preserves_independent_missing_output(tmp_path, recorded):
    root, vorgang = _prepare_workspace(tmp_path)
    path = vorgang / 'CONTEXT.md'
    metadata = read_context(path)
    if recorded is None:
        metadata['laufpfad'][0].pop('geschrieben')
    else:
        metadata['laufpfad'][0]['geschrieben'] = recorded
    replace_context(path, metadata)
    (vorgang / 'start/001/output/ergebnis.md').unlink()

    issues = validate(root).issues

    expected = ['binding.reference_missing', 'execution.attempt'] + (['schema.invalid'] if recorded is not None else [])
    assert sorted(issue.code for issue in issues) == sorted(expected), issues
    missing = next(issue for issue in issues if issue.code == 'binding.reference_missing')
    assert missing.path == 'vorgaenge/video-001/CONTEXT.md'
    assert 'vorgaenge/video-001/start/001/output/ergebnis.md' in missing.message
    assert '/laufpfad/0' in missing.message
    assert 'no regular file' in missing.message
    assert not any('Output hash does not match attempt files' in issue.message for issue in issues)


def test_missing_attempt_keeps_an_independent_orphan_directory(tmp_path):
    root, vorgang = _prepare_workspace(tmp_path)
    shutil.rmtree(vorgang / 'start')
    (vorgang / 'orphan/001').mkdir(parents=True)

    issues = validate(root).issues

    assert [issue.code for issue in issues] == ['execution.attempt', 'execution.attempt']
    assert any('/laufpfad/0' in issue.message and 'missing or unsafe' in issue.message for issue in issues)
    assert any(issue.path == 'vorgaenge/video-001/CONTEXT.md' and 'orphan/001' in issue.message and 'Laufpfad differ' in issue.message for issue in issues)
    assert not any(issue.path == 'vorgaenge/video-001/CONTEXT.md' and 'start/001' in issue.message and 'Laufpfad differ' in issue.message for issue in issues)


def test_yaml_timestamp_type_does_not_hide_independent_invalid_actor(tmp_path):
    root, vorgang = _prepare_workspace(tmp_path)
    path = vorgang / 'CONTEXT.md'
    metadata = read_context(path)
    metadata['laufpfad'][1]['freigabe']['by'] = 'agent:x'
    replace_context(path, metadata)
    path.write_text(path.read_text().replace("'2026-08-30T10:00:00+02:00'", '2026-08-30T10:00:00+02:00'))

    issues = validate(root).issues

    assert sorted(issue.code for issue in issues) == ['schema.invalid', 'schema.invalid', 'trust.invalid']
    assert any('/laufpfad/1/freigabe/at' in issue.message and 'datetime' in issue.message for issue in issues)
    trust = next(issue for issue in issues if issue.code == 'trust.invalid')
    assert "freigabe.by must be human:<id>" in trust.message
    assert "found 'agent:x'" in trust.message
    assert 'freigabe.at' not in trust.message


def test_waiting_entry_reports_each_invalid_field_and_missing_reentry(tmp_path):
    root, vorgang = _prepare_workspace(tmp_path)
    path = vorgang / 'CONTEXT.md'
    metadata = read_context(path)
    metadata['laufpfad'][1]['status'] = 'wartend'
    metadata['laufpfad'][1].pop('freigabe')
    replace_context(path, metadata)

    issues = validate(root).issues

    assert len(issues) == 3 and all(issue.code == 'execution.attempt' for issue in issues)
    assert all('/laufpfad/1 (arbeitsschritt:pruefen, nummer 1)' in issue.message for issue in issues)
    assert {issue.message.split(': ', 1)[1] for issue in issues} == {
        'wartend entry must not carry gewaehlte_route',
        'wartend entry must not carry geschrieben',
        'wartend entry needs wiedereinstieg with ausloeser and continuation_ref',
    }


# --- Attempt lifecycle (binding.md#hauptprozess-tree-rules) ----------------


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_active_entry_must_be_last(tmp_path):
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    first = make_attempt(vorgang, "start", 1, input_bytes="eins")
    second = make_attempt(vorgang, "pruefen", 1, input_bytes="zwei")
    entries = [entry_active("start", 1, first), entry_active("pruefen", 1, second)]
    write_vorgang(root, "video-001", revision, entries)

    assert "execution.attempt" in codes(root)


@pytest.mark.parametrize(
    "field,value",
    [
        ("gewaehlte_route", "weiter"),
        ("geschrieben", "sha256:" + "0" * 64),
        ("wiedereinstieg", {"ausloeser": "x", "continuation_ref": "y"}),
        ("freigabe", HUMAN),
    ],
)
def test_active_entry_carries_no_decision_fields(tmp_path, field, value):
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    attempt = make_attempt(vorgang, "start", 1, input_bytes="eins")
    entry = entry_active("start", 1, attempt)
    entry[field] = value
    write_vorgang(root, "video-001", revision, [entry])

    assert "execution.attempt" in codes(root)


@pytest.mark.parametrize(
    "field,value",
    [
        ("gewaehlte_route", "weiter"),
        ("geschrieben", "sha256:" + "0" * 64),
        ("freigabe", HUMAN),
    ],
)
def test_waiting_entry_carries_only_its_reentry_contract(tmp_path, field, value):
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    attempt = make_attempt(vorgang, "start", 1, input_bytes="eins")
    entry = entry_waiting("start", 1, attempt)
    entry[field] = value
    write_vorgang(root, "video-001", revision, [entry])

    assert "execution.attempt" in codes(root)


def test_waiting_entry_must_be_last(tmp_path):
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    first = make_attempt(vorgang, "start", 1, input_bytes="eins", output_bytes="a1")
    second = make_attempt(vorgang, "pruefen", 1, input_bytes="zwei")
    entries = [
        entry_completed("start", 1, first, "weiter"),
        entry_waiting("pruefen", 1, second),
    ]
    write_vorgang(root, "video-001", revision, entries)
    assert validate(root).valid, list(validate(root).issues)

    # A later entry after the waiting one violates the single-current-step rule.
    third = make_attempt(vorgang, "pruefen", 2, input_bytes="drei")
    entries.append(entry_active("pruefen", 2, third))
    rewrite_vorgang(vorgang, entries)

    assert "execution.attempt" in codes(root)


@pytest.mark.parametrize(
    "mutation",
    [
        "no_route",
        "undeclared_route",
        "no_output_hash",
    ],
)
def test_completed_entry_contract(tmp_path, mutation):
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    attempt = make_attempt(vorgang, "start", 1, input_bytes="eins", output_bytes="a1")
    entry = entry_completed("start", 1, attempt, "weiter")
    if mutation == "no_route":
        del entry["gewaehlte_route"]
    elif mutation == "undeclared_route":
        entry["gewaehlte_route"] = "erfunden"
    elif mutation == "no_output_hash":
        del entry["geschrieben"]
    write_vorgang(root, "video-001", revision, [entry])

    assert "execution.attempt" in codes(root)


def test_successor_must_follow_selected_route(tmp_path):
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    first = make_attempt(vorgang, "start", 1, input_bytes="eins", output_bytes="a1")
    second = make_attempt(vorgang, "start", 2, input_bytes="zwei")
    entries = [
        entry_completed("start", 1, first, "weiter"),  # route targets pruefen
        entry_active("start", 2, second),  # but the Vorgang continues at start
    ]
    write_vorgang(root, "video-001", revision, entries)

    assert "execution.attempt" in codes(root)


def test_laufpfad_must_not_continue_after_end_route(tmp_path):
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    first = make_attempt(vorgang, "start", 1, input_bytes="eins", output_bytes="a1")
    second = make_attempt(vorgang, "pruefen", 1, input_bytes="zwei", output_bytes="a2")
    third = make_attempt(vorgang, "start", 2, input_bytes="drei")
    entries = [
        entry_completed("start", 1, first, "weiter"),
        entry_completed("pruefen", 1, second, "freigegeben", freigabe=HUMAN),
        entry_active("start", 2, third),
    ]
    write_vorgang(root, "video-001", revision, entries)

    assert "execution.attempt" in codes(root)


def test_rejection_loop_retry_is_valid(tmp_path):
    """A rejection rework route opens a new attempt; a real end cannot continue."""
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    a1 = make_attempt(vorgang, "start", 1, input_bytes="eins", output_bytes="a1")
    p1 = make_attempt(vorgang, "pruefen", 1, input_bytes="zwei", output_bytes="p1")
    a2 = make_attempt(vorgang, "start", 2, input_bytes="drei", output_bytes="a2")
    p2 = make_attempt(vorgang, "pruefen", 2, input_bytes="vier", output_bytes="p2")
    entries = [
        entry_completed("start", 1, a1, "weiter"),
        entry_completed("pruefen", 1, p1, "abgelehnt", freigabe=HUMAN),
        entry_completed("start", 2, a2, "weiter"),
        entry_completed("pruefen", 2, p2, "freigegeben", freigabe=HUMAN),
    ]
    write_vorgang(root, "video-001", revision, entries)

    report = validate(root)
    assert report.valid, report.issues


def test_resumption_after_context_loss(tmp_path):
    """A fresh validator process sees the waiting state; resume preserves bytes."""
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    first = make_attempt(vorgang, "start", 1, input_bytes="eins", output_bytes="a1")
    second = make_attempt(vorgang, "pruefen", 1, input_bytes="zwei", output_bytes="p2")
    entries = [
        entry_completed("start", 1, first, "weiter"),
        entry_waiting("pruefen", 1, second),
    ]
    write_vorgang(root, "video-001", revision, entries)
    bound_input = (fixture_path(second, "input") / "auftrag.md").read_bytes()

    # Context loss: a separate OS process re-reads only the files on disk.
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
    rewrite_vorgang(vorgang, entries)

    report = validate(root)
    assert report.valid, report.issues
    assert (fixture_path(second, "input") / "auftrag.md").read_bytes() == bound_input


def test_permitted_draft_while_active_preserves_binding(tmp_path):
    """Independent preparation: undeclared draft under output/ of an active attempt."""
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    attempt = make_attempt(vorgang, "start", 1, input_bytes="eins")
    entry = entry_active("start", 1, attempt)
    write_vorgang(root, "video-001", revision, [entry])
    assert validate(root).valid

    _write(attempt / "output" / "entwurf.md", "ungebundener Entwurf")

    report = validate(root)
    assert report.valid, report.issues
    metadata = read_context(vorgang / "CONTEXT.md")
    assert metadata["laufpfad"][0]["gelesen"] == entry["gelesen"]



def test_duplicate_attempt_in_laufpfad_is_rejected(tmp_path):
    """The same (step, versuch) pair may not appear twice (structure.duplicate_id)."""
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    attempt = make_attempt(vorgang, "start", 1, input_bytes="eins")
    entry = entry_active("start", 1, attempt)
    write_vorgang(root, "video-001", revision, [entry, dict(entry)])

    assert "execution.attempt_duplicate" in codes(root)


@pytest.mark.parametrize("versuch", [0, -1, True, "1"])
def test_versuch_must_be_a_positive_integer(tmp_path, versuch):
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    attempt = make_attempt(vorgang, "start", 1, input_bytes="eins")
    entry = entry_active("start", 1, attempt)
    entry["nummer"] = versuch
    write_vorgang(root, "video-001", revision, [entry])

    report = validate(root)  # must fail closed, not raise
    assert not report.valid
    assert {"schema.invalid", "execution.attempt"} & {issue.code for issue in report.issues}


def test_orphan_attempt_directory_is_detected(tmp_path):
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    attempt = make_attempt(vorgang, "start", 1, input_bytes="eins")
    write_vorgang(root, "video-001", revision, [entry_active("start", 1, attempt)])
    assert validate(root).valid

    make_attempt(vorgang, "start", 2, input_bytes="ungebunden")

    assert "execution.attempt" in codes(root)


def test_torn_vorgang_router_fails_closed_without_exception(tmp_path):
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    attempt = make_attempt(vorgang, "start", 1, input_bytes="eins")
    write_vorgang(root, "video-001", revision, [entry_active("start", 1, attempt)])
    assert validate(root).valid

    # Simulate an interrupted write: frontmatter truncated, no closing delimiter.
    text = (vorgang / "CONTEXT.md").read_text(encoding="utf-8")
    (vorgang / "CONTEXT.md").write_text(text[: len(text) // 3], encoding="utf-8")

    report = validate(root)
    assert not report.valid
    assert "format.invalid" in {issue.code for issue in report.issues}


def test_captured_source_worktree_removal_preserves_recorded_blob(tmp_path):
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    attempt = make_attempt(vorgang, "start", 1, input_bytes="eins")
    write_vorgang(root, "video-001", revision, [entry_active("start", 1, attempt)])
    fixture_path(attempt, "input/auftrag.md").unlink()
    assert validate(root).valid


def test_captured_source_worktree_edit_preserves_recorded_blob(tmp_path):
    root, vorgang = _prepare_workspace(tmp_path)
    fixture_path(vorgang, "start/001/input/auftrag.md").write_text("later source")
    assert validate(root).valid


def test_unrelated_extra_content_changes_no_binding(tmp_path):
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    attempt = make_attempt(vorgang, "start", 1, input_bytes="eins", output_bytes="a1")
    entry = entry_completed("start", 1, attempt, "weiter")
    p1 = make_attempt(vorgang, "pruefen", 1, input_bytes="zwei")
    write_vorgang(root, "video-001", revision, [entry, entry_active("pruefen", 1, p1)])
    assert validate(root).valid

    # Content outside attempts changes no recorded binding.
    _write(root / "notes.md", "nicht deklariert")

    report = validate(root)
    assert report.valid, report.issues
    metadata = read_context(vorgang / "CONTEXT.md")
    assert metadata["laufpfad"][0]["geschrieben"] == entry["geschrieben"]


def test_continuation_ref_is_not_an_execution_route(tmp_path):
    """A route token cannot substitute for the required continuation file path."""
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-x"
    attempt = make_attempt(vorgang, "start", 1, input_bytes="E")
    entry = entry_waiting("start", 1, attempt)
    entry["wiedereinstieg"] = {"ausloeser": "Kundenanruf",
                               "continuation_ref": "arbeitsschritt:pruefen"}
    write_vorgang(root, "video-x", revision, [entry])

    assert "binding.reference_missing" in codes(root)


# --- Human gates and the trust boundary (binding.md, Signals and human gates)
# A written human:<id> attribution does not authenticate a person; Core checks shape only.

CAPABILITIES = ROOT / "02_protocol" / "capabilities.md"
METHOD = ROOT / "02_protocol" / "impacts-method.md"
COLD_WALK_CHECK = ROOT / "06_evaluations" / "cold-walk" / "check.py"


def _gate_vorgang(root: Path, revision: str, freigabe: dict | None, name="video-001") -> Path:
    vorgang = root / "vorgaenge" / name
    a1 = make_attempt(vorgang, "start", 1, input_bytes="eins", output_bytes="a1")
    p1 = make_attempt(vorgang, "pruefen", 1, input_bytes="zwei", output_bytes="p1")
    entries = [
        entry_completed("start", 1, a1, "weiter"),
        entry_completed("pruefen", 1, p1, "freigegeben", freigabe=freigabe),
    ]
    write_vorgang(root, name, revision, entries)
    return vorgang


def _cold_walk_module():
    spec = spec_from_file_location("impacts_cold_walk_for_audit_c", COLD_WALK_CHECK)
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_forged_human_attribution_passes_only_the_syntactic_check(tmp_path):
    """FORGERY CONSTRUCTED EXPLICITLY: this test is written by an agent, and the
    `human:` attribution below is fabricated by that same agent — no human decided
    anything. Core validation ACCEPTS it, because Core checks attribution SHAPE
    only. This is the documented narrow guarantee, not proof of authorization.
    """
    root, revision = committed_workspace(tmp_path)
    forged = {"by": "human:nicht-vorhanden", "at": "2026-08-30T10:00:00+02:00"}
    _gate_vorgang(root, revision, forged)

    report = validate(root)
    assert report.valid, report.issues  # forgery is structurally indistinguishable

    # The contract must keep disclaiming exactly this; if these sentences vanish,
    # the acceptance above becomes a contract defect.
    text = (ROOT / "02_protocol" / "ontology.md").read_text(encoding="utf-8").split(
        "## Enforcement and completion\n", 1
    )[1].split("\n## ", 1)[0]
    assert "nor authenticates a person or decision" in text
    assert "binding.md#signals-and-human-gates" in text
    assert "A written attribution does not authenticate a person" in (
        ROOT / "02_protocol" / "impacts-method.md"
    ).read_text(encoding="utf-8")


def test_reference_harness_consumes_a_fabricated_fixture_syntactically(tmp_path):
    """The reference harness's human-fixture check is syntactic as well: a
    fabricated decision dict passes close_human. The guarantee is only that the
    decision arrives as an EXTERNAL record, not that a human made it."""
    check = _cold_walk_module()
    with TemporaryDirectory() as directory:
        root, _, _, revision, _ = check._prepare_workspace(Path(directory))
        harness = check.Harness(root, revision)

        # Direct opening of the human gate is refused: it must arrive via handoff.
        with pytest.raises(check.ProofError, match="proven producer handoff"):
            harness.open("entscheiden", 1, {})

        # But a fabricated "human" decision dict is consumed without authentication.
        fabricated = {
            "route": "freigegeben",
            "freigabe": {"by": "human:erfunden", "at": "2026-09-01T09:00:00+02:00"},
            "output": "Prüfbericht: ok\nEntscheidung: freigegeben\nBegründung: synthetisch gefälscht\n",
        }
        source = check._hauptprozess_source(root, revision)
        rules, provenance = check._materialize_source(root, source)
        producer = harness.open("pruefen", 1, {
            "material/antrag.md": "synthetic hauptprozess\n",
            "material/antrag-herkunft.md": "synthetic origin\n",
            source.input_path: rules.decode(), source.provenance_input: provenance,
        })
        report = "synthetic report\n"
        handoff = check._hauptprozess_handoff(root, revision, "pruefen", "bestanden")
        entry = harness.advance(producer, {handoff.producer_output: report}, "bestanden", "entscheiden", 1, {
            handoff.consumer_input: report,
            handoff.provenance_input: check._handoff_provenance(handoff.origin("pruefen", 1), report.encode()),
        })
        harness.close_human(entry, fabricated)  # no ProofError: syntactic check only
        assert entry["freigabe"]["by"] == "human:erfunden"


@pytest.mark.parametrize(
    "freigabe",
    [
        {"by": "agent:codex", "at": "2026-08-30T10:00:00+02:00"},
        {"by": "human:", "at": "2026-08-30T10:00:00+02:00"},
        {"by": "human: namenslos", "at": "2026-08-30T10:00:00+02:00"},
        {"by": "Human:gross", "at": "2026-08-30T10:00:00+02:00"},
        {"by": "human:prueferin", "at": "2026-08-30T10:00:00"},  # no timezone
        {"by": "human:prueferin", "at": "bald"},
        {"by": "human:prueferin"},  # missing timestamp
        {"by": "human:prueferin", "at": "2026-08-30T10:00:00+02:00", "rolle": "chef"},
        "human:prueferin",  # not an object
    ],
)
def test_structural_approval_forgeries_are_rejected(tmp_path, freigabe):
    root, revision = committed_workspace(tmp_path)
    _gate_vorgang(root, revision, freigabe)

    report = validate(root)
    assert not report.valid
    assert {"trust.invalid", "schema.invalid"} & {
        issue.code for issue in report.issues
    }, report.issues


def test_missing_approval_on_human_gate_is_rejected(tmp_path):
    root, revision = committed_workspace(tmp_path)
    _gate_vorgang(root, revision, None)

    assert "trust.invalid" in codes(root)


def test_approval_on_non_human_gate_is_rejected(tmp_path):
    root, revision = committed_workspace(tmp_path)
    vorgang = root / "vorgaenge" / "video-001"
    a1 = make_attempt(vorgang, "start", 1, input_bytes="eins", output_bytes="a1")
    # "start" has no gate; an approval here is out of scope for the step.
    entry = entry_completed("start", 1, a1, "weiter", freigabe=HUMAN)
    p1 = make_attempt(vorgang, "pruefen", 1, input_bytes="zwei")
    write_vorgang(root, "video-001", revision, [entry, entry_active("pruefen", 1, p1)])

    assert "trust.invalid" in codes(root)


def test_reference_harness_refuses_to_overwrite_changed_output(tmp_path):
    """_write_outputs binds existing editable files only with their actual current
    bytes: the WRITER prevents stale-draft overwrite; Core's validator only DETECTS."""
    check = _cold_walk_module()
    with TemporaryDirectory() as directory:
        attempt = Path(directory) / "001"
        check._write_files(attempt, {"output/ergebnis.md": "vom Menschen überarbeitet\n"})

        with pytest.raises(check.ProofError, match="Existing output differs"):
            check._write_outputs(attempt, {"output/ergebnis.md": "veralteter Entwurf\n"})

        # Nothing was written: the reviewed draft survives.
        assert (attempt / "output" / "ergebnis.md").read_text(
            encoding="utf-8"
        ) == "vom Menschen überarbeitet\n"

        # Reading the actual bytes first (as the contract demands) succeeds.
        check._write_outputs(
            attempt, {"output/ergebnis.md": "vom Menschen überarbeitet\n"}
        )


# --- Binding history, writeback and transport (impacts-method.md, Scale) ------


@pytest.mark.parametrize("kind,expected", [
    ("branch", True), ("tag", True), ("annotated-tag", True),
    ("remote", True), ("detached", True), ("unborn-branch", True),
    ("unborn-tag", True), ("stash", False), ("stash-index", False),
    ("staged", False), ("unreachable", False), ("auxiliary", False),
])
def test_hauptprozess_history_uses_ordinary_roots_and_resolvable_head(tmp_path, kind, expected):
    root, _ = committed_workspace(tmp_path)
    base = git(root, "rev-parse", "HEAD")
    marker = root / "hauptprozesse/video/CONTEXT.md"
    marker.write_text(marker.read_text() + f"\nSynthetic distinct tree: {kind}.\n")
    if kind in {"stash", "stash-index"}:
        if kind == "stash-index":
            git(root, "add", "hauptprozesse")
        git(root, "stash", "push", "-m", "synthetic stash only")
        ref = "refs/stash^2" if kind == "stash-index" else "refs/stash"
        revision = git(root, "rev-parse", f"{ref}:hauptprozesse/video")
    elif kind == "staged":
        git(root, "add", "hauptprozesse")
        revision = git(root, "rev-parse", f"{git(root, 'write-tree')}:hauptprozesse/video")
    else:
        git(root, "checkout", "--detach", "HEAD")
        git(root, "add", "hauptprozesse")
        git(root, "commit", "-m", "synthetic distinct commit")
        commit = git(root, "rev-parse", "HEAD")
        revision = git(root, "rev-parse", "HEAD:hauptprozesse/video")
        refs = {
            "branch": "refs/heads/retained", "tag": "refs/tags/retained",
            "remote": "refs/remotes/origin/retained", "auxiliary": "refs/probe/retained",
            "unborn-branch": "refs/heads/retained", "unborn-tag": "refs/tags/retained",
        }
        if kind in refs:
            git(root, "update-ref", refs[kind], commit)
        elif kind == "annotated-tag":
            git(root, "tag", "-a", "retained", "-m", "synthetic tag", commit)
        if kind != "detached":
            git(root, "checkout", "main")
            assert git(root, "rev-parse", "HEAD") == base
        if kind.startswith("unborn-"):
            git(root, "symbolic-ref", "HEAD", "refs/heads/not-yet-born")

    vorgang = root / "vorgaenge/probe"
    attempt = make_attempt(vorgang, "start", 1, input_bytes="synthetic input")
    write_vorgang(root, "probe", revision, [entry_active("start", 1, attempt)])
    report = validate(root)
    assert report.valid is expected, report.issues
    if not expected:
        assert "binding.revision" in {issue.code for issue in report.issues}


def test_stash_duplicate_of_ordinary_history_remains_usable(tmp_path):
    root, revision = committed_workspace(tmp_path)
    (root / "synthetic-note.md").write_text("unrelated stash bytes")
    git(root, "stash", "push", "--include-untracked")
    _completed_vorgang(root, revision)
    assert validate(root).valid


def test_shallow_history_does_not_use_hidden_ancestor_objects(tmp_path):
    source, old_revision = committed_workspace(tmp_path, "source")
    marker = source / "hauptprozesse/video/CONTEXT.md"
    marker.write_text(marker.read_text() + "\nSynthetic shallow tip.\n")
    git(source, "add", "hauptprozesse")
    git(source, "commit", "-m", "shallow tip")
    tip_revision = git(source, "rev-parse", "HEAD:hauptprozesse/video")
    root = tmp_path / "shallow"
    subprocess.run(["git", "clone", "--depth=1", source.as_uri(), str(root)], check=True, capture_output=True)
    _completed_vorgang(root, tip_revision)
    assert validate(root).valid
    vorgang = root / "vorgaenge/video-001/CONTEXT.md"
    metadata = read_context(vorgang)
    metadata["hauptprozess_revision"] = f"git-tree:{old_revision}"
    replace_context(vorgang, metadata)
    assert "binding.revision" in codes(root)
    # Transfer old objects without altering the shallow boundary or selected refs.
    git(root, "fetch", "--unshallow", "origin")
    tip = git(root, "rev-parse", "refs/remotes/origin/main")
    (root / ".git/shallow").write_text(tip + "\n")
    assert git(root, "cat-file", "-t", old_revision) == "tree"
    assert "binding.revision" in codes(root)


def _completed_vorgang(root: Path, revision: str, name: str = "video-001") -> Path:
    vorgang = root / "vorgaenge" / name
    a1 = make_attempt(vorgang, "start", 1, input_bytes="eins", output_bytes="a1")
    p1 = make_attempt(vorgang, "pruefen", 1, input_bytes="zwei", output_bytes="p1")
    entries = [
        entry_completed("start", 1, a1, "weiter"),
        entry_completed("pruefen", 1, p1, "freigegeben", freigabe=HUMAN),
    ]
    write_vorgang(root, name, revision, entries)
    return vorgang


def _tree_digest(root: Path) -> str:
    entries = []
    for path in sorted(
        item for item in root.rglob("*") if item.is_file() and ".git" not in item.parts
    ):
        entries.append(
            (path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest())
        )
    return sha256(json.dumps(entries, separators=(",", ":")).encode()).hexdigest()


def test_current_hauptprozess_change_does_not_rebind_old_vorgang(tmp_path):
    root, revision = committed_workspace(tmp_path)
    _completed_vorgang(root, revision)
    assert validate(root).valid

    # Change TODAY's definition: different routes and input declaration.
    step = root / "hauptprozesse/video/produktion/pruefen/CONTEXT.md"
    metadata = read_context(step)
    metadata["routen"] = {"freigegeben": "end:video-veroeffentlicht"}  # gate now broken
    metadata["eingaben"] = ["input/neu.md"]
    replace_context(step, metadata)
    git(root, "add", "hauptprozesse")
    git(root, "commit", "-m", "current definition changed after the run")

    report = validate(root)
    # The current Hauptprozess is invalid on its own (gate route set) ...
    assert any(issue.code == "process.gate" for issue in report.issues)
    # ... but the historical Vorgang is still judged against the OLD bound definition.
    assert issues_for(root, "vorgaenge/") == []


def test_deleted_current_hauptprozess_leaves_historical_vorgang_valid(tmp_path):
    root, revision = committed_workspace(tmp_path)
    _completed_vorgang(root, revision)
    assert validate(root).valid

    git(root, "rm", "-r", "-q", "hauptprozesse/video")
    git(root, "commit", "-m", "hauptprozess removed from current worktree")

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
    _completed_vorgang(root, revision)
    assert validate(root).valid

    # Source commits must remain reachable independently of the rewritten main branch.
    git(root, "branch", "retained-sources", "HEAD")
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
    vorgang = _completed_vorgang(root, revision)

    # Bind the Vorgang to the repository ROOT tree instead of the Hauptprozess tree.
    metadata = read_context(vorgang / "CONTEXT.md")
    metadata["hauptprozess_revision"] = "git-tree:" + git(root, "rev-parse", "HEAD^{tree}")
    replace_context(vorgang / "CONTEXT.md", metadata)

    assert "binding.revision" in codes(root)


def test_writeback_to_continuing_record_preserves_vorgang_evidence(tmp_path):
    """Permitted writeback: result lands in a business record outside the Vorgang (O5.1)."""
    root, revision = committed_workspace(tmp_path)
    vorgang = _completed_vorgang(root, revision)
    assert validate(root).valid
    before = read_context(vorgang / "CONTEXT.md")

    record = root / "records" / "kunde" / "status.md"
    record.parent.mkdir(parents=True, exist_ok=True)
    output = (vorgang / "pruefen/001/output/ergebnis.md").read_text(encoding="utf-8")
    record.write_text(
        f"# Kunde\n\nLetztes Prüfergebnis (aus vorgang:video-001):\n{output}",
        encoding="utf-8",
    )

    report = validate(root)
    assert report.valid, report.issues
    assert read_context(vorgang / "CONTEXT.md") == before
    attempt = vorgang / "pruefen/001"
    assert fixture_references(attempt, ["output/ergebnis.md"]) == before["laufpfad"][1]["geschrieben"]


def test_writeback_into_completed_attempt_breaks_binding(tmp_path):
    """Vorgang evidence is immutable: using a bound output as writeback target fails (O5.2)."""
    root, revision = committed_workspace(tmp_path)
    vorgang = _completed_vorgang(root, revision)
    assert validate(root).valid

    (vorgang / "pruefen/001/output/ergebnis.md").write_text(
        "nachträglich überschrieben", encoding="utf-8"
    )

    mismatches = [
        issue for issue in validate(root).issues if issue.code == "binding.reference_digest"
    ]
    assert mismatches
    assert all(issue.path == "vorgaenge/video-001/CONTEXT.md" and "pruefen/001" in issue.message for issue in mismatches)


def test_validate_is_read_only_and_idempotent(tmp_path):
    """Core provides no write service: validation never changes the workspace (O5.3/O5.4)."""
    root, revision = committed_workspace(tmp_path)
    vorgang = _completed_vorgang(root, revision)
    # Introduce detectable damage: the checker must SEE it, not fix or worsen it.
    (vorgang / "start/001/output/ergebnis.md").write_text("manipuliert", encoding="utf-8")

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


def _build_vorgang_in(root: Path) -> tuple[str, Path]:
    revision = git(root, "rev-parse", "HEAD:hauptprozesse/video")
    vorgang = _completed_vorgang(root, revision)
    # Vorgaenge are evidence: commit them so clone/transport preserves old attempts.
    git(root, "add", "vorgaenge", "CONTEXT.md")
    git(root, "commit", "-m", "record run evidence")
    return revision, vorgang


def test_documented_transport_preserves_tree_oid_and_old_vorgaenge(tmp_path):
    """impacts-method.md §Scale move path: byte copy keeps OID; old attempts survive (O6.1)."""
    source, _ = committed_workspace(tmp_path / "src_repo")
    revision, vorgang = _build_vorgang_in(source)
    assert validate(source).valid

    # Documented path: archive the Hauptprozess tree into a second repository.
    kunde = init_workspace(tmp_path / "ziel" / "kunde")
    target = kunde / "hauptprozesse" / "video"
    target.mkdir()
    archive = subprocess.check_output(
        ["git", "-C", str(source), "archive", "--format=tar", f"HEAD:hauptprozesse/video"]
    )
    subprocess.run(["tar", "-x", "-C", str(target)], input=archive, check=True)
    git(kunde, "init", "-b", "main")
    git(kunde, "config", "user.email", "audit-c@example.invalid")
    git(kunde, "config", "user.name", "Audit C")
    git(kunde, "add", ".")
    git(kunde, "commit", "-m", f"import hauptprozesse/video (tree {revision})")

    imported = git(kunde, "rev-parse", "HEAD:hauptprozesse/video")
    assert imported == revision  # content identity preserved through transport
    assert validate(kunde).valid

    # Old attempts are preserved by clone and still verify in the clone.
    clone = tmp_path / "klon"
    subprocess.run(
        ["git", "clone", "--quiet", str(source), str(clone)], check=True
    )
    report = validate(clone)
    assert report.valid, report.issues
    assert (fixture_path(clone, "vorgaenge/video-001/start/001/input/auftrag.md")).read_bytes() == (
        fixture_path(vorgang, "start/001/input/auftrag.md")
    ).read_bytes()


def test_export_attributes_inside_hauptprozess_tree_fail_closed(tmp_path):
    """git archive honors in-tree export attributes — but such a tree is unbindable (O6.2).

    This fixture checks that archiving the Hauptprozess tree honors its
    export-ignore attribute. The layout in 02_protocol/templates/hauptprozess.md
    forbids these extra files, so binding a Vorgang to this tree is rejected with
    binding.revision.
    """
    source, _ = committed_workspace(tmp_path / "src_repo")
    app = source / "hauptprozesse/video"
    (app / "intern.md").write_text("interne Notiz\n", encoding="utf-8")
    (app / ".gitattributes").write_text("intern.md export-ignore\n", encoding="utf-8")
    git(source, "add", "hauptprozesse")
    git(source, "commit", "-m", "fixture with in-tree export-ignore")
    revision = git(source, "rev-parse", "HEAD:hauptprozesse/video")

    # The hazard is real: the documented archive path silently drops the file.
    archive = subprocess.check_output(
        ["git", "-C", str(source), "archive", "--format=tar", f"HEAD:hauptprozesse/video"]
    )
    target = tmp_path / "export"
    target.mkdir()
    subprocess.run(["tar", "-x", "-C", str(target)], input=archive, check=True)
    assert not (target / "intern.md").exists()

    # ... but no Vorgang can ever be bound to that poisoned tree.
    _completed_vorgang(source, revision)
    report = validate(source)
    assert not report.valid
    assert "binding.revision" in {issue.code for issue in report.issues}

    # The method mandates the OID comparison that keeps transport detectable.
    assert "Matching tree OIDs establish content identity" in METHOD.read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize("old_home", ["analyse", "applications"])
def test_v04_binds_only_trees_in_hauptprozesse_history(tmp_path, old_home):
    root, vorgang = _prepare_workspace(tmp_path)
    # Rebuild reachable history with this tree only at the excluded home.
    shutil.rmtree(root / ".git")
    (root / old_home).mkdir(exist_ok=True)
    (root / "hauptprozesse/video").rename(root / old_home / "video")
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    git(root, "add", ".")
    git(root, "commit", "-m", "synthetic excluded definition home")
    oid = git(root, "rev-parse", f"HEAD:{old_home}/video")
    # No source references needed: revision resolution must reject before execution.
    write_vorgang(root, vorgang.name, oid, [])
    assert "binding.revision" in codes(root)
    (root / "hauptprozesse").mkdir(exist_ok=True)
    (root / old_home / "video").rename(root / "hauptprozesse/video")
    git(root, "add", ".")
    git(root, "commit", "-m", "synthetic byte-identical move")
    assert git(root, "rev-parse", "HEAD:hauptprozesse/video") == oid
    assert "binding.revision" not in codes(root)


def test_first_import_and_reviewed_takeover_keep_open_vorgang_revision(tmp_path):
    source, source_oid = committed_workspace(tmp_path, "source")
    target = init_workspace(tmp_path / "target")
    git(target, "init", "-b", "main")
    git(target, "config", "user.email", "test@example.invalid")
    git(target, "config", "user.name", "Test")
    # First import into an empty folder preserves source bytes and records origin outside it.
    destination = target / "hauptprozesse/video"
    shutil.copytree(source / "hauptprozesse/video", destination)
    record = (target / "CONTEXT.md").read_text()
    record += f"\nImported hauptprozess:video: source repository {source}, commit {git(source, 'rev-parse', 'HEAD')}, tree git-tree:{source_oid}, source protocol v0.4.0\n"
    (target / "CONTEXT.md").write_text(record)
    git(target, "add", ".")
    git(target, "commit", "-m", "synthetic first import")
    assert git(target, "rev-parse", "HEAD:hauptprozesse/video") == source_oid
    vorgang = target / "vorgaenge/video-001"
    attempt = make_attempt(vorgang, "start", 1, input_bytes="synthetic test case")
    write_vorgang(target, vorgang.name, source_oid, [entry_active("start", 1, attempt)])
    before = (vorgang / "CONTEXT.md").read_bytes()
    assert validate(target).valid
    # Synthetic reviewed takeover: compare an empty staging copy, then replace the target.
    changed = source / "hauptprozesse/video/produktion/start/CONTEXT.md"
    changed.write_text(changed.read_text() + "\nSynthetic revised processing instruction.\n")
    git(source, "add", ".")
    git(source, "commit", "-m", "synthetic source revision")
    new_oid = git(source, "rev-parse", "HEAD:hauptprozesse/video")
    staging = target / "takeover-staging"
    shutil.copytree(source / "hauptprozesse/video", staging)
    assert (staging / "produktion/start/CONTEXT.md").read_bytes() == changed.read_bytes()
    shutil.rmtree(destination)
    staging.rename(destination)
    with (target / "CONTEXT.md").open("a") as router:
        router.write(f"\nImported hauptprozess:video: source repository {source}, commit {git(source, 'rev-parse', 'HEAD')}, tree git-tree:{new_oid}, source protocol v0.4.0\n")
    git(target, "add", ".")
    git(target, "commit", "-m", "synthetic reviewed takeover")
    assert git(target, "rev-parse", "HEAD:hauptprozesse/video") == new_oid != source_oid
    assert (vorgang / "CONTEXT.md").read_bytes() == before
    assert validate(target).valid


@pytest.mark.parametrize("target", ["records/missing.md", "records", "../outside.md", "/tmp/wait.md", "event:reply", "records\\wait.md"])
def test_wait_continuation_requires_an_existing_workspace_file(tmp_path, target):
    root, vorgang = _prepare_workspace(tmp_path)
    _wait_at_gate(root, vorgang, wiedereinstieg={"ausloeser": "response", "continuation_ref": target})
    assert "binding.reference_missing" in codes(root)


def test_wait_continuation_rejects_a_symlink(tmp_path):
    root, vorgang = _prepare_workspace(tmp_path)
    link = root / "records/wait-link.md"
    link.symlink_to(vorgang / "pruefen/001/output/ergebnis.md")
    _wait_at_gate(root, vorgang, wiedereinstieg={"ausloeser": "response", "continuation_ref": "records/wait-link.md"})
    assert "structure.symlink" in codes(root)
