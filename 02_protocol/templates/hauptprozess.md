---
type: hauptprozess
id: hauptprozess:prueffall
leistung:
  ergebnis: Decided review case
  kennzahl: Lead time from request to decision
  abnahme:
    - Check report is available
    - Decision is approved by the responsible human
einstieg_ref: arbeitsschritt:pruefen
---

# Decide a review case

This template applies to selected Core contracts under `02_protocol/impacts-architect/references/formwahl.md`, "Tooling stop", in the recorded protocol source/revision.

The main process is the Application root at `applications/<slug>/CONTEXT.md`. Its subfolders are subprocesses, whose subfolders are worksteps. It defines the complete path to the embedded result. `einstieg_ref` names the first workstep; each workstep owns its routes. This body carries Identify context for people and harnesses, not another schema. Replace example values in the customer's working language.

## Result and scope

State the accepted result, recipient, intended use and process boundary in one compact passage. Make `leistung.ergebnis`, `kennzahl` and every `abnahme` condition observable. Keep requested, offered, agreed and delivered results distinct; cite their existing definitions and evidence.

## Relevant environment

Recipient, participants, dependencies and result boundaries. Include market, demand or intermediary relationships only when relevant to the decision.

## Value flow

Valued result and recipient; customer, payer and external parties only where relevant. Link each required result component to its producing job, prerequisites and acceptance evidence. For retained coordination, link the dependency it manages and the evidence that the dependency remains necessary after Minimize; do not copy the Ist classification table into the Application. Given a product/service, distinguish its promised or agreed scope from this process's result and actual fulfillment. Reference existing definitions/records and observed cases; mark reconstructed work as `hypothesis` and unresolved dependencies as `open` with their next action and use restriction.

## Objective and guardrails

One primary objective and observable acceptance. Address Identify's questions for this bounded intervention: evidence and gaps, next intervention or observation, responsibility, expected effect and recheck/stop condition. Protect quality, time and cost with relevant guardrails.

## Touchpoints

`standard`: a person leads the customer interaction; the harness prepares and follows up. `sacred`: protected interaction whose reclassification needs human review of the Application. Internal human gates belong to worksteps.

## Automation boundary

Which human boundaries apply, why, and who may change them? Input variance, result tolerance, harm, reversibility and detectability determine permitted assistance. Distinguish habitual division of work from required authority and actual availability; each workstep names its concrete contributions.

## Path to the result

Which subprocesses contribute to the result, how their prerequisites are obtained, and how success, rejection or an incomplete case ends or waits. `einstieg_ref` and workstep routes own the sequence; this explanation does not maintain a second route table. Independent Applications exchange evidenced results through separate runs, not cross-Application step routes.

## Throughput and lead time

Expected throughput, work in progress and elapsed time. Define start and accepted end; distinguish active work, waiting, handoffs and rework. Name the source or reported range; leave unknowns open. Do not sum overlapping activities as lead time. The result metric is this process's lagging indicator.

## Bottleneck

Which evidenced constraint currently limits the result or lead time, and what observation would refute that assumption? Capacity, missing input or a pending decision may constrain it. Faster isolated work does not establish improvement of the whole process. Preserve required human boundaries during redesign.

## Setup completion

Definition setup is complete when every `abnahme` component maps to a producing workstep output and applicable check, `einstieg_ref` and every workstep route can reach a declared end, each material claim has its source and evidence state, and every unresolved dependency names its next action and use restriction. Before the candidate commit, review a supported path, a missing or conflicting prerequisite and a plausible forbidden inference; record premises, expected outcomes and open gaps. After commit, the Test phase supplies observed harness evidence against that revision. Structural validity and design review do not establish execution readiness or the process result.
