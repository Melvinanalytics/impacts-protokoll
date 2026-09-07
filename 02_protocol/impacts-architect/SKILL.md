---
name: impacts-architect
description: Use when customer initialization or knowledge topology needs the smallest fitting ICM form, when an observed process should become an IMPACTS Application, when an existing customer repository must be restructured, or when an approved Application should be imported from a Fachrepo.
---

# IMPACTS Architect

This skill selects the smallest fitting ICM form, then produces only the files that form needs. For a Pipeline, the core validates an Application tree of `CONTEXT.md` files. Other forms use the workspace's native routers, `grundlagen/` and `records/` where real content requires them. The skill never executes an Arbeitsschritt, never writes `human:<id>`, and never introduces a schema, field or folder kind the core does not have.

Read the core before designing: [formwahl.md](references/formwahl.md) defines form selection and native knowledge topology, `impacts template <kind>` prints the contract of every core object, [impacts-method.md](../impacts-method.md) owns the Pipeline method and UX/AX/DX acceptance, [zuschnitt.md](references/zuschnitt.md) owns process cutting rules, and the [Capability-Regel](../capabilities.md) owns optional processing boundaries. Use this skill with the protocol checkout; a standalone folder copy omits its sibling references.

## Invariants

1. One Application holds one Hauptprozess with one embedded Leistung. Two Leistungen mean two Applications.
2. Arbeitsschritte own their routes, the Hauptprozess owns the entry, every step reaches a named end.
3. The Application tree holds only `CONTEXT.md` files. Reference material lives in `grundlagen/`, customer instances in `records/`, reusable processing in Fachrepo- or Workspace-level `capabilities/<slug>/`, code otherwise in dependencies.
4. The workspace root is the git root. A Vorgang binds a committed Application tree.
5. `gate: human` marks an authority, risk or legal boundary and nothing else. `customer_touchpoint` marks where the customer is in the interaction.
6. Factory and run stay apart: no Vorgang changes the Application.
7. Every claim carries its source and the evidence label defined in [zuschnitt.md](references/zuschnitt.md#evidence); a confirmed document does not confirm every interpretation of it.
8. `impacts validate .` validates Applications and Vorgänge, not non-process knowledge topology. Run it before every commit when those core objects are present.

## Form selection

Before proposing a tree, complete the work-report recipe in [formwahl.md](references/formwahl.md). Then select the smallest fitting form from the units that grow or repeat: Pipeline, Record Library, Knowledge Bundle, Context Map, Umbrella or System Map. Enter Build mode only when the selected form is a Pipeline that will become an Application. For a non-process form, build only its native Markdown topology and use the applicable walk branch below.

## Choose a mode

- A selected Pipeline that will become an Application, described in conversation with no folder yet: Build mode.
- A newly described Record Library, Knowledge Bundle, Context Map, Umbrella or System Map: Topology path.
- An existing customer folder, repository or vault: Restructure mode, then route each found form through its selected path.
- An approved Application in a Fachrepo: Import mode.

## Topology path

Before proposing a tree, require the completed work-report recipe from [formwahl.md](references/formwahl.md). For a newly described Record Library, Knowledge Bundle or Context Map, create only populated native Markdown homes and links under its rules. Run its Knowledge Walk when the topology uses `records/` or fachliche `grundlagen/`; if a Context Map links only Applications, run the Process Walk for each linked Application. Add no checker or runtime.

For an Umbrella, create a small router to multiple independent Pipeline Applications, then run the Process Walk for each Application.

For a System Map, use the existing repository map and files, then select and test its child forms through their applicable walk branches.

## Build mode

Identify → Minimize → Perfect → Augment → Construct → Test → Scale, as a procedure.

**Identify.** Interview a few questions at a time and write one [ist-prozess.md](templates/ist-prozess.md) per observed process into `grundlagen/ist-prozesse/`:

- What leaves the process, who receives or accepts it, and what makes it usable? A payer matters only where relevant. That informs the Leistung: `ergebnis`, `kennzahl`, `abnahme`.
- Walk me through one run. Where must a person interact, judge or authorize, why, and who may change that boundary? Which decision and subsequent action does it cover? A pause alone establishes neither a Human Gate nor a Teilprozess.
- From which start to which accepted end does the reported duration run? Distinguish active work, waiting and rework using available evidence or reported ranges. What remains unknown?
- What stays the same every run, and what is new each time? Stable material goes to `grundlagen/`, the rest is Vorgang input.
- Where does customer interaction create trust, advice, commitment or experience? Classify those touchpoints as `standard` or `sacred`; other external participants remain dependencies, not automatic touchpoints.
- What breaks if this step is wrong, and would you notice? That feeds the automation boundary.
- Which outputs are calculated or derived? For each: which sanctioned rule, inputs, units, source, stand, required control, actual evidence and allowed business use produce it?

Then fill the existing sections of the Application template under [Identify](../impacts-method.md#identify). Put the bounded intervention and its evidence, decision-maker, intended effect and reassessment conditions under `Zielgröße und Guardrails`. Name the evidenced limit and what would falsify it; a missing input or waiting decision may matter more than processing capacity.

**Minimize.** Remove work and avoidable waits that contribute neither to the Leistung nor its guardrails, following [Minimize](../impacts-method.md#minimize). Preserve required human decisions while improving preparation and handoff. List changes under Wertfluss so the customer can see their consequences; actual availability remains a feasibility constraint.

**Perfect.** Cut with [zuschnitt.md](references/zuschnitt.md): Teilprozesse at closed context sections, Arbeitsschritte at one job each, routes named by the outcome of `pruefung`, one `end:<slug>` per terminal outcome including the negative ones, waits as `wartend` states, loops with an exit. Reverse-engineer each calculated result from acceptance through its producing step and sanctioned rule to actual run inputs and source. Materialize missing evidence or leave it `open`.

**Augment.** Compose the needed contributions inside each Arbeitsschritt using the [Automation boundary](references/zuschnitt.md#automation-boundary). Apply the Capability-Regel only when extraction is earned. The Arbeitsschritt retains business `pruefung`, Nutzungsgrenze and route. Every permitted `hypothesis` names impact and a `Validierungsauftrag`; every irreplaceable `open` input creates a `gezielte Frage`.

**Construct.** `impacts template <kind>` for every object, filled from the captures, under `applications/<slug>/`. `impacts validate applications/<slug>` until exit 0. Commit. `git rev-parse HEAD:applications/<slug>` is the revision new Vorgänge bind.

**Test.** Apply the walk branches below and the method's [Test](../impacts-method.md#test). The Architect prepares and reviews the Application; the responsible harness separately exercises representative Vorgänge, respecting Human Gates. Keep readability, technical execution and observed benefit as separate results. A consistency repair may finish with business-time improvement explicitly unproven.

**Scale.** Commit the tested revision. New Vorgänge bind it; running Vorgänge keep theirs.

## Restructure mode

1. Inventory, touch nothing. Name the protocol revision actually bound, its declaration and the intended comparison revision. Record whether the inspected files are a committed or explicitly captured working state; preserve others' changes. List the tree. Per area: what it is, when last touched, what refers to it.
2. Find the hidden forms before hidden Applications. Ask which units grow or repeat, select each form with [formwahl.md](references/formwahl.md), then identify Applications only inside selected Pipelines. For each Pipeline, ask where work enters and leaves; interview the folder the way you would interview the person.
3. Classify every file into one role and its home:

| Role | Home |
|---|---|
| Router: identity and routing | root `CONTEXT.md`, the body `impacts init` writes |
| Application: how a step works | `applications/<hauptprozess>/<teilprozess>/<arbeitsschritt>/CONTEXT.md` |
| Record or customer instance | `records/` |
| Grundlage: stable reference, rules, assets, rights | `grundlagen/` |
| Vorgang-Artefakt: input or output of one run | `vorgaenge/<slug>/<step>/<versuch>/input` or `output` |
| Capability: reusable bounded processing | `capabilities/<slug>/` in the Fachrepo or Workspace, outside Core and Application |
| Other tool: code that is not a Capability | `tools/` or `src/` as a foreign dir; an external tool becomes a pinned dependency |
| Tot: superseded, duplicate, unreferenced | delete after step 4; git history keeps it, no archive folder |

4. Reference check before any move: in-repo links, sibling paths, symlinks, and consumers outside the repo such as scripts, jobs and other repositories. Ask the owner for the outside ones. A file with a live referrer is held, or moved together with its referrers in one change.
5. Migration map for human approval: old path, new path, role, referrers found.
6. Migrate by copy, verify, remove: copy, compare file count and hashes, only then remove. Check case-folded destination collisions first.
7. Route every found form: Build mode only for Applications and Topology path for non-process forms. Run `impacts validate .` for Applications and Vorgänge present, then run the applicable walk-test branch for every form.

## Import mode

1. Check the declared source and target protocol revisions under [Review another Fachrepo](../impacts-method.md#review-another-fachrepo). Content identity alone does not establish compatibility with another protocol revision.
2. Use the single transport procedure in [Scale](../impacts-method.md#scale), including referenced Capability trees. Preserve existing target work; do not extract over an existing Application or Capability directory. Missing or different bound trees block execution under the [Capability-Regel](../capabilities.md#transport).
3. Keep imported revisions intact and run the applicable walks. Customer-specific data uses declared source bindings; a changed process or bound rule requires a reviewed new Application revision, not an unbound override.

## Walk test

Choose the branch established by form selection. For a Pipeline/Application, a cold agent with no memory performs the Process Walk:

1. Open the root `CONTEXT.md`. Can it say where it is and how to advance a Vorgang from this one file?
2. Validate the selected workspace or Application directory with `impacts validate`. Record the target and protocol revision; a different repository root is not automatically a Core workspace.
3. Open `vorgaenge/<slug>/CONTEXT.md`. The current step is the last Laufpfad entry. Open that step's `CONTEXT.md`: inputs, outputs, `pruefung`, routes and applicable human check are all named. For an Application with no Vorgang yet, inspect its declared entry and mark run evidence as not yet demonstrated.
   Use `impacts hash` on declared attempt surfaces to check recorded hashes; this reads files and does not execute the workstep.
4. Every Application body section holds the customer's facts, each labelled `verified`, `reported`, `hypothesis` or `open`.
5. Report the loaded router, Arbeitsschritt and input paths. Aim for at most 8k tokens of actual task payload, not a minimum size. If the payload tokenizer is unavailable, report bytes/words and that limitation instead of an exact token-PASS.
6. Where calculations or step handoffs exist, follow one applicable calculated output to its sanctioned rule and materialized inputs, and one applicable handoff to its attempt-qualified origin and content digest. Record absent features as not applicable; declared features without a run remain unproven, not absent.
7. Where a Human Gate exists, inspect the required input/control evidence and the scope of its decision. Before opening it, the responsible harness applies the Capability-Regel preflight. Opening creates neither route nor `freigabe`; `pruefung` evaluates the later Gate output. A read-only review does not open or approve the Gate.

Apply [Readability and processing](../impacts-method.md#readability-and-processing) to the existing capture, processing, verification, change and handoff surfaces. On failure, repair the authoritative wording or link first. Keep genuinely missing evidence as a focused question; split files only when the existing form or task boundary earns it.

Run the Knowledge Walk only when the topology uses `records/` or fachliche `grundlagen/`, following [formwahl.md](references/formwahl.md). This covers Record Libraries, Knowledge Bundles and Context Maps against their linked facts. A Context Map that links only Applications uses their Process Walks. Umbrellas and System Maps test each child form through its applicable branch. Do not automate the walk or introduce a new checker.

## Guardrails

- Use chat or a saved prompt while no repeatable Leistung and meaningful process boundary are established; form selection, not an arbitrary occurrence count, determines whether to build an Application.
- Stopp-Frage before any new term, field, folder kind or schema: name the existing structure that already does it.
- Never write `human:<id>`. The human writes `freigabe`; the agent prepares the evidence.
- The responsible customer confirms the Application before its first real Vorgang. This release decision does not overwrite the individual claims' evidence labels or supply missing source evidence.
