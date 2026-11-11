---
type: vorgang
protocol: v0.4.1
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

# Review case 001

A Vorgang is one instance of a committed Hauptprozess. Obtain `hauptprozess_revision` from `git rev-parse HEAD:hauptprozesse/<slug>`. `laufpfad` lists the attempts, each with its folder at `<arbeitsschritt>/<nnn>/`. An attempt's optional `status_seit` is a quoted timestamp with offset stating when it received its current status: set by the harness at the transition or recovered from a source retained in its attempt folder. Without it the start is unknown. Replace example values and explain the Vorgang in the customer's bound working language.

## Subject

What its Leistung is owed for, under the instance cut rule (`02_protocol/impacts-architect/references/zuschnitt.md#hauptprozess`). Link the existing business record at its local home or source-system reference. Its stage stays in that record.

## Progress

Derive position, status and Leistung achievement under `02_protocol/binding.md#vorgang-progress` at the workspace's recorded protocol source and revision.

Explain usable results, restricted drafts, missing evidence or decision, responsible person and next permitted work with links to their files. A prepared draft establishes neither sending nor approval. A `wartend` attempt with its declared continuation preserves usable preparation while the required decision or evidence remains open. Retain its event, next check in `wiedereinstieg.faellig` and responsible follow-up under Waits (`02_protocol/binding.md#waits`), including the expiry transition table. An event alone authorizes no transition.

## Friction

Did the work run cleanly, or did friction push the agent off the protocol? Record the observation and bound revision here; classify and correct it under `02_protocol/impacts-method.md#reviewed-correction`.
