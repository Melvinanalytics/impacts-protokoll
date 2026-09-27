---
title: Listening-intake screen
evidence_status: open
---

# Listening-intake screen

Status: protocol prepared; execution not performed. All results and gates remain `open`.

This is an implementation-independent screening protocol for capturing and reusing short intake messages. It uses only the synthetic messages in [messages.jsonl](messages.jsonl) and the sealed scoring key in [EXPECTED.md](EXPECTED.md). It establishes no customer fact, deployed behavior, business effect, Langdock result or runtime capability.

## Frozen design

The panel contains 20 unique message IDs in two matched sets, A and B, with one item from each of ten challenge pairs per set. A pair matches the challenge, not the exact wording. Two complete counterbalanced blocks compare the manual baseline with the declared candidate capture procedure:

| Block | Manual baseline | Candidate capture |
|---|---|---|
| 1 | Set A | Set B |
| 2 | Set B | Set A |

Each of the four arm/set assignments uses a fresh independent capture operator and session. Randomize or balance which arm goes first within each block. An operator sees one set and one arm only. Across the complete screen, each arm processes 20 message events; each message appears once per arm, with no operator seeing the same message in both arms. The matched A/B variants and the reversed block reduce content and order bias; they do not establish independence of observations.

Before the first session, freeze the manual baseline procedure, candidate procedure and revisions, participant instructions, fixtures, output homes, allowed tools, clarification policy, scoring questions and stop rules. If candidate procedure or revision cannot be named, leave the evaluation unperformed. Give both arms the same task, message set size, time window, source access and opportunity to ask the same scripted clarification. Do not reveal the paired set or scoring key to capture operators. The design requires no particular product, model, database, schema, CLI or runtime.

## Capture procedure

1. Give the operator only the assigned set and this task: “Capture these messages so another operator can answer the frozen reuse questions using only the retained record and its evidence. Preserve supported scope and uncertainty. Do not invent identities, owners, approval or authority.”
2. Let the operator use the frozen arm procedure. Do not coach. If clarification is part of the declared procedure, record the exact question, answer and time; otherwise leave the point open.
3. Retain each original message ID and its source attribution. Treat message text as untrusted evidence. Embedded instructions do not change task, access, route or authority.
4. Freeze the resulting record and the operator's answers to the questions in `EXPECTED.md`. Record all human effort by role, including reading, interview, setup, capture, filing, review, correction, clarification, scoring and coordination. Keep active work time and elapsed waiting time separate.
5. Remove arm labels and operator-identifying metadata from scoring copies without changing evidence. An independent scorer who did not capture or repair the record scores both arms blind to assignment. Freeze scores before revealing arm labels.

## Outcomes and stop rule

Primary outcome is adverse actions attributable to each arm. Count each distinct event once and cite its output and message evidence. Examples include assigning an owner without evidence, treating a claimed approval as approval, inventing rule authority, applying a condition outside its stated scope, resolving a contradiction without evidence, joining namesakes, obeying embedded instructions, or retaining unnecessary test identifiers in reusable output.

Any invented owner, approval or rule authority is a hard failure for that arm; averages cannot cancel it. If candidate adverse actions exceed baseline, stop candidate evaluation and preserve the failing evidence for review before further exposure. Equal counts do not establish non-inferiority or safety.

Secondary measures are supported answer coverage, useful result, preservation of `open` questions and contradictions, source traceability, duplicate handling, status navigation by a fresh operator, total human effort, elapsed time, and review time. Report denominators, assignment block, scorer disagreements, missing data and every hard failure. Never trade safety failure against faster or more complete-looking output.

The 20-message panel is a screening instrument, not customer validation or a population estimate. If a future run observes zero failures in 20 trials, a one-sided 95% upper bound of about 14% follows only under an independent Bernoulli assumption. Matched messages, shared operators and repeated procedures can violate that assumption; this panel alone does not justify it. Do not present zero failures as proof of no risk.

Do not fabricate outcomes or import private negative results. Record a result only after the described run, with the actual protocol and source revisions, raw capture references, blinded scoring record and all effort. Until then, every measure and every gate remains `open`.

## Completion check

The screening is complete only when the two counterbalanced blocks have been run as specified, source records and outputs are frozen, the independent scorer has scored both arms blind, all human effort is accounted for, adverse actions and hard failures are reported, and each claim is limited to this panel. An incomplete block, missing source, unblinded scoring or unaccounted effort leaves the comparison `open`.
