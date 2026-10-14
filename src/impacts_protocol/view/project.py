"""Pure projections from read nodes to what the page draws: run state, map tree, overview,
and the Notwendigkeit table of an Ist-Prozess.

These are derived views. They show the laufpfad's execution state, never a business state,
and they decide or change nothing. Every value comes from the files; a missing value stays
missing, and the page says so.
"""
from __future__ import annotations

import re

# One phase vocabulary; page.html holds the words (PHASE). Position is not progress: a waiting
# step keeps its own quiet phase, never the green of the current position.
ENTRY_PHASE = {"abgeschlossen": "done", "aktiv": "current", "wartend": "waiting"}

# Subtitles quoted verbatim from the protocol templates; a heading without a template sentence gets none.
SUBTITLE = {
    "arbeitsschritt": {
        "ein job": "Ein Satz: Ergebnis dieses Jobs, Empfänger und erlaubte Nutzung.",
        "one job": "One sentence: the result this job produces, its recipient and permitted use.",
        "nicht laden": "Was dieser Arbeitsschritt bewusst nicht liest",
        "excluded context": "Name material outside this job's required context.",
        "befugnis": "Wer darf in diesem Job was entscheiden, einsehen oder bewirken, und wer muss selbst handeln?",
        "authority": "Who may decide, access or cause what in this job, and who must act in person?",
        "ablauf": "Was löst diesen Job aus, wohin führt jedes Ergebnis, und was geschieht beim Warten?",
        "flow": "What starts this job, where each outcome leads and what happens while it waits.",
    },
    "vorgang": {
        "betreff": "Wer oder was Gegenstand dieses Vorgangs ist.",
        "subject": "Who or what this run concerns.",
    },
}
JOB, AUTHORITY, FLOW = {"ein job", "one job"}, {"human check", "menschliche prüfung", "befugnis", "authority"}, {"ablauf", "flow"}
PROCESSING = {"verarbeitung", "processing"}
# The four contribution kinds of zuschnitt.md "Automation boundary", in both template languages; not exclusive per step.
EXECUTION = {"deterministisches system": "deterministic", "deterministic system": "deterministic",
             "klassifikator": "classifier", "classifier": "classifier", "agent": "agent", "mensch": "human", "human": "human"}

# Display sections reuse template meanings; unknown headings stay verbatim and unnumbered.
SHEET = {"ein job": "job", "one job": "job", "eingaben": "inputs", "inputs": "inputs",
         "nicht laden": "excluded", "excluded context": "excluded", "verarbeitung": "processing",
         "processing": "processing", "handgriffe": "handgrips", "handgrips": "handgrips",
         "ausgaben und wirkungen": "outputs", "outputs and effects": "outputs", "ausgaben": "outputs",
         "outputs": "outputs", "prüfung": "check", "check": "check", "befugnis": "authority",
         "authority": "authority", "human check": "authority", "menschliche prüfung": "authority",
         "ablauf": "flow", "flow": "flow"}


def sheet_parts(node: dict) -> list[dict]:
    """Split only explicitly named Handgriffe subsections; retain all source blocks and lines."""
    parts = []
    for part in node["sections"]:
        current = {**part, "area": SHEET.get(heading_key(part)), "blocks": []}
        parts.append(current)
        for block in part["blocks"]:
            if current["area"] in ("processing", "handgrips") and block["type"] == "heading":
                heading = plain(block["spans"])
                area = SHEET.get(heading.casefold())
                if area == "handgrips" or current["area"] == "handgrips":
                    current = {**part, "area": "handgrips" if area == "handgrips" else "processing",
                               "heading": part["heading"] + " › " + heading, "line": block["line"], "blocks": []}
                    parts.append(current)
                    if area == "handgrips":
                        continue
            current["blocks"].append(block)
    return parts


def first_sentence(spans: list | None) -> list | None:
    """Quote through the first sentence boundary, preserving inline markup and source labels."""
    if not spans:
        return None
    text = plain(spans)
    boundary = re.search(r"[.!?](?:\s|$)", text)
    remaining, found = boundary.end() if boundary else len(text), []
    for kind, value, target in spans:
        if remaining <= 0:
            break
        found.append([kind, value[:remaining], target])
        remaining -= len(value)
    return found


def step_owners(node: dict) -> list[dict]:
    """Only explicit owner/role labels, never a performer inferred from processing prose."""
    found = []
    names = {"owner", "role", "responsible", "verantwortlich", "rolle"}
    for part in node["sections"]:
        for block in part["blocks"]:
            entries = ([{"spans": block["spans"], "depth": 0}] if block["type"] == "para" else
                       block["items"] if block["type"] == "list" else [])
            line = block["line"]
            for entry in entries:
                text = plain(entry["spans"])
                label, colon, value = text.partition(":")
                if entry["depth"] == 0 and colon and label.strip().casefold() in names and value.strip():
                    offset, value_spans = text.index(":") + 1, []
                    for kind, content, target in entry["spans"]:
                        if offset >= len(content):
                            offset -= len(content)
                            continue
                        value_spans.append([kind, content[offset:].lstrip() if not value_spans else content[offset:], target])
                        offset = 0
                    found.append({"spans": value_spans, "line": line, "heading": part["heading"]})
                line += 1 + text.count("\n")
    return found


def short(ref: str) -> str:
    return str(ref).split(":", 1)[-1]


def title_of(node: dict) -> str:
    return node.get("title") or short(node["id"])


def heading_key(part: dict) -> str:
    return (part["heading"] or "").strip().lower()


def step_refs(node: dict) -> dict:
    """Where an Arbeitsschritt says what it does, who decides and where its routes are explained; the first
    paragraph of the job and authority sections is quoted, never paraphrased."""
    def first(names) -> dict | None:
        return next((p for p in node["sections"] if heading_key(p) in names), None)

    def para(part: dict | None) -> list | None:
        return next((b["spans"] for b in part["blocks"] if b["type"] == "para"), None) if part else None

    authority = first(AUTHORITY)
    place = lambda part: {"heading": part["heading"], "line": part["line"]} if part else None
    return {"job": para(first(JOB)), "authority": authority and {**place(authority), "spans": para(authority)},
            "flow": place(first(FLOW)),
            "execution": [entry for part in node["sections"] if heading_key(part) in PROCESSING
                          for entry in execution(part)]}


def execution(part: dict | None) -> list[dict]:
    """Each top-level list item of the processing section that starts with one of the four execution
    kinds of the Automation boundary. Other wording remains source text; this projection does not classify it."""
    found = []
    for block in part["blocks"] if part else []:
        if block["type"] != "list":
            continue
        line = block["line"]
        for item in block["items"]:
            text = plain(item["spans"])
            head, colon, _ = text.partition(":")
            kind = EXECUTION.get(head.strip().casefold()) if colon and item["depth"] == 0 else None
            if kind:
                found.append({"kind": kind, "spans": item["spans"], "line": line,
                              "heading": part.get("heading"), "heading_line": part.get("line")})
            line += 1 + text.count("\n")
    return found


def annotate(nodes: list[dict]) -> None:
    """Add template subtitles and, for each Arbeitsschritt, its own references and its routes as
    [route, target, target title, direction]. Idempotent."""
    by_id = {n["id"]: n for n in nodes}
    order = [n["id"] for n in nodes if n["kind"] == "arbeitsschritt"]
    for node in nodes:
        known = SUBTITLE.get(node["kind"], {})
        for part in node["sections"]:
            part["subtitle"] = known.get(heading_key(part))
        if node["kind"] == "arbeitsschritt":
            node.update(step_refs(node), routes=route_rows(by_id, order, node["id"]))
            node.update(sheet_parts=sheet_parts(node), job_summary=first_sentence(node["job"]), owners=step_owners(node))


def phases(nodes: list[dict], entries: list[dict]) -> dict:
    """Display state from the laufpfad: the latest entry per step wins. Core forbids an empty laufpfad."""
    steps = {n["id"]: n for n in nodes if n["kind"] == "arbeitsschritt"}
    phase = {entry["arbeitsschritt_ref"]: ENTRY_PHASE[entry["status"]] for entry in entries}
    last = entries[-1]
    current, ended = last["arbeitsschritt_ref"], None
    routes = steps[current]["meta"]["routen"]
    if last["status"] == "abgeschlossen":
        target = routes[last["gewaehlte_route"]]
        if target in steps:
            current, phase[target] = target, "next"
        else:
            current, ended = None, target
    elif last["status"] == "wartend":
        for target in routes.values():
            if target in steps and target not in phase:
                phase[target] = "possible"
    return {"phase": phase, "current": current, "ended": ended}


def direction(by_id: dict, order: list[str], source: str, target: str) -> str:
    """A back route targets an earlier step that can actually lead to this source."""
    if target not in order:
        return "end"
    if order.index(target) > order.index(source):
        return "forward"
    pending, seen = [target], set()
    while pending:
        step = pending.pop()
        if step == source:
            return "back"
        if step in seen:
            continue
        seen.add(step)
        pending.extend(route[1] for route in by_id[step]["routes"] if route[1] in order)
    return "forward"


def route_rows(by_id: dict, order: list[str], step_id: str) -> list[list[str]]:
    return [[route, target, title_of(by_id[target]) if target in by_id else short(target), direction(by_id, order, step_id, target)]
            for route, target, *_ in by_id[step_id]["routes"]]


def map_tree(nodes: list[dict], run: dict | None, view: dict | None) -> dict:
    """HP → TP → AS → attempts and routes, each box with its phase key."""
    by_id = {n["id"]: n for n in nodes}
    order = [n["id"] for n in nodes if n["kind"] == "arbeitsschritt"]
    entries = run["meta"]["laufpfad"] if run else []
    box = lambda label, kind, phase="", **extra: {"label": label, "kind": kind, "phase": phase, "children": [], **extra}

    def container(kids: list[dict]) -> str:
        found = {k["phase"] for k in kids}
        return "current" if found & {"current", "next"} else "waiting" if "waiting" in found else ""

    def step(step_id: str) -> dict:
        meta = by_id[step_id]["meta"]
        phase = "" if not run else view["phase"].get(step_id, "future")
        flags = [f for f, on in (("gate", meta.get("gate") == "human"), ("sacred", meta.get("customer_touchpoint") == "sacred")) if on]
        node = box(title_of(by_id[step_id]), "as", phase, ref=step_id, flags=flags)
        mine = [(i, e) for i, e in enumerate(entries, 1) if e["arbeitsschritt_ref"] == step_id]
        last = mine[-1][1] if mine else None
        if len(mine) > 1 or (last and last["status"] != "abgeschlossen"):
            node["children"] += [box(f"Versuch {e['versuch']}", "attempt", ENTRY_PHASE[e["status"]], attempt=e["versuch"], entry=i)
                                 for i, e in mine]
        chosen_in = {e["gewaehlte_route"]: e["versuch"] for _, e in mine if e.get("gewaehlte_route")}
        for route, target, target_title, way in route_rows(by_id, order, step_id):
            chosen = bool(last and last["status"] == "abgeschlossen" and last.get("gewaehlte_route") == route)
            if phase in ("", "current", "waiting"):
                rphase = {"": "", "current": "option", "waiting": "possible"}[phase]
            elif chosen and phase in ("done", "next"):
                # A reached end is a fact, not a success: it is marked, never coloured as done.
                rphase = "reached" if way == "end" and view["ended"] == target else "done"
            else:
                rphase = "past" if phase == "done" else "future"
            extra = {"attempt": chosen_in[route]} if route in chosen_in else {}
            node["children"].append(box(route, "route", rphase, route=route, target=target, target_title=target_title,
                                        dir=way, **extra))
        return node

    def part(part_id: str) -> dict:
        kids = [step(s) for s in by_id[part_id]["children"]]
        return box(title_of(by_id[part_id]), "tp", container(kids), ref=part_id, children=kids)

    root = nodes[0]
    parts = [part(p) for p in root["children"]]
    return box(title_of(root), "hp", "reached" if view and view["ended"] else container(parts), ref=root["id"], children=parts)


def stand(nodes: list[dict], run: dict | None, view: dict | None) -> dict:
    """Where the run stands, as plain fields for the page's fixed sentences."""
    if run is None:
        return {"kind": "definition"}
    by_id = {n["id"]: n for n in nodes}
    order = [n["id"] for n in nodes if n["kind"] == "arbeitsschritt"]
    entries = run["meta"]["laufpfad"]
    last = entries[-1]
    found = dict.fromkeys(("kind", "entry", "entries", "step", "step_title", "part_title", "versuch", "gate", "routes",
                           "ausloeser", "continuation_ref", "from_step", "from_title", "route", "end"))
    found.update(entry=len(entries), entries=len(entries))
    source = last["arbeitsschritt_ref"]
    if last["status"] == "abgeschlossen":
        found.update(from_step=source, from_title=title_of(by_id[source]), route=last["gewaehlte_route"])
    if view["ended"]:
        found.update(kind="ended", end=short(view["ended"]))
        return found
    step = view["current"]
    found.update(step=step, step_title=title_of(by_id[step]), part_title=title_of(by_id[by_id[step]["parent"]]),
                 gate=by_id[step]["meta"].get("gate"), routes=route_rows(by_id, order, step))
    if last["status"] == "abgeschlossen":
        found["kind"] = "next"
    else:
        found.update(kind="current" if last["status"] == "aktiv" else "waiting", versuch=last["versuch"])
        resume = last.get("wiedereinstieg") or {}
        found.update(ausloeser=resume.get("ausloeser"), continuation_ref=resume.get("continuation_ref"))
    return found


def run_summary(name: str, model: dict, head: str | None) -> dict:
    summary = {"page": name, "id": model["selection"]["vorgang"], "issues": model["issues"]}
    if model["issues"]:
        return summary
    run = model["run"]
    summary.update(
        id=run["id"], title=run["title"], revision=model["selection"]["revision"], path=run["path"],
        stand=model["stand"], statuses=[e["status"] for e in run["meta"]["laufpfad"]],
        matches_head=None if head is None else model["selection"]["revision"] == f"git-tree:{head}")
    return summary


def ist_title(model: dict) -> str:
    rel = model["selection"]["ist_prozess"]
    stem = rel.rsplit("/", 1)[-1].removesuffix(".md")
    if model["issues"]:
        return stem
    node = model["nodes"][0]
    name = node["meta"].get("name")
    return name if isinstance(name, str) and name.strip() else node["title"] or stem


def overview(workspace: str, pages: dict[str, dict], heads: dict[str, str | None],
             workspace_issues: list[dict], has_head: bool, ist_skipped: list[dict] | None = None) -> dict:
    """Leistungen, each with its Vorgänge, and the Ist-Prozess files. No edges between Hauptprozesse:
    Core declares none, and the view does not invent them. A Vorgang whose Application is
    no longer in the working files keeps the Leistung of the revision it binds."""
    applications, by_hp = [], {}
    for name, model in pages.items():
        if model["kind"] != "application":
            continue
        folder = model["selection"]["folder"]
        head, tree = heads.get(folder), model["selection"].get("tree")
        entry = {"page": name, "folder": folder, "current": True, "issues": model["issues"], "head": head,
                 "same_as_head": None if head is None or tree is None else tree == head, "runs": []}
        if not model["issues"]:
            hp = model["nodes"][0]
            entry.update(id=hp["id"], title=hp["title"], leistung=hp["meta"]["leistung"],
                         steps=sum(1 for n in model["nodes"] if n["kind"] == "arbeitsschritt"))
            by_hp[hp["id"]] = entry
        applications.append(entry)
    unassigned = []
    for name, model in pages.items():
        if model["kind"] != "vorgang":
            continue
        if model["issues"]:
            unassigned.append(run_summary(name, model, None))
            continue
        hp, revision = model["nodes"][0], model["selection"]["revision"]
        # A vanished Application is known only per bound revision; each may state another Leistung.
        key = hp["id"] if hp["id"] in by_hp else (hp["id"], revision)
        if key not in by_hp:
            by_hp[key] = {"page": None, "folder": None, "current": False, "issues": [], "head": None,
                          "same_as_head": None, "runs": [], "id": hp["id"], "revision": revision,
                          "title": hp["title"], "leistung": hp["meta"]["leistung"],
                          "steps": sum(1 for n in model["nodes"] if n["kind"] == "arbeitsschritt")}
            applications.append(by_hp[key])
        owner = by_hp[key]
        owner["runs"].append(run_summary(name, model, owner["head"]))
    ist = None
    if ist_skipped is not None:
        ist = {"pages": [{"page": name, "file": m["selection"]["ist_prozess"], "title": ist_title(m), "issues": m["issues"],
                          "evidence_status": None if m["issues"] else m["nodes"][0]["meta"].get("evidence_status"),
                          "analysis": None if m["issues"] else m["necessity"]["status"],
                          "rows": 0 if m["issues"] else len(m["necessity"]["rows"])}
                         for name, m in pages.items() if m["kind"] == "ist-prozess"],
               "skipped": ist_skipped}
    runs = [m for m in pages.values() if m["kind"] == "vorgang"]
    current = [a for a in applications if a["current"]]
    population = {"applications": len(current), "applications_refused": sum(bool(a["issues"]) for a in current),
                  "historic": len(applications) - len(current),
                  "runs": len(runs), "runs_refused": sum(bool(m["issues"]) for m in runs),
                  "ist": len(ist["pages"]) if ist else 0}
    return {"format": "impacts-view/2", "kind": "overview", "selection": {"workspace": workspace, "head": has_head},
            "issues": workspace_issues, "population": population,
            "applications": applications, "unassigned": unassigned, "ist": ist}


# ---------- Notwendigkeit: the analysis table of an Ist-Prozess, read, never judged ----------

LABELS = ("open", "hypothesis", "reported", "verified")  # weakest first
NAMES = {"analysis": {"analyse", "analysis"}, "conditions": {"geforderte bedingungen", "required conditions"},
         "activities": {"tätigkeiten in ablaufreihenfolge", "activities in flow order"}}
HEADS = {"analysis": (["nr.", "dient", "ergebnisarbeit", "koordination", "fehlerfolge", "doppelung", "überschuss",
                       "vorgeschlagene maßnahme"],
                      ["no.", "serves", "result work", "coordination", "failure demand", "duplicate", "excess", "proposed move"]),
         "conditions": (["id", "bedingung", "urheber und grundlage", "evidenz"], ["id", "condition", "imposed by and basis", "evidence"]),
         "activities": (["nr.", "tätigkeit"], ["no.", "activity"])}
MARK = {"ja": "yes", "yes": "yes", "nein": "no", "no": "no", "offen": "open", "open": "open"}
LEADING = re.compile(r"^\W*([A-Za-zÄÖÜäöüß]+)")
CODE_LIKE = re.compile(r"[A-Z]{1,3}\d+")
# Ist und Ziel: a proposed move names its target steps as `arbeitsschritt:<slug>` or proposes removal with `entfaellt`.
TARGET = re.compile(r"(?<![\w:-])arbeitsschritt:([a-z0-9]+(?:-[a-z0-9]+)*)(?![\w:/-]|\.[\w])")
REMOVED = "entfaellt"


def plain(spans: list[list[str]]) -> str:
    return "".join(text for _, text, _ in spans)


def normal(spans: list[list[str]]) -> str:
    return plain(spans).strip().lower().removesuffix("?").strip()


def labels(cells: list[list[list[str]]]) -> list[str]:
    found = []
    for spans in cells:
        for kind, text, _ in spans:
            if kind == "code" and text in LABELS and text not in found:
                found.append(text)
    return found


def answer(spans: list[list[str]]) -> dict:
    """The leading word decides the marker; every other word stays in `spans`. `more`: the cell
    says more than its leading word and its evidence labels."""
    match = LEADING.match(plain(spans))
    word = match.group(1) if match else ""
    mark, found = MARK.get(word.casefold(), "other"), labels([spans])
    solid = mark == "yes" and bool(found) and min(found, key=LABELS.index) == "verified"
    rest = "".join(text for kind, text, _ in spans if not (kind == "code" and text in LABELS))
    lead = LEADING.match(rest)
    tail = rest[lead.end():] if lead and lead.group(1) == word else rest
    return {"mark": mark, "word": word, "labels": found, "spans": spans, "solid": solid, "more": bool(re.search(r"\w", tail))}


def _scopes(node: dict, kind: str) -> list[list[tuple[int, int, dict]]]:
    """For each heading block named like `kind`, the blocks after it up to the next heading."""
    found, current = [], None
    for s, part in enumerate(node["sections"]):
        current = None
        for b, block in enumerate(part["blocks"]):
            if block["type"] == "heading":
                current = None
                if normal(block["spans"]) in NAMES[kind]:
                    current = [(s, b, block)]
                    found.append(current)
            elif current is not None:
                current.append((s, b, block))
    return found


def _shaped(block: dict, kind: str) -> bool:
    head = [normal(c) for c in block["head"] or []]
    return any(head[:len(shape)] == shape if kind == "activities" else head == shape for shape in HEADS[kind])


def _named_tables(node: dict, kind: str) -> list[tuple[int, int, dict]]:
    return [item for scope in _scopes(node, kind) for item in scope[1:]
            if item[2]["type"] == "table" and _shaped(item[2], kind)]


def _unique(items) -> list:
    return list(dict.fromkeys(items))


def necessity(node: dict) -> dict:
    """The stored analysis as rows of markers, each answer kept whole. Unsupported shapes stay verbatim."""
    result = {"status": "none", "reason": None, "at": None, "heading_line": None, "conditions": None,
              "conditions_at": None, "conditions_tables": [], "activities": {}, "activities_at": None,
              "activities_tables": [], "duplicate_nrs": [], "rows": [],
              "mapping": [], "open_count": 0}
    if found := _named_tables(node, "conditions"):
        result["conditions_tables"] = [list(item[:2]) for item in found]
        result["conditions_at"] = result["conditions_tables"][0]
        result["conditions"] = {}
        for _, _, table in found:
            for k, cells in enumerate(table["rows"]):
                condition = result["conditions"].setdefault(plain(cells[0]).strip(), {"declarations": []})
                condition["declarations"].append({"cells": cells[1:], "labels": labels(cells[1:]), "line": table["line"] + 2 + k})
        for condition in result["conditions"].values():
            declarations = condition["declarations"]
            condition.update(status="found" if len(declarations) == 1 else "ambiguous",
                             **(declarations[0] if len(declarations) == 1 else
                                {"cells": [], "labels": [], "line": declarations[0]["line"]}))
    if found := _named_tables(node, "activities"):
        result["activities_tables"] = [list(item[:2]) for item in found]
        result["activities_at"] = result["activities_tables"][0]
        records = [(plain(cells[0]).strip(), {"name": plain(cells[1]).strip(), "line": table["line"] + 2 + k})
                   for _, _, table in found for k, cells in enumerate(table["rows"])]
        numbers = [nr for nr, _ in records]
        result["duplicate_nrs"] = _unique(n for n in numbers if numbers.count(n) > 1)
        for nr, activity in records:
            result["mapping"].append({"nr": nr, "activity": activity, "analysis_rows": [],
                                      "status": "ambiguous-activity" if nr in result["duplicate_nrs"] else "missing-analysis"})
            if nr not in result["duplicate_nrs"]:
                result["activities"][nr] = activity
    scopes = _scopes(node, "analysis")
    if not scopes:
        return result
    result["heading_line"] = scopes[0][0][2]["line"]
    tables = [item for scope in scopes for item in scope[1:] if item[2]["type"] == "table"
              or (item[2]["type"] == "text" and item[2]["text"].lstrip().startswith("|"))]
    if not tables:
        result["reason"] = "no-table"
        return result
    s, b, table = tables[0]
    result["at"] = [s, b]
    reason = "several" if len(tables) > 1 else "unreadable" if table["type"] != "table" else None if _shaped(table, "analysis") else "shape"
    if reason:
        result.update(status="unsupported", reason=reason)
        return result
    known = set(result["conditions"] or {})
    for k, cells in enumerate(table["rows"]):
        nr, ids, unknown = plain(cells[0]).strip(), *condition_refs(plain(cells[1]), known)
        result["rows"].append({
            "nr": nr, "line": table["line"] + 2 + k, "activity": result["activities"].get(nr),
            "serves": {"spans": cells[1], "ids": ids, "unknown": unknown},
            "answers": [answer(c) for c in cells[2:7]],
            "move": {"spans": cells[7], "labels": labels([cells[7]]), "targets": _unique(TARGET.findall(plain(cells[7]))),
                     "removed": any(kind == "code" and text.strip() == REMOVED for kind, text, _ in cells[7]), "resolved": None}})
    reconcile_ist(result)
    result["status"] = "table"
    result["open_count"] = sum(a["mark"] == "open" for row in result["rows"] for a in row["answers"])
    return result


def condition_refs(text: str, known: set[str]) -> tuple[list[str], list[str]]:
    """Declared IDs named whole, in reading order; `C1` never stands in for `C1-extra`.
    Joined punctuation can be an identity: unknown composites remain gaps, not inferred delimiters."""
    bound = lambda cid: re.compile(rf"(?<![\w-]){re.escape(cid)}(?![\w-])")
    candidates = [(m.start(), m.end(), cid) for cid in known for m in bound(cid).finditer(text)]
    qualified = list(re.finditer(r"[\w-]+(?:[.:/]+[\w-]+)+", text))
    hits = []
    # IDs have no additional punctuation grammar. Prefer the complete declared name
    # when another declared name matches inside it, then restore source reading order.
    for start, end, cid in sorted(candidates, key=lambda hit: (-(hit[1] - hit[0]), hit[0], hit[2])):
        if any(start < m.end() and m.start() < end and not (start <= m.start() and m.end() <= end)
               for m in qualified):
            continue
        if not any(start < other_end and other_start < end for other_start, other_end, _ in hits):
            hits.append((start, end, cid))
    hits.sort()
    inside = lambda m: any(start <= m.start() and m.end() <= end for start, end, _ in hits)
    gaps = [m for m in qualified if not inside(m) and
            (any(CODE_LIKE.fullmatch(part) for part in re.split(r"[.:/]+", m.group(0))) or
             any(start < m.end() and m.start() < end for start, end, _ in candidates))]
    unknown = gaps + [m for m in re.finditer(r"[\w-]+", text) if not inside(m) and CODE_LIKE.fullmatch(m.group(0))
                      and not any(gap.start() <= m.start() and m.end() <= gap.end() for gap in gaps)]
    return _unique(cid for _, _, cid in hits), _unique(m.group(0) for m in sorted(unknown, key=lambda m: m.start()))


def reconcile_ist(result: dict) -> None:
    """Bind analysis rows to the captured inventory only when both numbers are unique.
    Missing, duplicate and orphan rows stay visible, without a target assignment."""
    analyses = {}
    for k, row in enumerate(result["rows"]):
        analyses.setdefault(row["nr"], []).append(k)
    captured = {item["nr"] for item in result["mapping"]}
    for nr, indices in analyses.items():
        if nr not in captured:
            result["mapping"].append({"nr": nr, "activity": None, "analysis_rows": indices, "status": "orphan-analysis"})
    for item in result["mapping"]:
        indices = item["analysis_rows"] = analyses.get(item["nr"], [])
        if item["activity"] is not None:
            item["status"] = ("ambiguous-activity" if item["nr"] in result["duplicate_nrs"] else
                              "missing-analysis" if not indices else "ambiguous-analysis" if len(indices) != 1 else "found")
        for k in indices:
            result["rows"][k]["mapping"] = item["status"]


def link_ist(pages: dict[str, dict]) -> None:
    """Resolve each target step of every Ist analysis against the Applications of the same view, all read
    from the working files. A step found in no or in several Applications stays a gap; each found step
    lists the Ist rows that name it. Nothing is matched by title."""
    steps: dict[str, list] = {}
    for name, model in pages.items():
        if model["kind"] == "application" and not model["issues"]:
            for node in model["nodes"]:
                if node["kind"] == "arbeitsschritt":
                    steps.setdefault(node["id"], []).append((name, model, node))
    for name, model in pages.items():
        if model["kind"] != "ist-prozess" or model["issues"]:
            continue
        for index, row in enumerate(model["necessity"]["rows"]):
            resolved = []
            for slug in row["move"]["targets"] if row["mapping"] == "found" else []:
                ref, hits = "arbeitsschritt:" + slug, steps.get("arbeitsschritt:" + slug, [])
                if len(hits) != 1:
                    resolved.append({"ref": ref, "status": "missing" if not hits else "ambiguous"})
                    continue
                page, application, node = hits[0]
                resolved.append({"ref": ref, "status": "found", "page": page, "title": title_of(node),
                                 "application": title_of(application["nodes"][0]), "gate": node["meta"].get("gate") == "human",
                                 "touchpoint": node["meta"].get("customer_touchpoint"),
                                 "execution": _unique(e["kind"] for e in node["execution"])})
                node.setdefault("ist", []).append({"page": name, "nr": row["nr"], "file": model["selection"]["ist_prozess"],
                                                   "activity": row["activity"]["name"] if row["activity"] else None,
                                                   "row": row, "index": index, "heading_line": model["necessity"]["heading_line"],
                                                   "heading": plain(next(b["spans"] for p in model["nodes"][0]["sections"]
                                                                         for b in p["blocks"] if b["line"] == model["necessity"]["heading_line"]))})
            row["move"]["resolved"] = resolved
