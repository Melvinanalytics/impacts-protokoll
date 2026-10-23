"""A read-only view of IMPACTS files: `impacts view <source> --out <folder> [--json]`.

<source> is an Application folder, a workspace folder or vorgaenge/<slug>/CONTEXT.md.
The folder receives index.html; for a workspace also one page per Application, per
Vorgang and per Ist-Prozess file (a-, v- and i- pages). The folder must not exist.
Completed generation returns 0, or 1 when some selections were refused and shown as such.
Operational failure can also return 1, leaving no output or an incomplete folder.
The view shows; it decides, schedules and changes nothing. Generate it
again into a new folder after the files change.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from ..io import load_frontmatter
from ..generator import LANGUAGES
from . import selection
from .blocks import FENCE, closes
from .write import write_site

SETTING = re.compile(r"^Working language: (\S+)\s*$", re.M)
__all__ = ["site_model"]


def working_language(source: Path) -> str | None:
    """The setting recorded in the nearest workspace CONTEXT.md, as the language contract binds it."""
    for folder in (source if source.is_dir() else source.parent, *source.parents):
        context = folder / "CONTEXT.md"
        try:
            if not context.is_file():
                continue
            if load_frontmatter(context).get("type") != "workspace":
                continue
            fence, found = None, None
            for line in context.read_text(encoding="utf-8").splitlines():
                if fence:
                    if closes(line, fence):
                        fence = None
                elif marker := FENCE.match(line):
                    fence = marker.group(1)
                elif found := SETTING.fullmatch(line):
                    break
        except (OSError, ValueError):
            continue
        return found.group(1) if found else None
    return None


def choose_language(source: Path, requested: str | None) -> str:
    recorded = working_language(source)
    if recorded is not None and recorded not in LANGUAGES:
        raise SystemExit(f"unsupported working language in the workspace: {recorded}")
    if recorded and requested and recorded != requested:
        raise SystemExit(f"the workspace records working language {recorded}; --language {requested} cannot override it")
    return recorded or requested or "de"


def site_model(workspace: Path) -> dict[str, dict]:
    """The pages `impacts view <workspace> --json` writes as model.json, without the display language.

    Stable like that export: each page's `format` names the version. Core validates the workspace once
    and reads bound trees through Git, as `impacts validate` does; a refused selection is a page with
    its issues and stops no other. A path that is not a Git-root workspace raises ValueError."""
    try:
        return selection.workspace_site(Path(workspace))
    except SystemExit as error:
        raise ValueError(str(error)) from None


def run(source: Path, out: Path, *, write_json: bool = False, language: str | None = None) -> int:
    source = source.resolve()
    chosen = choose_language(source, language)
    kind = selection.kind_of(source)
    if kind == "workspace":
        pages, protected = selection.workspace_site(source), source
    elif kind == "application":
        pages = {"index.html": selection.application_page(source)}
        protected = source
        for parent in source.parents:
            context = parent / "CONTEXT.md"
            try:
                if context.is_file() and load_frontmatter(context).get("type") == "workspace":
                    protected = parent
                    break
            except (OSError, ValueError):
                continue
    else:
        pages = {"index.html": selection.single_vorgang(source)}
        protected = selection.workspace_of(source.parent) or source.parent
    pages = {name: {**model, "language": chosen} for name, model in pages.items()}
    write_site(out, protected, pages, write_json)
    problems = [(name, issue) for name, model in pages.items() for issue in model["issues"]]
    for name, issue in problems:
        print(f"{name}: {issue['path']}: {issue['code']}: {issue['message']}", file=sys.stderr)
    return 1 if problems else 0
