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

# Prüffall 001

Ein Vorgang ist ein konkreter Lauf einer committeten Application. `application_revision` kommt aus `git rev-parse HEAD:applications/<slug>`. Der Laufpfad ist die einzige Zustandsautorität; jeder Eintrag besitzt seinen Versuchsordner unter `<arbeitsschritt>/<versuch>/`. Hashes liefert `impacts hash`. Beispielwerte ersetzen.

## Betreff

Wer oder was Gegenstand dieses Vorgangs ist. Verweis auf den Record unter `records/`, falls vorhanden.

## Stand

Erklärung des Laufpfads für Menschen: aktueller Schritt, offene Frage, nächster Mensch. Der Laufpfad selbst bleibt maschinenlesbar im Frontmatter.
