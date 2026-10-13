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
    status: aktiv
    eingabe_hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
---

<!-- Translation source: 02_protocol/templates/vorgang.md; sha256: 6de46d48c9310c1bf3f916f707751874eb463f8885cdfb7d87d4f9576b69b983 -->

# Prüffall 001

Ein Vorgang ist ein konkreter Lauf einer committeten Application. `application_revision` kommt aus `git rev-parse HEAD:applications/<slug>`. Allein `laufpfad` besitzt den Ausführungszustand; jeder Eintrag besitzt seinen Versuchsordner unter `<arbeitsschritt>/<versuch>/`. Beispielwerte ersetzen.

## Betreff

Wer oder was Gegenstand dieses Vorgangs ist. Vorhandenen Geschäftsrecord über seine lokale Heimat oder Quellsystem-Referenz verlinken.

## Stand

Erklärung des Laufpfads für Menschen: aktueller Schritt und Versuch, verwendbare Ergebnisse, noch begrenzte Entwürfe, fehlende Evidenz oder Entscheidung, zuständiger Mensch und nächste erlaubte Arbeit. Auf die jeweiligen Dateien verlinken; den Status aus `laufpfad` ableiten, statt einen weiteren Status zu pflegen. Ein vorbereiteter Entwurf bedeutet weder Versand noch Freigabe. Bei Warten das erklärte Ereignis, den nächsten Fälligkeits- oder zeitlichen Prüftermin, die zuständige Nachverfolgung und die Ausbleibensbehandlung nach `02_protocol/impacts-architect/references/zuschnitt.md#waits` erhalten. Ein Ereignis allein erlaubt keinen Übergang.

Ein `wartend`-Eintrag mit seiner erklärten Fortsetzung ist eine korrekte, fortsetzbare Pause: verwendbare Vorbereitung bleibt erhalten, während die erforderliche Entscheidung oder Evidenz offen ist; das ist weder ein Fehler noch ein abgeschlossenes Ergebnis.
