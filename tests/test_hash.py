from contextlib import redirect_stderr, redirect_stdout
import hashlib
from io import StringIO
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import pytest

ROOT = Path(__file__).resolve().parents[1]

from impacts_protocol import HashSurfaceError, file_references
from impacts_protocol.cli import main


def _canonical(attempt: Path, files: dict[str, str]) -> list[dict]:
    return [{"pfad": path, "sha256": "sha256:" + hashlib.sha256((attempt / path).read_bytes()).hexdigest()}
            for path in sorted(files, key=lambda name: name.encode("utf-8"))]


def _attempt(base: Path, files: dict[str, str]) -> Path:
    attempt = base / "001"
    for relative, content in files.items():
        path = attempt / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return attempt


def test_single_file_surface_matches_canonical_serialization():
    with TemporaryDirectory() as directory:
        files = {"input/auftrag.md": "Auftrag"}
        attempt = _attempt(Path(directory), files)

        assert file_references(attempt, ["input/auftrag.md"]) == _canonical(attempt, files)


def test_directory_surface_collects_files_recursively_in_path_byte_order():
    with TemporaryDirectory() as directory:
        files = {
            "input/zwei/b.md": "b",
            "input/a.md": "a",
            "input/ä.md": "umlaut",
        }
        attempt = _attempt(Path(directory), files)

        assert file_references(attempt, ["input/"]) == _canonical(attempt, files)


def test_file_references_match_frozen_raw_byte_vector(tmp_path):
    attempt = _attempt(tmp_path, {"input/a.md": "abc", "input/empty": ""})
    assert file_references(attempt, ["input"]) == [
        {"pfad": "input/a.md", "sha256": "sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"},
        {"pfad": "input/empty", "sha256": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
    ]


def test_content_and_identity_are_bound_separately(tmp_path):
    attempt = _attempt(tmp_path, {"input/a.md": "gleich", "input/b.md": "andere"})
    original = file_references(attempt, ["input"])

    # Identity mutation only: same bytes under a new name.
    (attempt / "input" / "a.md").rename(attempt / "input" / "umbenannt.md")
    renamed = file_references(attempt, ["input"])
    assert renamed != original

    # Content mutation only: original name, changed bytes.
    (attempt / "input" / "umbenannt.md").rename(attempt / "input" / "a.md")
    (attempt / "input" / "a.md").write_text("verändert", encoding="utf-8")
    mutated = file_references(attempt, ["input"])
    assert mutated != original
    assert mutated != renamed


def test_declaration_and_creation_order_do_not_change_hash(tmp_path):
    first = _attempt(tmp_path / "a", {"input/a.md": "a", "input/zwei.md": "b"})
    forward = file_references(first, ["input/a.md", "input/zwei.md"])
    assert file_references(first, ["input/zwei.md", "input/a.md"]) == forward

    second = _attempt(tmp_path / "b", {"input/zwei.md": "b", "input/a.md": "a"})
    assert file_references(second, ["input"]) == forward

    # Overlapping declarations include each path exactly once.
    assert file_references(first, ["input", "input/a.md"]) == forward


def test_missing_surface_raises_hash_mismatch():
    with TemporaryDirectory() as directory:
        attempt = _attempt(Path(directory), {"input/auftrag.md": "x"})

        with pytest.raises(HashSurfaceError) as error:
            file_references(attempt, ["input/fehlt.md"])

        assert error.value.code == "binding.reference_missing"


def test_empty_directory_surface_raises_hash_mismatch():
    with TemporaryDirectory() as directory:
        attempt = Path(directory) / "001"
        (attempt / "output").mkdir(parents=True)

        with pytest.raises(HashSurfaceError) as error:
            file_references(attempt, ["output/"])

        assert error.value.code == "binding.reference_missing"
        assert error.value.message == "Declared reference has no regular file"


@pytest.mark.parametrize("target_kind", ["inside", "outside"])
def test_symlink_inside_surface_raises_actionable_structure_symlink(target_kind):
    with TemporaryDirectory() as directory:
        base = Path(directory)
        attempt = _attempt(base, {"input/auftrag.md": "x"})
        outside = base / "outside.md"
        outside.write_text("fremd", encoding="utf-8")
        target = attempt / "input" / "auftrag.md" if target_kind == "inside" else outside
        link = attempt / "input" / "link.md"
        link.symlink_to(target)

        with pytest.raises(HashSurfaceError) as error:
            file_references(attempt, ["input/"])

        assert error.value.code == "structure.symlink"
        assert error.value.path == link
        assert "materialize approved regular-file bytes before binding" in error.value.message
        assert "record provenance separately" in error.value.message
        assert "preserve it" in error.value.message
        assert "new attempt/revision path" in error.value.message
        assert str(target) not in error.value.message


def test_surface_escaping_attempt_raises_hash_mismatch():
    with TemporaryDirectory() as directory:
        base = Path(directory)
        attempt = _attempt(base, {"input/auftrag.md": "x"})
        (base / "outside.md").write_text("fremd", encoding="utf-8")

        with pytest.raises(HashSurfaceError) as error:
            file_references(attempt, ["../outside.md"])

        assert error.value.code == "binding.reference_missing"


def test_cli_hash_prints_digest_and_exits_zero():
    with TemporaryDirectory() as directory:
        files = {"input/auftrag.md": "Auftrag", "output/ergebnis.md": "Ergebnis"}
        attempt = _attempt(Path(directory), files)
        output = StringIO()

        with redirect_stdout(output):
            exit_code = main(["hash", str(attempt), "input/auftrag.md", "output/ergebnis.md"])

        assert exit_code == 0
        assert json.loads(output.getvalue()) == _canonical(attempt, files)


def test_cli_hash_reports_invalid_surface_and_exits_one():
    with TemporaryDirectory() as directory:
        attempt = _attempt(Path(directory), {"input/auftrag.md": "x"})
        errors = StringIO()

        with redirect_stderr(errors):
            exit_code = main(["hash", str(attempt), "input/fehlt.md"])

        assert exit_code == 1
        assert "binding.reference_missing" in errors.getvalue()


def test_cli_hash_reports_non_utf8_path_and_exits_one(tmp_path, monkeypatch):
    attempt = _attempt(tmp_path, {"input/auftrag.md": "x"})
    source = attempt / "input" / "auftrag.md"
    invalid_resolved = attempt / "input" / "bad-\udcff.md"
    original_resolve = Path.resolve

    def resolve_with_invalid_name(path, *args, **kwargs):
        if path == source:
            return invalid_resolved
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve_with_invalid_name)
    errors = StringIO()
    with redirect_stderr(errors):
        exit_code = main(["hash", str(attempt), "input/auftrag.md"])

    assert exit_code == 1
    assert "binding.reference_missing" in errors.getvalue()
    assert "not valid UTF-8" in errors.getvalue()


@pytest.mark.skipif(sys.platform != "linux", reason="Linux permits non-UTF-8 filename bytes")
def test_cli_hash_rejects_actual_non_utf8_filename_on_linux(tmp_path):
    attempt = _attempt(tmp_path, {"input/auftrag.md": "x"})
    raw_path = os.fsencode(attempt / "input") + b"/bad-\xff.md"
    descriptor = os.open(raw_path, os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        os.write(descriptor, b"synthetic")
    finally:
        os.close(descriptor)

    errors = StringIO()
    with redirect_stderr(errors):
        exit_code = main(["hash", str(attempt), "input/"])

    assert exit_code == 1
    assert "binding.reference_missing" in errors.getvalue()
    assert "not valid UTF-8" in errors.getvalue()


@pytest.mark.parametrize("declared", [[], iter(()), 42, True, {"input/"}, "input/", b"input/", [""], [None], ["/input/"]])
def test_invalid_declaration_uses_hash_error_boundary(tmp_path, declared):
    with pytest.raises(HashSurfaceError) as error:
        file_references(tmp_path, declared)
    assert error.value.code == "binding.reference_missing"
    assert "hash surface" not in error.value.message


def test_unreadable_surface_uses_hash_error_boundary(tmp_path, monkeypatch):
    attempt = _attempt(tmp_path, {"input/auftrag.md": "x"})

    def denied(*args, **kwargs):
        raise PermissionError("synthetic unreadable file")

    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(HashSurfaceError, match="Hash surface cannot be read"):
        file_references(attempt, ["input/auftrag.md"])
