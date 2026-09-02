---
type: ist-prozess
name: Antrag prüfen und entscheiden
owner: Sachbearbeitung
frequency: je Auftrag
trigger: Antrag geht ein
inputs:
  - Antrag mit Anlagen
outputs:
  - Bescheid
tools:
  - E-Mail
  - Fachanwendung
duration: drei Tage bis zwei Wochen
value: 4
pain: 3
touchpoint: standard
evidence_status: reported
---

# Antrag prüfen und entscheiden

Beobachtet, nicht optimiert. Diese Datei ist Quellmaterial für Identify und liegt unter `grundlagen/ist-prozesse/`. Sie wird nie zur Application; die Application entsteht nach Minimize und Perfect. Beispielwerte ersetzen.

## Ablauf heute

1. Antrag geht per E-Mail ein und wird in der Fachanwendung angelegt.
2. Sachbearbeitung prüft Vollständigkeit.
3. Bei Lücken Rückfrage beim Antragsteller, Vorgang bleibt liegen.
4. Prüfbericht, dann Entscheidung durch die Leitung.
5. Bescheid geht raus.

## Wo wird angehalten und geprüft

Vor der Entscheidung liest die Leitung den Prüfbericht. Sonst niemand.

## Was bleibt gleich, was ist je Lauf neu

Gleich: Prüfkatalog, Bescheidvorlage, Zuständigkeiten. Neu: Antrag, Anlagen, Rückfragen.

## Was verlässt den Prozess, wer zahlt dafür

Der Bescheid. Zahler ist der Antragsteller über die Gebühr.

## Wer fasst es an

Intern: Sachbearbeitung, Leitung. Kunde: Antragsteller bei Rückfragen. Extern: niemand.

## Was bricht, wenn ein Schritt falsch läuft, und fällt es auf

Eine falsche Entscheidung kostet ein Widerspruchsverfahren; sie fällt erst beim Widerspruch auf. Ein unvollständiger Prüfbericht fällt der Leitung auf.

## Quellen

Gespräch mit der Sachbearbeitung am 2026-09-02. Prüfkatalog Version 3.
