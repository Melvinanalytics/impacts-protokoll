"""Owner C audit support: builders for lifecycle/binding/authorization tests.

Fixtures derive from tests.support.write_application (video: start -> pruefen,
pruefen is a human gate with freigegeben/abgelehnt routes). The consuming tests
name their protocol sources; this module supplies synthetic builders and a fixed
hash vector.
"""

from pathlib import Path

from impacts_protocol import surface_hash, validate
from tests.support import codes as codes
from tests.support import git, read_context, replace_context, write_application, write_context


FROZEN_SURFACE_HASH = (
    "sha256:5cfbcff1a57fb9bc011fd69209052640ae01464aa5213acca911fc51c4a55c7e"
)


def committed_workspace(base: Path, name: str = "kunde") -> tuple[Path, str]:
    """A workspace with the video application committed; returns (root, app tree oid)."""
    root = base / name
    from impacts_protocol import init_workspace

    init_workspace(root)
    write_application(root / "applications" / "video")
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "audit-c@example.invalid")
    git(root, "config", "user.name", "Audit C")
    git(root, "add", ".")
    git(root, "commit", "-m", "application v1")
    revision = git(root, "rev-parse", "HEAD:applications/video")
    return root, revision


def make_attempt(
    run: Path,
    slug: str,
    versuch: int,
    *,
    input_bytes: str | None = None,
    output_bytes: str | None = None,
) -> Path:
    attempt = run / slug / f"{versuch:03d}"
    (attempt / "input").mkdir(parents=True, exist_ok=True)
    if input_bytes is not None:
        (attempt / "input" / "auftrag.md").write_text(input_bytes, encoding="utf-8")
    if output_bytes is not None:
        (attempt / "output").mkdir(exist_ok=True)
        (attempt / "output" / "ergebnis.md").write_text(output_bytes, encoding="utf-8")
    return attempt


def entry_active(slug: str, versuch: int, attempt: Path) -> dict:
    return {
        "arbeitsschritt_ref": f"arbeitsschritt:{slug}",
        "versuch": versuch,
        "status": "aktiv",
        "eingabe_hash": surface_hash(attempt, ["input/auftrag.md"]),
    }


def entry_waiting(slug: str, versuch: int, attempt: Path) -> dict:
    entry = entry_active(slug, versuch, attempt)
    entry["status"] = "wartend"
    entry["wiedereinstieg"] = {
        "ausloeser": "synthetisches Ereignis",
        "continuation_ref": "records/antwort.md",
    }
    return entry


def entry_completed(
    slug: str,
    versuch: int,
    attempt: Path,
    route: str,
    *,
    freigabe: dict | None = None,
) -> dict:
    entry = entry_active(slug, versuch, attempt)
    entry["status"] = "abgeschlossen"
    entry["gewaehlte_route"] = route
    entry["ausgabe_hash"] = surface_hash(attempt, ["output/ergebnis.md"])
    if freigabe is not None:
        entry["freigabe"] = freigabe
    return entry


HUMAN = {"by": "human:prueferin", "at": "2026-08-30T10:00:00+02:00"}


def write_run(root: Path, name: str, revision: str, entries: list[dict]) -> Path:
    run = root / "vorgaenge" / name
    write_context(
        run / "CONTEXT.md",
        {
            "type": "vorgang",
            "id": f"vorgang:{name}",
            "application_revision": f"git-tree:{revision}",
            "laufpfad": entries,
        },
        f"# {name}",
    )
    return run


def issues_for(root: Path, prefix: str):
    return [
        issue for issue in validate(root).issues if issue.path.startswith(prefix)
    ]


def rewrite_run(root: Path, run: Path, entries: list[dict]) -> None:
    metadata = read_context(run / "CONTEXT.md")
    metadata["laufpfad"] = entries
    replace_context(run / "CONTEXT.md", metadata)
