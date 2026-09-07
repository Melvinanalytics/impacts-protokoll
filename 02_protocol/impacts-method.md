# IMPACTS build method

IMPACTS turns observed customer work into an optimized Application. The observed process remains source evidence. The Application becomes the reusable target process for new Vorgänge.

The protocol is domain- and use-case-agnostic. It defines the result boundary, process topology, local orientation and where verification belongs. Domain rules and calculations stay in their existing Fachrepo or workspace homes; the Application references them rather than making them protocol requirements. A commercial funnel, valuation method or feasibility criterion is not a universal process model.

First use the Architect's [form selection](impacts-architect/references/formwahl.md). The seven phases below apply only after selecting a Pipeline that will become an Application; Record Libraries, Knowledge Bundles, Context Maps and other non-process forms do not enter Identify.

```text
Identify -> Minimize -> Perfect -> Augment -> Construct -> Test -> Scale
```

## Identify

Describe the work before changing it. Start with the intended recipient, accepted Leistung and relevant boundary; use the following perspectives only where they affect the next decision:

- Relevant environment: participants, dependencies and constraints that affect the Leistung. Include market, demand or access relationships when they matter; an internal process need not have a market funnel.
- Value flow: value object, recipient and, where relevant, customer, payer or external participant.
- Performance: one primary outcome, its lagging indicator and controllable leading indicators. Consider margin, throughput, cycle time, attention and customer satisfaction where they affect the Leistung.
- Magic Triangle: improve speed, quality or cost while explicit guardrails protect the other dimensions.
- Process physics: throughput, cycle time, work in progress and the current constraint.
- Human boundaries: Customer-Touchpoints and internal Human Gates.
- Automation boundary: input variance, result tolerance, possible damage, reversibility and detectability.
- Calculated results: accepted output, sanctioned rule, parameters, actual source and stand, required control and allowed business use.

Do not assume the useful boundary starts at an incoming request. Inspect upstream causes or downstream use when evidence suggests they constrain the outcome; do not require a complete market or organization inventory. Under the Application's existing `Zielgröße und Guardrails`, record the bounded question or intervention, its evidence and unknowns, responsible decision-maker, intended observable effect and conditions for reassessment or stopping. Missing evidence may make observation the next step rather than automation.

Keep metric meaning with its existing definition: what is counted or assessed, unit, relevant population or time basis, source and comparison. Missing is not zero; a reported estimate is not an observed result. Channel attribution and causal effect are different claims where channels are relevant. These distinctions require no new status vocabulary or universal metric schema.

A Customer-Touchpoint creates trust, advice, commitment or experience. `standard` keeps the interaction human and prepares it with better information. `sacred` protects the interaction until a human approves a changed classification.

A Human Gate controls risk or authority. The agent prepares short, inspectable evidence. The human decision remains in the Vorgang.

Before redesign, identify where a person must interact, judge or authorize, why that boundary exists and who may change it. Distinguish a required boundary from a current staffing habit or temporary lack of data or tools. An unresolved permission does not authorize automation across that boundary. Preparing evidence can be automated without transferring the decision itself.

For each Arbeitsschritt, distinguish the human contribution, agent reasoning and deterministic system processing that are actually needed. These are composable contributions, not three mandatory actors, three new steps or exclusive step types. Identify sets their constraints; Augment selects the execution mix within them. Rule-based processing still needs correct inputs and a valid rule; an agent proposal does not supply missing authority.

Define the start and accepted end of the process-time comparison. Separate active work from waiting for inputs, queues, handoffs, decisions and rework where relevant. Use existing traces or explicitly reported ranges; unknown timing can require a small observation first. Do not obtain end-to-end duration by adding overlapping activities or confuse elapsed duration with total labor effort.

## Minimize

Remove work that does not contribute to the Leistung. Challenge handoffs, waits, duplicate capture, role boundaries and data movement. Working hours, organizational history and current staffing do not define the target process.

Combine or remove work only while preserving the identified authority and customer boundaries. Reduce avoidable waiting around required human decisions by preparing usable evidence and a workable handoff; do not erase the decision to make the diagram shorter. Actual availability remains a feasibility constraint even when current role boundaries are challenged.

## Perfect

Close the remaining path. Every Arbeitsschritt receives declared inputs, visible outputs, one verification rule and complete routes. Each step must contribute to its Teilprozess and the Hauptprozess must end at its Leistung.

Use **Reverse Engineering der Leistung** for every calculated result:

```text
Leistung -> accepted result component -> producing Arbeitsschritt -> sanctioned calculation rule -> parameter -> actual source
```

For each parameter record meaning and unit, origin, stand, required control and actual control evidence. The Application names expected source and minimum control. The Vorgang materializes actual input bytes and provenance before hashing. Extract a Capability only when the [Capability-Regel](capabilities.md) earns that boundary.

## Augment

Assign each remaining part to its best execution form. Deterministic calculations stay in the workstep or an earned Capability. The model handles variable language and context. People retain customer interaction, judgement and authority where the identified boundary requires them.

Every calculation has a sanctioned rule even when it remains local. A Capability returns a visible technical result; the Arbeitsschritt adds business verification, Nutzungsgrenze and route. A permitted `hypothesis` names impact and validation action. An irreplaceable missing value stays `open` and produces a focused question.

## Construct

Write one Application as `CONTEXT.md` files. The folder tree carries containment. `einstieg_ref` and Arbeitsschritt routes carry execution order. The Markdown body gives the current step its processing instructions.

## Test

Run representative Vorgänge against a baseline. Compare the primary outcome, guardrails, throughput and failure cases. Treat a leading indicator as a hypothesis until observed runs support its relation to the outcome.

Keep structural validity, correct domain processing and observed benefit separate. A successful validator run proves only its declared checks. For a shorter-process claim, use Identify's time boundary, include preparation, review and rework, and check whether waiting or backlog merely moved to another participant. Report labor savings separately and retain the agreed guardrails. Without a defensible comparison, leave the effect unproven; a consistency repair does not require a business-time improvement unless it claims one.

## Scale

Commit the tested Application revision and use it for new Vorgänge. Existing Vorgänge remain bound to their historical revision. A later improvement produces another reviewable Application revision.

Transfer only within the demonstrated domain and operating assumptions. Reusing the protocol in another Fachrepo does not transfer its predecessor's business rules, approvals or effect claims. Reassess the limiting dependency after a change; a faster step may merely move the constraint.

An Application moves between repositories as a byte copy of `applications/<slug>/`:

Use a new target directory; if it already exists, review the update and its referrers before changing it. Do not overlay an archive on existing work.

```bash
mkdir -p applications/<slug>
git -C <source-repo> archive <commit>:applications/<slug> | tar -x -C applications/<slug>
git add applications/<slug>
git commit -m "import applications/<slug> from <source>@<commit> (tree <oid>)"
```

The tree oid is content-addressed, so `git rev-parse HEAD:applications/<slug>` yields the same value in both repositories; that equality is the proof of origin. Provenance lives in the commit message, never inside the tree: one changed byte changes the oid. Running Vorgänge keep their oid after a later import; new Vorgänge bind the new one.

If the imported Application has Capability calls, materialize each referenced `capabilities/<slug>/` tree separately from the same source-repository commit at the same relative path. Commit it, then require `git rev-parse HEAD:capabilities/<slug>` to equal the Application's bound Capability Tree-OID before the first Vorgang. An Application-only import remains valid only when it has no Capability call. The cold walk proves both the missing-Capability rejection and the executable import.

## Load context locally first

Start at the closest `CONTEXT.md` and follow only the Markdown links needed for the current stage or question. If an already recorded fact is not reachable through that path, repair the existing router, link or source binding at the fact's single home before adding another summary.

External research is ingestion. Use it only when the local path exposes a real evidence gap, the requested freshness exceeds the local source state, or the user explicitly requests new external evidence. Any optional graph projection or database follows the single [Tooling-Stopp](impacts-architect/references/formwahl.md#tooling-stopp).

## Where the context lives

The Application body explains the relevant environment, value flow and optimization contract. The embedded Leistung holds the result, its main metric and acceptance conditions. A Teilprozess body explains its contribution and leading indicator. An Arbeitsschritt owns inputs, outputs, verification, routes and optional human markers.

These are human-readable instructions in existing files. They add no schema, state machine or execution engine.

Stable material stays at one source home. A run materializes the smallest professionally sufficient source or projection plus separate provenance under attempt `input/`. A step handoff declares `output -> input`; the run binds byte content, attempt-qualified origin and content digest. Details remain solely in the [Capability-Regel](capabilities.md).

## Review another Fachrepo

Name the protocol revision actually used before assessing compatibility. Check its machine-readable structure against that revision; do not treat a successful check against an older pin as compatibility with this one. Select the applicable [Walk test](impacts-architect/SKILL.md#walk-test): Process Walk for Applications, Knowledge Walk for records and fachliche Grundlagen, both for mixed forms. Exercise domain processing and outcome checks separately where required. Legitimately missing evidence produces a focused question; unreachable existing evidence requires a routing repair.

A later nodes-and-edges view is a disposable projection, not a second authority. Containment comes from folders, execution edges from `einstieg_ref` and routes, and knowledge links from their source files. Preserve these different meanings and the source revision; do not infer execution order or causal influence from an ordinary hyperlink. Graph construction is not a prerequisite for reading, validating or transferring a repository.

## Readability and processing

Apply these acceptance questions to existing surfaces at capture, processing, verification, change and handoff:

- UX: Can the responsible person understand what is needed, why, and the consequences of their decision?
- AX: Can the agent find unambiguous inputs and sources, permitted actions and boundaries, or ask the specific unresolved question?
- DX: Can a developer locate the authoritative contract, responsible implementation and applicable verification and change path?

Human-readable meaning and machine-readable fields must agree. Different views use the same authoritative definition. These questions add no mandatory fields or documents; fix the existing rule, wording or link when a reader cannot apply it.
