"""Local fixed-output offer demonstration; no production engine or human authority."""
from __future__ import annotations

import argparse
from decimal import Decimal, DecimalException, Inexact, localcontext
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import quote

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from impacts_protocol import init_workspace, surface_hash, validate
from impacts_protocol.io import load_frontmatter_and_body

DOCUMENT = ROOT / "02_protocol/impacts-architect/references/datenbezug.md"
RUN = "vorgaenge/angebot-001"
APP = "applications/angebot-erstellen"
UNITS = {"P-10": {"de": "Stück", "en": "piece"}, "S-20": {"de": "Stunde", "en": "hour"}}
# Supported fixed blanks are pinned with the renderer, not resolved from live docs.
TEMPLATE_SHA256 = {
    "de": "fd025a17ae4e70afdcce9265074fdac6b02f5bb54cf85fb22374fe4eea74a1f1",
    "en": "a86665142add3bd7935df05861c064cb78c7121a07c1717dbb51e594367a5f15",
}


def block(heading: str, kind: str) -> str:
    section = DOCUMENT.read_text().split(f"### {heading}\n", 1)[1]
    return re.search(r"```" + kind + r"\n(.*?)\n```", section, re.S)[1]


def fixture() -> dict:
    return json.loads(block("Concrete run inputs", "json"))


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def encode(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def write_context(path: Path, data: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + yaml.safe_dump(data, allow_unicode=True, sort_keys=False) + "---\n\n" + body + "\n")


def fill_offer(template: str, values: dict, *, language: str = "de") -> str:
    """Pure local calculation/rendering; source facts and approval remain unverified."""
    if language not in {"en", "de"}:
        raise ValueError("unsupported working language")
    for key, pattern in (("offer_id", r"O-\d+"), ("customer_id", r"C-\d+"), ("request_ref", r"AN-\d+")):
        if not isinstance(values.get(key), str) or not re.fullmatch(pattern, values[key]):
            raise ValueError("invalid offer identity")
    if type(values.get("version")) is not int or values["version"] < 1:
        raise ValueError("invalid offer version")
    if not isinstance(values.get("items"), list) or not values["items"]:
        raise ValueError("missing offer input")
    positions, ids, total = [], set(), Decimal(0)
    with localcontext() as context:
        context.prec = 50
        context.traps[Inexact] = True
        for item in values["items"]:
            item_id = item.get("item_id")
            if not isinstance(item_id, str) or not re.fullmatch(r"OI-\d+", item_id) or item_id in ids or not re.fullmatch(r"PREIS-\d+", str(item.get("price_source", ""))):
                raise ValueError("missing or duplicate position identity/source")
            ids.add(item_id)
            references = [(key, item[key]) for key in ("product_id", "service_id") if item.get(key)]
            if len(references) != 1 or references[0] not in (("product_id", "P-10"), ("service_id", "S-20")):
                raise ValueError("unknown or ambiguous catalog reference")
            kind = references[0][1]
            if item.get("unit") != UNITS[kind]["de"] or item.get("currency") != "EUR":
                raise ValueError("incompatible unit or currency")
            if item.get("quantity") in (None, "") or item.get("unit_price") in (None, ""):
                raise ValueError("missing quantity or price")
            try:
                quantity, price = Decimal(str(item["quantity"])), Decimal(str(item["unit_price"]))
                if any(not number.is_finite() or number < 0 for number in (quantity, price)):
                    raise ValueError("invalid quantity or price")
                amount = quantity * price
                if amount != amount.quantize(Decimal(".01")) or price != price.quantize(Decimal(".01")):
                    raise ValueError("rounding rule required")
            except Inexact as exc:
                raise ValueError("rounding rule required") from exc
            except DecimalException as exc:
                raise ValueError("invalid quantity or price") from exc
            total += amount
            unit = UNITS[kind][language]
            quantity_unit = unit if quantity == 1 or unit == "Stück" else unit + ("n" if language == "de" else "s")
            positions.append(f"{item_id}: {kind} — {quantity} {quantity_unit} × {price:.2f} EUR/{unit} = {amount:.2f} EUR")
    replacements = {key: str(values[key]) for key in ("offer_id", "version", "customer_id", "request_ref")}
    replacements.update(positions="\n".join(positions), total=f"{total:.2f}")
    result = template
    for key, value in replacements.items():
        result = result.replace("{{" + key + "}}", value)
    if "{{" in result or "}}" in result:
        raise ValueError("unfilled placeholder")
    return result


def open_offer(target: Path, values: dict, language: str) -> Path:
    root = init_workspace(target, language=language)
    de = language == "de"
    template = block("Document blank" if de else "English document blank", "text")
    sources = {"data.json": encode(values), "template.md": template,
               "language.md": f"Working language: {language}\n",
               "renderer.py": Path(__file__).read_text(),
               "language-contract.md": (ROOT / "02_protocol/language.md").read_text()}
    for name, text in sources.items():
        path = root / "grundlagen" / name
        path.parent.mkdir(exist_ok=True)
        path.write_text(text)
    rule = "Prüfbarer interner Angebotsentwurf; Versand nicht erlaubt." if de else "Reviewable internal offer draft; sending is not permitted."
    write_context(root / APP / "CONTEXT.md", {
        "type": "hauptprozess", "id": "hauptprozess:angebot-erstellen",
        "leistung": {"ergebnis": rule, "kennzahl": "Durchlaufzeit" if de else "Lead time", "abnahme": [rule]},
        "einstieg_ref": "arbeitsschritt:entwerfen"}, rule)
    write_context(root / APP / "ausarbeitung/CONTEXT.md", {
        "type": "teilprozess", "id": "teilprozess:ausarbeitung", "ergebnis": rule}, rule)
    inputs = [f"input/{name}" for name in sources] + ["input/herkunft.json"]
    write_context(root / APP / "ausarbeitung/entwerfen/CONTEXT.md", {
        "type": "arbeitsschritt", "id": "arbeitsschritt:entwerfen", "eingaben": inputs,
        "ausgaben": ["output/angebot.md", "output/pruefbericht.json"],
        "pruefung": "checked_offer bestätigt Eingabebindung, Identität, Einheiten, Rechnung und exakte deutsche Ausgabe." if de else
                    "checked_offer confirms input binding, identity, units, calculation and exact English output.",
        "routen": {"bestanden": "arbeitsschritt:freigeben", "fehlerhaft": "end:ungeklaert"}},
        ("MUST: Vor Übergabe an die menschliche Prüfung müssen gebundene Eingaben, Rechnung und deutsche Ausgabe geprüft sein.\n"
         "Basis: Dieser gebundene Beispielvertrag, input/language-contract.md und input/renderer.py gelten ausschließlich für den synthetischen internen Entwurf.\n"
         "Prüfung: Das lokale Harness führt checked_offer aus und bindet den tatsächlichen Bericht output/pruefbericht.json an Eingaben, Regeln und Ausgabe.\n"
         "Fehlerfolge: Keine Übergabe; der aktuelle Schritt bleibt aktiv. Eine spätere Schließung über fehlerhaft führt nach end:ungeklaert.\n" if de else
         "MUST: Before human review, verify bound inputs, calculation and English output.\n"
         "Basis: This bound example contract, input/language-contract.md and input/renderer.py apply only to the synthetic internal draft.\n"
         "Check: The local harness executes checked_offer and binds the actual output/pruefbericht.json report to inputs, rules and output.\n"
         "Failure: No handoff; the current step stays active. A later closure through fehlerhaft leads to end:ungeklaert.\n") +
        "Working language: " + language + "\n" +
        "Route `bestanden`: `output/angebot.md -> arbeitsschritt:freigeben/input/angebot.md`.\n" +
        "Route `bestanden`: `output/pruefbericht.json -> arbeitsschritt:freigeben/input/pruefbericht.json`.")
    write_context(root / APP / "ausarbeitung/freigeben/CONTEXT.md", {
        "type": "arbeitsschritt", "id": "arbeitsschritt:freigeben",
        "eingaben": ["input/angebot.md", "input/pruefbericht.json", "input/herkunft.json"],
        "ausgaben": ["output/entscheidung.md"], "gate": "human",
        "pruefung": "Die benannte Person entscheidet über den geprüften internen Entwurf und begründet freigegeben oder abgelehnt in output/entscheidung.md." if de else
                    "The named reviewer decides on the checked internal draft and records freigegeben or abgelehnt with reasons in output/entscheidung.md.",
        "routen": {"freigegeben": "end:entwurf-freigegeben", "abgelehnt": "end:abgelehnt"}},
        "Rolle: Verantwortliche Person für den Angebotsprozess. Konkrete Person und Befugnis sind offen; vor einer Entscheidung benennen und prüfen. Angebot und Prüfbericht lesen. Entscheidung mit Begründung bleibt offen; Versand ist nicht Teil dieses Laufs." if de else
        "Role: offer-process owner. The actual person and authority are open; identify and check them before a decision. Read the offer and check report. A reasoned decision remains pending; sending is outside this run.")
    git(root, "init", "-q")
    git(root, "add", ".")
    git(root, "-c", "user.name=IMPACTS synthetic fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Synthetic offer inputs and Application")
    commit = git(root, "rev-parse", "HEAD")
    protocol = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--show-toplevel", "HEAD"], capture_output=True, text=True)
    reference = protocol.stdout.splitlines()
    protocol_ref = reference[1] if protocol.returncode == 0 and len(reference) == 2 and Path(reference[0]).resolve() == ROOT.resolve() else ("nicht versioniert" if de else "unversioned")
    protocol_link = quote(Path(os.path.relpath(ROOT / "CONTEXT.md", root.resolve())).as_posix(), safe="/")
    architect_link = quote(Path(os.path.relpath(ROOT / "02_protocol/impacts-architect/SKILL.md", root.resolve())).as_posix(), safe="/")
    with (root / "CONTEXT.md").open("a", encoding="utf-8") as router:
        router.write(("\n## Synthetisches Angebotsbeispiel\n\n" if de else "\n## Synthetic offer example\n\n") +
            f"[Application]({APP}/CONTEXT.md) · [" + ("Aktueller Vorgang" if de else "Current run") + f"]({RUN}/CONTEXT.md)\n\n" +
            ("Gebundene Quelldateien: " if de else "Bound source files: ") +
            "[data.json](grundlagen/data.json) · [renderer.py](grundlagen/renderer.py)\n\n" +
            ("Quellrevision: " if de else "Source revision: ") + f"`{commit}`.\n\n" +
            ("Protokoll-Navigation: " if de else "Protocol navigation: ") + f"[CONTEXT.md]({protocol_link}) · [Architect]({architect_link}). " +
            ("Checkout-Referenz: " if de else "Checkout reference: ") + f"`{protocol_ref}`. " +
            ("Diese Links zeigen lebende Referenzseiten; sie binden keine zusätzlichen Lauf-Eingaben. Die Renderer-Kopie ist gebundene Evidenz, kein eigenständiges Programm. Das Beispiel wird im vollständigen Protokoll-Checkout ausgeführt.\n" if de else
             "These links open live reference pages; they bind no additional run inputs. The renderer copy is bound evidence, not a standalone program. Execute the example from the complete protocol checkout.\n"))
    provenance = {name: {"revision": commit, "path": f"grundlagen/{name}", "sha256": digest(text.encode())} for name, text in sources.items()}
    attempt = root / RUN / "entwerfen/001"
    (attempt / "input").mkdir(parents=True)
    for name in sources:
        content = subprocess.check_output(["git", "-C", str(root), "show", f"{commit}:grundlagen/{name}"])
        (attempt / "input" / name).write_bytes(content)
    (attempt / "input/herkunft.json").write_text(encode(provenance))
    entry = {"arbeitsschritt_ref": "arbeitsschritt:entwerfen", "versuch": 1, "status": "aktiv", "eingabe_hash": surface_hash(attempt, inputs)}
    write_context(root / RUN / "CONTEXT.md", {"type": "vorgang", "id": "vorgang:angebot-001", "application_revision": "git-tree:" + git(root, "rev-parse", f"HEAD:{APP}"), "laufpfad": [entry]},
                  "Entwurf in Bearbeitung; Freigabe und Versand stehen aus." if de else "Draft in progress; approval and sending remain pending.")
    return root


def bound_inputs(root: Path) -> tuple[dict, Path, str, str]:
    """Resolve this fixture's committed inputs and rules without mutating the run."""
    if not validate(root).valid:
        raise ValueError("invalid bound run")
    meta, _ = load_frontmatter_and_body(root / RUN / "CONTEXT.md")
    if len(meta["laufpfad"]) != 1 or meta["laufpfad"][0]["status"] != "aktiv":
        raise ValueError("draft step is not active")
    attempt = root / RUN / "entwerfen/001"
    provenance = json.loads((attempt / "input/herkunft.json").read_text())
    app_tree = meta["application_revision"].removeprefix("git-tree:")
    for name in ("data.json", "template.md", "language.md", "renderer.py", "language-contract.md"):
        source = provenance[name]
        if git(root, "rev-parse", f'{source["revision"]}:{APP}') != app_tree:
            raise ValueError("Application differs from bound source revision")
        if source["path"] != f"grundlagen/{name}":
            raise ValueError("wrong source path")
        original = subprocess.check_output(["git", "-C", str(root), "show", f'{source["revision"]}:{source["path"]}'])
        if original != (attempt / "input" / name).read_bytes() or digest(original) != source["sha256"]:
            raise ValueError("source binding mismatch")
    if (attempt / "input/renderer.py").read_bytes() != Path(__file__).read_bytes():
        raise ValueError("bound renderer differs from executing implementation")
    language = (attempt / "input/language.md").read_text().removeprefix("Working language: ").strip()
    if language not in {"de", "en"}:
        raise ValueError("unsupported working language")
    definition = git(root, "show", f"{app_tree}:ausarbeitung/entwerfen/CONTEXT.md")
    if f"Working language: {language}\n" not in definition:
        raise ValueError("working language differs from bound Application")
    expected_mappings = {(f"output/{name}", f"arbeitsschritt:freigeben/input/{name}") for name in ("angebot.md", "pruefbericht.json")}
    actual_mappings = re.findall(r'Route `bestanden`: `(output/[^` ]+) -> ([^` ]+)`', definition)
    if len(actual_mappings) != 2 or set(actual_mappings) != expected_mappings:
        raise ValueError("unsupported bound handoff mappings")
    # The example supports exactly the published fixed blanks, not arbitrary translated prose.
    blank = (attempt / "input/template.md").read_bytes()
    if digest(blank) != TEMPLATE_SHA256[language]:
        raise ValueError("unrecognized localized template")
    return meta, attempt, language, blank.decode("utf-8")


def checked_offer(root: Path) -> tuple[str, dict]:
    """Preflight only. Does not write a report or mutate the run."""
    meta, attempt, language, blank = bound_inputs(root)
    result = fill_offer(blank, json.loads((attempt / "input/data.json").read_text()), language=language)
    report = {"working_language": language, "input_hash": meta["laufpfad"][0]["eingabe_hash"],
              "renderer_sha256": digest(Path(__file__).read_bytes()), "application_revision": meta["application_revision"],
              "language_contract_sha256": digest((attempt / "input/language-contract.md").read_bytes()), "output_sha256": digest(result.encode()),
              "checks": ["source-binding", "identity", "units", "calculation", "fixed-language-output"],
              "result": "passed", "use": "Interner Entwurf; menschliche Entscheidung offen." if language == "de" else "Internal draft; human decision pending."}
    return result, report


def prepare_gap(root: Path) -> str:
    """Produce only an internal missing-price note for this fixture's scoped gap."""
    _, attempt, language, _ = bound_inputs(root)
    values = json.loads((attempt / "input/data.json").read_text())
    if not any(item.get("unit_price") in (None, "") for item in values["items"]):
        raise ValueError("no missing price to clarify")
    result = ("Interner Klärungsvermerk: In den gebundenen Eingaben fehlt mindestens eine Preisangabe. Identität, Mengen, Einheiten und weitere Voraussetzungen sind ungeprüft. Eingaben und Preisquelle klären. Kein geprüftes Angebot, keine Preiszusage oder Versandfreigabe." if language == "de" else
              "Internal clarification note: the bound inputs lack at least one price. Identity, quantities, units and other prerequisites are unchecked. Clarify the inputs and price source. No checked offer, price commitment or sending approval.")
    (attempt / "output").mkdir(exist_ok=True)
    (attempt / "output/angebot.md").write_text(result)
    return result


def handoff(root: Path, candidate: str) -> None:
    """Verify actual output, then write both mappings and open the pending gate."""
    expected, report = checked_offer(root)
    if candidate != expected:
        raise ValueError("output differs from checked localized rendering")
    meta, _ = load_frontmatter_and_body(root / RUN / "CONTEXT.md")
    attempt = root / RUN / "entwerfen/001"
    gate = root / RUN / "freigeben/001"
    outputs = {"angebot.md": expected, "pruefbericht.json": encode(report)}
    for name, content in outputs.items():
        (attempt / "output").mkdir(exist_ok=True)
        (attempt / "output" / name).write_text(content)
        (gate / "input").mkdir(parents=True, exist_ok=True)
        (gate / "input" / name).write_text(content)
    (gate / "input/herkunft.json").write_text(encode({name: {"origin": f"entwerfen/001/output/{name}", "sha256": digest(content.encode())} for name, content in outputs.items()}))
    entry = meta["laufpfad"][0]
    entry.update(status="abgeschlossen", gewaehlte_route="bestanden", ausgabe_hash=surface_hash(attempt, ["output/angebot.md", "output/pruefbericht.json"]))
    meta["laufpfad"].append({"arbeitsschritt_ref": "arbeitsschritt:freigeben", "versuch": 1, "status": "aktiv", "eingabe_hash": surface_hash(gate, ["input/angebot.md", "input/pruefbericht.json", "input/herkunft.json"])})
    write_context(root / RUN / "CONTEXT.md", meta,
                  ("Geprüfter Entwurf bereit. Menschliche Entscheidung und Versand stehen aus.\n\n[Angebot](freigeben/001/input/angebot.md) · [Prüfbericht](freigeben/001/input/pruefbericht.json) · [Herkunft](freigeben/001/input/herkunft.json)\n\n" if report["working_language"] == "de" else
                   "Checked draft ready. Human decision and sending remain pending.\n\n[Offer](freigeben/001/input/angebot.md) · [Check report](freigeben/001/input/pruefbericht.json) · [Provenance](freigeben/001/input/herkunft.json)\n\n") +
                  ("Aktueller Schritt: " if report["working_language"] == "de" else "Current step: ") +
                  "[freigeben](../../applications/angebot-erstellen/ausarbeitung/freigeben/CONTEXT.md). " +
                  ("Definition nur bearbeiten, ohne damit die gebundene Fassung dieses Vorgangs zu ändern; maßgeblich ist `application_revision` oben." if report["working_language"] == "de" else
                   "Editing the definition does not change this run’s bound version; `application_revision` above is authoritative."))


def daily_capacity(preparation: int, review: int, demand: int) -> dict:
    """Synthetic steady daily rates; every prepared case requires one review.

    All cases stay in the population; no rework, carryover processing or change
    in review quality is assumed. Reviewed capacity is an upper bound on accepted
    outputs, not evidence that customers accepted anything.
    """
    if any(type(v) is not int or v < 0 for v in (preparation, review, demand)):
        raise ValueError("capacities require nonnegative whole cases per day")
    prepared = min(preparation, demand)
    reviewed = min(prepared, review)
    return {"prepared_per_day": prepared, "reviewed_per_day": reviewed,
            "accepted_upper_bound_per_day": reviewed, "review_backlog_growth_per_day": prepared - reviewed}


def discovery_case(language: str) -> tuple[str, dict]:
    scenarios = {name: {"inputs": dict(preparation=p, review=r, demand=d), "result": daily_capacity(p, r, d)}
                 for name, p, r, d in (("baseline", 6, 6, 18), ("preparation_only", 18, 6, 18),
                                       ("review_sensitivity", 18, 9, 18), ("low_demand", 18, 6, 4))}
    if language == "de":
        text = ("# Synthetische Entscheidung zur Angebotsvorbereitung\n\n"
                "Anfrage: Vorbereitung von 6 auf 18 Angebote pro Arbeitstag erhöhen. Entscheidende Rückfrage: Muss jedes Angebot weiterhin durch dieselbe Prüfung, und wie viele Fälle schafft sie bei unveränderten Qualitätsanforderungen?\n\n"
                "Synthetische Antwort: Ja; die Prüfung schafft 6 Fälle täglich. Bei ausreichender Nachfrage begrenzt sie die geprüften Ergebnisse auf 6, während der Prüfbestand durch schnellere Vorbereitung um 12 Fälle pro Tag wächst. Kundenannahme bleibt unbelegt.\n\n"
                "Bedingte Intervention: Freigabe neuer Vorarbeit an die Prüfkapazität koppeln und die Ursache der Prüfbelastung untersuchen. Erst eine geprüfte Änderung dieser Grenze oder ihrer Voraussetzungen rechtfertigt mehr Vorarbeit. Menschliche Prüfung und Qualitätsanforderungen bleiben erhalten. Dies ist eine simulierte Entscheidung, keine echte Freigabe. Zuständig im realen Fall wäre die benannte verantwortliche Person für den Angebotsprozess; sie ist hier nicht identifiziert.\n\n"
                "Annahmen: einheitliche Fälle pro Arbeitstag, jede Vorbereitung benötigt eine Prüfung, unveränderte Qualität, kein Nacharbeitsumlauf; alle Fälle bleiben im Nenner. Der Bestandszuwachs ist eine Tagesrate, keine gemessene Durchlaufzeit. Anfangsbestand und Wartezeit wurden nicht erhoben. Bei Prüfungskapazität 9 wächst der Bestand um 9; bei Nachfrage 4 entsteht kein Prüfbestand. Reale Verbesserung braucht gemessene Annahmequote, Wartezeit, Nacharbeit und menschlichen Aufwand gegenüber derselben Grundgesamtheit.\n")
    else:
        text = ("# Synthetic offer-preparation decision\n\n"
                "Request: increase preparation from 6 to 18 offers per working day. Consequential clarification: must every offer still pass the same review, and how many cases can it review under unchanged quality requirements?\n\n"
                "Synthetic answer: yes; review handles 6 cases daily. With sufficient demand, reviewed output remains bounded by 6 while faster preparation adds 12 cases to the review backlog each day. Customer acceptance remains unevidenced.\n\n"
                "Conditional intervention: release new preparation against review capacity and investigate what consumes review effort. Increase preparation only after an evidenced change to that constraint or its premises. Preserve human review and quality requirements. This decision is simulated, not a real approval. A real decision belongs to the named offer-process owner, who has not been identified here.\n\n"
                "Assumptions: comparable cases per working day, one review per prepared case, unchanged quality, no rework loop; every case remains in the denominator. Backlog growth is a daily rate, not measured lead time. Initial backlog and waiting time were not measured. Review capacity 9 leaves growth of 9; demand 4 creates no review backlog. Real improvement requires acceptance, waiting, rework and human-attention measures against the same population.\n")
    return text, scenarios


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=("de", "en"), default="en")
    parser.add_argument("--keep", type=Path, help="Retain a new synthetic workspace at this path")
    parser.add_argument("--discovery", action="store_true", help="Include the synthetic downstream-capacity decision")
    args = parser.parse_args()

    def execute(target: Path) -> None:
        root = open_offer(target, fixture(), args.language)
        result, _ = checked_offer(root)
        handoff(root, result)
        if args.discovery:
            note, scenarios = discovery_case(args.language)
            (root / "grundlagen/discovery.md").write_text(note, encoding="utf-8")
            (root / "grundlagen/capacity.json").write_text(encode(scenarios), encoding="utf-8")
            with (root / "CONTEXT.md").open("a", encoding="utf-8") as router:
                router.write("\n[" + ("Synthetische Kapazitätsentscheidung" if args.language == "de" else "Synthetic capacity decision") + "](grundlagen/discovery.md) · [" + ("Berechnete Szenarien" if args.language == "de" else "Calculated scenarios") + "](grundlagen/capacity.json)\n")
            print(note)
        if not validate(root).valid:
            raise ValueError("invalid resulting run")
        print(result)
        print("\nPASS: Übergabe geprüft; menschliche Entscheidung offen." if args.language == "de" else "\nPASS: handoff checked; human decision pending.")
        if args.keep:
            print(("Artefakte: " if args.language == "de" else "Artifacts: ") + str(root.resolve()))

    if args.keep:
        try:
            execute(args.keep)
        except FileExistsError:
            parser.error(f"workspace target exists: {args.keep}")
    else:
        with TemporaryDirectory(prefix="impacts-offer-") as temporary:
            execute(Path(temporary) / "workspace")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
