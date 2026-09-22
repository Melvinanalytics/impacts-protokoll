---
type: ist-prozess
name: Review and decide a request
owner: Case worker
frequency: Per request
trigger: Request arrives
inputs:
  - Request with attachments
outputs:
  - Decision notice
tools:
  - Email
  - Domain application
duration: Three days to two weeks
touchpoint: standard
evidence_status: reported
---

# Review and decide a request

Synthetic capture example. Reuse an existing source home; otherwise capture under `grundlagen/ist-prozesse/`. This is source material for Identify, never an Application itself. When starting from a product/service description or finished result, distinguish source claims from a reconstructed workflow (`hypothesis`); an unknown current workflow stays `open`. Replace example values in the customer's working language; the German counterpart is `de/ist-prozess.md`. Keep evidence labels and sources beside individual claims.

The illustrative `owner` attributes this capture to the named role. It establishes neither ownership of a rule nor decision authority; record those roles separately with their evidence.

## Current workflow

1. A request arrives by email and is registered.
2. A case worker checks completeness.
3. Missing information prompts a question; the case waits.
4. A check report precedes the responsible manager's decision.
5. The decision notice is sent.

## Stops and checks

In this example, the manager reads the report before deciding. Clarify why the human boundary is required, its decision scope and who may change it. Distinguish required authority, human interaction and habitual division of work. Name already permitted assistance and unresolved decisions.

For duration, define start and accepted end. Distinguish active work, missing inputs, handoffs, decisions and rework. Name sources/reported ranges; leave missing measurement open. While waiting, identify the missing information or decision and the contributions already possible within known rules and authority. Keep observations separate from proposed improvements.

## Reused definition and new run values

The check catalog, notice blank and responsibilities recur. Requests, attachments and questions belong to the case; its business record may outlive several process runs. Each run binds the necessary excerpt. Identify relevant offerings or domain subjects, instances/versions and their evidence. Link existing definitions and records rather than duplicating them.

## Result and acceptance

The notice goes to the requester; the responsible manager checks acceptance conditions. Include a payer only when relevant. For each required result component, identify its producing job, prerequisites and observable acceptance. For an offering, distinguish catalog promise, agreed scope and actual fulfillment. Apply the method's “Reverse-engineer a product or service”; name unsupported links and the next evidence action instead of inventing observed work.

## Participants

Synthetic roles: case worker, manager and requester during clarification; no external participant is asserted.

## Failure and detectability

A wrong decision may cause an appeal and become visible only then; the manager may detect an incomplete report earlier. Capture the actual harm and detection evidence.

## Observations and evidence

An observation is a bounded claim about a subject or case, recorded from a direct observation, source read, report or measurement. It is not the source/evidence artifact or a future workstep; recording it as an observation verifies neither the claim nor the artifact. Retain each relevant clock under its own meaning: event or validity time; source issue/as-of time or revision; actual observation, acquisition or read time; and recording time. Distinguish them whenever they differ, keep an unknown required time `open`, and never substitute one clock for another. Record the claim, evidence origin and label, relevant domain links and remaining gaps. A source-derived observation may restate or paraphrase what the source says, but it must not silently turn that statement into actual behaviour, cause, rule validity or authority. When another file independently cites the observation, give it a stable address under [domain addresses and relationships](../../ontology.md#domain-addresses-and-relationships). The reporter, input provider, calculator, maintainer, rule owner and decision authority remain distinct roles even when evidence shows that one actor performs several; support each assignment separately. An observation remains captured with its evidence status while its process assignment stays `open`.

## Calculations and decisions

For each relevant observed calculation or derivation, copy this case note once; list all figures it yields together. Give each independently cited observation about this calculation a stable address. For the concrete calculation occurrence, also retain its case-local key or source reference; this identifies the occurrence, not a second `rechenweg:` identity. Link the relevant metric definitions, rules and sources by their existing addresses, using optional local tokens only where needed, instead of making this note another rule master. Keep prescribed rule, observed practice and proposed change as separately evidenced scoped claims. If an observed formula materially differs from the prescribed one, give it another `rechenweg:` address only when it is independently cited, reused or changed; otherwise retain it in this case note. The workbook or code remains its implementation/evidence artifact. Mark an unknown answer `open` with its next evidence action.

- Result and meaning: Which figures were produced for which case, with what unit, population and period? Link the KPI definition where applicable.
- Prescribed rule: Where is the applicable rule held, which revision applies, who may change it and which controls are required?
- Actual calculation: Who calculated, where (including mental arithmetic or a personal spreadsheet), with which actual formula or artifact/revision, and who maintains it? What triggers recalculation or review?
- Inputs: For each used value, which source or provider, key/selection, validity time or revision, actual acquisition/read time and transfer path fed this calculation? Which source check was required?
- Check and acceptance: What condition made each figure usable by its dependent recipient, what check was actually performed, by whom or what, with which result and evidence? Was the figure accepted for its intended use, by whom or what, with which result and evidence? Keep unknown acceptance `open`; distinguish it from acceptance that the governing rule does not require. A required check alone does not prove performance.
- Destination and use: Where did each figure go, who used it, and for which next work, decision or customer output? A calculated figure alone authorizes none of these. Leave unknown use `open`; claim non-use only after checking relevant recipients, period and obligations, not from silence.

Record existing human, agent and deterministic contributions. Design their future mix only within clarified boundaries.

## Sources and freshness

Where do needed values, rules and blanks live? Name their key/selection, revision or as-of date, actual read operation or provider, receiving input and required source check; use the calculation note above for a computed result's input-to-use path. Where freshness matters, name the update or review trigger and responsible maintainer; an unknown revision or as-of date stays `open`. Record missing access separately from missing data or unknown existence. Identify which processing is an existing instruction, implemented tool or proposed change. Illustrative evidence is a dated case-worker conversation record from 2026-09-02; it supports only a reported case claim and creates no `quelle:` address. The illustrative check catalog version 3 can be a reusable rule source when independently cited. Replace both with reachable evidence; neither asserts a real interview or catalog.
