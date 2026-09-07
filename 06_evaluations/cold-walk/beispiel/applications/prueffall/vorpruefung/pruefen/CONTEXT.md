---
type: arbeitsschritt
id: arbeitsschritt:pruefen
eingaben:
  - input/antrag.md
  - input/pruefregeln.md
  - input/pruefregeln-herkunft.md
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

`input/pruefregeln.md`: materialisierter Snapshot. `input/pruefregeln-herkunft.md`: gebundener Herkunfts- und Kontrollnachweis.

## Nicht laden

Frühere Prüfberichte anderer Vorgänge.

## Verarbeitung

### Capability-Aufruf

- Aufruf-ID: `pruefen-1`
- Capability-Pfad: `capabilities/vollstaendigkeitsgrad/CONTEXT.md`
- Capability-Revision: `git-tree:{{CAPABILITY_TREE_OID}}`
- Operation: `vollstaendigkeitsgrad-berechnen`
- erwartete Ausgabe: `output/pruefbericht.md`
- Mindestprüfung: gebundene Rechenautorität, Source-Snapshot und sichtbarer Vollständigkeitsgrad

### Quellenanforderung

- Quell-Eingabe: `input/pruefregeln.md`
- Herkunft: `synthetischer Prüfkatalog`
- Ursprung: `grundlagen/pruefregeln.md`
- Stand: `git:{{SOURCE_REVISION}}`
- Erforderliche Kontrolle: `revisionsgebunden materialisieren`

1. Gebundene Capability mit den materialisierten Eingaben ausführen.
2. Befund je Pflichtfeld festhalten.
3. Bericht mit Rechenbeleg formulieren.

## Ausgaben

`output/pruefbericht.md`.

Bei Route `bestanden`: `output/pruefbericht.md -> arbeitsschritt:entscheiden/input/pruefbericht.md`.

## Prüfung

Fehlt eine Pflichtangabe, führt die Route `klaerung` zur Nachforderung. Sonst `bestanden`.

## Human Check

Kein Gate. Der Mensch liest den Bericht am nächsten Schritt.
