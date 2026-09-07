---
status: draft
review_state: ready-for-human-review
evidence_status: verified where marked
normative: true
date: 2026-09-07
extends: docs/superpowers/specs/2026-08-30-minimal-core-design.md
amends:
  - docs/superpowers/specs/2026-08-30-minimal-core-design.md
  - docs/superpowers/specs/2026-09-02-executable-core-design.md
source: decision by Melvin Voigtländer on 2026-09-07 (reported, recorded by the agent); attribution documents, it does not authenticate
---

# Fachlich benannter Application-Baum

## 1. Entscheidung

Die Rollen Hauptprozess, Teilprozess und Arbeitsschritt gehören in die Schablone. Im angewandten Baum tragen die Ordner die Namen des Prozesses und seiner Schritte; die Rolle jeder `CONTEXT.md` steht in ihrem `type`. Ein Kunde liest `applications/machbarkeitsstudie/angebot/ausschreibung-pruefen/CONTEXT.md`, nicht `applications/machbarkeitsstudie/hauptprozess/teilprozesse/angebot/arbeitsschritte/ausschreibung-pruefen/CONTEXT.md`.

Begründung: Die generischen Zwischenordner trugen keine Information, die nicht schon im `type` steht. Sie verdoppelten die Routerkette von vier auf sechs Dateien und machten den Baum für den Menschen unlesbar. Die Schablone bleibt der Ort, an dem man sieht, wo und wie eine Application aufgestellt sein muss.

## 2. Baum

```text
applications/<hauptprozess>/
├── CONTEXT.md                  # type: hauptprozess, id hauptprozess:<hauptprozess>
└── <teilprozess>/
    ├── CONTEXT.md              # type: teilprozess, id teilprozess:<teilprozess>
    └── <arbeitsschritt>/
        └── CONTEXT.md          # type: arbeitsschritt, id arbeitsschritt:<arbeitsschritt>

vorgaenge/<vorgang>/
├── CONTEXT.md                  # type: vorgang, id vorgang:<vorgang>
└── <arbeitsschritt>/<versuch>/
    ├── input/
    └── output/
```

Regeln, vom Validator geprüft:

1. Die Wurzel einer Application ist ihr Hauptprozess. Ein eigener Application-Router entfällt; die Identify-Abschnitte (Relevantes Umfeld, Wertfluss, Zielgröße und Guardrails, Touchpoints, Automationsgrenze) stehen im Body des Hauptprozesses vor Weg zur Leistung, Durchsatz und Engpass.
2. Jeder Unterordner der Wurzel ist ein Teilprozess, jeder Unterordner eines Teilprozesses ein Arbeitsschritt. Ein Arbeitsschritt hat keine Unterordner. Die Tiefe bestimmt die erwartete Rolle; `type` und `id` müssen ihr entsprechen, die ID ist `<type>:<ordnername>`.
3. Ordnernamen sind Slugs. Neben `CONTEXT.md` und Slug-Ordnern ist nichts erlaubt; ein Nicht-Slug-Ordner oder eine weitere Datei ist `structure.invalid`.
4. Jeder Hauptprozess hat mindestens einen Teilprozess, jeder Teilprozess mindestens einen Arbeitsschritt. Arbeitsschritt-IDs sind in der Application eindeutig. Graphregeln (Einstieg, Routen, Erreichbarkeit, Ende, Human Gate) bleiben unverändert.
5. Der Vorgang legt seine Versuchsordner direkt unter seiner Wurzel an: `<arbeitsschritt>/<versuch>/`. Der Sammelordner `arbeitsschritte/` entfällt. Ein Ordner neben `CONTEXT.md`, der kein Slug-Ordner ist, ist `run.invalid`.
6. Als Wurzel für `impacts validate` gilt ein Workspace (`type: workspace`) oder eine Application (`type: hauptprozess`). Andere Wurzeltypen sind `routing.type`.

## 3. Schablone

`impacts template application` liefert keine `CONTEXT.md` mehr, sondern die Schablone des Baums: die Ordnerform mit generischen Rollennamen, welche Vorlage in welche Datei gehört, die Regeln aus §2 und ein Beispiel. Die vier `CONTEXT.md`-Vorlagen (`hauptprozess`, `teilprozess`, `arbeitsschritt`, `vorgang`) bleiben; ihre Frontmatter nennt weiterhin genau die Schemafelder. Die Zahl der Vorlagen bleibt fünf, die Zahl der Schemas fünf, die Zahl der Kommandos vier.

## 4. Was sich nicht ändert

Schemas, IDs, Routen, Laufpfad, Hash-Flächen (§7 des V0.3-Entwurfs, relativ zum Versuchsordner), `application_revision: git-tree:<oid>`, der Transport per Byte-Kopie und der Betriebsvertrag in seiner Substanz. Ein Vorgang, der eine Application alter Form gebunden hat, bindet nach der Umstellung die neue Revision desselben Prozesses; die Schritt-IDs bleiben, nur der Tree-OID wechselt. Der Validator akzeptiert keine zwei Formen: eine Application hat genau eine Gestalt.

## 5. Nachweis

`verified` am 2026-09-07: 134 Tests, Cold Walk `PASS` mit der Routerkette `CONTEXT.md`, `applications/prueffall/CONTEXT.md`, `applications/prueffall/vorpruefung/CONTEXT.md`, `applications/prueffall/vorpruefung/pruefen/CONTEXT.md`; Komplexitätsbudget eingehalten (5/5/12 von 5/5/15). Das Beispiel `06_evaluations/cold-walk/beispiel/applications/prueffall/` zeigt die angewandte Form, die Schablone die generische.
