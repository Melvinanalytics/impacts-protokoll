from contextlib import redirect_stderr, redirect_stdout
import hashlib
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

ROOT = Path(__file__).resolve().parents[1]

from impacts_protocol import HashSurfaceError, surface_hash
from impacts_protocol.cli import main


def _canonical(attempt: Path, files: dict[str, str]) -> str:
    entries = [
        {"path": relative, "sha256": hashlib.sha256((attempt / relative).read_bytes()).hexdigest()}
        for relative in files
    ]
    entries.sort(key=lambda entry: entry["path"].encode("utf-8"))
    payload = (
        json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


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

        assert surface_hash(attempt, ["input/auftrag.md"]) == _canonical(attempt, files)


def test_directory_surface_collects_files_recursively_in_path_byte_order():
    with TemporaryDirectory() as directory:
        files = {
            "input/zwei/b.md": "b",
            "input/a.md": "a",
            "input/ä.md": "umlaut",
        }
        attempt = _attempt(Path(directory), files)

        assert surface_hash(attempt, ["input/"]) == _canonical(attempt, files)


def test_missing_surface_raises_hash_mismatch():
    with TemporaryDirectory() as directory:
        attempt = _attempt(Path(directory), {"input/auftrag.md": "x"})

        with pytest.raises(HashSurfaceError) as error:
            surface_hash(attempt, ["input/fehlt.md"])

        assert error.value.code == "hash.mismatch"


def test_empty_directory_surface_raises_hash_mismatch():
    with TemporaryDirectory() as directory:
        attempt = Path(directory) / "001"
        (attempt / "output").mkdir(parents=True)

        with pytest.raises(HashSurfaceError) as error:
            surface_hash(attempt, ["output/"])

        assert error.value.code == "hash.mismatch"


def test_symlink_inside_surface_raises_structure_symlink():
    with TemporaryDirectory() as directory:
        base = Path(directory)
        attempt = _attempt(base, {"input/auftrag.md": "x"})
        outside = base / "outside.md"
        outside.write_text("fremd", encoding="utf-8")
        (attempt / "input" / "link.md").symlink_to(outside)

        with pytest.raises(HashSurfaceError) as error:
            surface_hash(attempt, ["input/"])

        assert error.value.code == "structure.symlink"


def test_surface_escaping_attempt_raises_hash_mismatch():
    with TemporaryDirectory() as directory:
        base = Path(directory)
        attempt = _attempt(base, {"input/auftrag.md": "x"})
        (base / "outside.md").write_text("fremd", encoding="utf-8")

        with pytest.raises(HashSurfaceError) as error:
            surface_hash(attempt, ["../outside.md"])

        assert error.value.code == "hash.mismatch"


def test_cli_hash_prints_digest_and_exits_zero():
    with TemporaryDirectory() as directory:
        files = {"input/auftrag.md": "Auftrag", "output/ergebnis.md": "Ergebnis"}
        attempt = _attempt(Path(directory), files)
        output = StringIO()

        with redirect_stdout(output):
            exit_code = main(["hash", str(attempt), "input/auftrag.md", "output/ergebnis.md"])

        assert exit_code == 0
        assert output.getvalue().strip() == _canonical(attempt, files)


def test_cli_hash_reports_invalid_surface_and_exits_one():
    with TemporaryDirectory() as directory:
        attempt = _attempt(Path(directory), {"input/auftrag.md": "x"})
        errors = StringIO()

        with redirect_stderr(errors):
            exit_code = main(["hash", str(attempt), "input/fehlt.md"])

        assert exit_code == 1
        assert "hash.mismatch" in errors.getvalue()


@pytest.mark.parametrize("declared", [[], iter(()), 42, True, {"input/"}, "input/", b"input/", [""], [None], ["/input/"]])
def test_invalid_declaration_uses_hash_error_boundary(tmp_path, declared):
    with pytest.raises(HashSurfaceError) as error:
        surface_hash(tmp_path, declared)
    assert error.value.code == "hash.mismatch"


def test_unreadable_surface_uses_hash_error_boundary(tmp_path, monkeypatch):
    attempt = _attempt(tmp_path, {"input/auftrag.md": "x"})

    def denied(*args, **kwargs):
        raise PermissionError("synthetic unreadable file")

    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(HashSurfaceError, match="Hash surface cannot be read"):
        surface_hash(attempt, ["input/auftrag.md"])
