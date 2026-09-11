from pathlib import Path

import yaml


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


def write_application(root: Path) -> Path:
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
    text = path.read_text(encoding="utf-8").splitlines()
    end = text[1:].index("---") + 1
    return yaml.safe_load("\n".join(text[1:end]))


def replace_context(path: Path, metadata: dict) -> None:
    write_context(path, metadata, "## Bearbeitung\n\nErzeuge das deklarierte Ergebnis.")
