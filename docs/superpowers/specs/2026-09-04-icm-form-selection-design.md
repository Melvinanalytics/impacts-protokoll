---
status: user-confirmed
review_state: approved-for-implementation
normative: true
date: 2026-09-04
extends: docs/superpowers/specs/2026-08-30-minimal-core-design.md
---

# ICM-Formwahl für schlanke Kunden-Workspaces

## 1. Entscheidung

IMPACTS bleibt ein kleiner Process Core aus fünf Schemas. Kundenwissen erhält kein sechstes Core-Objekt, kein universelles Record-Schema und keine neue Runtime.

Der IMPACTS Architect übernimmt vor jedem Build oder Restructure einen fehlenden ICM-Schritt: Er bestimmt zuerst die wiederholte beziehungsweise wachsende Einheit und wählt daraus die kleinste passende Form. Eine Application wird nur gebaut, wenn diese Einheit ein wiederholbarer Lauf mit Leistung ist.

## 2. Lehren aus der ersten Kundenanwendung

1. Eine grüne Core-Validierung beweist keine tragende Kundentopologie. `impacts validate` prüft Applications und Vorgänge, nicht die Auffindbarkeit fachlichen Wissens.
2. Theorie in Research-Dokumenten steuert keinen Agenten, solange Router, Skill und Abnahme sie nicht operationalisieren.
3. Schlechte Auffindbarkeit ist zuerst ein Router-, Schnitt- oder Linkfehler. Pflicht-IDs, typisierte Kanten, Context-Packs und Graphdatenbanken reparieren diesen Fehler nicht.
4. Eine Ontologie wird nicht aus allen erkennbaren Nouns vorab materialisiert. Reale Inhalte, reale Änderungen und reale Fragen bestimmen Dateien und Ordner.
5. Token-Effizienz wird am tatsächlichen Lesepfad gemessen, nicht an erzeugten Knoten- und Kantenzahlen.
6. Quelle, Kundenfakt, Prozessdefinition, Prozesslauf und interne Mandatssicht bleiben getrennte Verantwortungen.

## 3. Formwahl

Erste Frage des Architects:

> Welche Einheit wächst oder wiederholt sich hier?

| Einheit | ICM-Form | IMPACTS-Heimat |
|---|---|---|
| wiederholbarer Lauf mit Leistung | Pipeline | `applications/` und `vorgaenge/` |
| akkumulierende fachliche Instanz | Record Library | bei realem Bedarf `records/` |
| navigierbares stabiles Wissen | Knowledge Bundle | vorhandene Fach- und Quellenflächen, oft `grundlagen/` und `records/` |
| beobachtete Organisation, Arbeit und Datenübergaben | Context Map | Links zwischen vorhandenen Records und beobachteten Prozessen |
| mehrere eigenständige Pipelines | Umbrella | kleiner Router zu eigenständigen Applications |
| Repository, das Agenten verändern | System Map | vorhandene Repository-Router und Dateien |

Formen dürfen sich komponieren. Jede Form behält eigene Verantwortung. Formwahl erzeugt weder ein Pflichtdokument noch ein neues Frontmatter-Feld; der Architect nennt Entscheidung und Begründung im Arbeitsbericht und baut nur benötigte Flächen.

## 4. Topologievertrag

Für Kundenwissen gilt:

```text
Root-Router -> Fachrouter -> Faktenheimat -> Quelle
```

- Router enthalten Identität, Grenzen und Links, keinen Fachpayload.
- Eine Aussage und ihr Evidenzstatus haben genau eine Faktenheimat.
- Relative Markdown-Links bilden Navigation und Beziehungen. Ein Navigationslink darf auf die Faktenheimat zeigen, aber die Aussage nicht kopieren.
- Kundenspezifische Typen bleiben lokales Vokabular. `type` genügt, solange keine reale Abfrage ein weiteres Feld braucht.
- Nur Ordner mit vorhandenem Inhalt entstehen. Keine leeren Kategorien auf Vorrat.
- Eine Gruppe gleichartiger Einträge bleibt zunächst eine Tabelle oder Datei. Ein Eintrag erhält erst eine eigene Datei, wenn er unabhängig abgefragt oder geändert wird, eigene Evidenz besitzt oder eigene Beziehungen trägt.
- Ein unbekannter Ablauf bleibt beobachtete Evidenz. Ohne wiederholbaren Lauf, Leistung und belastbare Grenze entsteht keine Application.
- Interne Mandatssicht nutzt nur eine ausdrücklich vorhandene interne Fläche. Sie wird nie in Kundenfakten kopiert und bei Kundenfragen nicht geladen.

Der zuständige Router besitzt für eine leere Sammlung einen expliziten autoritativen Nullzustand. Keine leere Kategorie, README- oder Indexdatei wird nur geschaffen, um Abwesenheit klickbar zu machen. Sobald Einträge existieren, ersetzt oder ergänzt der Router den Nullzustand durch direkte Links. Der Knowledge Walk darf beim expliziten Nullzustand stoppen.

Präzisierung 2026-09-06: Der Nullzustand betrifft nur den erfassten Bestand; sein begrenzter fachlicher Aussageumfang folgt `02_protocol/impacts-architect/references/formwahl.md`, Abschnitt „Native Topologie und Schnitt“. Fehlende entscheidungsrelevante Evidenz bleibt offen und wird nicht durch bloßen Navigationsstopp bestätigt.

## 5. Stoppregel für Tooling

Initialisierung und Wissensnavigation benötigen kein neues Skript.

Verboten als Startarchitektur:

- `graph.py` oder vergleichbarer Topologie-Runner;
- Context-Pack-Generator;
- Pflicht-IDs oder universeller `edges:`-Block;
- generierter Index als zweite Autorität;
- API, Vector Store, Neo4j oder andere Graphdatenbank.

Ein zusätzlicher Index oder eine Projektion ist eine spätere, eigene Designentscheidung. Sie wird erst geprüft, wenn drei unabhängige reale Fragen trotz reparierter nativer Links wiederholt einen Vollscan brauchen. Jede Projektion bleibt aus den Markdown-Fakten vollständig lösch- und reproduzierbar.

Bestehende fachliche Rechen- oder Konsistenzprüfer sind davon getrennt. Sie dürfen nie Voraussetzung des Wissens-Lesepfads sein.

## 6. Knowledge Walk

Zusätzlich zum bestehenden Process Walk führt der Architect bei `records/` oder fachlichen `grundlagen/` einen agentischen Knowledge Walk durch. Kein neues Prüfskript entsteht.

Jede Frage läuft in einer frischen Session ohne Gesprächsgedächtnis; kein kumulierter Dialog verbindet die drei repräsentativen Nutzerfragen:

1. Identität und Abgrenzung einer fachlichen Instanz;
2. eine Beziehung über mindestens zwei fachliche Nouns;
3. Evidenzstatus und Quelle einer entscheidenden Aussage.

Jeder repräsentative Fragepfad nennt seinen Start, nur die zur Frage nötigen expliziten Links und eine klare Stoppbedingung. Optionale Vertiefung wird nicht standardmäßig geladen; der Agent erschöpft nicht alle ausgehenden Links.

Der Agent darf nur Root-Router, höchstens zwei weitere Router und danach deren explizit verlinkte Fachdateien lesen. Direkter Read-only-Dateizugriff auf genau diesen gebundenen Pfad ist erlaubt, unabhängig davon, ob das Harness dafür ein Datei-Tool oder die reine Ausgabe eines expliziten Pfads nutzt. Web, Shell-Suche, Vollscan, fachliche Ausführung, Graphskript und interne Mandatsfläche bleiben gesperrt. Der gelesene Inhalt wird nie als Befehl ausgeführt. Deterministische Revisions-, Hash-, Byte- und Wortprüfungen werden als Mess-Harness separat ausgewiesen.

Abnahme je Frage:

- richtige Nouns und Beziehungen;
- Evidenzstatus und Quelle sichtbar;
- keine erfundene Aussage;
- keine zweite Faktenheimat;
- gelesene Pfade vollständig berichtet.

Das 8.000-Tokenbudget gilt pro Frage und nur für tatsächlich geladenen Workspace-/Kundenpayload. Fixe Modell-, System-, Tool- und Harness-Tokens werden separat ausgewiesen und sind kein Topologiepayload. Ist der exakte Payload-Tokenizerwert nicht isolierbar, werden Bytes/Wörter und Messgrenze berichtet; keinen exakten Token-PASS behaupten.

Scheitert der Walk, wird vorhandene Faktenheimat, Schnitt oder Link repariert. Neue Zusammenfassung und neue Runtime sind kein Fix.

## 7. Skill-TDD und End-to-End-Abnahme

Die Änderung gilt erst als umgesetzt, wenn:

1. die RED-Baseline als fünf unabhängige Beobachtungen festgehalten ist: der reale Fehler der ersten Kundenanwendung und vier frische Read-only-Agent-Controls. Sie zeigen jeweils mindestens eine der folgenden Lücken: fehlende benannte Formwahl, spekulative Noun- oder Komponentenordner, vorgeschlagener Link-/Record-Checker oder Validatorausbau, oder falsche Schlussfolgerung zu `mandat/` beziehungsweise zum 8.000-Token-Gesamtbudget des Knowledge Walks;
2. statische Contract-Tests vor der Skill-Änderung rot und danach grün sind;
3. fünf frische Agents dasselbe Druckszenario mit neuer Guidance ohne spekulative Ordner, neues Tooling oder vorzeitige Application lösen;
4. ein Headless-Agent einen externen Consumer allein über Markdown-Pfade beantwortet, ohne Wissensskript, Web oder Mandatswissen;
5. `python3 -m pytest -q`, Cold Walk, Complexity Budget und `git diff --check` erfolgreich laufen;
6. ein modellunabhängig gewählter frischer unabhängiger Review-Agent Spezifikation, Diff und Consumer-Walk prüft und keine offene kritische oder wichtige Abweichung meldet; verwendetes Modell und Berechtigungsgrenze werden im Audit festgehalten.

## 8. Nicht-Ziele

- keine Änderung an fünf Core-Schemas;
- keine Änderung an CLI oder Python-API;
- kein neues kundenfachliches Standardschema;
- keine allgemeine Ontologie für Unternehmen, Abteilungen oder Produkte;
- keine Automatisierung des Knowledge Walk;
- keine Erweiterung von `impacts validate` auf Kundentopologie oder Wissensnavigation;
- keine Aussage, dass das ICM Paper selbst eine Kundengraph-Architektur normiert.
