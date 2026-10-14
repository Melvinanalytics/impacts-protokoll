"""The only Markdown reader of the view. Pure text in, plain data out.

Every shape it does not support stays verbatim; nothing is dropped or reordered.
"""
from __future__ import annotations

import re

FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")
SECTION = re.compile(r"## +(\S.*?)\s*$")
TITLE = re.compile(r"# +(\S.*?)\s*$")
SUB = re.compile(r"#{3,6} +(\S.*?)\s*$")
ITEM = re.compile(r"([ \t]*)([-*+]|\d+[.)])[ \t]+")
INLINE = re.compile(r"\*\*([^*]+)\*\*|\[([^\]]+)\]\(([^)\s]+)\)", re.S)
INDENTED = ("    ", "\t")


def closes(line: str, fence: str) -> bool:
    """A closing fence repeats the opening character at least as often; only spaces or tabs follow."""
    marker = FENCE.match(line)
    return bool(marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence)
                and not line[marker.end():].strip(" \t"))


def sections(body: str, first_line: int) -> tuple[str | None, list[dict]]:
    """Split a body at level-2 headings outside code fences; keep every line and its file line."""
    title, _, parts = document(body, first_line)
    return title, parts


def document(body: str, first_line: int) -> tuple[str | None, int | None, list[dict]]:
    """The same section reader, including the source line of the title."""
    title, title_line, fence = None, None, None
    found = [{"heading": None, "line": first_line, "lines": [], "numbers": []}]
    for number, line in enumerate(body.split("\n"), start=first_line):
        if fence:
            if closes(line, fence):
                fence = None
        elif marker := FENCE.match(line):
            fence = marker.group(1)
        elif heading := SECTION.fullmatch(line):
            found.append({"heading": heading.group(1), "line": number, "lines": [], "numbers": []})
            continue
        elif title is None and len(found) == 1 and (top := TITLE.fullmatch(line)):
            title, title_line = top.group(1), number
            continue
        found[-1]["lines"].append(line)
        found[-1]["numbers"].append(number)
    result = []
    for part in found:
        lines, numbers = part["lines"], part["numbers"]
        start = next((i for i, line in enumerate(lines) if line), len(lines))  # strip("\n") drops only empty lines
        text = "\n".join(lines).strip("\n")
        if part["heading"] is not None or text.strip():
            result.append({"heading": part["heading"], "line": part["line"], "text": text,
                           "blocks": blocks(text, numbers[start:] or [part["line"]])})
    return title, title_line, result


def spans(text: str) -> list[list[str]]:
    """Inline text as [kind, text, title]; every character outside markup survives."""
    runs = list(re.finditer(r"`+", text))
    closing, seen = {}, {}
    for i in range(len(runs) - 1, -1, -1):
        length = len(runs[i][0])
        closing[i] = seen.get(length)
        seen[length] = i
    markup = list(INLINE.finditer(text))
    out, last, code_at, other_at = [], 0, 0, 0
    while code_at < len(runs) or other_at < len(markup):
        if code_at < len(runs) and (other_at == len(markup) or runs[code_at].start() < markup[other_at].start()):
            opening = runs[code_at]
            end = closing[code_at]
            code_at += 1
            if opening.start() < last or end is None:
                continue
            close = runs[end]
            start, stop = opening.start(), close.end()
            item = ["code", text[opening.end():close.start()], ""]
        else:
            match = markup[other_at]
            other_at += 1
            if match.start() < last:
                continue
            start, stop = match.span()
            item = ["b", match[1], ""] if match[1] else ["link", match[2], match[3]]
        if start > last:
            out.append(["t", text[last:start], ""])
        out.append(item)
        last = stop
    if last < len(text):
        out.append(["t", text[last:], ""])
    return out


def table(rows: list[str]) -> dict | None:
    """A table only when every row splits cleanly into the same width."""
    parsed = []
    for row in rows:
        inner = row.strip()
        if not (inner.startswith("|") and inner.endswith("|")) or "\\" in inner:
            return None
        parsed.append([cell.strip() for cell in inner[1:-1].split("|")])
    if len({len(r) for r in parsed}) != 1:
        return None
    rule = len(parsed) > 1 and all(re.fullmatch(r":?-{3,}:?", c) for c in parsed[1])
    head, body = (parsed[0], parsed[2:]) if rule else (None, parsed)
    return {"type": "table", "head": [spans(c) for c in head] if head else None,
            "rows": [[spans(c) for c in r] for r in body]}


def items(lines: list[str]) -> dict | None:
    """A list keeps each marker and its nesting rank; a lost parent or deep nesting stays verbatim."""
    found = []
    for line in lines:
        if match := ITEM.match(line):
            found.append([match.group(1).expandtabs(4), match.group(2), line[match.end():]])
        elif found:
            if len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip()) >= 4:
                return None  # an indented block inside a list is code-like: keep the whole list verbatim
            found[-1][2] += "\n" + line.strip()
    ranks = sorted({len(indent) for indent, _, _ in found})
    if ranks[0] > 0 or len(ranks) > 4:
        return None
    return {"type": "list", "items": [{"depth": ranks.index(len(indent)), "marker": marker, "spans": spans(text)}
                                      for indent, marker, text in found]}


def _starts_block(line: str) -> bool:
    return bool(FENCE.match(line) or line.lstrip().startswith("|") or ITEM.match(line)
                or SUB.fullmatch(line) or line.startswith(INDENTED))


def _comment_end(lines: list[str], i: int) -> int | None:
    """An HTML comment that fills whole lines: the index of its closing line, else None."""
    if not lines[i].lstrip().startswith("<!--"):
        return None
    for j in range(i, len(lines)):
        if "-->" in lines[j]:
            close = lines[j].index("-->", lines[j].index("<!--") + 4 if j == i else 0)
            return j if not lines[j][close + 3:].strip() else None
    return None


def blocks(text: str, first_line: int | list[int] = 1) -> list[dict]:
    """Code, table, list, subheading, whole-line HTML comment and paragraph blocks; any other shape as verbatim text.
    Each block carries `line`, the file line of its first text line (`first_line` is the line of
    the text's first line, or the file line of every text line). Body row k of a table with a
    header sits at line + 2 + k."""
    out, lines, i = [], text.split("\n"), 0
    at = (lambda k: first_line + k) if isinstance(first_line, int) else (lambda k: first_line[min(k, len(first_line) - 1)])
    verbatim = lambda start, end: {"type": "text", "text": "\n".join(lines[start:end])}
    while i < len(lines):
        line, start = lines[i], i
        if not line.strip():
            i += 1
            continue
        if marker := FENCE.match(line):
            i += 1
            while i < len(lines) and not closes(lines[i], marker.group(1)):
                i += 1
            found = {"type": "code", "text": "\n".join(lines[start:i + 1])}
            i += 1
        elif line.startswith(INDENTED):
            while i < len(lines) and (lines[i].startswith(INDENTED) or not lines[i].strip()):
                i += 1
            end = i
            while end > start and not lines[end - 1].strip():
                end -= 1
            found = verbatim(start, end)
        elif line.lstrip().startswith("|"):
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                i += 1
            found = table(lines[start:i]) or verbatim(start, i)
        elif ITEM.match(line):
            while i < len(lines) and lines[i].strip() and not FENCE.match(lines[i]) \
                    and not lines[i].lstrip().startswith("|") and not SUB.fullmatch(lines[i]):
                i += 1
            found = items(lines[start:i]) or verbatim(start, i)
        elif (end := _comment_end(lines, i)) is not None:
            i = end + 1
            found = {"type": "comment", "text": "\n".join(lines[start:i])}
        elif heading := SUB.fullmatch(line):
            found = {"type": "heading", "spans": spans(heading.group(1))}
            i += 1
        elif line.strip():
            while i < len(lines) and lines[i].strip() and not _starts_block(lines[i]):
                i += 1
            found = {"type": "para", "spans": spans(" ".join(l.strip() for l in lines[start:i]))}
        else:
            i += 1
            continue
        out.append({**found, "line": at(start)})
    return out
