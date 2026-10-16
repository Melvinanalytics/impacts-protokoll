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

# Review case 001

A run executes a committed Application. Obtain `application_revision` from `git rev-parse HEAD:applications/<slug>`. `laufpfad` alone owns execution state; each entry has an attempt folder at `<arbeitsschritt>/<versuch>/`. An entry's optional `status_seit` is a quoted timestamp with offset stating when it received its current status: set by the harness at the transition or recovered from a source retained in its attempt folder. Without it the start is unknown; a commit time records the file change, not the status start. Replace example values and explain the run in the customer's bound working language.

## Subject

Who or what this run concerns. Link the existing business record at its local home or source-system reference.

## Progress

Explain the execution path for people: current step and attempt, usable results, restricted drafts, missing evidence or decision, responsible person and next permitted work. Link the files; derive status from `laufpfad` rather than maintaining another status. A prepared draft establishes neither sending nor approval. For a wait, retain its declared event, its next check in `wiedereinstieg.faellig`, responsible follow-up and non-arrival handling under `02_protocol/impacts-architect/references/zuschnitt.md#waits`. An event alone authorizes no transition. A closed attempt states its route, not acceptance; a reached end names which end, not success; an elapsed `faellig` selects no route and supplies no decision.

A `wartend` entry with its declared continuation is a correct, resumable pause: preserve usable preparation while the required decision or evidence remains open; it is neither failure nor a completed outcome.
