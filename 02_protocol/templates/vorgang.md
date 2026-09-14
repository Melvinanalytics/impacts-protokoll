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

# Review case 001

This template applies to selected Core contracts under `02_protocol/impacts-architect/references/formwahl.md`, "Tooling stop", in the recorded protocol source/revision.

A run executes a committed Application. Obtain `application_revision` from `git rev-parse HEAD:applications/<slug>`. `laufpfad` alone owns execution state; each entry has an attempt folder at `<arbeitsschritt>/<versuch>/`. Use `impacts hash` for hashes. Replace example values and explain the run in the customer's bound working language.

## Subject

Who or what this run concerns. Link the existing business record at its local home or source-system reference.

## Progress

Explain the execution path for people: current step and attempt, usable results, restricted drafts, missing evidence or decision, responsible person and next permitted work. Link the files; derive status from `laufpfad` rather than maintaining another status. A prepared draft establishes neither sending nor approval. For a wait, name the expected event or deadline and the responsible follow-up; if it does not arrive, use the declared fallback route or escalate the missing decision. An event alone authorizes no transition.

A `wartend` entry with its declared continuation is a correct, resumable pause: preserve usable preparation while the required decision or evidence remains open; it is neither failure nor a completed outcome.
