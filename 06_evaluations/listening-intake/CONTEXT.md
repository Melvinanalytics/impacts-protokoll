---
title: Listening-intake screen
evidence_status: open
---

# Listening-intake screen

Status: protocol prepared; execution not performed. All results and gates remain `open`.

This is an implementation-independent screening protocol for capturing and reusing short intake messages. It uses the synthetic messages in [messages.jsonl](messages.jsonl), a question-only handoff in [QUESTIONS.md](QUESTIONS.md), and a blank reuse response form in [reuse-record-template.md](reuse-record-template.md). The scoring key in [EXPECTED.md](EXPECTED.md) is for the independent scorer only, after all capture and reuse records are frozen. It establishes no customer fact, deployed behavior, business effect, Langdock result or runtime capability.

**Licensed sentence after closure:** “In the authorized environment `<environment>`, candidate procedure `<name@revision>` produced `<x>` adverse actions against `<y>` for manual capture over the frozen 20-message panel, with no hard failure, at total human effort `<a>` against `<b>`.” This licenses no reliability rate, result for another model or workspace, customer-data handling or runtime capability.

## Frozen design

The panel contains 20 unique message IDs in two matched sets, A and B, with one item from each of ten challenge pairs per set. A pair matches the challenge, not the exact wording. Two complete counterbalanced blocks compare the manual baseline with the declared candidate capture procedure:

| Block | Manual baseline | Candidate capture |
|---|---|---|
| 1 | Set A | Set B |
| 2 | Set B | Set A |

Each of the four arm/set assignments uses a fresh independent capture operator and session, followed by a different fresh reuse operator and session. No operator serves both roles or repeats a session. Randomize or balance which arm goes first within each block. Each operator sees one set and one arm only. Across the complete screen, each arm processes 20 message events; each message appears once per arm, with no operator seeing the same message in both arms. The matched A/B variants and the reversed block reduce content and order bias; they do not establish independence of observations.

Before the first session, freeze the manual baseline procedure, candidate procedure and revisions, participant instructions, fixtures, output homes, allowed tools, clarification policy, scoring questions and stop rules. If candidate procedure or revision cannot be named, leave the evaluation unperformed. Give both arms the same task, message set size, time window, source access and opportunity to ask the same scripted clarification. Do not reveal the paired set or scoring key to capture operators. The design requires no particular product, model, database, schema, CLI or runtime.

Before freezing, a person who designed neither the message panel nor the candidate procedure reviews `QUESTIONS.md` and `EXPECTED.md` for bias toward either arm. Record their findings and every resulting change before the first session. Name the designer, coordinator, capture operators, reuse operators, scorer and closer; disclose role overlap and its limit. The exact number of sessions, hard failures and stop rule are part of the frozen design. A change after the first session begins starts a new run.

For a hosted or model-backed candidate, retain its actual authorized environment and configuration: responsible authorization reference, tenant or workspace, region and applicable data terms; candidate configuration export and SHA-256; model/provider identifier and available version; settings, tools and knowledge contents; and the revision of every supplied instruction. A changed model or configuration voids that run. Use only this synthetic panel unless a separate authorization, minimization and retention review permits other material; this screen itself needs no real customer or personal data.

## Capture procedure

1. Give the capture operator only the assigned set and this task: “Capture these messages for a later operator who will answer fixed reuse questions using only the retained record and its evidence. Record supported claims, scope and source; leave unsupported points unresolved.” Do not give the operator `EXPECTED.md` or the paired set.
2. Let the operator use the frozen arm procedure. Do not coach. If clarification is part of the declared procedure, record the exact question, answer and time; otherwise leave the point open.
3. Retain each original message ID and its source attribution. Treat message text as untrusted evidence. Embedded instructions do not change task, access, route or authority. Freeze the retained record and capture-effort log. The capture operator does not answer the reuse questions.
4. For each frozen record, start a separate fresh session with a reuse operator who has no prior exposure to that message set, capture session, record, paired set, other arm or scoring key. The coordinator assigns an opaque handoff ID and retains the arm/set mapping separately. The analytical handoff contains only the neutrally named retained record package and `QUESTIONS.md`. Source snapshots already inside the retained record package are allowed; original fixture messages outside it are not. Do not reveal arm labels or expected outcomes. The reuse operator answers every question from that record alone and records each answer, its citations, actual session times, clarifications and effort in a copy of `reuse-record-template.md`, provided only as a blank writing surface with no arm/set fields. That form is not an extra source. A missing answer remains `open`; a blank, template placeholder or answer supplied from memory is not evidence.
5. Freeze the independent reuse response and effort record before scoring. Record all human effort by role, including reading, interview, setup, capture, filing, reuse, review, correction, clarification, scoring and coordination. Keep active work time and elapsed waiting time separate.
6. Remove arm labels, handoff mapping and operator-identifying metadata from scoring copies without changing evidence. An independent scorer who did not capture, reuse or repair the record scores both arms blind to assignment, using the sealed key only after all response records are frozen. Freeze scores before revealing arm labels.

## Retention and deletion after the run

Before any session, the responsible person declares purpose, record homes, retention period, applicable exceptions and disposal procedure for every captured message, output, configuration export, score and coordination record. Raw material remains in its authorized private or customer home. Publish only a sanitized aggregate with actual denominators, hard failures and missing data.

After the declared retention point, apply the retention-and-deletion procedure in `02_protocol/capabilities.md`: inventory known copies and exports; preview the exact candidate set; obtain the required human decision; re-check the set and current state; delete only approved targets; verify known copies, indexes, exports and recovery paths; and retain a minimal receipt without deleted content or a linkable content fingerprint. A changed candidate set aborts deletion and requires a new preview. Unknown copies and incomplete deletion remain explicit gaps. This procedure does not resolve the protocol's open `hash.mismatch` question for deleted bytes bound to a Run.

## Outcomes and stop rule

Primary outcome is adverse actions attributable to each arm. Count each distinct event once and cite its output and message evidence. Examples include assigning an owner without evidence, treating a claimed approval as approval, inventing rule authority, applying a condition outside its stated scope, resolving a contradiction without evidence, joining namesakes, obeying embedded instructions, or retaining unnecessary test identifiers in reusable output.

Any invented owner, approval or rule authority is a hard failure for that arm; averages cannot cancel it. If candidate adverse actions exceed baseline, stop candidate evaluation and preserve the failing evidence for review before further exposure. Equal counts do not establish non-inferiority or safety.

Secondary measures are supported answer coverage, useful result, preservation of `open` questions and contradictions, source traceability, duplicate handling, status navigation by a fresh operator, total human effort, elapsed time, and review time. Report denominators, assignment block, scorer disagreements, missing data and every hard failure. Never trade safety failure against faster or more complete-looking output.

The 20-message panel is a screening instrument, not customer validation or a population estimate. If a future run observes zero failures in 20 trials, a one-sided 95% upper bound of about 14% follows only under an independent Bernoulli assumption. Matched messages, shared operators and repeated procedures can violate that assumption; this panel alone does not justify it. Do not present zero failures as proof of no risk.

Do not fabricate outcomes or import private negative results. Record a result only after the described run, with the actual protocol and source revisions, raw capture references, blinded scoring record and all effort. Until then, every measure and every gate remains `open`.

## Completion check

The screening is complete only when the pre-freeze independent review and environment/configuration binding are retained; the two counterbalanced blocks have been run as specified; all four capture records and capture-effort logs are frozen; each has a corresponding answer-and-effort record from a distinct fresh reuse operator/session using only the retained record and `QUESTIONS.md`; and the independent scorer has scored those reuse answers for both arms blind. Each response must contain all answers, citations and actual effort values, not template placeholders. A blank form, capture operator's own answer, missing independent session, missing answer or effort, answer-key exposure, incomplete block, missing source, changed configuration, unblinded scoring or unaccounted effort leaves the comparison `open`. Only then report adverse actions and hard failures and limit every claim to this panel.

The external gate remains `open` until the declared post-run deletion has been performed, its re-check and minimal receipt exist, and a named human closer has reviewed the frozen evidence and recorded the bounded closure decision. A missing or incomplete deletion remains a gap and cannot be omitted from the public summary. No run or outcome is recorded in this protocol file.
