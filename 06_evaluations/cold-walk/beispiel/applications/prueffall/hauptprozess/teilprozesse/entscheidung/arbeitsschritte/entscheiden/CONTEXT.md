---
type: arbeitsschritt
id: arbeitsschritt:entscheiden
eingaben:
  - input/pruefbericht.md
ausgaben:
  - output/entscheidung.md
pruefung: Entscheidung nennt Prüfbericht und Begründung
gate: human
routen:
  freigegeben: end:entschieden
  abgelehnt: arbeitsschritt:pruefen
customer_touchpoint: sacred
---

# Entscheiden

## Ein Job

Aus dem bestandenen Prüfbericht eine Entscheidungsvorlage erzeugen, die ein Mensch freigibt oder ablehnt.

## Eingaben

`input/pruefbericht.md`.

## Nicht laden

Nachforderungen; sie sind im Bericht aufgegangen.

## Verarbeitung

1. Vorlage mit Bezug auf jeden Befund formulieren.
2. Begründung ausformulieren.
3. Am Gate stoppen.

## Ausgaben

`output/entscheidung.md`.

## Prüfung

Die Vorlage nennt den Prüfbericht und eine Begründung.

## Human Check

Der Mensch liest Vorlage und Bericht und schreibt `freigabe` in den Laufpfad. `freigegeben` beendet den Vorgang. `abgelehnt` führt zurück zur Prüfung.
