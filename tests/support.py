from pathlib import Path
import subprocess

import yaml

from impacts_protocol import init_workspace, file_references as raw_references, validate
from impacts_protocol.io import load_frontmatter, load_frontmatter_and_body


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True
    ).strip()


def codes(root: Path) -> set[str]:
    return {issue.code for issue in validate(root).issues}


def write_context(path: Path, metadata: dict, body: str = "Arbeitskontext") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).rstrip()
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}\n", encoding="utf-8")


def write_workstep(
    root: Path,
    slug: str,
    *,
    step_id: str | None = None,
    routes: dict[str, str] | None = None,
    gate: str | None = None,
) -> Path:
    path = root / slug / "CONTEXT.md"
    metadata = {
        "type": "arbeitsschritt",
        "id": step_id or f"arbeitsschritt:{slug}",
        "eingaben": ["input/auftrag.md"],
        "ausgaben": ["output/ergebnis.md"],
        "pruefung": "Ergebnis ist vollständig",
        "routen": routes or {"fertig": "end:fertig"},
    }
    if gate is not None:
        metadata["gate"] = gate
    write_context(path, metadata, "## Bearbeitung\n\nErzeuge das deklarierte Ergebnis.")
    return path


def write_hauptprozess(root: Path) -> Path:
    write_context(
        root / "CONTEXT.md",
        {
            "type": "hauptprozess",
            "id": "hauptprozess:video",
            "leistung": {
                "ergebnis": "Veröffentlichtes Video",
                "kennzahl": "Durchlaufzeit",
                "abnahme": ["Video veröffentlicht"],
            },
            "einstieg_ref": "arbeitsschritt:start",
        },
        "# Video-Produktion",
    )
    part = root / "produktion"
    write_context(
        part / "CONTEXT.md",
        {
            "type": "teilprozess",
            "id": "teilprozess:produktion",
            "ergebnis": "Produziertes Video",
        },
        "# Produktion",
    )
    write_workstep(
        part,
        "start",
        routes={"weiter": "arbeitsschritt:pruefen"},
    )
    write_workstep(
        part,
        "pruefen",
        routes={
            "freigegeben": "end:video-veroeffentlicht",
            "abgelehnt": "arbeitsschritt:start",
        },
        gate="human",
    )
    return root


def read_context(path: Path) -> dict:
    return load_frontmatter(path)


def replace_context(path: Path, metadata: dict) -> None:
    if metadata.get("type") == "workspace":
        _, body = load_frontmatter_and_body(path)
        write_context(path, metadata, body)
        return
    if metadata.get("type") == "vorgang":
        for entry in metadata.get("laufpfad", []):
            if isinstance(entry, dict):
                for reference in entry.get("geschrieben", []) if isinstance(entry.get("geschrieben"), list) else []:
                    if isinstance(reference, dict) and "pfad" in reference:
                        parts = reference["pfad"].split("/")
                        if len(parts) > 2 and parts[0] == "vorgaenge":
                            parts[1] = path.parent.name
                            reference["pfad"] = "/".join(parts)
    write_context(path, metadata, "## Bearbeitung\n\nErzeuge das deklarierte Ergebnis.")


# Committed-Vorgang builders: the video Hauptprozess from write_hauptprozess,
# committed once; attempts and laufpfad entries are synthetic.

HUMAN = {"by": "human:prueferin", "at": "2026-08-30T10:00:00+02:00"}


def committed_workspace(base: Path, name: str = "kunde") -> tuple[Path, str]:
    """A workspace with the video Hauptprozess committed; returns (root, app tree oid)."""
    root = base / name
    init_workspace(root)
    router = root / "CONTEXT.md"
    router.write_text(router.read_text() + "\nAblage: synthetic-store Synthetic inaccessible store\nAblage: unavailable-synthetic-store Synthetic inaccessible store\n")
    write_hauptprozess(root / "hauptprozesse" / "video")
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    git(root, "add", ".")
    git(root, "commit", "-m", "hauptprozess v1")
    return root, git(root, "rev-parse", "HEAD:hauptprozesse/video")


def make_attempt(
    vorgang: Path,
    slug: str,
    versuch: int,
    *,
    input_bytes: str | None = None,
    output_bytes: str | None = None,
) -> Path:
    attempt = vorgang / slug / f"{versuch:03d}"
    (attempt / "output").mkdir(parents=True, exist_ok=True)
    (fixture_path(attempt, "input")).mkdir(parents=True, exist_ok=True)
    if input_bytes is not None:
        (fixture_path(attempt, "input") / "auftrag.md").write_text(input_bytes, encoding="utf-8")
    if output_bytes is not None:
        (attempt / "output").mkdir(parents=True, exist_ok=True)
        (attempt / "output" / "ergebnis.md").write_text(output_bytes, encoding="utf-8")
    return attempt


def entry_active(slug: str, versuch: int, attempt: Path) -> dict:
    return {
        "arbeitsschritt_ref": f"arbeitsschritt:{slug}",
        "nummer": versuch,
        "status": "aktiv",
        "gelesen": fixture_references(attempt, ["input/auftrag.md"]),
    }


def entry_waiting(slug: str, versuch: int, attempt: Path) -> dict:
    entry = entry_active(slug, versuch, attempt)
    entry["status"] = "wartend"
    request = attempt / "output/warten.md"
    request.write_text("Synthetic request recorded as sent; awaiting response.\n", encoding="utf-8")
    entry["wiedereinstieg"] = {
        "ausloeser": "synthetisches Ereignis",
        "continuation_ref": request.relative_to(attempt.parents[3]).as_posix(),
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
    entry["geschrieben"] = fixture_references(attempt, ["output/"])
    if freigabe is not None:
        entry["freigabe"] = freigabe
    return entry


def write_vorgang(root: Path, name: str, revision: str, entries: list[dict]) -> Path:
    vorgang = root / "vorgaenge" / name
    write_context(
        vorgang / "CONTEXT.md",
        {
            "type": "vorgang", "protocol": "v0.5.0",
            "id": f"vorgang:{name}",
            "hauptprozess_revision": f"git-tree:{revision}",
            "laufpfad": entries,
        },
        f"# {name}",
    )
    return vorgang


def rewrite_vorgang(vorgang: Path, entries: list[dict]) -> None:
    metadata = read_context(vorgang / "CONTEXT.md")
    metadata["laufpfad"] = entries
    replace_context(vorgang / "CONTEXT.md", metadata)


def issues_for(root: Path, prefix: str):
    return [issue for issue in validate(root).issues if issue.path.startswith(prefix)]


def source_home(attempt: Path) -> Path:
    workspace = attempt.parents[3]
    (workspace / "records").mkdir(exist_ok=True)
    router = workspace / "CONTEXT.md"
    declaration = "Form: records/ Record Library per source record"
    if declaration not in router.read_text():
        with router.open("a") as handle:
            handle.write("\n" + declaration + "\n")
    return workspace / "records" / attempt.parents[1].name / attempt.parent.name / attempt.name


def fixture_path(base: Path, relative: str) -> Path:
    """Resolve synthetic input declarations to their record home."""
    joined = base / relative
    parts = joined.parts
    if "vorgaenge" in parts and "input" in parts:
        index = parts.index("input")
        attempt = Path(*parts[:index])
        return source_home(attempt).joinpath(*parts[index + 1:])
    return joined


def fixture_references(root: Path, declared: list[str]) -> list[dict]:
    """Commit synthetic record sources; emit actual Core file references."""
    if "vorgaenge" not in root.parts or not root.name.isdigit():
        return raw_references(root, declared)
    workspace = root.parents[3]
    references = []
    for item in declared:
        path = fixture_path(root, item)
        relative = path.relative_to(workspace).as_posix()
        records = raw_references(workspace, [relative])
        if item == "input" or item.startswith("input/"):
            git(workspace, "add", "--", relative)
            changed = subprocess.run(["git", "-C", str(workspace), "diff", "--cached", "--quiet", "HEAD", "--", relative]).returncode
            if changed:
                git(workspace, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--only", "-m", "Capture synthetic source", "--", relative)
            revision = "git-commit:" + git(workspace, "log", "-1", "--format=%H", "--", relative)
            for record in records:
                record["revision"] = revision
                record["eingabe"] = item
        references.extend(records)
    return references
