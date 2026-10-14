"""The single writer: page models in, one new folder of self-contained HTML pages out.

The writer only creates and never deletes. It refuses an existing output and works through
a handle of the parent folder it checked, so swapping that path redirects nothing.
The output is complete only when the command exits successfully; after a failure, the
new folder is incomplete and is left for you to remove. To regenerate, choose a new folder.

Trust boundary: the output's parent and the source's ancestors must not be moved or
replaced by another process while the view is generated. A process with your rights can
still substitute the new folder or move its parent into the source; no path check can
exclude that.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from pathlib import Path

TEMPLATE = Path(__file__).with_name("page.html")
NAME = re.compile(r"(index|[aiv]-[a-z0-9-]+)\.html|model\.json")


def embed(model: dict) -> str:
    """JSON that cannot leave its script element."""
    text = json.dumps(model, ensure_ascii=False, separators=(",", ":"), default=str)
    for char, escape in (("&", "\\u0026"), ("<", "\\u003c"), (">", "\\u003e"),
                         (" ", "\\u2028"), (" ", "\\u2029")):
        text = text.replace(char, escape)
    return text


def exactly_one(template: str, pattern: str, what: str) -> re.Match:
    found = list(re.finditer(pattern, template, re.S))
    if len(found) != 1:
        raise RuntimeError(f"template needs exactly one {what}")
    return found[0]


def page_html(model: dict) -> str:
    template = TEMPLATE.read_text(encoding="utf-8")
    script = exactly_one(template, r"<script>(.*?)</script>", "plain <script> element").group(1)
    style = exactly_one(template, r"<style>(.*?)</style>", "<style> element").group(1)
    exactly_one(template, r'http-equiv="Content-Security-Policy" content="__POLICY__"', "CSP marker")
    exactly_one(template, "__POLICY__", "__POLICY__ marker")
    exactly_one(template, "__MODEL__", "__MODEL__ marker")
    sha = lambda text: base64.b64encode(hashlib.sha256(text.encode()).digest()).decode()
    policy = f"default-src 'none'; script-src 'sha256-{sha(script)}'; style-src 'sha256-{sha(style)}'; img-src data:"
    head, _, tail = template.replace("__POLICY__", policy).partition("__MODEL__")
    return head + embed(model) + tail


def outside(real: Path, source: Path) -> bool:
    # Existing ancestors are compared by filesystem identity, including case aliases.
    source_stat = os.stat(source)
    source_id = source_stat.st_dev, source_stat.st_ino
    for ancestor in (real, *real.parents):
        if ancestor.exists():
            st = os.stat(ancestor)
            if (st.st_dev, st.st_ino) == source_id:
                return False
    return real not in source.parents


def write_site(out: Path, source: Path, pages: dict[str, dict], export: bool) -> None:
    source = Path(os.path.realpath(source))
    out = Path(os.path.abspath(out))
    files = {name: page_html(model).encode() for name, model in pages.items()}
    if export:
        files["model.json"] = (json.dumps(pages, ensure_ascii=False, indent=1, default=str) + "\n").encode()
    if not all(NAME.fullmatch(name) for name in files) or "index.html" not in files:
        raise RuntimeError(f"unexpected page names {sorted(files)}")
    try:
        parent = os.open(out.parent, os.O_RDONLY | os.O_DIRECTORY)
    except OSError as error:
        raise SystemExit(f"cannot open output parent {out.parent}: {error}") from error
    try:
        # Check the folder the handle actually holds; a later swap of the path no longer matters.
        real = Path(os.path.realpath(out.parent))
        held, seen = os.fstat(parent), os.stat(real)
        if (held.st_dev, held.st_ino) != (seen.st_dev, seen.st_ino) or not outside(real / out.name, source):
            raise SystemExit(f"refusing to write {out}: it overlaps the selected source {source} or moved")
        try:
            os.mkdir(out.name, 0o755, dir_fd=parent)
        except FileExistsError:
            raise SystemExit(f"refusing to write {out}: it exists; choose a new folder or remove it yourself")
        folder = os.open(out.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            for name in sorted(files, key=lambda n: n == "index.html"):
                handle = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644, dir_fd=folder)
                with os.fdopen(handle, "wb") as stream:
                    stream.write(files[name])
        finally:
            os.close(folder)
    finally:
        os.close(parent)
