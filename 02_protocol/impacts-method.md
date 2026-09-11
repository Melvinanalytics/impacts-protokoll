# IMPACTS build method

IMPACTS designs the necessary work backwards from an accepted result. Observed customer work supplies evidence about information, dependencies and protective functions. The Application becomes the reusable target process for new Vorgänge.

The protocol is domain- and use-case-agnostic. It defines the result boundary, process topology, local orientation and where verification belongs. Domain rules and calculations stay in their existing Fachrepo or workspace homes; the Application references them rather than making them protocol requirements. A commercial funnel, valuation method or feasibility criterion is not a universal process model.

First use the Architect's [work report and form selection](impacts-architect/references/formwahl.md#arbeitsbericht-vor-baumvorschlag). The seven phases below apply only after selecting a Pipeline that will become an Application; Record Libraries, Knowledge Bundles, Context Maps and other non-process forms do not enter Identify. Every form uses [Reviewed correction](#reviewed-correction) when an observed defect or repeated friction needs a change.

```text
Identify -> Minimize -> Perfect -> Augment -> Construct -> Test -> Scale
```

## Capture business meaning

For every ICM form, the method guides how business meaning is elicited and linked. The customer supplies the actual vocabulary, relationships, rules and source bindings. These distinctions belong to the capture method; they do not add business entities to the executable Core schemas.

Start with the intended result and recipient, then inspect one relevant source or case. Reuse existing evidence. Ask only the unresolved questions needed for the next decision:

| Interview question | What the answer establishes |
|---|---|
| What should the recipient receive, and what makes it usable? | Required result, acceptance and scope. Keep a reported wish, existing obligation and proposed improvement distinguishable. |
| What product, service or other subject is involved: a reusable kind, requested or offered scope, an agreement, or something actually delivered? | Relevant business objects and their distinct meanings. Capture products/services when the business offers them; an internal assessment need not invent a catalog or contract. |
| Which particular objects, versions and states belong together? | Identity, participant roles, relevant relationships and their multiplicity. Keep each object's state distinct from the process run. Existing source keys or stable file references may suffice; names alone do not establish identity. |
| Which information and rule justify each required result component? | Applicable meaning and derivation; separate rule definition from this case's values and observed result. Use [Data Governance](capabilities.md#data-governance) and, for calculations, [Perfect](#perfect) for the required binding and checks. |
| Where is each needed fact maintained, how can it be obtained, and who may change it? | Authoritative source, actual key/field or document location, usable access and update responsibility. Missing access, missing data and unknown existence are different findings. |

For commercial work, link fulfillment evidence to the applicable agreed items, quantities and version. The embedded `Leistung` defines the process result, metric and acceptance; the offering and continuing agreement retain their domain definitions. The [backward trace](#reverse-engineer-a-product-or-service) establishes their relationship to processes without prescribing a commercial lifecycle or set of tables.

**Capture → clarify → bind:** Preserve each relevant source statement with its origin and [evidence label](impacts-architect/references/zuschnitt.md#evidence). Place it and its proposed interpretation at the existing or smallest populated home under [Formwahl](impacts-architect/references/formwahl.md#native-topologie-und-schnitt). A useful follow-up distinguishes interpretations that would change a result, check or permission. Keep a discovered rule distinct from a newly authorized decision. Use clarified definitions for binding work; drafts may retain explicit assumptions within their permitted use. If no rule exists, retain a decision question or limit use. Make corrections reachable from the affected claim's home. Known facts need not be re-elicited.

The customer's foundations hold definitions and source mappings. An Application links the relevant business definitions and record homes in its `Value flow`; it does not copy their facts. Continuing instances live in their designated source system or maintained records; a run binds the needed excerpt and provenance as inputs and records its results as outputs. A confirmed storage gap may justify a maintained file/table; unavailable access alone does not justify a competing master. Relevant changes require checking affected uses while preserving historical evidence. Transferring a run's result into a business record follows the separately permitted [writeback](capabilities.md#rückübertragung-in-geschäftsrecords).

**Stop when** each needed result component has an inspectable path through meaning, identity/relationship, source or sanctioned derivation and verification—or a named gap with its next evidence action/decision and effect on use. Check that path against the selected case; involve the responsible person for unresolved meaning or decisions. This closes the bounded capture, not the open gaps or result acceptance. Confirm or revise the provisional form under Formwahl; only a bounded repeatable process earns an Application. The applicable Architect Walk tests navigation or process structure separately; it does not replace the required factual or calculation checks.

Use the [Author or change](ontology.md#author-or-change) branch for new or changing meaning and the [Use](ontology.md#use) branch for existing definitions. Define meaning once; declare each operation’s needed conditions at its boundary. Routine use does not refill the model. Customer-readable work follows the bound [working language](language.md#enforce-at-use-boundaries), including its actual check before use. The [worked company example](impacts-architect/references/datenbezug.md#from-catalog-through-pipeline-to-a-filled-offer) connects catalog, pipelines, document blanks and run instances.

## Reverse-engineer a product or service

Use a supplied catalog, service description, agreement, finished artifact or observed case as evidence for [capture](#capture-business-meaning), even when no workflow is documented. A promise describes an intended result; it does not prove how work currently happens or that delivery is feasible. Preserve the observed process separately from the proposed target.

1. **Choose one result boundary.** Identify the offering/subject and applicable version, recipient, trigger and accepted end state. Name inclusions, exclusions and observable acceptance. Keep promised, agreed and actually delivered scope distinct. Missing acceptance remains a decision question.
2. **Trace every required result component backwards.** Use the chain below for documents, decisions, calculations and real-world effects. Inspect one source case where available; otherwise mark the reconstruction `hypothesis`. For physical work, name the performer and delivery evidence; producing a document does not perform that work.
3. **Resolve each prerequisite.** Follow dependencies until each leaf is an obtainable source, an applicable bound rule, an available resource or a responsible decision. Name its acquisition operation, owner, required check and permitted use. Mark missing access, unknown facts and contradictory rules separately; a circle of mutually assumed results is unresolved.
4. **Cut the process by accepted contributions.** If no bounded repeatable result is established, retain the selected knowledge form and open questions. Otherwise apply the [Leistung and boundary rules](impacts-architect/references/zuschnitt.md#leistung): independent accepted results earn separate Applications, coherent context sections become Teilprozesse, and separately checked jobs or authority boundaries become Arbeitsschritte. One offering can need several processes; one process can serve several offerings. Recurring services need a bounded case or period and completion evidence; scheduling further runs belongs to the harness.
5. **Establish the forward check.** The process description states obtainable entry inputs, the producer-output → consumer-input handoff at each boundary, and every outcome's route, end or wait with a usable continuation. Check a supported case, a missing prerequisite and a plausible forbidden inference. Record expected outcomes separately from observed execution evidence; an unexecuted design remains unproven.

```text
Accepted result -> required component/effect -> producing job -> inputs + rule + resources + authority -> actual source or decision
```

Put this trace in the existing Application `Value flow` and workstep input/processing sections; before a Pipeline is justified, keep it at the selected source/domain home. Apply capture's completion condition to every required component. Execution readiness additionally requires the prerequisites and declared checks to be available; a complete diagram alone does not supply them.

## Compose an Arbeitsschritt

First resolve the roles and paths in [Protocol vocabulary](ontology.md#protocol-vocabulary). Prompt, tools and data then have distinct jobs inside the existing step contract:

| Component | Responsibility and home |
|---|---|
| Prompt | The bound step body is the job instruction: purpose, processing order, permitted actions, uncertainty handling and output contract. A separate prompt file or LLM call is optional. Reused instruction/rule/template content outside the Application is bound as input; a link to its current copy is insufficient. |
| Tools | The body names the callable operation and resolvable implementation/version, parameters from declared inputs, allowed effects, expected evidence and failure handling. The harness supplies access and credentials, checks availability and executes the bound operation. Tool availability grants no business authority. Extract a Capability only under its existing criteria. |
| Data | The domain home owns meaning, keys and source mappings; source records supply values. Each declared input identifies its acquisition or producer handoff and minimum control. The harness materializes the sufficient excerpt and provenance before opening the attempt. Data includes rules, documents and evidence. |

The harness loads the bound main/subprocess context needed for this job, the current workstep and its declared inputs. It exposes only operations permitted for that job. Source text and tool responses are evidence to interpret, not instructions that can change routes, permissions or the bound processing rule. If an LLM contributes, preserve its used configuration and decision-relevant result in the ordinary output evidence; a source hash does not make nondeterministic processing reproducible.

Inputs, outputs, `pruefung`, routes and authority delimit all three; they add no Core fields or mandatory actors. [Source binding](capabilities.md#snapshot-und-herkunftsnachweis) owns acquisition and provenance; [Work from prerequisites](#work-from-prerequisites) owns processing and changed evidence. Declare actual output files and their check, including any action confirmation or handoff. The [linked-table read path](impacts-architect/references/datenbezug.md#the-question-determines-the-read-path) illustrates bounded context without a graph server.

## Work from prerequisites

HP → TP → AS provides understandable scope, ownership and auditable handoffs. Design execution around the information, applicable rules, resources and authority each contribution actually requires. A department's historical queue is not automatically a dependency. Independent contributions can be prepared together inside one coherent Arbeitsschritt; separate results, checks or authority boundaries still earn separate steps.

Within the current declared job, perform useful permitted work as soon as its prerequisites hold. If one contribution is blocked, preserve the usable results and name the missing evidence or decision, its responsible party and the next allowed action. The existing processing body defines permitted preparation, acquisition and effects; the Vorgang's `Stand` explains progress using its Laufpfad and linked outputs. A reply draft may help while waiting; sending it requires its own applicable permission. Data availability alone grants neither a decision nor an external action.

For example, prepare an offer's supported content while its delivery confirmation is outstanding. Mark the missing confirmation and retain any required review before a commitment. Preparation needs sufficient inputs for that contribution; a file recording an unknown value proves the gap, not the missing value. If a declared input file cannot yet be materialized, acquire it through the preceding job or a permitted preparation path before opening that attempt. Intermediate transformations of bound inputs stay within the job; they need no extra step merely because a tool was called. Newly acquired source evidence becomes declared output with provenance and then input to the next designated attempt before dependent processing. Never replace already bound input bytes. A relevant change requires rechecking affected drafts; a new input set belongs to a new routed attempt. If the required return route is absent, a necessary restart begins at the entry of a new Vorgang with an explicit reference to the old one.

The current Core has one sequential Laufpfad: the last entry identifies the current step and attempt. Within it, independent operations may be organized by the harness; the Core does not schedule them. An `aktiv` or `wartend` attempt may hold permitted, uncompleted drafts under its declared `output/`; those drafts do not select a route, close the step or release a Gate. Resume follows the declared route. Starting another Arbeitsschritt early, bypassing a Gate or opening concurrent Laufpfad branches is not implied. Recurring waits may justify a reviewed change to future Applications, not a silent rewrite of the running definition.

## Identify

Describe the work before changing it. Reuse sufficient reachable observations and clarify the relevant gaps. Start with the intended recipient, accepted Leistung and relevant boundary; use the following perspectives only where they affect the next decision:

- Relevant environment: participants, dependencies and constraints that affect the Leistung. Include market, demand or access relationships when they matter; an internal process need not have a market funnel.
- Value flow: value object, recipient and, where relevant, customer, payer or external participant.
- Performance: one primary outcome and its result metric. Use a controllable leading indicator only when an early observation supports a concrete steering decision; its relation to the later result remains a hypothesis until supported by observed runs. Consider margin, throughput, cycle time, attention and customer satisfaction where relevant.
- Magic Triangle: improve speed, quality or cost while explicit guardrails protect the other dimensions.
- Process physics: throughput, cycle time, work in progress and the current constraint.
- Human boundaries: Customer-Touchpoints and internal Human Gates.
- Automation boundary: input variance, result tolerance, possible damage, reversibility and detectability.
- Calculated results: accepted output, sanctioned rule, parameters, actual source and stand, required control and allowed business use.

Do not assume the useful boundary starts at an incoming request. Inspect upstream causes or downstream use when evidence suggests they constrain the outcome; do not require a complete market or organization inventory. Under the Application's existing `Objective and guardrails`, record the bounded question or intervention, its evidence and unknowns, responsible decision-maker, intended observable effect and conditions for reassessment or stopping. Missing evidence may make observation the next step rather than automation.

Keep metric meaning with its existing definition: what is counted or assessed, unit, relevant population or time basis, source and comparison. Missing is not zero; a reported estimate is not an observed result. Channel attribution and causal effect are different claims where channels are relevant. These distinctions require no new status vocabulary or universal metric schema.

A Customer-Touchpoint creates trust, advice, commitment or experience. `standard` keeps the interaction human and prepares it with better information. `sacred` protects the interaction until a human approves a changed classification. For the declared action, responsible human and execution preflight, apply [Signals and human gates](capabilities.md#signale-und-human-gate).

A Human Gate controls risk or authority. The agent prepares short, inspectable evidence. The human decision remains in the Vorgang.

Before redesign, identify where a person must interact, judge or authorize, why that boundary exists and who may change it. Distinguish a required boundary from a current staffing habit or temporary lack of data or tools. An unresolved permission does not authorize automation across that boundary. Preparing evidence can be automated without transferring the decision itself.

For each Arbeitsschritt, distinguish the human contribution, agent reasoning and deterministic system processing that are actually needed. These are composable contributions, not three mandatory actors, three new steps or exclusive step types. Identify sets their constraints; Augment selects the execution mix within them. Rule-based processing still needs correct inputs and a valid rule; an agent proposal does not supply missing authority.

Define the start and accepted end of the process-time comparison. Separate active work from waiting for inputs, queues, handoffs, decisions and rework where relevant. Use existing traces or explicitly reported ranges; unknown timing can require a small observation first. Do not obtain end-to-end duration by adding overlapping activities or confuse elapsed duration with total labor effort.

## Minimize

Remove work that does not contribute to the Leistung. Challenge handoffs, waits, duplicate capture, role boundaries and data movement. Working hours, organizational history and current staffing do not define the target process.

Combine or remove work only while preserving the identified authority and customer boundaries. Reduce avoidable waiting around required human decisions by preparing usable evidence and a workable handoff; do not erase the decision to make the diagram shorter. Actual availability remains a feasibility constraint even when current role boundaries are challenged. Before removing or combining a handoff, list each successor’s declared inputs and show where each is still produced with its required evidence and authority; [Test](#test) checks that downstream effort and backlog have not merely moved.

## Perfect

Close the remaining path. Every Arbeitsschritt receives declared inputs, visible outputs, one verification rule and complete routes. Each step must contribute to its Teilprozess and the Hauptprozess must end at its Leistung.

Close the [backward trace](#reverse-engineer-a-product-or-service) for every required result component. For calculations, the producing job names the sanctioned rule and each parameter's meaning, unit, origin, revision and required control. Actual control evidence belongs to the run. Extract a Capability only when the [Capability contract](capabilities.md) [extraction criteria](capabilities.md#wann-extrahieren) earn that boundary; its local call uses the [Capability call contract](capabilities.md#capability-aufruf).

## Augment

Assign each remaining part to its best execution form. Deterministic calculations stay in the Arbeitsschritt or an earned Capability. The model handles variable language and context. People retain customer interaction, judgement and authority where the identified boundary requires them.

Every calculation has a sanctioned rule even when it remains local. A Capability returns a visible technical result; the Arbeitsschritt adds business verification, use restriction and route. A permitted `hypothesis` names impact and validation action. An irreplaceable missing value stays `open` and produces a focused question.

## Construct

Write one Application as `CONTEXT.md` files from the existing templates. The folder tree carries containment; `einstieg_ref` and routes carry execution order. Fill each workstep's [prompt, tools and data contract](#compose-an-arbeitsschritt), including source acquisition and required check. Keep code, shared reference content and run bytes in their [existing homes](impacts-architect/references/formwahl.md#native-topologie-und-schnitt). An unresolved input, operation or check remains an explicit execution blocker, even when the tree validates.

## Test

Run representative Vorgänge against a baseline. Compare the primary outcome, guardrails, throughput and failure cases. Treat a leading indicator as a hypothesis until observed runs support its relation to the outcome.

Keep structural validity, correct domain processing and observed benefit separate. A successful validator run proves only its declared checks. For a shorter-process claim, use Identify's time boundary, include preparation, review and rework, and check whether waiting or backlog merely moved to another participant. Report labor savings separately and retain the agreed guardrails. Without a defensible comparison, leave the effect unproven; a consistency repair does not require a business-time improvement unless it claims one.

For a context-efficiency claim, compare the same representative questions and source state with the prior retrieval path. Record actual loaded tokens, answer correctness and evidence coverage, unsupported conclusions and total retrieval/review effort. Keep model and settings comparable and repeat variable model runs. A smaller excerpt is useful only if the required answer remains supported; do not remove identities, rule conditions, contradictions or provenance to improve a token count. No universal saving follows from the file structure.

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

## Reviewed correction

This procedure applies to every form. On one demonstrated defect or consequential repeated friction, retain the actual observation and source revision in the existing run, record or review. Keep the explanation and expected benefit `hypothesis` until supported. Follow the affected claim to its existing home and choose the smallest legitimate correction or deletion:

| Finding | Correction home |
|---|---|
| Wrong case value or exceptional customer preference | That case record and its source; the preference stays local. |
| Missing or conflicting meaning, mapping, reusable rule or calculation | Its existing domain/source or sanctioned calculation home. |
| Existing fact cannot be reached or bound | Its nearest router/link or source binding; preserve the fact’s home. |
| Applicable rule was not checked or delivered correctly | The consuming workstep or its actual checker. |
| Shared method defect or changed authority | The existing method or responsible human policy decision; observations alone change no authority. |

Prepare the concrete edit with its evidence, affected consumers, one important non-applicable case and required check. The same review names the responsible owner and who observes the next comparable case, with its trigger. Repeated evidence updates that proposal; duplicate or rejected proposals close there. Obtain the review or decision required by the affected scope before adopting changed operating meaning. A written attribution does not authenticate a person.

Correct or delete at that single home, repair its referrers and exercise the original failure, the nearby exception and a new related question not used to design the correction. Preserve previously valid results. A fresh consumer follows ordinary routes with no injected lesson; record its actual result separately from the expected outcome. Execute deterministic fixtures for computational conditions. Recheck affected uses before binding the reviewed revision in future runs; earlier definitions and bound inputs remain unchanged. A known serious defect in active work follows its existing pause, escalation or restart route with the evidence intact.

Transfer only where the assumptions hold, binding the target’s own sources and permissions. The named observer checks recurrence, quality and review burden at the declared comparable-case trigger; revise or remove a contradicted change. Publication alone proves neither adoption nor improvement. This uses existing files, tests and revision review; it adds no phase, learning store or automatic promotion rule.

## Load context locally first

Start at the closest `CONTEXT.md` and follow only the Markdown links needed for the current stage or question. If an already recorded fact is not reachable through that path, repair the existing router, link or source binding at the fact's single home before adding another summary.

External research is ingestion. Use it only when the local path exposes a real evidence gap, the requested freshness exceeds the local source state, or the user explicitly requests new external evidence. Any optional graph projection or database follows the single [Tooling-Stopp](impacts-architect/references/formwahl.md#tooling-stopp).

## Where the context lives

The Application body explains the relevant environment, value flow and optimization contract. The embedded Leistung holds the result, its main metric and acceptance conditions. A Teilprozess body explains its contribution; a leading indicator is included only under Identify's decision-use criterion. An Arbeitsschritt owns inputs, outputs, verification, routes and optional human markers.

These are human-readable instructions in existing files. They add no schema, state machine or execution engine.

Stable material stays at one source home. A run materializes the smallest professionally sufficient source or projection plus separate provenance under attempt `input/`. A step handoff declares `output -> input`; the run binds byte content, attempt-qualified origin and content digest. Follow the [snapshot/provenance contract](capabilities.md#snapshot-und-herkunftsnachweis) and [visible handoff contract](capabilities.md#sichtbare-ausgabe-und-übergabe) for those details.

## Review another Fachrepo

Name the protocol revision actually used before assessing compatibility. Check its machine-readable structure against that revision; do not treat a successful check against an older pin as compatibility with this one. Select the applicable [Walk test](impacts-architect/SKILL.md#walk-test): Process Walk for Applications, Knowledge Walk for records and domain foundations, both for mixed forms. Exercise domain processing and outcome checks separately where required. Legitimately missing evidence produces a focused question; unreachable existing evidence requires a routing repair.

A later nodes-and-edges view is a disposable projection, not a second authority. Containment comes from folders, execution edges from `einstieg_ref` and routes, and knowledge links from their source files. Preserve these different meanings and the source revision; do not infer execution order or causal influence from an ordinary hyperlink. Graph construction is not a prerequisite for reading, validating or transferring a repository.

## Readability and processing

Apply these acceptance questions to existing surfaces at capture, processing, verification, change and handoff:

- UX: Can the responsible person understand what is needed, why, and the consequences of their decision?
- AX: Can the agent find unambiguous inputs and sources, permitted actions and boundaries, or ask the specific unresolved question?
- DX: Can a developer locate the authoritative contract, responsible implementation and applicable verification and change path?

Human-readable meaning and machine-readable fields must agree. Different views use the same authoritative definition. These questions add no mandatory fields or documents; fix the existing rule, wording or link when a reader cannot apply it.
