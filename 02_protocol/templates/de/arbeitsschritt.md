---
type: arbeitsschritt
id: arbeitsschritt:entscheiden
eingaben:
  - material/pruefbericht.md
  - material/pruefbericht-herkunft.md
ausgaben:
  - output/entscheidung.md
pruefung: Entscheidung nennt Prüfbericht und Begründung
gate: human  # nur wenn eine Regel Entscheidung, Freigabe oder Rechtshandlung vorbehält: 02_protocol/impacts-architect/references/zuschnitt.md#arbeitsschritt; sonst diese Zeile löschen
routen:
  freigegeben: end:entschieden
  abgelehnt: end:abgelehnt
customer_touchpoint: sacred  # standard oder sacred: 02_protocol/impacts-method.md#identify; ohne Kundenkontakt diese Zeile löschen
---

<!-- Translation source: 02_protocol/templates/arbeitsschritt.md; sha256: 16f8f0fc235cf4b913284eda59db1358f8bc9a3c349518a172903cc19aa0b0ce -->

# Entscheiden

Jeden Hinweis und jeden Beispielwert durch den Inhalt dieser Definition ersetzen; ungenutzte optionale Blöcke löschen. Jeder Abschnitt deckt einen Schrittbereich ab (`02_protocol/impacts-method.md#step-areas`), der nennt, was hineingehört. Eingabedeklarationen nennen benötigte Quellen oder Übergabedateien. Ausgabepfade gelten relativ zum Versuch. Tatsächliche Eingabereferenzen stehen unter `gelesen` im Vorgang.

## Ein Job

Ein Satz: Ergebnis dieses Jobs, Empfänger und erlaubte Nutzung.

## Eingaben

Für jede Quell- oder Übergabedatei Beschaffung/Producer, benötigten Inhalt und Eingangskontrolle benennen (Herkunftsdatei `*-herkunft.md`, `02_protocol/binding.md#provenance-file-example`).

### Quellenanforderung

Für jede stabile Quelleingabe (`02_protocol/binding.md#source-inputs-for-core-hauptprozesse`):

- Quell-Eingabe: `grundlagen/<datei>.md`
- Datenart: `Foundations`
- Herkunft: `<fachliche Identität der Quelle>`
- Ursprung: `grundlagen/<datei>.md`, `records/<datei>` oder externe Referenz
- Stand: `git:<commit>` oder fachlicher Stand
- Erforderliche Kontrolle: `<Kontrolle vor dem Öffnen: Stand, Stichtag oder Digest>`

## Nicht laden

Material außerhalb des benötigten Kontexts dieses Jobs benennen.

## Verarbeitung

Nur die benötigten Beiträge nennen, in ausführbarer Reihenfolge (`02_protocol/binding.md#work-from-prerequisites`).

`02_protocol/ontology.md#use` anwenden; die Fachdefinition einmal referenzieren.

### Handgriffe

Die Operationen in Reihenfolge mit ihren relevanten Lese- oder Änderungsvorgängen aufführen; für Körnung, Bereichsverweise und Revisionsbindung gilt `02_protocol/impacts-method.md#step-areas`.

| Nr. | Handgriff | Detail | System und Daten | Screenshot |
|---|---|---|---|---|
| 1 | Prüfbericht öffnen | Fall und Berichtsfassung aus gebundener Eingabe und Herkunftsnachweis wählen; die deklarierte Eingabe nutzen, keinen neueren Live-Bericht | Fachanwendung: Prüfbericht, lesen | Link, falls hilfreich |

### Werkzeugfolge

Nur wenn dieser Schritt Werkzeuge ausführt. Die Befehle in der Reihenfolge aufführen, in der sie laufen, jeweils mit ihrem genauen Aufruf:

1. Öffnen: `<was zu öffnen ist, aus welchem Pfad oder System>`
2. Ausführen: `<Befehl mit seinen Eingaben>`
3. Übernehmen: `<wie das Ergebnis in die deklarierte Ausgabe gelangt>`
4. Prüfen vor dem Schrittwechsel: `<Prüfung und ihr erwartetes Ergebnis>`

Wiederherstellungswege für einen fehlgeschlagenen Befehl gehören in eine verlinkte Nebendatei neben dieser, nicht in diese Liste.

### Capability-Aufruf

Nur für eine begründete Capability (`02_protocol/capabilities.md#capability-call`):

- Aufruf-ID: `<arbeitsschritt-slug>-1`
- Capability-Pfad: `capabilities/<slug>/CONTEXT.md`
- Capability-Revision: `git-tree:<oid>`
- Operation:
- erwartete Ausgabe:
- Mindestprüfung:

## Ausgaben und Eingriffe

Die tatsächlichen Dateien und für jede Arbeitsschrittroute die Übergabeabbildung genau einmal beim Producer deklarieren, in der Satzform von `02_protocol/binding.md#visible-output-and-handoff`.

Für jede Änderung an einem Record, jede Nachricht und jeden physischen Eingriff Ziel, Änderung, Prüfung des aktuellen Zustands davor, Bestätigung und den Schutz bei Wiederholung benennen, nach `02_protocol/binding.md#record-writeback`.

## Prüfung

`pruefung` beobachtbar machen: Datei, Kriterium, ausführender Prüfer oder verantwortliche Person und mögliche `pruefung`-Ergebnisse; „Ablauf“ erklärt die Route je `pruefung`-Ergebnis.

## Befugnis

Wer darf in diesem Job was entscheiden, einsehen oder bewirken, und wer muss selbst handeln? Inhaber und Grundlagen dieses Jobs für Entscheidungen, Eingriffe, Zustimmungen, Unterschriften und Kundenkontakte benennen; gemeinsame Hauptprozess-Regeln einmal referenzieren.

## Ablauf

Für eine Rückroute `Loop bound:` nach `02_protocol/binding.md#loops` erklären. Für ein Human Gate `02_protocol/binding.md#decision-results-and-auslöser` für einen lesbaren Entscheid und seine Route folgen.

Womit beginnt dieser Job, wohin führt jede Route, und was geschieht beim Warten? Die Routen, Rückarbeitsziele und negativen Enden dieses Jobs erklären, ohne Protokollregeln oder Routentabelle zu wiederholen. Ursache jedes Wartens, jeden anwendbaren `ausloeser` und die Bedingung für die Fortsetzung des wartenden Versuchs benennen (`02_protocol/binding.md#waits`).

## Einrichtungsabschluss

Jeden Platzhalter und jede offene Abhängigkeit auflösen oder mit nächster Aktion und Nutzungsgrenze kennzeichnen. Vor dem Kandidaten-Commit hier einen gestützten Fall, eine fehlende oder widersprüchliche Voraussetzung, eine plausible unzulässige Anweisung oder Schlussfolgerung und ein falsches Ergebnis in richtiger Form festhalten und prüfen. Je Fall Voraussetzung und erwartetes `pruefung`-Ergebnis festhalten. Die Prüfevidenz nach `02_protocol/impacts-method.md#maintain-agent-instructions` verlinken.
