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

<!-- Translation source: 02_protocol/templates/vorgang.md; sha256: 8006122821d6c7731b1bacd2b8dc222cff4337000feedd4bf9a27081427591c5 -->

# Prüffall 001

Diese Vorlage gilt für gewählte Core-Verträge gemäß `02_protocol/impacts-architect/references/formwahl.md`, Abschnitt „Tooling stop“, in der benannten Protokollquelle und Revision.

Ein Vorgang ist ein konkreter Lauf einer committeten Application. `application_revision` kommt aus `git rev-parse HEAD:applications/<slug>`. Der Laufpfad ist die einzige Zustandsautorität; jeder Eintrag besitzt seinen Versuchsordner unter `<arbeitsschritt>/<versuch>/`. Hashes liefert `impacts hash`. Beispielwerte ersetzen.

## Betreff

Wer oder was Gegenstand dieses Vorgangs ist. Vorhandenen Geschäftsrecord über seine lokale Heimat oder Quellsystem-Referenz verlinken.

## Stand

Erklärung des Laufpfads für Menschen: aktueller Schritt und Versuch, verwendbare Ergebnisse, noch begrenzte Entwürfe, fehlende Evidenz oder Entscheidung, zuständiger Mensch und nächste erlaubte Arbeit. Auf die jeweiligen Dateien verlinken; keinen zweiten Status pflegen. Die Zustandshoheit bleibt beim Laufpfad im Frontmatter. Ein vorbereiteter Entwurf bedeutet weder Versand noch Freigabe. Bei Warten das erwartete Ereignis oder die Frist und die zuständige Nachverfolgung benennen; bleibt es aus, den erklärten Ausweichweg nutzen oder die fehlende Entscheidung eskalieren. Ein Ereignis allein erlaubt keinen Übergang.

Ein `wartend`-Eintrag mit seiner erklärten Fortsetzung ist eine korrekte, fortsetzbare Pause: verwendbare Vorbereitung bleibt erhalten, während die erforderliche Entscheidung oder Evidenz offen ist; das ist weder ein Fehler noch ein abgeschlossenes Ergebnis.
