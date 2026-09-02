---
status: user-confirmed
review_state: implemented
evidence_status: verified
normative: true
date: 2026-09-02
extends: docs/superpowers/specs/2026-08-30-minimal-core-design.md
verified:
  by: human:melvin
  at: 2026-09-02
  source: conversation decision of 2026-09-02, recorded by the agent; attribution documents, it does not authenticate
---

# Ausführbarer IMPACTS-Core V0.3

## 1. Befund

Gemessen am Release `v0.2.0` (`1a0cf9c`) am 2026-09-02:

- `verified`: Der Validator deckt Spec §4 bis §10 vollständig ab. 760 LOC, 55 Tests.
- `verified`: `impacts init` schreibt drei Flächen und zwei Sätze. Der Cold Walk erzeugt eine leere Vorlage und prüft, dass sie leer ist.
- `verified`: Kein Beispiel liegt im Produkt. Die einzige Application steht in `tests/support.py`.
- `verified`: Die Methode (`02_protocol/impacts-method.md`, 53 Zeilen) sagt, welcher Kontext in welchem Body steht. Keine Vorlage trägt ihn. Der Validator akzeptiert leere Bodies für Application, Hauptprozess und Teilprozess und ein Zeichen für den Arbeitsschritt.
- `verified`: `_surface_hash` ist privat. Die Tests kopieren die Funktion. Jedes Harness müsste §7 byteweise nachbauen.
- `verified`: Ein Harness, das in einen initialisierten Workspace kommt, findet keine Betriebsregel. Die Regeln stehen in der privaten Synthese (§6, §14).

Drei Zusagen der freigegebenen Synthese vom 2026-08-30 sind damit offen: P1 "neuer Operator kann Application in einer Sitzung entwerfen", §14 "Das Harness pflegt Versuchsverzeichnisse sowie Eingabe- und Ausgabehashes", §16 Nr. 11 "synthetischen Vorgang mit Schleife, Human Gate und Customer-Touchpoint prüfen".

## 2. Grenze

Unverändert bleiben: fünf Schemas, Budget `5/5/15`, keine Capability-Bindung (D-10), `init` erzeugt nur das Skelett (D-04), Validierung schreibt keine Datei. Der Core führt keinen Arbeitsschritt aus. Kein neues Schema, kein Pflichtfeld, keine Laufzeit.

Die Lücke ist Anwendungsfläche. Sie besteht aus Dateien in vorhandenen Ordnern und zwei lesenden Befehlen.

## 3. Sechs Ergänzungen

### 3.1 Öffentliche Hash-Rechnung

```text
impacts hash VERSUCHSORDNER FLAECHE [FLAECHE ...]
```

Gibt `sha256:<hex>` nach §7 aus und endet mit 0. Eine fehlende, leere, verlinkte oder ausbrechende Fläche endet mit 1 und einer Meldung. Die Python-API erhält `surface_hash(attempt_root, declared) -> str`; sie wirft `HashSurfaceError` mit `code`, `path` und `message`. Der Validator ruft dieselbe Funktion. Es gibt genau eine Rechnung.

### 3.2 Vorlagen

```text
impacts template ART
```

`ART` ist `application`, `hauptprozess`, `teilprozess`, `arbeitsschritt` oder `vorgang`. Quelle ist `02_protocol/templates/<art>.md`, paketiert wie die Schemas. Die Frontmatter jeder Vorlage nennt genau die Felder ihres Schemas. Der Body trägt die Methode aus `impacts-method.md`, "Where the context lives":

| Vorlage | Body-Abschnitte |
|---|---|
| application | Markttopologie, Wertfluss, Zielgröße und Guardrails, Touchpoints, Automationsgrenze |
| hauptprozess | Weg zur Leistung, Durchsatz und Durchlaufzeit, Engpass |
| teilprozess | Beitrag zur Leistung, Frühindikator |
| arbeitsschritt | Ein Job, Eingaben, Nicht laden, Verarbeitung, Ausgaben, Prüfung, Human Check |
| vorgang | Betreff, Stand |

Der Validator prüft die Body-Struktur nicht. Er bleibt bei Nichtleere für den Arbeitsschritt.

### 3.3 Betriebsvertrag im Workspace-Router

`init` schreibt in den Body der Root-`CONTEXT.md` den Betriebsvertrag für Mensch und Harness:

1. Workspace-Root ist Git-Root. Vorgänge binden nur committete Application-Trees.
2. Application entwerfen: `impacts template`, Dateien nur `CONTEXT.md`, committen, `git rev-parse HEAD:applications/<slug>`.
3. Vorgang öffnen: `vorgaenge/<slug>/CONTEXT.md` mit `application_revision`, erster Laufpfadeintrag am Einstieg, Versuch `001`, Eingaben nach `input/`, `impacts hash`.
4. Versuch abschließen: Ausgaben nach `output/`, `impacts hash`, `gewaehlte_route`, nächster Eintrag.
5. Human Gate: der Eintrag bleibt `aktiv`. Nur der benannte Mensch schreibt `freigabe`. Kein Agent schreibt `human:<id>`.
6. Warten: `wartend` mit `wiedereinstieg`. Fortsetzung durch eine Route.
7. `impacts validate .` vor jedem Commit. Exit 1 blockiert.
8. Der Core führt nichts aus. Capabilities sind Abhängigkeiten des Kunden-Repos.

Frontmatter bleibt `type: workspace`. Spec §9 ändert sich von "kurze menschliche Erklärung" zu "Betriebsvertrag".

### 3.4 Cold Walk als Beispiel

`06_evaluations/cold-walk/beispiel/applications/prueffall/` hält eine synthetische Application:

```text
hauptprozess:prueffall            einstieg: arbeitsschritt:pruefen
├── teilprozess:vorpruefung
│   ├── arbeitsschritt:pruefen        routen: bestanden -> entscheiden, klaerung -> nachfordern
│   └── arbeitsschritt:nachfordern    routen: nachgereicht -> pruefen   (Schleife, touchpoint standard)
└── teilprozess:entscheidung
    └── arbeitsschritt:entscheiden    gate: human, touchpoint sacred
                                      routen: freigegeben -> end:entschieden, abgelehnt -> pruefen
```

`check.py` baut daraus in einem temporären Git-Repository einen Workspace, committet die Application, bindet den Vorgang `prueffall-001` und führt ihn mit der öffentlichen API durch diese Zustände:

| Schritt | Zustand | Erwartung |
|---|---|---|
| pruefen 001 | `aktiv` | valid |
| nachfordern 001 | `aktiv` nach Route `klaerung` | valid |
| nachfordern 001 | `wartend`, `wiedereinstieg` | valid |
| pruefen 002 | `aktiv` nach Route `nachgereicht` (Schleife) | valid |
| entscheiden 001 | `aktiv` nach Route `bestanden`, Human Gate | valid, Walk stoppt |
| entscheiden 001 | synthetische `freigabe` durch `human:beispiel-pruefer`, Route `freigegeben` | valid, Vorgang endet |
| Mutation | ein Byte in `pruefen/001/input` geändert | `hash.mismatch` |

`verified` am Validator: Ein abgeschlossener Eintrag, dessen Route auf einen Arbeitsschritt zeigt, braucht den Folgeeintrag im selben Schreibvorgang (`run.invalid: Next Laufpfad entry must follow selected route`). Abschluss und Öffnung des Nachfolgers sind ein Schritt des Harness.

Der Walk druckt die Routerkette, jeden Zustand und das Mutationsergebnis. Exit 0 nur, wenn jede Erwartung zutrifft. Spec §12 nennt diesen Walk als Abnahme.

### 3.5 Transport zwischen Repositories

Eine Application wandert als Byte-Kopie von `applications/<slug>/` (`git archive | tar -x`), committet mit Quellcommit und Tree-OID in der Commit-Nachricht. Der Tree-OID ist inhaltsadressiert; `git rev-parse HEAD:applications/<slug>` liefert auf beiden Seiten denselben Wert, das ist der Herkunftsbeweis. Herkunftsangaben stehen nie im Tree. Die Regel steht unter Scale in `impacts-method.md` und in Regel 2 des Betriebsvertrags; der Cold Walk beweist sie mit einem zweiten Repository.

### 3.6 Architect-Skill

`02_protocol/impacts-architect/` hält die Methode als ausführbare Prozedur für ein Agenten-Harness: `SKILL.md` mit Build-Modus (Identify bis Scale als Schritte mit Interviewfragen), Restructure-Modus (sechs Dateirollen mit Zuhause, Referenzprüfung, Migrationskarte, copy-verify-remove) und Import-Modus, `references/zuschnitt.md` mit den Schnittregeln je Objekt und der Automationsgrenze, `templates/ist-prozess.md` als Erfassungsbogen für beobachtete Prozesse. Kein Schema, kein Pflichtfeld, kein Root-Ordner. Installation durch Kopie nach `.claude/skills/`.

## 4. Öffentliche Oberfläche V0.3

```text
impacts init PATH
impacts validate ROOT
impacts hash VERSUCHSORDNER FLAECHE...
impacts template ART
```

```python
init_workspace(path) -> Path
validate(root) -> ValidationReport
surface_hash(attempt_root, declared) -> str
```

Version `0.3.0`. Budget unverändert.

## 5. Abnahme

- Vorlagen-Frontmatter entspricht den Schema-Properties (Test).
- `impacts hash` liefert denselben Digest, den der Validator nachrechnet (Test).
- `init`-Body nennt `template`, `hash`, `validate` und die Gate-Regel (Test).
- Cold Walk durchläuft die sieben Zustände, importiert die Application in ein zweites Repository mit gleichem OID (Test) und endet mit 0.
- Skill-Tests: Frontmatter, drei Modi, Phasenreihenfolge, Core-Befehle, auflösbare Links, Erfassungsbogen.
- Installiertes Paket führt alle vier Befehle aus fremdem Arbeitsverzeichnis aus (Test).
- `python3 06_evaluations/complexity-budget/check.py` Exit 0.

## 6. Geänderte Sätze der V1-Spec

Diese Ergänzung ändert drei Sätze in `2026-08-30-minimal-core-design.md`: §1 (zwei lesende Befehle), §9 (Body des Root-Routers), §12 (Cold Walk). Die Sätze sind dort eingearbeitet; das Frontmatter der V1-Spec nennt diese Ergänzung als `amended_by`. Die Attribution `human:melvin` vom 2026-09-02 stammt aus der Gesprächsentscheidung und wurde vom Agenten eingetragen.
