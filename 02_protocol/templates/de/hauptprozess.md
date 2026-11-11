---
type: hauptprozess
id: hauptprozess:prueffall
leistung:
  ergebnis: Entschiedener Prüffall
  kennzahl: Durchlaufzeit von Antrag bis Entscheidung
  abnahme:
    - Prüfbericht liegt vor
    - Entscheidung ist menschlich freigegeben
  erreicht:  # optional: jedes Ende, das die Leistung erreicht; jedes andere Ende ist negativ
    - end:entschieden
einstieg_ref: arbeitsschritt:pruefen
---

<!-- Translation source: 02_protocol/templates/hauptprozess.md; sha256: ae2fb1b0870173ba4ff76b045747416cb91ad1706a4133b0f913ae38c9e8479f -->

# Prüffall entscheiden

Der Hauptprozess ist die Wurzel: `hauptprozesse/<slug>/CONTEXT.md`. Seine Teilprozesse sind seine Unterordner, deren Arbeitsschritte wiederum deren Unterordner. Er ist der vollständige Weg bis zur eingebetteten Leistung. `einstieg_ref` nennt den ersten Arbeitsschritt; dessen „Ablauf“ nennt den Auslöser, der einen Vorgang öffnet. Die Routen stehen an den Arbeitsschritten. Dieser Body trägt das Identify-Ergebnis der IMPACTS-Methode; er ist Kontext für Mensch und Harness, kein Schema. Beispielwerte ersetzen.

## Ergebnis und Geltungsbereich

Die Leistung, Empfänger, beabsichtigte Nutzung und Prozessgrenze in einem kompakten Abschnitt festhalten. `leistung.ergebnis`, `kennzahl` und jede `abnahme`-Bedingung beobachtbar machen. Angefragte, angebotene, vereinbarte und gelieferte Ergebnisse unterscheiden; ihre bestehenden Definitionen und Evidenz referenzieren. Hat das Ergebnis mehr als einen Bestandteil, die erforderlichen Bestandteile, Baugruppen und Verbindungen innerhalb der Abnahmegrenze dieses Hauptprozesses gemäß `02_protocol/impacts-method.md`, Abschnitt „Leistungsstückliste“, nachvollziehbar machen, einschließlich der Teilprozesse, deren Arbeitsschritte sie erzeugen oder vollenden. Eine vorhandene vollständige Darstellung oder ein Verweis darauf genügt. Mehrere Bestandteile allein erfordern keine gesonderte Liste oder zusätzliche Baugruppe.

## Relevantes Umfeld

Empfänger, Beteiligte, Abhängigkeiten und Grenzen der Leistung. Markt-, Nachfrage- oder Vermittlungsbeziehungen nur aufnehmen, wenn sie für die betrachtete Entscheidung relevant sind.

## Wertfluss

Wertobjekt und Empfänger; Kunde, Zahler und beteiligte Externe nur bei Relevanz. Jede geforderte Bedingung samt Urheber und Grundlage mit erzeugendem Job, Voraussetzungen und Abnahmenachweis verbinden. Für verbleibende Koordination die von ihr geregelte Abhängigkeit verlinken. Für deren Evidenz die Analysedatei verlinken. Bei einem Produkt oder Service dessen zugesagten oder vereinbarten Umfang vom Ergebnis dieses Prozesses und tatsächlicher Erfüllung unterscheiden. Bestehende Definitionen und Records referenzieren; ungeklärte Abhängigkeiten als `open` mit nächster Aktion und Nutzungsgrenze kennzeichnen.

## Zielgröße und Leitplanken

Ein primäres Ziel und seine beobachtbare Abnahme. Qualität, Zeit und Kosten durch entschiedene Leitplanken, Schwellen und Abnahmegrenzen schützen.

## Kundenkontaktpunkte

Jeden Kundenkontaktpunkt dieses Prozesses mit seinem Grund nennen; sein Wert, `standard` oder `sacred`, wird einmal in `customer_touchpoint` des Arbeitsschritts erklärt, der ihn enthält (`02_protocol/impacts-method.md#identify` bestimmt die Werte). Interne Human Gates stehen am Arbeitsschritt.

## Automationsgrenze

Welche menschlichen Grenzen gelten, warum und wer darf sie ändern? Eingangsvarianz, Ergebnistoleranz, Schadenshöhe, Umkehrbarkeit und Entdeckbarkeit bestimmen die erlaubte Unterstützung. Gewohnte Arbeitsteilung von erforderlicher Autorität und tatsächlicher Verfügbarkeit unterscheiden; konkrete Beiträge stehen im jeweiligen Arbeitsschritt.

## Weg zur Leistung

Welche Teilprozesse zum Ergebnis beitragen, wie ihre Voraussetzungen beschafft werden und wie Erfolg, Ablehnung oder ein unvollständiger Vorgang endet beziehungsweise wartet. Jedes `end:<slug>`, das die Leistung erreicht, in `leistung.erreicht` aufführen; jedes andere Ende ist ein negatives Ende. `einstieg_ref` und Arbeitsschrittrouten bestimmen die Reihenfolge; diese Erklärung führt keine zweite Routentabelle. Unabhängige Hauptprozesse übergeben belegte Ergebnisse zwischen getrennten Vorgängen, nicht durch Hauptprozess-übergreifende Arbeitsschrittrouten. Gegenstandsstufen stehen im Record nach `02_protocol/binding.md#record-writeback`; Fortschrittsgewichte gehören in die Analyse.

## Einrichtungsabschluss

Die Definitionseinrichtung ist abgeschlossen, wenn jede anwendbare erforderliche Bedingung im erklärten Geltungsbereich dieses Hauptprozesses, einschließlich `abnahme`, erforderlicher Bestandteile, Baugruppen, Verbindungen, Pflichten und wesentlicher Voraussetzungen, zu verantwortlicher Arbeit/Prüfung oder einer belegten Voraussetzung mit Nutzungsgrenze zurückverfolgt ist. Bedingungen behalten ihre Rolle; nicht jede muss zur Ausgabe oder zu einem neuen Arbeitsschritt werden. Bei fortdauernden Pflichten die innerhalb dieses Prozesses erforderliche Handlung oder Kontrolle und den fortdauernden Verantwortlichen belegen; siebenjährige Aufbewahrung erfordert keinen siebenjährigen aktiven Vorgang. Designabdeckung und tatsächliche Erfüllung bleiben getrennt. Zum Abschluss gehört außerdem, dass `einstieg_ref` und jede Arbeitsschrittroute eine Route `end:<slug>` erreichen kann, jede wesentliche Aussage Quelle und Evidenzstand trägt und jede ungeklärte Abhängigkeit nächste Aktion und Nutzungsgrenze nennt. Vor dem Kandidaten-Commit hier einen gestützten Pfad, eine fehlende oder widersprüchliche Voraussetzung und eine plausible unzulässige Schlussfolgerung festhalten und prüfen. Je Fall Voraussetzung und erwartetes Ergebnis festhalten. Die Prüfevidenz nach `02_protocol/impacts-method.md#maintain-agent-instructions` verlinken. Synthetische Fälle kennzeichnen; erwartete Ergebnisse sind keine beobachteten Ausführungsergebnisse. Nach dem Commit liefert die Test-Phase beobachtete Harness-Evidenz für genau diese Revision. Strukturelle Gültigkeit und Designprüfung belegen weder Einsatzbereitschaft noch Prozessergebnis.
