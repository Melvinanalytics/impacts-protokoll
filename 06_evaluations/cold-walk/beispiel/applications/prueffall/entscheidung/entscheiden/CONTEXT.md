---
type: arbeitsschritt
id: arbeitsschritt:entscheiden
eingaben:
  - input/pruefbericht.md
  - input/pruefbericht-herkunft.md
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

`input/pruefbericht.md` und `input/pruefbericht-herkunft.md`. Das Producer-Mapping steht einmalig im erzeugenden Schritt `arbeitsschritt:pruefen`; der konkrete Vorgang belegt hier den versuchsqualifizierten Ursprung.

## Nicht laden

Nachforderungen; sie sind im Bericht aufgegangen.

## Verarbeitung

1. Vor `open()` müssen Bericht, versuchsqualifizierter Ursprung, Content-Digest und Kontrollnachweis vollständig sein.
2. Menschliche Entscheidung mit Bezug auf den Befund formulieren.
3. Ausgabe schreiben; `pruefung` bewertet danach diese Ausgabe.

## Ausgaben

`output/entscheidung.md`.

## Prüfung

Die Vorlage nennt den Prüfbericht und eine Begründung.

## Human Check

Der offene Gate-Schritt besitzt weder Route noch `freigabe`. Der Mensch liest Bericht und Herkunftsnachweis, schreibt Entscheidung und `freigabe` in den Laufpfad. `freigegeben` beendet den Vorgang. `abgelehnt` führt zurück zur Prüfung. Der synthetische Cold Walk erhält diese Angaben aus einer externen Fixture und authentifiziert keine Person.
