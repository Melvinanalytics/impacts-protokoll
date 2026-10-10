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

<!-- Translation source: 02_protocol/templates/hauptprozess.md; sha256: e3c4ce28110311257b6ea6934625bd1b175a43154eda8219f5cb621a557c636b -->

# Prüffall entscheiden

Der Hauptprozess ist die Wurzel der Application: `applications/<slug>/CONTEXT.md`. Seine Teilprozesse sind seine Unterordner, deren Arbeitsschritte wiederum deren Unterordner. Er ist der vollständige Weg bis zur eingebetteten Leistung. `einstieg_ref` nennt den ersten Arbeitsschritt. Die Routen stehen an den Arbeitsschritten. Dieser Body trägt das Identify-Ergebnis der IMPACTS-Methode; er ist Kontext für Mensch und Harness, kein Schema. Beispielwerte ersetzen.

## Ergebnis und Geltungsbereich

Akzeptiertes Ergebnis, Empfänger, beabsichtigte Nutzung und Prozessgrenze in einem kompakten Abschnitt festhalten. `leistung.ergebnis`, `kennzahl` und jede `abnahme`-Bedingung beobachtbar machen. Angefragte, angebotene, vereinbarte und gelieferte Ergebnisse unterscheiden; ihre bestehenden Definitionen und Evidenz referenzieren. Hat das Ergebnis mehr als einen Bestandteil, die erforderlichen Bestandteile, Baugruppen und Verbindungen innerhalb der Abnahmegrenze dieses Hauptprozesses gemäß `02_protocol/impacts-method.md`, Abschnitt „Leistungsstückliste“, nachvollziehbar machen, einschließlich der erzeugenden oder vollendenden Teilprozesse. Eine vorhandene vollständige Darstellung oder ein Verweis darauf genügt. Mehrere Bestandteile allein erfordern keine gesonderte Liste oder zusätzliche Baugruppe.

## Relevantes Umfeld

Empfänger, Beteiligte, Abhängigkeiten und Grenzen der Leistung. Markt-, Nachfrage- oder Vermittlungsbeziehungen nur aufnehmen, wenn sie für die betrachtete Entscheidung relevant sind.

## Wertfluss

Wertobjekt und Empfänger; Kunde, Zahler und beteiligte Externe nur bei Relevanz. Jede geforderte Bedingung samt Urheber und Grundlage mit erzeugendem Job, Voraussetzungen und Abnahmenachweis verbinden. Für verbleibende Koordination die von ihr geregelte Abhängigkeit und den Nachweis verlinken, dass ihre Trennung nach Minimize weiterhin nötig ist. Bei einem Produkt oder Service dessen zugesagten oder vereinbarten Umfang vom Ergebnis dieses Prozesses und tatsächlicher Erfüllung unterscheiden. Bestehende Definitionen/Records und beobachtete Fälle referenzieren; rekonstruierte Arbeit als `hypothesis`, ungeklärte Abhängigkeiten als `open` mit nächster Aktion und Nutzungsgrenze kennzeichnen.

## Zielgröße und Leitplanken

Ein primäres Ziel und seine beobachtbare Abnahme. Die Fragen aus Identify für dieses begrenzte Vorhaben beantworten: Evidenz und offene Fragen, nächster Eingriff oder Beobachtung, Zuständigkeit, erwartete Wirkung sowie Wiederprüf-/Stoppbedingung. Qualität, Zeit und Kosten durch passende Guardrails schützen.

## Kundenkontaktpunkte

Jeden Customer-Touchpoint dieses Prozesses mit Grund und Wert nennen, `standard` oder `sacred` wie in `02_protocol/impacts-method.md#identify` bestimmt. Interne Human Gates stehen am Arbeitsschritt.

## Automationsgrenze

Welche menschlichen Grenzen gelten, warum und wer darf sie ändern? Eingangsvarianz, Ergebnistoleranz, Schadenshöhe, Umkehrbarkeit und Entdeckbarkeit bestimmen die erlaubte Unterstützung. Gewohnte Arbeitsteilung von erforderlicher Autorität und tatsächlicher Verfügbarkeit unterscheiden; konkrete Beiträge stehen im jeweiligen Arbeitsschritt.

## Weg zur Leistung

Welche Teilprozesse zum Ergebnis beitragen, wie ihre Voraussetzungen beschafft werden und wie Erfolg, Ablehnung oder ein unvollständiger Fall endet beziehungsweise wartet. `einstieg_ref` und Arbeitsschrittrouten bestimmen die Reihenfolge; diese Erklärung führt keine zweite Routentabelle. Unabhängige Applications übergeben belegte Ergebnisse zwischen getrennten Vorgängen, nicht durch Application-übergreifende Schrittrouten.

## Durchsatz und Durchlaufzeit

Erwarteter Durchsatz, Work in Progress und Durchlaufzeit. Für den Zeitvergleich Start und akzeptiertes Ende festlegen; aktive Bearbeitung von Warten, Übergaben und Nacharbeit unterscheiden. Quelle oder berichtete Spanne nennen, Unbekanntes offenlassen. Überlappende Tätigkeiten nicht zur Durchlaufzeit addieren. Die Kennzahl der Leistung ist der Lagging Indicator dieses Prozesses.

## Engpass

Welche belegte Begrenzung bestimmt derzeit die Leistung oder Durchlaufzeit, und welche Beobachtung würde diese Annahme widerlegen? Das kann Verarbeitungskapazität, eine fehlende Eingabe oder eine wartende Entscheidung sein. Kürzere Einzelarbeit allein belegt keine Verbesserung des Gesamtprozesses. Erforderliche menschliche Grenzen bleiben bei einer Umgestaltung erhalten.

## Einrichtungsabschluss

Die Definitionseinrichtung ist abgeschlossen, wenn jede anwendbare erforderliche Bedingung im erklärten Geltungsbereich dieses Hauptprozesses, einschließlich `abnahme`, erforderlicher Bestandteile, Baugruppen, Verbindungen, Pflichten und wesentlicher Voraussetzungen, zu verantwortlicher Arbeit/Prüfung oder einer belegten Voraussetzung mit Nutzungsgrenze zurückverfolgt ist. Bedingungen behalten ihre Rolle; nicht jede muss zur Ausgabe oder zu einem neuen Schritt werden. Bei fortdauernden Pflichten die innerhalb dieses Prozesses erforderliche Handlung oder Kontrolle und den fortdauernden Verantwortlichen belegen; siebenjährige Aufbewahrung erfordert keinen siebenjährigen aktiven Vorgang. Designabdeckung und tatsächliche Erfüllung bleiben getrennt. Zum Abschluss gehört außerdem, dass `einstieg_ref` und jede Arbeitsschrittroute eine Route `end:<slug>` erreichen kann, jede wesentliche Aussage Quelle und Evidenzstand trägt und jede ungeklärte Abhängigkeit nächste Aktion und Nutzungsgrenze nennt. Vor dem Kandidaten-Commit hier einen gestützten Pfad, eine fehlende oder widersprüchliche Voraussetzung und eine plausible unzulässige Schlussfolgerung festhalten und prüfen. Je Fall Voraussetzung, erwartetes Ergebnis, Prüfergebnis und offene Lücken festhalten. Synthetische Fälle kennzeichnen; erwartete Ergebnisse sind keine beobachteten Ausführungsergebnisse. Nach dem Commit liefert die Test-Phase beobachtete Harness-Evidenz für genau diese Revision. Strukturelle Gültigkeit und Designprüfung belegen weder Einsatzbereitschaft noch Prozessergebnis.
