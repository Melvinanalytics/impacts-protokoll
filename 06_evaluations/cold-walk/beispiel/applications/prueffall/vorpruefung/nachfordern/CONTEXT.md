---
type: arbeitsschritt
id: arbeitsschritt:nachfordern
eingaben:
  - input/pruefbericht.md
ausgaben:
  - output/nachforderung.md
pruefung: Nachforderung nennt jede fehlende Pflichtangabe aus dem Prüfbericht
routen:
  nachgereicht: arbeitsschritt:pruefen
customer_touchpoint: standard
---

# Nachfordern

## Ein Job

Fehlende Angaben beim Antragsteller anfordern und auf die Nachreichung warten.

## Eingaben

`input/pruefbericht.md` mit den Lücken.

## Nicht laden

Den Antrag selbst; der Bericht trägt die Lücken.

## Verarbeitung

1. Liste der fehlenden Angaben aus dem Bericht ziehen.
2. Anschreiben vorbereiten; ein Mensch führt das Gespräch.
3. Versuch auf `wartend` setzen, bis die Nachreichung eintrifft.

## Ausgaben

`output/nachforderung.md`.

## Prüfung

Jede Lücke des Berichts erscheint in der Nachforderung. Nach Eingang führt `nachgereicht` zurück zur Prüfung.

## Human Check

Kein Gate. Der Touchpoint ist `standard`: der Mensch spricht mit dem Antragsteller.
