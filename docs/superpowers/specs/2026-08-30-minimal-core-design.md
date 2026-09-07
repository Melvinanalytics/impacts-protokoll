---
status: user-confirmed
review_state: implemented
evidence_status: verified
normative: true
date: 2026-08-30
verified:
  by: human:melvin
  at: 2026-08-30
amended_by:
  - docs/superpowers/specs/2026-09-02-executable-core-design.md
  - docs/superpowers/specs/2026-09-07-domain-named-tree-design.md
amended_at: 2026-09-07
---

# Minimaler IMPACTS-Core V1

## 1. Zweck und Grenze

IMPACTS formt Kundenrealität über `Identify -> Minimize -> Perfect -> Augment -> Construct -> Test -> Scale` in eine optimierte Application. Der öffentliche Core definiert Dateien, fünf Schemas, atomare Initialisierung und read-only Validierung.

Die Build-Methodik steht in [`02_protocol/impacts-method.md`](../../../02_protocol/impacts-method.md). Sie führt Application-Autoren durch Marktform, Wertfluss, Zielgrößen, Prozessphysik, menschliche Grenzen und den getesteten Sollprozess. Diese Angaben stehen als menschlich lesbarer Kontext in den vorhandenen `CONTEXT.md`-Dateien. Sie erzeugen kein weiteres Schema.

Das Harness führt Arbeitsschritte aus und schreibt Laufdaten. Git transportiert und versioniert Applications. Capabilities besitzen Werkzeuge und deterministische Rechnungen. Kundenbezogene Inhalte leben im Kunden-Repository.

Der Core besitzt vier Befehle:

```text
impacts init PATH
impacts validate ROOT
impacts hash VERSUCHSORDNER FLAECHE...
impacts template ART
```

Die öffentliche Python-API lautet:

```python
init_workspace(path: Path) -> Path
validate(root: Path) -> ValidationReport
surface_hash(attempt_root: Path, declared: Sequence[str]) -> str
```

`hash` und `template` lesen nur. Sie kamen mit V0.3, siehe [2026-09-02-executable-core-design.md](2026-09-02-executable-core-design.md).

## 2. Domänenmodell

Der Core besitzt genau fünf Schemas:

| Schema | Verantwortung |
|---|---|
| Leistung | ID-loser, eingebetteter Vertrag für den prüfbaren wertstiftenden Endzustand |
| Hauptprozess | Aggregate Root einer Application und vollständiger Weg bis zur Leistung |
| Teilprozess | fachlich geschlossener Abschnitt eines Hauptprozesses |
| Arbeitsschritt | ausführbarer Stage-Vertrag mit Ein- und Ausgaben, Prüfung und Routen |
| Vorgang | konkreter revisionsgebundener Lauf einer Application |

Eine Application enthält genau einen Hauptprozess. Der Hauptprozess enthält genau eine Leistung. Mehrere Hauptprozesse ergeben mehrere Applications. Kundenfachliche Records dürfen Vorgänge verbinden; der Core validiert diese Verbindung nicht.

Workspace und Application sind strukturelle Router. Sie tragen ausschließlich `type` im Frontmatter und erhalten kein Schema.

## 3. Dateibäume

Ein leerer Workspace enthält exakt die vom Core erzeugten Flächen:

```text
workspace/
├── CONTEXT.md                    # type: workspace
├── applications/
└── vorgaenge/
```

`grundlagen/` und `records/` dürfen bei einem realen Kundenbedarf hinzukommen. Andere kundenfachliche Flächen bleiben außerhalb der Core-Prüfung.

Eine Application besitzt diesen Baum (Amendment 2026-09-07, siehe [domain-named-tree-design.md](2026-09-07-domain-named-tree-design.md); die Ordner tragen fachliche Namen, die Rolle steht im `type`):

```text
applications/<hauptprozess-slug>/
├── CONTEXT.md                    # type: hauptprozess, mit Leistung
└── <teilprozess-slug>/
    ├── CONTEXT.md                # type: teilprozess
    └── <arbeitsschritt-slug>/
        └── CONTEXT.md            # type: arbeitsschritt
```

`<hauptprozess-slug>`, `<teilprozess-slug>` und `<arbeitsschritt-slug>` folgen `[a-z0-9]+(?:-[a-z0-9]+)*`; die ID jeder Datei ist `<type>:<ordnername>`. Der Application-Baum ist geschlossen: Neben `CONTEXT.md` und Slug-Ordnern der nächsten Ebene ist nichts zulässig, ein Arbeitsschritt hat keine Unterordner. Kundenfachliche Erweiterungen liegen auf Workspace-Ebene.

Ein Vorgang besitzt diesen Baum:

```text
vorgaenge/<vorgang-slug>/
├── CONTEXT.md
└── <arbeitsschritt-slug>/
    └── <versuch>/
        ├── input/
        └── output/
```

`<versuch>` ist dreistellig. `versuch: 1` entspricht `001`. Nur im Laufpfad erreichte Arbeitsschritte und Versuche besitzen Ordner.

## 4. Schemas

Alle Schemas verwenden JSON Schema 2020-12, `additionalProperties: false` und stabile URN-IDs mit Version `v1`.

### 4.1 Leistung

Leistung ist ausschließlich der Wert unter `hauptprozess.leistung`:

```yaml
ergebnis: Nachvollziehbar hergeleiteter Marktwert
kennzahl: Durchlauf bis zur prüffähigen Fassung
abnahme:
  - Herleitung vollständig
  - Qualitätsprüfung bestanden
```

Pflichtfelder sind `ergebnis`, `kennzahl` und eine nichtleere, eindeutige Liste `abnahme`. Jeder Wert ist ein nichtleerer String. Leistung trägt weder `type` noch `id`.

### 4.2 Hauptprozess

```yaml
type: hauptprozess
id: hauptprozess:verkehrswertermittlung
leistung:
  ergebnis: Nachvollziehbar hergeleiteter Marktwert
  kennzahl: Durchlauf bis zur prüffähigen Fassung
  abnahme:
    - Herleitung vollständig
einstieg_ref: arbeitsschritt:auftrag-pruefen
```

Pflichtfelder sind `type`, `id`, `leistung` und `einstieg_ref`. `leistung` referenziert normativ `leistung.schema.json`.

### 4.3 Teilprozess

```yaml
type: teilprozess
id: teilprozess:befund
ergebnis: Prüffähiger Befund
```

Pflichtfelder sind `type`, `id` und `ergebnis`. Elternschaft folgt aus dem Ordner.

### 4.4 Arbeitsschritt

```yaml
type: arbeitsschritt
id: arbeitsschritt:auftrag-pruefen
eingaben:
  - input/auftrag/
ausgaben:
  - output/pruefstand.md
pruefung: Vollständigkeitsprüfung bestanden
gate: human
routen:
  freigegeben: arbeitsschritt:befund-erfassen
  abgelehnt: end:unterlagen-unvollstaendig
customer_touchpoint: sacred
```

Pflichtfelder sind `type`, `id`, `eingaben`, `ausgaben`, `pruefung` und `routen`. Listen sind nichtleer und eindeutig. Pfade sind POSIX-relativ zum Versuchsordner, beginnen mit `input/` beziehungsweise `output/` und enthalten weder `.` noch `..`.

`gate` fehlt oder ist `human`. Ein Human Gate besitzt exakt `freigegeben` und `abgelehnt`. `customer_touchpoint` fehlt oder ist `standard` beziehungsweise `sacred`. Routennamen sind nichtleere Slugs. Routenziele sind `arbeitsschritt:<slug>` oder `end:<slug>`.

Bearbeitung steht als nichtleere Arbeitsanweisung im Markdown-Body derselben `CONTEXT.md`. Ein fehlender oder ausschließlich aus Whitespace bestehender Body schlägt geschlossen fehl. Tätigkeit erhält kein Feld und keine Identität.

### 4.5 Vorgang

```yaml
type: vorgang
id: vorgang:gutachten-001
application_revision: git-tree:<oid>
laufpfad:
  - arbeitsschritt_ref: arbeitsschritt:auftrag-pruefen
    versuch: 1
    status: abgeschlossen
    eingabe_hash: sha256:<digest>
    gewaehlte_route: freigegeben
    ausgabe_hash: sha256:<digest>
    freigabe:
      by: human:<id>
      at: 2026-08-30T10:00:00+02:00
```

Pflichtfelder sind `type`, `id`, `application_revision` und eine nichtleere Liste `laufpfad`. `hauptprozess_ref`, `leistung_ref`, `current_arbeitsschritt_ref`, `status`, `run_id` und Receipt-Referenzen entfallen.

## 5. Prozessgraph

Der Hauptprozess besitzt `einstieg_ref`. Jeder Arbeitsschritt besitzt seine ausgehenden Routen. Arbeitsschritt-IDs sind innerhalb einer Application eindeutig. Der Ordnername entspricht dem Teil nach `arbeitsschritt:`.

Validierung beweist:

1. Einstieg und jedes Schrittziel lösen innerhalb derselben Application auf.
2. Jeder vorhandene Arbeitsschritt ist vom Einstieg erreichbar.
3. Von jedem Arbeitsschritt existiert ein Weg zu einem benannten `end:<slug>`.
4. Schleifen besitzen damit mindestens eine erreichbare Ausstiegsroute.
5. Ein Human Gate besitzt seine beiden Entscheidungsrouten.

Ein separater Knotensatz, reziproke Elternreferenzen und ein zweiter Graph entfallen.

## 6. Laufpfad

Der Laufpfad ist die einzige Zustandsautorität. Sein erster Eintrag entspricht dem Einstieg der gebundenen Application. Das Paar aus `arbeitsschritt_ref` und `versuch` ist eindeutig.

Ein Eintrag besitzt genau einen Zustand:

| Zustand | Pflicht | Unzulässig |
|---|---|---|
| `aktiv` | Schritt, Versuch, `eingabe_hash` | Route, Ausgabehash, Wiedereinstieg, Freigabe |
| `wartend` | Schritt, Versuch, `eingabe_hash`, `wiedereinstieg` | Route, Ausgabehash, Freigabe |
| `abgeschlossen` | Schritt, Versuch, `eingabe_hash`, Route, `ausgabe_hash` | Wiedereinstieg |

Nur der letzte Eintrag darf `aktiv` oder `wartend` sein. Ein abgeschlossenes Routenziel zu einem Arbeitsschritt verlangt diesen Schritt als nächsten Eintrag. Ein Routenziel `end:<slug>` beendet den Vorgang. Der aktuelle Arbeitsschritt und der Vorgangsstatus werden aus dem letzten Eintrag abgeleitet.

`wiedereinstieg` enthält genau `ausloeser` und `continuation_ref`. Beide Werte sind nichtleer.

Bei `gate: human` verlangt der abgeschlossene Eintrag `freigabe` mit genau `by` und `at`. `by` folgt `human:<id>`. `at` ist RFC-3339 mit Zeitzone. Andere Arbeitsschritte dürfen keine Freigabe tragen.

## 7. Hashvertrag

`eingabe_hash` bindet alle Dateien unter den im Arbeitsschritt deklarierten Eingaben beim Versuchsbeginn. `ausgabe_hash` bindet alle Dateien unter den deklarierten Ausgaben beim Abschluss.

Für jede deklarierte Fläche werden Dateien rekursiv gesammelt. Jede Fläche muss existieren und mindestens eine reguläre Datei enthalten. Symlinks und Pfadausbrüche schlagen fehl. Jeder Eintrag lautet:

```json
{"path":"input/auftrag/datei.pdf","sha256":"<hex>"}
```

`path` ist der normalisierte POSIX-Pfad relativ zum Versuchsordner. `sha256` ist der Digest der unveränderten Dateibytes. Einträge werden nach UTF-8-Bytes ihres Pfads sortiert. Die vollständige Liste wird mit UTF-8, `ensure_ascii=false`, `sort_keys=true`, `separators=(",", ":")` und abschließendem Newline serialisiert. Der Flächenhash ist SHA-256 dieser Bytes und wird als `sha256:<hex>` gespeichert.

## 8. Application-Revision

`application_revision` folgt `git-tree:<oid>` und bezeichnet den Tree genau eines Application-Verzeichnisses. Der Validator verwendet ausschließlich lokale Git-Objekte.

Der Tree muss:

1. als Git-Objekttyp `tree` existieren;
2. als `applications/<application-slug>/` in mindestens einem über lokale Refs erreichbaren Commit vorkommen;
3. ohne Symlink als vollständige Application lesbar sein;
4. genau einen gültigen Hauptprozess enthalten.

Der Validator liest den historischen Tree in ein temporäres Verzeichnis und entfernt dieses nach der Prüfung. Er verändert Repository und Workspace nicht. Ein nicht erreichbarer, falscher oder unlesbarer Tree schlägt geschlossen fehl.

Eine Revision bleibt während eines Vorgangs unverändert. Neue Application-Fassungen steuern neue Vorgänge. Ein fachlicher Neustart erhält eine neue Vorgangs-ID.

## 9. Initialisierung und Validierung

`init_workspace` erzeugt den Zielbaum atomar über ein benachbartes Staging-Verzeichnis. Ein vorhandenes Ziel bleibt unverändert. Das Root-`CONTEXT.md` enthält ausschließlich `type: workspace` im Frontmatter und als Body den Betriebsvertrag für Mensch und Harness (V0.3, Abschnitt 3.3).

`validate` liest `type` aus Root-`CONTEXT.md`:

- `workspace`: prüft Router, jede direkte Application und jeden Vorgang;
- `application`: prüft genau diese Application;
- anderer oder fehlender Typ: Fehler.

Validierung schreibt keine Datei. Unbekannte kundenfachliche Flächen bleiben unberührt.

## 10. Stabile Fehlerklassen

| Code | Beobachtbarer Fehler |
|---|---|
| `routing.missing` | erforderliche `CONTEXT.md` oder Arbeitsanweisung fehlt |
| `routing.type` | Frontmatter oder Root-Typ fehlt beziehungsweise ist falsch |
| `format.invalid` | YAML, Frontmatter, JSON oder UTF-8 ist ungültig |
| `structure.symlink` | gelesene Core-Fläche enthält einen Symlink |
| `structure.invalid` | Ordnername, Kindanzahl oder Versuchsbaum ist ungültig |
| `schema.invalid` | eines der fünf Schemas wird verletzt |
| `reference.duplicate` | Arbeitsschritt-ID oder Versuch ist im geltenden Scope doppelt |
| `reference.unresolved` | Einstieg, Route oder Laufpfad-Schritt löst nicht auf |
| `process.unreachable` | Arbeitsschritt ist vom Einstieg unerreichbar |
| `process.no_end` | Arbeitsschritt besitzt keinen erreichbaren Endzustand |
| `process.gate` | Gate und Routen widersprechen sich |
| `revision.invalid` | Git-Tree ist falsch, unerreichbar oder keine Application |
| `run.invalid` | Laufpfad, Zustand, Reihenfolge oder Ordner weicht ab |
| `hash.mismatch` | deklarierte Fläche fehlt oder Digest weicht ab |
| `trust.invalid` | Human Gate besitzt keinen gültigen Freigabebeweis |

CLI liefert Exit 0 bei gültigem Vertrag und Exit 1 bei mindestens einem Issue.

## 11. Migration

Die Umsetzung ersetzt die bisherige Workspace-Topologie und ihre Spiegelverträge. Entfernt werden:

- `00_charter/`;
- Paketaktivierungs- und Wiedervorlage-Schema;
- Paketaktivierung, Datenautorität, Process-Delta, Snapshots, Receipts, Freigabeordner und Ansichten als Core-Pflichten;
- eigene Leistung-Datei und reziproke Elternreferenzen;
- Hauptprozess-Knotensatz;
- `--customer`, `validate_workspace`, `validate_application` und `generate_workspace` als öffentliche Interfaces;
- historische Tests ohne verbleibenden Interface-Fehler.

README, Root-Router, Protokollrouter und Invarianten zeigen anschließend ausschließlich auf diesen Vertrag. Ältere Specs bleiben als `superseded` historische Evidenz oder verlassen aktive Router.

## 12. Abnahme

Umsetzung ist vollständig, wenn Mutationstests jeden Fehler aus Abschnitt 10 am öffentlichen Interface rot zeigen, das Init-Ergebnis exakt drei Flächen besitzt, fünf Schemas verbleiben, Validierung read-only bleibt und installierte CLI aus fremdem Arbeitsverzeichnis funktioniert, und wenn der Cold Walk einen synthetischen Vorgang mit Schleife, Wartezustand und Human Gate durchläuft, eine Eingangsmutation als `hash.mismatch` erkennt und die Application in ein zweites Repository mit gleichem Tree-OID überträgt (V0.3, Abschnitte 3.4 und 3.5).

Zielbudget:

```text
root_dirs: 5
protocol_schemas: 5
max_total_required_fields_per_schema: 15
```

Eine Verringerung braucht keine Budgetfreigabe. Eine spätere Erhöhung verlangt menschliche Attribution gemäß `AGENTS.md`.
