---
name: impacts-architect
description: Use when customer initialization or knowledge topology needs a file home, when deriving processes from products/services or observed work, restructuring a customer repository, or importing an approved Application from a Fachrepo.
---

# IMPACTS Architect

This skill selects the smallest fitting ICM form, then produces only the files that form needs. For a Pipeline, the core validates an Application tree of `CONTEXT.md` files. Other forms use the workspace's native routers, `grundlagen/` and `records/` where real content requires them. The skill never executes an Arbeitsschritt, never writes `human:<id>`, and never introduces a schema, field or folder kind the core does not have.

Start with the [formwahl work report](references/formwahl.md#arbeitsbericht-vor-baumvorschlag), including its business-capture branch. For a Pipeline, load the [capture/build method](../impacts-method.md#capture-business-meaning) and the phase section in use; load the [decomposition rules](references/zuschnitt.md#arbeitsschritt) when cutting work and the [automation boundary](references/zuschnitt.md#automation-boundary) when assigning contributions. Load the [Capability contract](../capabilities.md) and its relevant [extraction/call rules](../capabilities.md#wann-extrahieren) plus [source](../capabilities.md#snapshot-und-herkunftsnachweis), [handoff](../capabilities.md#sichtbare-ausgabe-und-übergabe), [writeback](../capabilities.md#rückübertragung-in-geschäftsrecords) or [Gate](../capabilities.md#signale-und-human-gate) rules only when that branch is present, including work without an extracted Capability. For every form, use the linked [evidence labels](references/zuschnitt.md#evidence) and [UX/AX/DX acceptance](../impacts-method.md#readability-and-processing). Use this skill with the protocol checkout; a standalone folder copy omits its sibling references.

Before capturing, changing or applying domain meaning in any form, read [Author or change](../ontology.md#author-or-change) or [Use](../ontology.md#use), then apply the ontology's [evidence and obligations](../ontology.md#evidence-and-obligations) and [enforcement/completion](../ontology.md#enforcement-and-completion). Routine use does not recapture the model; Core validity alone does not establish domain correctness. For catalog, pipeline and document-template composition, follow the [worked company example](references/datenbezug.md#from-catalog-through-pipeline-to-a-filled-offer).

Resolve the customer’s [working language](../language.md#select-and-bind) before capture or import. Use localized templates (`--language de` for German-only work); keep all customer-readable instructions, drafts and decision requests in that language. Apply the actual [language/meaning check](../language.md#enforce-at-use-boundaries) before customer use. The protocol’s English does not override the customer setting.

## Invariants

1. One Application holds one Hauptprozess with one embedded process Leistung. Two independently bounded process results mean two Applications; catalog items are not Application boundaries.
2. Arbeitsschritte own their routes, the Hauptprozess owns the entry, every step reaches a named end.
3. The Application tree holds only `CONTEXT.md` files. Reference material lives in `grundlagen/`; continuing business instances stay in their designated systems or maintained records. Reusable processing lives in Fachrepo- or Workspace-level `capabilities/<slug>/`, code otherwise in dependencies.
4. The workspace root is the git root. A Vorgang binds a committed Application tree.
5. `gate: human` marks an authority, risk or legal boundary and nothing else. `customer_touchpoint` marks where the customer is in the interaction.
6. Factory and run stay apart: no Vorgang changes the Application.
7. Every claim carries its source and the evidence label defined in [zuschnitt.md](references/zuschnitt.md#evidence); a confirmed document does not confirm every interpretation of it.
8. `impacts validate .` validates Applications and Vorgänge, not non-process knowledge topology. Run it before every commit when those core objects are present.

## Form selection

Before proposing a tree, complete the work-report recipe in [formwahl.md](references/formwahl.md#arbeitsbericht-vor-baumvorschlag). Then select the smallest fitting form from the units that grow or repeat: Pipeline, Record Library, Knowledge Bundle, Context Map, Umbrella or System Map. Enter Build mode only when the selected form is a Pipeline that will become an Application. For a non-process form, build only its native Markdown topology and use the applicable walk branch below.

## Choose a mode

- A selected Pipeline that will become an Application, described in conversation with no folder yet: Build mode.
- A newly described Record Library, Knowledge Bundle, Context Map, Umbrella or System Map: Topology path.
- An existing customer folder, repository or vault: Restructure mode, then route each found form through its selected path.
- An approved Application in a Fachrepo: Import mode.

## Topology path

For a newly described Record Library, Knowledge Bundle or Context Map, create only populated native Markdown homes and links under its rules. Run its Knowledge Walk when the topology uses `records/` or domain `grundlagen/`; if a Context Map links only Applications, run the Process Walk for each linked Application. Add no checker or runtime.

For an Umbrella, create a small router to multiple independent Pipeline Applications, then run the Process Walk for each Application.

For a System Map, use the existing repository map and files, then select and test its child forms through their applicable walk branches.

## Build mode

Follow the method's phases in order; load each linked section when doing that work. Reuse the form-selection evidence and fill the existing Application template sections.

1. [Identify](../impacts-method.md#identify). Use [reverse engineering](../impacts-method.md#reverse-engineer-a-product-or-service) for supplied products/services. For new observations without a suitable home, use [ist-prozess.md](templates/ist-prozess.md) or its [German counterpart](templates/de/ist-prozess.md) under `grundlagen/ist-prozesse/`.
2. [Minimize](../impacts-method.md#minimize). Record proposed removals and their consequences in `Value flow`.
3. [Perfect](../impacts-method.md#perfect). Use [Leistung and decomposition](references/zuschnitt.md#leistung) to cut the supported work into the existing tree.
4. [Augment](../impacts-method.md#augment). Select contributions through the [automation boundary](references/zuschnitt.md#automation-boundary); load Capability [extraction](../capabilities.md#wann-extrahieren) and [call](../capabilities.md#capability-aufruf) rules only when applicable.
5. [Construct](../impacts-method.md#construct). Generate each object with `impacts template <kind>` under `applications/<slug>/`. Build mode is incomplete until every Hauptprozess, Teilprozess and Arbeitsschritt retains its role-specific sections and satisfies its localized setup-completion section under [Maintain agent instructions](../impacts-method.md#maintain-agent-instructions). Complete [workstep composition](../impacts-method.md#compose-an-arbeitsschritt) and the [workspace/harness setup](references/formwahl.md#native-topologie-und-schnitt). Before the candidate commit, record the semantic design cases with their premises, expected outcomes and open gaps; this review does not execute an Arbeitsschritt or establish readiness. Run `impacts validate applications/<slug>` until exit 0, then commit the candidate. `git rev-parse HEAD:applications/<slug>` identifies the tree that the Test phase's responsible harness exercises and new Vorgänge bind.
6. [Test](../impacts-method.md#test). Apply the walk branches below. The Architect prepares and reviews; the responsible harness exercises representative Vorgänge within their declared authority.
7. [Scale](../impacts-method.md#scale). Commit the tested revision. Follow [Reviewed correction](../impacts-method.md#reviewed-correction) for subsequent changes in any form.

## Restructure mode

1. Inventory, touch nothing. Name the protocol revision actually bound, its declaration and the intended comparison revision. Record whether the inspected files are a committed or explicitly captured working state; preserve others' changes. List the tree. Per area: what it is, when last touched, what refers to it.
2. Find the hidden forms before hidden Applications. Ask which units grow or repeat, select each form with the [formwahl work report](references/formwahl.md#arbeitsbericht-vor-baumvorschlag), then identify Applications only inside selected Pipelines. For each Pipeline, ask where work enters and leaves; interview the folder the way you would interview the person.
3. Classify every file by the [existing homes](references/formwahl.md#native-topologie-und-schnitt). Retain non-Capability code at its existing `tools/`, `src/` or dependency home outside the Application. Mark superseded, duplicate or unreferenced files for retirement only after the reference check; Git history preserves them without an archive folder.
4. Reference check before any move: in-repo links, sibling paths, symlinks, and consumers outside the repo such as scripts, jobs and other repositories. Ask the owner for the outside ones. A file with a live referrer is held, or moved together with its referrers in one change.
5. Migration map for human approval: old path, new path, role, referrers found.
6. Migrate by copy, verify, remove: copy, compare file count and hashes, only then remove. Check case-folded destination collisions first.
7. Route every found form: Build mode only for Applications and Topology path for non-process forms. Run `impacts validate .` for Applications and Vorgänge present, then run the applicable walk-test branch for every form.

## Import mode

1. Check the declared source and target protocol revisions under [Review another Fachrepo](../impacts-method.md#review-another-fachrepo). Content identity alone does not establish compatibility with another protocol revision.
2. Use the single transport procedure in [Scale](../impacts-method.md#scale), including referenced Capability trees. Preserve existing target work; do not extract over an existing Application or Capability directory. Missing or different bound trees block execution under the [Capability contract](../capabilities.md#transport).
3. Keep imported revisions intact and run the applicable walks. Customer-specific data uses declared source bindings; a changed process or bound rule requires a reviewed new Application revision, not an unbound override.

## Walk test

Choose the branch established by form selection. For a Pipeline/Application, a cold agent with no memory performs the Process Walk:

1. Open the root `CONTEXT.md`. Can it say where it is and how to advance a Vorgang from this one file?
2. Validate the selected workspace or Application directory with `impacts validate`. Record the target and protocol revision; a different repository root is not automatically a Core workspace.
3. Open `vorgaenge/<slug>/CONTEXT.md`. The current step is the last Laufpfad entry. Open that step's `CONTEXT.md`: inputs, outputs, `pruefung`, routes and applicable human check are all named. For an Application with no Vorgang yet, inspect its declared entry and mark run evidence as not yet demonstrated.
   Use `impacts hash` on declared attempt surfaces to check recorded hashes; this reads files and does not execute the Arbeitsschritt.
4. Every Application body section holds the customer's facts, each labelled `verified`, `reported`, `hypothesis` or `open`.
5. Report the loaded router, Arbeitsschritt and input paths. Aim for at most 8k tokens of actual task payload, not a minimum size. If the payload tokenizer is unavailable, report bytes/words and that limitation instead of an exact token-PASS.
6. Trace every Leistung acceptance condition through the [backward trace](../impacts-method.md#reverse-engineer-a-product-or-service) to its producing work, required output/effect evidence and applicable `pruefung`. Record design coverage and actual case satisfaction separately; missing work, checks or evidence leave that condition unproven. Where calculations or step handoffs exist, follow one applicable calculated output to its sanctioned rule and materialized inputs, and one applicable handoff to its attempt-qualified origin and content digest. Record absent features as not applicable; declared features without a run remain unproven, not absent.
7. Where a Human Gate exists, inspect the required input/control evidence and the scope of its decision. Before opening it, the responsible harness applies the Capability contract preflight. Opening creates neither route nor `freigabe`; `pruefung` evaluates the later Gate output. A read-only review does not open or approve the Gate.

Apply [Readability and processing](../impacts-method.md#readability-and-processing) to the existing capture, processing, verification, change and handoff surfaces. On failure, follow [Reviewed correction](../impacts-method.md#reviewed-correction) at the authoritative wording or link. Keep genuinely missing evidence as a focused question; split files only when the existing form or task boundary earns it.

Where preparation during a wait is declared, exercise a representative case against [Work from prerequisites](../impacts-method.md#work-from-prerequisites). Record its observed draft, blocker and continuation.

Run the [Knowledge Walk](references/formwahl.md#knowledge-walk) only when the topology uses `records/` or domain `grundlagen/`. This covers Record Libraries, Knowledge Bundles and Context Maps against their linked facts. A Context Map that links only Applications uses their Process Walks. Umbrellas and System Maps test each child form through its applicable branch. Do not automate the walk or introduce a new checker.

## Guardrails

- Use chat or a saved prompt while no repeatable Leistung and meaningful process boundary are established; form selection, not an arbitrary occurrence count, determines whether to build an Application.
- Stop question before any new term, field, folder kind or schema: name the existing structure that already does it.
- Never write `human:<id>`. The human writes `freigabe`; the agent prepares the evidence.
- The responsible customer confirms the Application before its first real Vorgang. This release decision does not overwrite the individual claims' evidence labels or supply missing source evidence.
