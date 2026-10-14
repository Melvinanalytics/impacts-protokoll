---
type: hauptprozess
id: hauptprozess:invoice-entry
leistung:
  ergebnis: Correctly recorded vendor invoice with its original retained and payment scheduled or marked for approval
  kennzahl: Elapsed time per eligible invoice from receipt to confirmed accepted entry and disposition
  abnahme:
    - Bill fields match the controlled invoice and applicable coding and PO evidence
    - Required duplicate and bounded intake-completeness checks have usable evidence
    - Required PDF attachment and original Drive filing are confirmed
    - Scheduled payment has applicable approval or the bill is confirmed marked for approval
    - Issues affecting the accepted entry are resolved and pending approval follow-up is explicit
einstieg_ref: arbeitsschritt:prepare-entry
---

# Enter a vendor invoice

`hypothesis`: unadopted target design `candidate-v2`, derived from the [preserved SOP](../../grundlagen/invoice-source.md). Reported rules, definitions and gaps have their single home in the [invoice definition](../../grundlagen/invoice-definition.md). This Application is design only; it grants no access or effect permission.

## Result and scope

Prepare one normal operating-expense invoice for the proposed recipient Accounting. The embedded result retains the SOP's scheduled-or-pending alternative. Refunds, credit-card charges, duplicate-process execution and actual payment are outside scope. This bounded result is supported by the described procedure; recipient acceptance and the scope of “no missing invoices” remain G1/G2, so no operational success may yet be claimed.

## Relevant environment

The SOP names Office Coordinator, Office Manager, Accounting, Owner/Finance, QuickBooks, Drive, Gmail and Slack. [Source mappings and distinctions](../../grundlagen/invoice-definition.md#sources-and-acquisition) retain what is known and missing. No product capability, legal requirement, current frequency or actual staffing arrangement is inferred.

## Value flow

| Accepted component | Producing job and prerequisite | Receiving use and evidence |
|---|---|---|
| Correct record with pre-entry support (C1/C6/C8) | [Prepare entry](entry/prepare-entry/CONTEXT.md) establishes evidence; [Record and file](entry/record-and-file/CONTEXT.md) uses it | Final confirmation consumes checked source-to-bill comparison and confirmed bill identity |
| No duplicate and bounded completeness (C2) | Prepare entry identifies scope and search evidence; Record and file refreshes action-boundary conflicts | [Confirm disposition](disposition/confirm-disposition/CONTEXT.md) inspects actual check scope and acceptance evidence; G2 restricts claims |
| Attachment and original storage (C3/C5) | Prepare entry retains the original when its independent prerequisites permit; Record and file carries that evidence, supplies attachment and safely completes any remaining storage work | Confirm disposition consumes separately confirmed attachment and Drive states |
| Scheduled or pending (C4/C7) | [Decide scheduling](disposition/decide-scheduling/CONTEXT.md) supplies required new human decision only when requested; Confirm disposition applies a covered existing decision or pending alternative | Accounting receives actual disposition confirmation; opening a gate supplies no decision |
| Resolved issues and continuing follow-up (C8) | Prepare entry resolves entry blockers; Confirm disposition distinguishes permitted pending approval from unresolved acceptance defects | Final evidence names remaining approval action, holder and trigger; G6 prevents claiming a functioning monitor |

Each condition's independent imposer and source remains in the definition's conditions table. The necessary information transfer and distinct pre-entry versus final-bill decision objects survive this cut. No baseline duty is deleted. Screen navigation is contained within the record job; this reduces contract fragmentation, not measured work. [Capture analysis](../../grundlagen/ist-prozesse/invoice-entry.md) retains uncertain removals and separate M1/M2 proposals.

## Objective and guardrails

Proposed objective: reduce avoidable total entry lead time without losing field accuracy, evidence, originals, completeness, duplicate protection or authority. Baseline duration, effort, backlog and defect frequency are open. Next observation: Office Manager identifies a permitted representative invoice trace and Accounting identifies actual check purposes and boundaries. Compare receipt-to-accepted-result elapsed time and separate labor, decision wait, preparation, review and rework before adopting a change. Stop or revise a simplification if required evidence disappears, duplicates/incorrect coding increase, or downstream effort merely moves. Improvement remains unproven.

## Touchpoints

No customer interaction is established. Vendor update requests are external supplier communications under the prepare job's permission boundary; an SOP instruction is not evidence of a configured sending right. Internal decisions remain at their stated boundaries. Do not invent a protected customer classification.

## Automation boundary

People retain actual decisions and unresolved accountable judgments. The proposed agent assists with extraction, comparison explanations and request drafts; fixed comparisons and identity/control checks require deterministic or accountable actual checking. Actual operations and versions remain G5. Incorrect amount, duplicate bill, wrong recipient or premature scheduling could cause financial harm; some errors appear only after effects, and reversibility is unknown. No autonomous write or model-only release is authorized by this candidate. G1/G4/G7 identify who must settle essential review and authority.

## Path to the result

[Entry](entry/CONTEXT.md) supplies a confirmed bill and stored original. [Disposition](disposition/CONTEXT.md) supplies approval evidence when needed and confirms the scheduled/pending end. The entry and workstep routes own execution. Out-of-scope, duplicate-excluded and incomplete ends do not achieve this result. Current waits keep their step; the gate has no timeout approval. Later payment and continuing approval monitoring remain outside the accepted entry result and require their own supported operating home.

## Throughput and lead time

One case is one eligible invoice. Start: actual invoice receipt; end: all acceptance evidence confirmed, including an allowed pending disposition. Time unit for an eventual comparison: elapsed hours, using actual event timestamps. No measured values, SLA or throughput/WIP estimates exist. Active effort, waiting, handoffs and rework require separate observation; do not add overlapping durations.

## Bottleneck

`open`: no observed bottleneck. Approval or incomplete information may constrain a case (`hypothesis`); E1 illustrates a stipulated delay, not baseline frequency. Compare actual contribution-ready and decision-available timestamps before changing sequencing or staffing.

## Setup completion

The required components map to producing jobs and outputs above; open premises are G1–G8 with next actions and restrictions. Author report records supported, missing/conflicting and forbidden-inference design cases plus actual static checks. This is a reviewable candidate with operational blockers, not an adopted or execution-ready definition. No Run, human approval, actual check of a bill or business result has been produced. The unavailable applicable Core validator and any static limitations remain in the report.
