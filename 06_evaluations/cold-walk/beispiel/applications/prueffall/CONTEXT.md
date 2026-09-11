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

Synthetische Application für den Cold Walk. Ein Antrag wird geprüft, bei Lücken beim Antragsteller nachgefordert und am Ende von einem Menschen entschieden. Kein Kundenbezug.

## Relevantes Umfeld

Antragsteller reichen Anträge ein. Eine Prüfstelle entscheidet. Kein Vermittler.

## Wertfluss

Wertobjekt ist die begründete Entscheidung. Kunde und Zahler ist der Antragsteller. Externe Beteiligte gibt es nicht.

## Zielgröße und Guardrails

Primäres Ziel ist die Durchlaufzeit von Antrag bis Entscheidung. Guardrails: jede Entscheidung nennt ihren Prüfbericht; keine Entscheidung ohne menschliche Freigabe. Gegenmetrik: Anteil der Entscheidungen, die nach Einspruch aufgehoben werden.

## Touchpoints

Die Nachforderung beim Antragsteller ist ein `standard`-Touchpoint: ein Mensch führt das Gespräch, das Harness bereitet die Liste vor. Die Entscheidung ist `sacred`: sie bleibt beim Menschen.

## Automationsgrenze

Vollständigkeitsprüfung ist deterministisch und läuft in Code. Der Prüfbericht wird vom Modell formuliert. Die Entscheidung trägt Schadenshöhe und geringe Umkehrbarkeit und bleibt am Human Gate.

## Weg zur Leistung

Vorprüfung erzeugt den Prüfbericht, bei Lücken über eine Nachforderungsschleife. Entscheidung führt den Bericht zum Human Gate. Das Ende `entschieden` ist die Leistung.

## Durchsatz und Durchlaufzeit

Ein Vorgang je Antrag. Work in Progress ist die Zahl offener Nachforderungen.

## Engpass

Die Nachforderung: sie wartet auf den Antragsteller. Falsifikator: Vorgänge ohne Nachforderung dauern nicht kürzer.
