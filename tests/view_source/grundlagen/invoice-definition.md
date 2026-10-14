# Invoice-entry meaning and source requirements

Revision: `candidate-v2`; namespace is declared in the [root router](../CONTEXT.md).
`reported` claims below refer to the preserved [synthetic SOP](invoice-source.md#supplied-procedure). They report a procedure, not observed execution, adopted rules or legal authority. Target interpretations are `hypothesis`. This file is the single reusable rule/source home; bind the needed content as `input/rules.md` with separate provenance in future attempts.

## Result boundary

One incoming vendor invoice for a normal operating expense is the proposed case grain. Refunds and credit-card charges are excluded. Known duplicates belong to an unsupplied duplicate process. A reported acceptable end has a correct QuickBooks bill, invoice attachment, payment scheduled **or marked for approval**, and the original in Drive under `Invoices/Vendor/YYYY-MM`, with no duplicate and resolved issues. Actual payment is later and outside this result. Global completeness of incoming invoices cannot be inferred from one bill; the intake population/reconciliation source is open (G2).

Accounting is the proposed receiving role for this candidate (`hypothesis`); the SOP names Accounting as answering questions, not explicitly accepting every result. Confirm recipient and acceptance authority under G1. Office Manager is the reported document owner and escalation contact, Office Coordinator the primary performer, Owner/Finance an approver when required. These role labels neither identify individuals nor establish rule ownership, access rights or delegation. “Owner” in the no-PO instruction remains ambiguous.

## Conditions and their independent bases

| ID | Condition | Imposer / basis | Claim evidence |
|---|---|---|---|
| C1 | Correct vendor, invoice number/date, amount, due date, category or applicable customer/job in the bill | SOP purpose, rules, rows 4–5 and checklist; actual recipient/imposer open G1 | reported |
| C2 | Search vendor name and invoice number before creation; no duplicate; no missing invoice within an established intake scope | SOP result, row 2 and verification; independent recipient or own-rule basis open G1/G2 | reported |
| C3 | PDF attached to bill | SOP row 6 and verification; imposer open G1 | reported |
| C4 | Payment scheduled if approved, otherwise marked for approval | SOP result and row 7; imposer and approval scope open G1/G4 | reported |
| C5 | Original saved in Drive in the prescribed location | SOP row 8 and verification; imposer open G1; no statutory retention basis supplied | reported |
| C6 | Match PO if available; where no PO, check with Owner **before entry** | SOP rules and exception; imposer/meaning of Owner open G1/G4 | reported |
| C7 | Above $1,000, obtain approval before scheduling payment | SOP rule and exception; rule owner and currency basis open G1/G3/G4 | reported |
| C8 | Resolve issues; missing information requires vendor update; uncertain category follows stated consultation | SOP exceptions, checklist; imposer open G1 | reported |

The relationship C6 → permission to proceed with entry and C7 → permitted scheduling have different timing and objects. A consulted person is not automatically the scheduling decision holder. C5 serves the accepted storage state even though it transfers existing bytes. None of these bases establishes a law, retention duration, independent reviewer duty or authority to delete a check.

## Case identity and interpretation

Retain original document locator, original media type, exact byte digest, provider and revision/read time. Vendor name plus invoice number is the reported search selection, not a proven unique or idempotency key. QuickBooks tenant, vendor record ID, bill ID/revision, search coverage and Drive object ID/version must be resolved before dependent writes. A search returning nothing proves no duplicate only within its adequate checked scope; no source establishes that scope yet (G2).

Copy amounts exactly from the controlled source with their currency. The `$` symbol does not establish a supported currency mapping. For a confirmed matching currency, the reported threshold comparison is strictly `amount > 1000`; equality does not trigger this threshold alone and does not grant scheduling permission. Use fixed decimal arithmetic in the future configured checker, never model arithmetic or guessed conversion. Original date fields and filing `YYYY-MM` are separate: the SOP does not identify which date determines the folder (G3).

Unclear category: the SOP says “best fit and add a note; ask Accounting if unsure.” Preserve that wording. No supplied chart, tolerated uncertainty or determination of when a guess is acceptable exists. Prepare a noted candidate and ask Accounting where uncertainty remains; do not present the proposal as a verified correct category. A returned answer supplies evidence only for its stated scope.

## Sources and acquisition

| Needed source | Reported home/form and proposed provider | Required selection/control | Current finding |
|---|---|---|---|
| Original invoice | Gmail PDF or paper/photo/scan; Office Coordinator provides original bytes | Case locator, vendor/invoice reference, MIME, revision, legibility, exact original; verify any derived PDF against original | Procedure described; no case acquired |
| PO or pre-entry consultation | Supplied PO or actual Owner response; Coordinator obtains | Exact invoice and PO scope, applicable revision, consultation before entry; resolve Owner identity | Existence/access/rights open |
| Coding and vendor details | Chart-of-accounts/coding information and vendor list; Accounting supplies controlled excerpt | Tenant, vendor identity, allowed category/customer/job, currency, effective time, provenance | Mapping and actual provider authority open |
| Existing bills and final bill | QuickBooks named by SOP; configured reader/operator open | Vendor/invoice search coverage before write; bill ID/revision readback after write | No interface, access, readback or repeat-safe mechanism demonstrated |
| Original storage | Drive location named in SOP | Vendor/folder mapping, date basis, original bytes and stored object confirmation | No mapping, access or permission demonstrated |
| Approval and permissions | Actual authorized holder/authority record | Specific decision object/revision, permitted consequence, validity, current-state conflict check | Named role labels only; authentication and adoption absent |

No API, integration, endpoint or product feature is asserted. Access verification, acquired data, permitted use and a documented source are separate findings. Email/Slack may carry communication only after its exact sender, recipient, content scope and sending permission are established.

## Bound inputs and provenance

This scoped instruction excerpt preserves the frozen protocol's binding contract and provenance labels; those sources own their reusable meanings. It accompanies this definition in each declared `input/rules.md`, with the rule-source revision/provenance. It adds no source truth, effect permission or authentication. The responsible configured harness must apply the canonical opening contract; G5 keeps that configuration unestablished.

The harness materializes every declared input before opening, with separate provenance containing Local input, Origin / locator, Source state, Acquired by / provider, Acquired at, Selection, Content-Digest, Required control and Actual control. Upstream handoffs preserve byte-identical content, attempt-qualified origin and SHA-256; source state and actual acquisition time remain distinct. Missing inputs leave the previous state unchanged. Newly acquired evidence becomes the job's declared output with provenance and use restrictions, then a declared new attempt's input; never replace bound bytes. Each workstep owns its specific acquisition, opening controls and handoff mappings.

## Setup gaps and restricted uses

| Gap | Next evidence action / responsible contact | Dependent use restriction |
|---|---|---|
| G1 — recipient, acceptance, condition imposers and adopted rule revisions | Ask Office Manager to identify applicable recipient, rule owners and authorized design reviewer; obtain their actual decisions and rule revisions | No adoption, removal/combination of required controls, or operational acceptance claim |
| G2 — invoice/tenant/vendor identity, search coverage, intake census, missing-invoice check | Accounting and source maintainer supply mappings and bounded intake reconciliation; execute checks on that scope | No duplicate-safe create or “no missing invoices” claim outside established scope |
| G3 — coding, currency and filing-date mapping | Accounting/source owner supplies applicable coding/currency rules and date-to-folder mapping | No guessed category, currency conversion, threshold applicability or filing location |
| G4 — Owner identity, consultation meaning, scheduling rights and effect permissions | Office Manager locates actual holders; obtain scope-bound access, message and write permissions plus human decision evidence | No pre-entry bypass, scheduling without applicable approval, inferred delegation or automatic release |
| G5 — concrete readers/writers/checkers and repeat-safe operations | Responsible harness implementer and system owner configure versioned operations, controls, confirmation and reconciliation on permitted fixtures | No real system operation, external message, live check, retry or execution-readiness claim |
| G6 — wait follow-up, due times and escalation scope | Office Manager identifies follow-up responsibility, review trigger and permitted fallback for each missing document/PO/category/decision and partial write | No invented deadline, timer execution, automatic rejection or approval; dependent work stays pending |
| G7 — checklist/verification checker, multiplicity and review purpose | Office Manager/Accounting explain actual checks, timing, material revisions and essential review decisions | No baseline duplicate-check deletion or assertion that one check replaces independent obligations |
| G8 — unsupplied duplicate procedure and unsupported vendor/currency handling | Accounting supplies applicable duplicate home; rule owner resolves uncovered operation and handling | Do not execute unknown procedure, create vendor, convert currency or invent an exception route |

Closing one gap unlocks only the contribution for which all other prerequisites also hold. Gaps do not block this synthetic design or independent permitted preparation.
