from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol import init_workspace, surface_hash, validate
from tests.support import read_context, replace_context, write_application, write_context


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True
    ).strip()


def _prepare_workspace(base: Path) -> tuple[Path, Path]:
    root = init_workspace(base / "kunde")
    write_application(root / "applications" / "video")
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Test")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "application v1")
    revision = _git(root, "rev-parse", "HEAD:applications/video")

    run = root / "vorgaenge" / "video-001"
    entries = []
    for index, (slug, route) in enumerate(
        (("start", "weiter"), ("pruefen", "freigegeben")), start=1
    ):
        attempt = run / "arbeitsschritte" / slug / "001"
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


def _codes(root: Path) -> set[str]:
    return {issue.code for issue in validate(root).issues}


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

        assert "revision.invalid" in _codes(root)


def test_laufpfad_must_start_at_application_entry():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        metadata = read_context(run / "CONTEXT.md")
        metadata["laufpfad"] = metadata["laufpfad"][1:]
        replace_context(run / "CONTEXT.md", metadata)

        assert "run.invalid" in _codes(root)


def test_malformed_laufpfad_entry_fails_closed_without_exception():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        metadata = read_context(run / "CONTEXT.md")
        metadata["laufpfad"] = ["invalid"]
        replace_context(run / "CONTEXT.md", metadata)

        codes = _codes(root)

        assert "schema.invalid" in codes
        assert "run.invalid" in codes


def test_malformed_selected_route_fails_closed_without_exception():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        metadata = read_context(run / "CONTEXT.md")
        metadata["laufpfad"][0]["gewaehlte_route"] = ["weiter"]
        replace_context(run / "CONTEXT.md", metadata)

        codes = _codes(root)

        assert "schema.invalid" in codes
        assert "run.invalid" in codes


def test_changed_input_bytes_break_hash_binding():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        (run / "arbeitsschritte/start/001/input/auftrag.md").write_text(
            "verändert", encoding="utf-8"
        )

        assert "hash.mismatch" in _codes(root)


def test_changed_output_bytes_break_hash_binding():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        (run / "arbeitsschritte/pruefen/001/output/ergebnis.md").write_text(
            "verändert", encoding="utf-8"
        )

        assert "hash.mismatch" in _codes(root)


def test_human_gate_rejects_agent_approval():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        metadata = read_context(run / "CONTEXT.md")
        metadata["laufpfad"][1]["freigabe"]["by"] = "agent:codex"
        replace_context(run / "CONTEXT.md", metadata)

        assert "trust.invalid" in _codes(root)


def test_missing_attempt_directory_is_rejected():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        attempt = run / "arbeitsschritte/start/001"
        for path in sorted(attempt.rglob("*"), reverse=True):
            path.unlink() if path.is_file() else path.rmdir()
        attempt.rmdir()

        assert "run.invalid" in _codes(root)


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

        assert "run.invalid" in _codes(root)


def test_completed_entry_must_not_carry_reentry_contract():
    with TemporaryDirectory() as directory:
        root, run = _prepare_workspace(Path(directory))
        metadata = read_context(run / "CONTEXT.md")
        metadata["laufpfad"][0]["wiedereinstieg"] = {
            "ausloeser": "Termin",
            "continuation_ref": "calendar:1",
        }
        replace_context(run / "CONTEXT.md", metadata)

        assert "run.invalid" in _codes(root)


def test_hash_surface_rejects_a_directory_symlink():
    with TemporaryDirectory() as directory:
        base = Path(directory)
        root, run = _prepare_workspace(base)
        application = root / "applications/video"
        for slug in ("start", "pruefen"):
            path = application / f"hauptprozess/teilprozesse/produktion/arbeitsschritte/{slug}/CONTEXT.md"
            metadata = read_context(path)
            metadata["eingaben"] = ["input"]
            metadata["ausgaben"] = ["output"]
            replace_context(path, metadata)
        _git(root, "add", "applications/video")
        _git(root, "commit", "-m", "directory surfaces")

        metadata = read_context(run / "CONTEXT.md")
        metadata["application_revision"] = "git-tree:" + _git(
            root, "rev-parse", "HEAD:applications/video"
        )
        for entry in metadata["laufpfad"]:
            slug = entry["arbeitsschritt_ref"].removeprefix("arbeitsschritt:")
            attempt = run / "arbeitsschritte" / slug / "001"
            entry["eingabe_hash"] = surface_hash(attempt, ["input"])
            entry["ausgabe_hash"] = surface_hash(attempt, ["output"])
        replace_context(run / "CONTEXT.md", metadata)

        external = base / "external"
        external.mkdir()
        (external / "secret.txt").write_text("outside", encoding="utf-8")
        input_root = run / "arbeitsschritte/start/001/input"
        (input_root / "auftrag.md").unlink()
        input_root.rmdir()
        input_root.symlink_to(external, target_is_directory=True)

        assert "structure.symlink" in _codes(root)
