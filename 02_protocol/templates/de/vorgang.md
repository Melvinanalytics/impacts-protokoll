---
type: vorgang
id: vorgang:prueffall-001
application_revision: git-tree:0000000000000000000000000000000000000000
laufpfad:
  - arbeitsschritt_ref: arbeitsschritt:pruefen
    versuch: 1
    status: abgeschlossen
    eingabe_hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
    gewaehlte_route: bestanden
    ausgabe_hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
  - arbeitsschritt_ref: arbeitsschritt:entscheiden
    versuch: 1
    status: wartend
    status_seit: "2026-01-05T09:00:00+01:00"
    eingabe_hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
    wiedereinstieg:
      ausloeser: "gate: human (freigegeben | abgelehnt)"
      continuation_ref: entscheiden/001/output/entscheidung.md
      faellig: "2026-01-07T17:00:00+01:00"
---

<!-- Translation source: 02_protocol/templates/vorgang.md; sha256: 777de3a1fcd873b42ec5a3910e5a6af2c2e032f8280754b532fe5fa65260c750 -->

# Prüffall 001

Ein Vorgang ist eine Instanz einer committeten Application. `application_revision` kommt aus `git rev-parse HEAD:applications/<slug>`. Allein `laufpfad` besitzt den Ausführungszustand; jeder Eintrag besitzt seinen Versuchsordner unter `<arbeitsschritt>/<versuch>/`. Das optionale `status_seit` eines Eintrags ist ein Zeitpunkt mit Offset in Anführungszeichen und sagt, seit wann der Eintrag seinen aktuellen Status hat: vom Harness beim Übergang gesetzt oder aus einer im Versuchsordner aufbewahrten Quelle nachgetragen. Ohne diese Angabe ist der Beginn unbekannt; eine Commit-Zeit hält die Dateiänderung fest, nicht den Statusbeginn. Beispielwerte ersetzen.

## Betreff

Wer oder was Gegenstand dieses Vorgangs ist. Vorhandenen Geschäftsrecord über seine lokale Heimat oder Quellsystem-Referenz verlinken.

## Stand

Erklärung des Laufpfads für Menschen: aktueller Schritt und Versuch, verwendbare Ergebnisse, noch begrenzte Entwürfe, fehlende Evidenz oder Entscheidung, zuständiger Mensch und nächste erlaubte Arbeit. Auf die jeweiligen Dateien verlinken; den Status aus `laufpfad` ableiten, statt einen weiteren Status zu pflegen. Diese Werte anzeigen, keinen leer: die Position (aktueller Schritt oder letzter Schritt und erreichtes Ende); die Stufe des aktuellen Schritts oder erreichten Endes, wenn der Hauptprozess `stufen` erklärt; und den Zustand: `aktiv` oder `wartend` aus dem letzten Eintrag, oder `beendet`, sobald ein Ende erreicht ist. Alle aus `laufpfad`, den gebundenen Routen und diesen Stufen ableiten; ein nicht ableitbarer Wert lautet `open`. Ein vorbereiteter Entwurf bedeutet weder Versand noch Freigabe. Bei Warten das erklärte Ereignis, die nächste Prüfung in `wiedereinstieg.faellig`, die zuständige Nachverfolgung und die Ausbleibensbehandlung nach `02_protocol/impacts-architect/references/zuschnitt.md#waits` erhalten. Ein Ereignis allein erlaubt keinen Übergang. Ein abgeschlossener Versuch nennt seine Route, keine Annahme; ein erreichtes Ende nennt, welches Ende, keinen Erfolg; ein verstrichenes `faellig` wählt keine Route und liefert keine Entscheidung.

Ein `wartend`-Eintrag mit seiner erklärten Fortsetzung ist eine korrekte, fortsetzbare Pause: verwendbare Vorbereitung bleibt erhalten, während die erforderliche Entscheidung oder Evidenz offen ist; das ist weder ein Fehler noch ein abgeschlossenes Ergebnis.
