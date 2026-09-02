---
type: hauptprozess
id: hauptprozess:prueffall
leistung:
  ergebnis: Entschiedener Prüffall
  kennzahl: Durchlauf von Antrag bis Entscheidung
  abnahme:
    - Prüfbericht liegt vor
    - Entscheidung ist menschlich freigegeben
einstieg_ref: arbeitsschritt:pruefen
---

# Prüffall entscheiden

## Weg zur Leistung

Vorprüfung erzeugt den Prüfbericht, bei Lücken über eine Nachforderungsschleife. Entscheidung führt den Bericht zum Human Gate. Das Ende `entschieden` ist die Leistung.

## Durchsatz und Durchlaufzeit

Ein Vorgang je Antrag. Work in Progress ist die Zahl offener Nachforderungen.

## Engpass

Die Nachforderung: sie wartet auf den Antragsteller. Falsifikator: Vorgänge ohne Nachforderung dauern nicht kürzer.
