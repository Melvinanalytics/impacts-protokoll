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

Capture the result's required conditions backwards and today's activities forwards, then match them under “Step areas” and “Result work and coordination” in `02_protocol/impacts-method.md` at the recorded protocol revision; “Minimize” proposes each move. Replace the synthetic rows with observed wording, sources and open questions. Ask a person only for a cell whose answer could change a proposed move. A `yes` states a scoped finding with its evidence label; it assigns no executor and grants no permission. The frontmatter `touchpoint` summarizes the capture; classify each customer interaction in its activity's “Decides or permits” cell.

### Required conditions

| ID | Condition | Imposed by and basis | Evidence |
|---|---|---|---|
| C1 | The requester receives a reasoned decision supported by recorded findings. | Recipient acceptance, expressly stipulated in this synthetic case | `reported`: synthetic premise; confirm with the responsible manager |
| C2 | A decision on the merits rests on a file that is complete under check catalog version 3. | Recipient acceptance expressly requires this criterion; it serves C1, without deriving its imposer from that dependency | `reported`; catalog revision `open` |
| C3 | A second person co-signs every notice. | Own rule; owner: head of department; whether the owner keeps it for the proposed design is `open` | `reported`; locate the rule and the applicable owner decision |
| C4 | The notice is retained for the statutory period. | Third-party obligation; legal basis `open` | `reported` |

### Activities in flow order

One row per activity; a repeated pass gets its own row. The columns follow the step areas; the analysis below supplies each activity's job.

| No. | Activity | Trigger and wait before | Takes, from where | Done by, with | Gives, to whom | Checks | Decides or permits | Next |
|---|---|---|---|---|---|---|---|---|
| 1 | Register the emailed request | Email arrives | Request with attachments, email inbox | Case worker, case system | Case record created in the case system by copying the request data, to the case worker's queue | None | None | 2 |
| 2 | Check completeness | Case record exists; waits in the queue (duration `open`) | File, catalog version 3 | Case worker | Finding recorded in the case system | Against the catalog | None | Complete: 6; incomplete, about 4 in 10 (`reported`): 3 |
| 3 | Ask the requester for missing documents | Finding: incomplete | Finding, requester's address | Case worker, email | Email request for documents, to the requester | None | Contact permitted (`open`) | Reply: 4; no reply within the deadline (`open`): 8 rejects as incomplete |
| 4 | Add the late documents to the case | Reply arrives after 2 to 10 days (`reported`) | Reply, email inbox; case record | Case worker | Documents copied from the email into the case file | None | None | 5 |
| 5 | Check completeness again | Documents added | File, catalog version 3 | Case worker | Finding recorded in the case system | Against the catalog | None | Complete: 6; incomplete: 3 |
| 6 | Prepare the check report | Finding: complete | File, catalog, completeness finding from 2 or the latest 5 | Case worker | Newly recorded decision findings and a full copy of every attachment, to the manager; not merely a copy of the completeness finding | None | None | 7 |
| 7 | Reread all attachments | Report arrives | Report, file | Manager | None | Completeness against the catalog | None | 8 |
| 8 | Decide | Rereading done, or no reply to 3 by the deadline | Report from 6; for a rejection without reply, the finding from 2 or 5 and the missed deadline | Manager | Decision recorded in the case system | None | Decides under a delegation rule (`open`) | Approve or reject: 9 |
| 9 | Draft the notice | Decision made | Decision, notice blank | Case worker | Draft notice created in the case system | None | None | 10 |
| 10 | Co-sign the notice | Draft ready | Draft notice | Deputy | Signed notice | None | Approves under C3 | 11 |
| 11 | Send the notice | Co-signed | Notice, requester's address | Case worker, post | Notice, by post to the requester | None | Customer touchpoint `standard` (`hypothesis`) | 12 |
| 12 | File the notice for retention | Sent | Notice | Case worker, archive | Notice copied into the archive | None | None | End |

### Analysis

| No. | Serves | Result work? | Coordination? | Failure demand? | Duplicate? | Excess? | Proposed move |
|---|---|---|---|---|---|---|---|
| 1 | Routes the request into processing | No | Yes; separated only by the email channel and the case system (`hypothesis`) | No; first pass | No | No | Remove the separation: intake writes the case record directly (`hypothesis`) |
| 2 | C2 | Yes (`reported`) | No | No; first pass | No | No | Keep; cannot be reduced further as far as C2 holds (`reported`); judge the queue before it under the timing rule |
| 3 | Missing input for C2 | No | Yes; the requester is a third party | Yes (`hypothesis`): the request form, upstream of this capture, does not ask for these documents; Identify inspects it | No | No | Report the form defect to its owner and correct the form; keep the request for files that still arrive incomplete |
| 4 | Missing input for C2 | No | Yes | Yes; follows 3 (`hypothesis`) | No | No | The same correction as 3 |
| 5 | C2 | Yes (`reported`) | No | Yes; follows 3 (`hypothesis`) | No; the material changed | No | The same correction as 3 |
| 6 | Recorded decision findings required by C1 | Yes (`reported`) | No for producing the findings; classify their handoff separately if it manages a dependency | No | No | Yes: the copies serve no condition or dependency after checking relevant recipients and duties (`reported`) | Trim the report to findings with links |
| 7 | C2 | Yes (`reported`) | No | No | Yes: the applicable check, 2 or the latest 5, checks C2 by the same catalog on the same file revision; no rule requiring a second check found (`hypothesis`) | No | Keep the applicable case-worker check and its evidence; the manager inspects cited items |
| 8 | C1 | Yes (`reported`) | No | No | No | No | Keep; cannot be reduced further as far as C1 holds (`reported`) |
| 9 | C1 | Yes (`reported`) | No | No | No | No | Keep; cannot be reduced further as far as C1 holds (`reported`) |
| 10 | C3 | Yes, own rule only (`reported`) | No | No | No | No | Ask the head of department to keep or change the rule |
| 11 | C1 | Yes (`reported`) | No | No | No | No | Keep; cannot be reduced further as far as C1 holds (`reported`) |
| 12 | C4 | Yes, third-party obligation (`reported`) | No | No | No | No | Keep (`reported`); confirm the legal basis before claiming more |

Each activity names a condition or dependency, and each condition names an activity. Keep unresolved answers open. `Neither` is a Minimize question, not deletion authority. Correcting 3 prevents the wait before 4 in later cases; judge the queue before 2 under the timing rule. For comparisons under one result boundary, population, period and unit, count non-overlapping observed effort once, under its activity's combination and proposed move; keep waiting separate and do not force a 100 percent pie.

## Stops and checks

In this example, the manager reads the report before deciding. Clarify why the human boundary is required, its decision scope and who may change it. Distinguish required authority, human interaction and habitual division of work. Name already permitted assistance and unresolved decisions.

For duration, define start and accepted end. Distinguish active work, missing inputs, handoffs, decisions and rework. Name sources/reported ranges; leave missing measurement open. While waiting, identify the missing information or decision and the contributions already possible within known rules and authority. Keep observations separate from proposed improvements.

## Reused definition and new run values

The check catalog, notice blank and responsibilities recur. Requests, attachments and questions belong to the case; its business record may outlive several process runs. Each run binds the necessary excerpt. Identify relevant offerings or domain subjects, instances/versions and their evidence. Link existing definitions and records rather than duplicating them.

## Result and acceptance

The notice goes to the requester. Record acceptance conditions under Required conditions; Current workflow names the activity that meets each. Include a payer only when relevant. For an offering, distinguish catalog promise, agreed scope and actual fulfillment. Apply the method's “Reverse-engineer a product or service”; name unsupported links and the next evidence action instead of inventing observed work.

## Participants

Synthetic roles: case worker, manager, deputy and the head of department as rule owner; the requester is an external participant.

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

Where do needed values, rules and blanks live, which system leads and where are copies? Use the data objects and facets in `02_protocol/impacts-architect/references/datenumgang.md`. Name their key/selection, revision or as-of date, actual read operation or provider, receiving input and required source check; use the calculation note above for a computed result's input-to-use path. Where freshness matters, name the update or review trigger and responsible maintainer; an unknown revision or as-of date stays `open`. Record missing access separately from missing data or unknown existence. Identify which processing is an existing instruction, implemented tool or proposed change. Illustrative evidence is a dated case-worker conversation record from 2026-09-02; it supports only a reported case claim and creates no `quelle:` address. The illustrative check catalog version 3 can be a reusable rule source when independently cited. Replace both with reachable evidence; neither asserts a real interview or catalog.
