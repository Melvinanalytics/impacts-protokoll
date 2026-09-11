---
type: vorgang
id: vorgang:prueffall-001
application_revision: git-tree:0000000000000000000000000000000000000000
laufpfad:
  - arbeitsschritt_ref: arbeitsschritt:pruefen
    versuch: 1
    status: aktiv
    eingabe_hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
---

<!-- Translation source: 02_protocol/templates/vorgang.md; sha256: 7e4504f4cbfce0ef5c9bebb7e7cde29593d6b2be1eeb7a8aa3441abde8415baa -->

# Prüffall 001

Ein Vorgang ist ein konkreter Lauf einer committeten Application. `application_revision` kommt aus `git rev-parse HEAD:applications/<slug>`. Der Laufpfad ist die einzige Zustandsautorität; jeder Eintrag besitzt seinen Versuchsordner unter `<arbeitsschritt>/<versuch>/`. Hashes liefert `impacts hash`. Beispielwerte ersetzen.

## Betreff

Wer oder was Gegenstand dieses Vorgangs ist. Vorhandenen Geschäftsrecord über seine lokale Heimat oder Quellsystem-Referenz verlinken.

## Stand

Erklärung des Laufpfads für Menschen: aktueller Schritt und Versuch, verwendbare Ergebnisse, noch begrenzte Entwürfe, fehlende Evidenz oder Entscheidung, zuständiger Mensch und nächste erlaubte Arbeit. Auf die jeweiligen Dateien verlinken; keinen zweiten Status pflegen. Die Zustandshoheit bleibt beim Laufpfad im Frontmatter. Ein vorbereiteter Entwurf bedeutet weder Versand noch Freigabe. Bei Warten das erwartete Ereignis oder die Frist und die zuständige Nachverfolgung benennen; bleibt es aus, den erklärten Ausweichweg nutzen oder die fehlende Entscheidung eskalieren. Ein Ereignis allein erlaubt keinen Übergang.
