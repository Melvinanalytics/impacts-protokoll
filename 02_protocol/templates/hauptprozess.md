---
type: hauptprozess
id: hauptprozess:prueffall
leistung:
  ergebnis: Decided review case
  kennzahl: Lead time from request to decision
  abnahme:
    - Check report is available
    - Decision is approved by the responsible human
  erreicht:  # optional: each end that achieves the Leistung
    - end:entschieden
einstieg_ref: arbeitsschritt:pruefen
---

# Decide a review case

The Hauptprozess is the root at `hauptprozesse/<slug>/CONTEXT.md`. This body carries Identify context for people and harnesses, not another schema. Replace every prompt and example value with this definition's content; delete optional blocks you do not use.

## Result and scope

State the Leistung, recipient, intended use and process boundary in one compact passage. Make `leistung.ergebnis`, `kennzahl` and every `abnahme` condition observable. For a result with more than one component, make the required components, assemblies and joints within the scope of this Hauptprozess's Leistung traceable under `02_protocol/impacts-method.md`, "Leistungsstückliste", including the Teilprozesse whose Arbeitsschritte produce or complete them. Having several components alone requires no separate list or additional assembly.

## Relevant environment

Recipient, participants, dependencies and result boundaries. Include market, demand or intermediary relationships only when relevant to the decision.

## Value flow

Valued result and recipient; customer, payer and external parties only where relevant. Link each required condition, with who imposes it and its basis, to its producing job, prerequisites and acceptance evidence. For retained coordination, link the dependency it manages. Link the analysis file for its evidence. Given a product/service, distinguish its promised or agreed scope from this process's result and actual fulfillment. Reference existing definitions and records; mark unresolved dependencies as `open` with their next action and use restriction.

## Objective and guardrails

One primary objective and observable acceptance. Protect quality, time and cost with decided guardrails, thresholds and acceptance limits.

## Touchpoints

Name each customer touchpoint of this process with its reason; its value, `standard` or `sacred`, is declared once in `customer_touchpoint` of the Arbeitsschritt that holds it (`02_protocol/impacts-method.md#identify` defines the values).

## Automation boundary

Which human boundaries apply, why, and who may change them? Input variance, result tolerance, harm, reversibility and detectability determine permitted assistance. Distinguish habitual division of work from required authority and actual availability; each Arbeitsschritt names its concrete contributions.

## Path to the result

Which Teilprozesse contribute to the result, how their prerequisites are obtained, and how success, rejection or an incomplete Vorgang ends or waits. List each `end:<slug>` that achieves the Leistung in `leistung.erreicht`. `einstieg_ref` and Arbeitsschritt routes own the sequence; this explanation does not maintain a second route table. Subject stages belong to the subject record under `02_protocol/binding.md#record-writeback`; progress weights belong in analysis.

## Setup completion

Definition setup is complete when every applicable required condition within this Hauptprozess's declared scope, including `abnahme`, required components, assemblies, joints, obligations and material prerequisites, traces to responsible work/check or an evidenced prerequisite and its use boundary. Conditions retain their role; they need not each become an output or new Arbeitsschritt. For a continuing duty, trace the action/control required within this process and its continuing owner; a seven-year retention duty does not require a seven-year active Vorgang. Completion also requires that `einstieg_ref` and every Arbeitsschritt route can reach an `end:<slug>` route, each material claim has its source and evidence state, and every unresolved dependency names its next action and use restriction. Before the candidate commit, write and review here a supported path, a missing or conflicting prerequisite and a plausible forbidden inference. For each, record its premise and expected result. Link the review evidence under `02_protocol/impacts-method.md#maintain-agent-instructions`.
