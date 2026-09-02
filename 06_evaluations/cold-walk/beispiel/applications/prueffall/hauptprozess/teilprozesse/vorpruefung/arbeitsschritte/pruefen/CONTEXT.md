---
type: arbeitsschritt
id: arbeitsschritt:pruefen
eingaben:
  - input/antrag.md
ausgaben:
  - output/pruefbericht.md
pruefung: Prüfbericht nennt jede Pflichtangabe des Antrags mit Befund
routen:
  bestanden: arbeitsschritt:entscheiden
  klaerung: arbeitsschritt:nachfordern
---

# Prüfen

## Ein Job

Aus dem Antrag einen Prüfbericht erzeugen, der jede Pflichtangabe mit Befund nennt.

## Eingaben

`input/antrag.md`: der eingereichte Antrag, bei einer Wiederholung mit den nachgereichten Angaben.

## Nicht laden

Frühere Prüfberichte anderer Vorgänge.

## Verarbeitung

1. Pflichtangaben deterministisch gegen den Antrag prüfen.
2. Befund je Angabe festhalten.
3. Bericht formulieren.

## Ausgaben

`output/pruefbericht.md`.

## Prüfung

Fehlt eine Pflichtangabe, führt die Route `klaerung` zur Nachforderung. Sonst `bestanden`.

## Human Check

Kein Gate. Der Mensch liest den Bericht am nächsten Schritt.
