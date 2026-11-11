---
type: arbeitsschritt
id: arbeitsschritt:entscheiden
eingaben:
  - material/pruefbericht.md
  - material/pruefbericht-herkunft.md
ausgaben:
  - output/entscheidung.md
pruefung: Decision identifies the check report and its rationale
gate: human  # only when a rule reserves a decision, approval or legal act: 02_protocol/impacts-architect/references/zuschnitt.md#arbeitsschritt; otherwise remove this line
routen:
  freigegeben: end:entschieden
  abgelehnt: end:abgelehnt
customer_touchpoint: sacred  # standard or sacred: 02_protocol/impacts-method.md#identify; without a customer interaction remove this line
---

# Decide

Replace every prompt and example value with this definition's content; delete optional blocks you do not use. Each section covers one step area (`02_protocol/impacts-method.md#step-areas`), which lists what belongs in it. Input declarations name required sources or handoff files. Output paths are relative to the attempt. Record actual input references under `gelesen` in the Vorgang.

## One job

One sentence: the result this job produces, its recipient and permitted use.

## Inputs

For each source or handed-off file, name acquisition/producer, required content and opening control (provenance file `*-herkunft.md`, `02_protocol/binding.md#provenance-file-example`).

### Source requirement

For each stable source input (`02_protocol/binding.md#source-inputs-for-core-hauptprozesse`):

- Quell-Eingabe: `grundlagen/<file>.md`
- Datenart: `Foundations`
- Herkunft: `<business identity of the source>`
- Ursprung: `grundlagen/<file>.md`, `records/<file>` or external reference
- Stand: `git:<commit>` or domain revision
- Erforderliche Kontrolle: `<check before opening: revision, as-of time or digest>`

## Excluded context

Name material outside this job's required context.

## Processing

Name only the required contributions, in executable order (`02_protocol/binding.md#work-from-prerequisites`).

Apply `02_protocol/ontology.md#use`; reference the domain definition once.

### Handgriffe

List the operations in order with their relevant data reads or changes; apply `02_protocol/impacts-method.md#step-areas` for their granularity, area references and revision binding.

| No. | Handgriff | Detail | System and data | Screenshot |
|---|---|---|---|---|
| 1 | Open the check report | Select the case and report revision identified by the bound input and its provenance; use the declared input, not a newer live report | Case system: check report, read | Link, if helpful |

### Capability call

Only for an earned Capability (`02_protocol/capabilities.md#capability-call`):

- Aufruf-ID: `<arbeitsschritt-slug>-1`
- Capability-Pfad: `capabilities/<slug>/CONTEXT.md`
- Capability-Revision: `git-tree:<oid>`
- Operation:
- erwartete Ausgabe:
- Mindestprüfung:

## Outputs and effects

Declare the actual files and, for each Arbeitsschritt route, the handoff mapping once at the producer, in the sentence form of `02_protocol/binding.md#visible-output-and-handoff`.

For each record change, message or physical effect, name the target, the change, the current-state check before it, its confirmation and how a repeat stays safe, following `02_protocol/binding.md#record-writeback`.

## Check

Make `pruefung` observable: file, condition, executing checker or accountable person and the check results it can return; Flow explains the route for each check result.

## Authority

Who may decide, access or cause what in this job, and who must act in person? Name this job's holders and bases for decisions, effects, consent, signatures and customer touchpoints; reference common Hauptprozess rules once.

## Flow

For a return route, declare `Loop bound:` under `02_protocol/binding.md#loops`. For a human gate, follow `02_protocol/binding.md#decision-results-and-auslöser` for a readable decision and its route.

What starts this job, where each route leads and what happens while it waits. Explain this job's routes, rework targets and negative ends without repeating protocol execution rules or the route table. Name each wait's cause, each applicable `ausloeser` and the condition under which it continues the waiting attempt (`02_protocol/binding.md#waits`).

## Setup completion

Resolve or mark every placeholder and open dependency with its next action and use restriction. Before the candidate commit, write and review here a supported case, a missing or conflicting prerequisite, a plausible forbidden instruction or inference and a wrong result of correct form. For each, record its premise and expected check result. Link the review evidence under `02_protocol/impacts-method.md#maintain-agent-instructions`.
