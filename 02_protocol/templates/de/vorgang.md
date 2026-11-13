---
type: vorgang
protocol: v0.5.0
id: vorgang:prueffall-001
hauptprozess_revision: git-tree:0000000000000000000000000000000000000000
# vorgaenger: vorgaenge/prueffall-alt/CONTEXT.md
laufpfad:
  - arbeitsschritt_ref: arbeitsschritt:pruefen
    nummer: 1
    status: abgeschlossen
    gelesen:
      - eingabe: material/antrag.md
        pfad: records/prueffall-001/antrag.md
        revision: git-commit:0000000000000000000000000000000000000000
        sha256: sha256:0000000000000000000000000000000000000000000000000000000000000000
      - eingabe: material/antrag-herkunft.md
        pfad: records/prueffall-001/antrag-herkunft.md
        revision: git-commit:0000000000000000000000000000000000000000
        sha256: sha256:0000000000000000000000000000000000000000000000000000000000000000
    gewaehlte_route: bestanden
    geschrieben:
      - pfad: vorgaenge/prueffall-001/pruefen/001/output/pruefbericht.md
        sha256: sha256:0000000000000000000000000000000000000000000000000000000000000000
  - arbeitsschritt_ref: arbeitsschritt:entscheiden
    nummer: 1
    status: wartend
    status_seit: "2026-01-05T09:00:00+01:00"
    gelesen:
      - eingabe: material/pruefbericht.md
        pfad: vorgaenge/prueffall-001/pruefen/001/output/pruefbericht.md
        sha256: sha256:0000000000000000000000000000000000000000000000000000000000000000
    wiedereinstieg:
      ausloeser: "gate: human (freigegeben | abgelehnt)"
      continuation_ref: vorgaenge/prueffall-001/entscheiden/001/output/entscheidung.md
      faellig: "2026-01-07T17:00:00+01:00"
---

<!-- Translation source: 02_protocol/templates/vorgang.md; sha256: b058b12acbd8ca2f181f25590d64bb5b48b4822ad5a63c672f395cf8b9fda28a -->

# Prüffall 001

Ein Vorgang ist eine Instanz eines committeten Hauptprozesses. `hauptprozess_revision` kommt aus `git rev-parse HEAD:hauptprozesse/<slug>`. Allein `laufpfad` besitzt den Ausführungszustand; er listet die Versuche, jeder mit seinem Ordner unter `<arbeitsschritt>/<nnn>/`. Das optionale `status_seit` eines Versuchs ist ein Zeitpunkt mit Offset in Anführungszeichen und sagt, seit wann der Versuch seinen aktuellen Status hat: vom Harness beim Übergang gesetzt oder aus einer im Versuchsordner aufbewahrten Quelle nachgetragen. Ohne diese Angabe ist der Beginn unbekannt; eine Commit-Zeit hält die Dateiänderung fest, nicht den Statusbeginn. Beispielwerte ersetzen.

## Gegenstand

Wofür seine Leistung geschuldet ist, nach der Instanz-Schnittregel (`02_protocol/impacts-architect/references/zuschnitt.md#hauptprozess`). Vorhandenen Geschäftsrecord über seine lokale Heimat oder Quellsystem-Referenz verlinken. Seine Stufe bleibt in diesem Record.

## Fortschritt

Position, Status und Leistungserreichung nach `02_protocol/binding.md#vorgang-progress` an der im Arbeitsbereich festgehaltenen Protokollquelle und Revision ableiten.

Verwendbare Ergebnisse, noch begrenzte Entwürfe, fehlende Evidenz oder Entscheidung, zuständigen Menschen und nächste erlaubte Arbeit mit Links auf ihre Dateien erklären. Ein vorbereiteter Entwurf bedeutet weder Versand noch Freigabe. Ein `wartend`-Versuch mit seiner erklärten Fortsetzung erhält verwendbare Vorbereitung, während die erforderliche Entscheidung oder Evidenz offen ist. Sein Ereignis, die nächste Prüfung in `wiedereinstieg.faellig` und die zuständige Nachverfolgung nach Waits (`02_protocol/binding.md#waits`) erhalten, einschließlich der Übergangstabelle für Fristablauf. Ein Ereignis allein erlaubt keinen Übergang.

## Reibung

Lief die Arbeit reibungslos, oder drängte Reibung den Agenten aus dem Protokoll? Beobachtung und gebundene Revision hier festhalten; Einordnung und Korrektur folgen `02_protocol/impacts-method.md#reviewed-correction`.
