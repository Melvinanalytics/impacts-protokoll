---
type: arbeitsschritt
id: arbeitsschritt:entscheiden
eingaben:
  - input/pruefbericht.md
  - input/pruefbericht-herkunft.md
ausgaben:
  - output/entscheidung.md
pruefung: Entscheidung nennt Prüfbericht, tatsächliche Gate-Entscheidung und Begründung
gate: human
routen:
  freigegeben: end:entschieden
  abgelehnt: end:abgelehnt
customer_touchpoint: sacred
---

# Entscheiden

## Ein Job

Die tatsächliche menschliche Entscheidung zum gebundenen Prüfbericht mit Begründung festhalten. Diese Fixture ersetzt den Gate-Schritt erst in einer neuen Application-Revision; der historische Baum bleibt erhalten.

## Eingaben

`input/pruefbericht.md` und `input/pruefbericht-herkunft.md`. Das Producer-Mapping steht im erzeugenden Schritt `arbeitsschritt:pruefen`; der Vorgang belegt den versuchsqualifizierten Ursprung.

## Nicht laden

Nachforderungen; sie sind im Bericht aufgegangen.

## Verarbeitung

Vor Gate-Öffnung prüft das Harness Bericht, versuchsqualifizierten Ursprung, Content-Digest und Kontrollnachweis. Der verantwortliche Mensch entscheidet über diesen Bericht. Das Harness erhält die belegte Entscheidung über den eingerichteten vertrauenswürdigen Weg und bewahrt ihre Quelle; die synthetische Fixture authentifiziert keine Person.

## Ausgaben und Wirkungen

`output/entscheidung.md` nennt `Prüfbericht`, `Entscheidung` (`freigegeben` oder `abgelehnt`) und `Begründung` mit nicht leeren Werten. Das Harness erhält darin die empfangenen synthetischen Entscheidungsfelder einschließlich Inhaber und Entscheidungszeit sowie die gebundene Application-Revision und den Digest des entschiedenen Berichts. Keine externe Wirkung ist erlaubt.

## Prüfung

Die aufgezeichnete Entscheidung stimmt mit der tatsächlichen belegten Entscheidung und gewählten Route überein. Bericht und Begründung sind vorhanden. Fehlende oder widersprüchliche Evidenz lässt den Übergang offen.

## Befugnis

Die positive Fixture nennt `human:beispiel-pruefer` als gesetzten Entscheidungsinhaber. Eine echte Entscheidung benötigt ihre tatsächliche zuständige Person und den eingerichteten vertrauenswürdigen Herkunftsweg nach `02_protocol/capabilities.md#signale-und-human-gate`; die Fixture erteilt keine reale Befugnis.

## Ablauf

Der offene Gate-Schritt besitzt weder Route noch `freigabe`. Die Freigabe hält tatsächlichen Inhaber und Entscheidungszeit fest. `freigegeben` endet bei `end:entschieden`; die endgültige Ablehnung endet negativ bei `end:abgelehnt`. Eine neue Prüfung benötigt einen neuen, vollständig gebundenen Vorgang und liefert keine rückwirkende Freigabe.

## Einrichtungsabschluss

Synthetische erwartete Fälle: Eine belegte `freigegeben`-Entscheidung mit Bericht und Begründung endet positiv; eine belegte endgültige `abgelehnt`-Entscheidung endet negativ. Fehlende Entscheidung oder eine Entscheidung, die der Route widerspricht, hält das Gate offen. Ein `human:<id>`-Text authentifiziert keine Person. Die ausgeführten Tests in `tests/test_cold_walk.py` liefern ihre beobachteten Ergebnisse getrennt von diesen Erwartungen.
