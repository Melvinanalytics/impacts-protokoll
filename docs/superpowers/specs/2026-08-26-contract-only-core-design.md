---
status: user-confirmed
review_state: implemented-on-design-branch
date: 2026-08-26
---

# IMPACTS contract-only core

## Zweck

IMPACTS beschreibt eine file-native Arbeitsarchitektur. Menschen und Agenten lesen dieselben Dateien. Git trägt Versionen und Übergaben. Ein Agent-Harness übernimmt die Ausführung.

Der Core veröffentlicht Begriffe, Ordnerkonventionen, Schemas, eine leere Workspace-Vorlage und read-only Prüfungen. Fachwissen, Fallwissen, Prozesse und Werkzeuge bleiben eigenständige Pakete.

## Architektur

| Ebene | Autorität |
| --- | --- |
| Core | Dateivertrag, Hierarchie, Schemas und Prüfregeln |
| Application | benannter Prozess mit Hauptprozess, Teilprozessen und Arbeitsschritten |
| Expertise | geltende Methoden, Quellen und fachliche Grenzen |
| Experience | nachvollziehbare Referenzfälle und Ergebnisse |
| Capability | Werkzeuge, Berechnungen und fachliche Prüfer |
| Kunden-Workspace | kundeneigene Grundlagen, Records, Vorgänge und Entscheidungen |
| Harness | LLM, Shell, Filesystem und optionaler Heartbeat |

Branchenprofile bestehen aus einer Aktivierungsliste dieser Paketrollen. Eine eigene Branchen-Repositoryklasse entsteht erst nach drei realen Konsumenten mit derselben Komposition.

## File-Graph

Der Arbeitsgraph entsteht direkt aus Dateien:

| Graphbegriff | Dateivertrag |
| --- | --- |
| Knoten | eine Markdown-, YAML- oder JSON-Datei |
| Identität | eine stabile ID |
| Kante | eine Referenz oder ein Wikilink |
| Typ | Frontmatter oder ein typisiertes Schemafeld |
| Kontext | der umgebende Ordner und dessen `CONTEXT.md` |

Obsidian, Canvas, Graphviz und Neo4j dürfen denselben Graphen als abgeleitete Ansicht darstellen. Solche Darstellungen liegen unter `99_ansichten/` und tragen keine Schreibautorität. Dieser Core-Vertrag entscheidet nicht, ob eine aktivierte Capability außerhalb des file-nativen Workspace zusätzlich eine wiederaufbaubare Graph-Intelligence-Projektion betreibt. Die nichtnormative [Forschungs- und Diskussionsgrundlage](../../research/2026-08-29-graph-intelligence-layer.md) beschreibt dafür Grenzen und Entscheidungskriterien.

Jeder autoritative Application-Router heißt `CONTEXT.md` und trägt ein nichtleeres `type` im Frontmatter. Diese Pflicht gilt für den Paket-Root sowie die Ordner von Leistung, Hauptprozess, Teilprozess und Arbeitsschritt.

YAML-, JSON- und Markdown-Ansichten tragen `generated` und `generated_from` direkt. Andere Formate verwenden die benachbarte Datei `<dateiname>.provenance.yaml`. Damit bleiben auch Canvas-, DOT-, SVG-, PNG- und CSV-Ergebnisse prüfbar.

## ICM-Zuordnung

Eine Application hält die wiederverwendbare Factory. Jeder Arbeitsschritt beschreibt Inputs, Bearbeitung, Outputs, Prüfung und Gate. Das Harness lädt nur den aktiven Arbeitsschritt sowie dessen deklarierte Referenzen.

Ein `Vorgang` ist ein vollständiger konkreter Lauf genau eines Hauptprozesses. Seine Dateien bilden ICM Layer 4. Änderungen eines einzelnen Vorgangs verändern keine wiederverwendbare Application.

Unternehmenswissen besteht aus stabilen Nomen und benannten Verben über Workspaces hinweg. `02_grundlagen/` enthält kundeneigene Grundlagen. Der Ordner bezeichnet weder das gesamte Second Brain noch eine fachrechtliche Grundlage nach ImmoWertV. `03_records/` enthält konkrete Instanzen.

## Core-Repository

```text
impacts-protokoll/
├── README.md
├── CONTEXT.md
├── AGENTS.md
├── 02_protocol/
│   ├── CONTEXT.md
│   ├── invariants/
│   └── schemas/
├── src/impacts_protocol/
│   ├── cli.py
│   ├── generator.py
│   ├── io.py
│   ├── model.py
│   └── validator.py
├── 06_evaluations/
└── docs/
```

Die CLI besitzt zwei Befehle:

```text
impacts init
impacts validate
```

`init` stempelt die leere Ordnerstruktur. `validate` liest Dateien und meldet Vertragsverletzungen. Der Core besitzt keine fachliche Paketimplementierung.

## Kunden-Workspace

```text
customer-workspace/
├── CONTEXT.md
├── 00_steuerung/
│   └── paketaktivierungen.yaml
├── 01_prozesse/
│   └── <application-id>/
│       ├── provenance.yaml
│       └── delta.yaml
├── 02_grundlagen/
│   └── datenautoritaet.yaml
├── 03_records/                         nur bei lokaler Record-Autorität
├── 04_aktive-verbesserung/
├── 05_aenderungsnachweise/
├── 06_vorgaenge/
│   └── <vorgang-id>/
│       ├── vorgang.yaml
│       ├── snapshot/
│       ├── receipts/
│       └── freigaben/
└── 99_ansichten/
```

`01_prozesse/<application-id>/provenance.yaml` bindet genau eine aktive Paketaktivierung mit derselben `id` und `version`. Der Ordnername ist der Teil hinter `application:`. `delta.yaml` enthält ausschließlich skalare Änderungen als `{path, value}`. Jeder `path` ist ein absoluter Pfad innerhalb des Application-Vertrags. Listen, Abbildungen und vollständige Prozessbäume sind als Werte unzulässig. Der vollständige Hauptprozessbaum bleibt im Application-Paket.

`datenautoritaet.yaml` wird immer angelegt. Jeder Schlüssel unter `records` bezeichnet einen Record-Typ. Ein lokaler Record darf nur existieren, wenn sein `type` auf eine lokale Autorität zeigt. Der Schlüssel `default` gilt nur als Rückfall für nicht einzeln benannte Typen. Bei rein externer Autorität entfällt der lokale Record-Ordner. Records sind Instanzen. Vorgänge bleiben konkrete Läufe.

Dateien unter `receipts/` folgen dem Vertrag der aktivierten Capability. Der Core besitzt dafür kein Evidence-Schema. Er liest aus jeder YAML- oder JSON-Abbildung nur die stabile `id`. Diese ID ist innerhalb eines Vorgangs eindeutig. Jede `receipt_ref` in `vorgang.yaml` muss auf genau eine solche Datei im selben Vorgang zeigen. `06_vorgaenge/<vorgang-id>/vorgang.yaml` trägt entsprechend `id: vorgang:<vorgang-id>`. Eine Wiedervorlage bindet ihren Vorgang, dessen `run_id`, dessen Receipt-Referenzen und eine externe Continuation-ID. Der Application-Baum bleibt im Paket.

## Paketvertrag

Ein Paket darf ein statisches `pack.json` besitzen. Der minimale Inhalt umfasst `id`, `version`, `rolle`, `entrypoint` und `hash`. Git transportiert das Paket. Das Harness checkt die gebundene Version aus und liest den Einstiegspunkt.

Der Core prüft Aktivierungsmetadaten und doppelte Paket-IDs. Paketcode, Pakettransport und fachliche Paketprüfung bleiben bei Paket und Harness.

## Validator

Die Prüfung ist read-only. Sie deckt folgende Oberflächen ab:

- kanonische Ordner, Router, Frontmatter und strikte JSON-Dateien
- stabile IDs und auflösbare Referenzen
- Hierarchie `Leistung 1:1 Hauptprozess → Teilprozess 1:n → Arbeitsschritt 1:n`
- vorhandene JSON-Schemas
- genau eine Paketaktivierungsdatei
- zulässige Record-Autorität
- Herkunft abgeleiteter Ansichten
- ausschließliche Process-Bindings aus `provenance.yaml` und `delta.yaml`
- vollständige Prozesspfade und die Hierarchie `1:n` über die öffentliche Python-Funktion `validate_application`

Der Customer-Validator weist eingebettete `Leistung`-, `Hauptprozess`-, `Teilprozess`- und `Arbeitsschritt`-Dateien ab. `validate_application` prüft ausgecheckte Application-Pakete statisch. Eine Application braucht mindestens eine Leistung und einen Hauptprozess. Jeder Hauptprozess braucht mindestens einen Teilprozess. Jeder Teilprozess braucht mindestens einen Arbeitsschritt. Daraus entsteht kein weiterer CLI-Befehl.

Eine Prüfung schreibt keine Workspace-Datei.

## Initialisierung

Ein neuer Workspace enthält genau diese Dateien:

```text
CONTEXT.md
00_steuerung/paketaktivierungen.yaml
02_grundlagen/datenautoritaet.yaml
```

Die acht Workspace-Ordner werden leer angelegt. `03_records/` ist im Ausgangsprofil vorhanden, weil `datenautoritaet.yaml` mit lokaler Datei-Autorität startet. `01_prozesse/`, `05_aenderungsnachweise/`, `06_vorgaenge/` und `99_ansichten/` enthalten nach `init` keine Artefakte.

## Einfachheitsgrenzen

Das Core-Budget bleibt:

```text
root_dirs: 6
protocol_schemas: 9
max_total_required_fields_per_schema: 21
```

Dieses Vorhaben ergänzt kein Schema. Zusätzliche Ausführungslogik gehört in Capability oder Harness. Ein neuer Core-Begriff braucht einen bestehenden Verbraucher und einen klaren Dateipfad.

Die Grenzen bleiben `6/9/21`. Der vereinfachte Core nutzt sieben Protokollschemas; neun bleiben die Obergrenze.

## Nachweis

Der Vertrag gilt als umgesetzt, wenn:

- `impacts init` nur die leere Vorlage erzeugt
- `impacts validate` den Workspace unverändert lässt
- der Generator keinen Hauptprozessbaum und keinen Vorgang anlegt
- die Paketaktivierung keine Paketbytes einbettet
- das Komplexitätsbudget unverändert besteht
- der Cold Walk nur Ordner und Vertragsdateien prüft
