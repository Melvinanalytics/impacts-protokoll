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

Der Hauptprozess ist die Wurzel der Application: `applications/<slug>/CONTEXT.md`. Seine Teilprozesse sind seine Unterordner, deren Arbeitsschritte wiederum deren Unterordner. Er ist der vollständige Weg bis zur eingebetteten Leistung. `einstieg_ref` nennt den ersten Arbeitsschritt. Die Routen stehen an den Arbeitsschritten. Dieser Body trägt das Identify-Ergebnis der IMPACTS-Methode; er ist Kontext für Mensch und Harness, kein Schema. Beispielwerte ersetzen.

## Relevantes Umfeld

Empfänger, Beteiligte, Abhängigkeiten und Grenzen der Leistung. Markt-, Nachfrage- oder Vermittlungsbeziehungen nur aufnehmen, wenn sie für die betrachtete Entscheidung relevant sind.

## Wertfluss

Wertobjekt und Empfänger; Kunde, Zahler und beteiligte Externe nur bei Relevanz. Wo Wert entsteht, übergeben und abgenommen wird.

## Zielgröße und Guardrails

Ein primäres Ziel und seine beobachtbare Abnahme. Die Fragen aus Identify für dieses begrenzte Vorhaben beantworten: Evidenz und offene Fragen, nächster Eingriff oder Beobachtung, Zuständigkeit, erwartete Wirkung sowie Wiederprüf-/Stoppbedingung. Qualität, Zeit und Kosten durch passende Guardrails schützen.

## Touchpoints

Customer-Touchpoints dieser Application. `standard`: ein Mensch führt die Interaktion, das Harness bereitet vor und nach. `sacred`: geschützt, eine Reklassifizierung braucht menschliche Prüfung der Application. Interne Human Gates stehen am Arbeitsschritt.

## Automationsgrenze

Welche menschlichen Grenzen gelten, warum und wer darf sie ändern? Eingangsvarianz, Ergebnistoleranz, Schadenshöhe, Umkehrbarkeit und Entdeckbarkeit bestimmen die erlaubte Unterstützung. Gewohnte Arbeitsteilung von erforderlicher Autorität und tatsächlicher Verfügbarkeit unterscheiden; konkrete Beiträge stehen im jeweiligen Arbeitsschritt.

## Weg zur Leistung

Welche Teilprozesse in welcher Folge zur Leistung führen und woran das Ende erkennbar ist.

## Durchsatz und Durchlaufzeit

Erwarteter Durchsatz, Work in Progress und Durchlaufzeit. Für den Zeitvergleich Start und akzeptiertes Ende festlegen; aktive Bearbeitung von Warten, Übergaben und Nacharbeit unterscheiden. Quelle oder berichtete Spanne nennen, Unbekanntes offenlassen. Überlappende Tätigkeiten nicht zur Durchlaufzeit addieren. Die Kennzahl der Leistung ist der Lagging Indicator dieses Prozesses.

## Engpass

Welche belegte Begrenzung bestimmt derzeit die Leistung oder Durchlaufzeit, und welche Beobachtung würde diese Annahme widerlegen? Das kann Verarbeitungskapazität, eine fehlende Eingabe oder eine wartende Entscheidung sein. Kürzere Einzelarbeit allein belegt keine Verbesserung des Gesamtprozesses. Erforderliche menschliche Grenzen bleiben bei einer Umgestaltung erhalten.
