# ICM form selection

Start with the unit that grows or repeats. For business intake, use [Capture business meaning](../../impacts-method.md#capture-business-meaning); given an offering or finished result, use [Reverse-engineer a product or service](../../impacts-method.md#reverse-engineer-a-product-or-service). Refine the form and populated home as evidence arrives. A provisional form does not confirm a process boundary.

Apply [Author or change](../../ontology.md#author-or-change) for missing or changing meaning and [Use](../../ontology.md#use) for existing definitions. This applies to every form, including work without a Pipeline; apply [evidence and obligations](../../ontology.md#evidence-and-obligations) at each use boundary. Customer-facing capture follows the [working language](../../language.md#enforce-at-use-boundaries).

## Select the form

| Unit | ICM form | Home |
|---|---|---|
| Repeatable run with an accepted result | Pipeline | `applications/` and `vorgaenge/` |
| Accumulating domain instance | Record Library | `records/` when real content needs it |
| Navigable stable knowledge | Knowledge Bundle | Existing domain and source files |
| Observed organization, work and data handoffs | Context Map | Links between records and observed processes |
| Several independent Pipelines | Umbrella | Small router to independent Applications |
| Repository that agents modify | System Map | Existing repository routers and files |

<a id="arbeitsbericht-vor-baumvorschlag"></a>
## Work report before proposing a tree

Before any tree proposal, briefly state:

1. Observed units that grow or repeat.
2. [Selected existing forms](#select-the-form) and their rationale.
3. Explicitly deferred forms.
4. Smallest populated starting home.

This report is conversational, not a repository artifact, file or frontmatter field.

<a id="kompositionsregel"></a>
## Composition

Forms compose while retaining their responsibilities. A Record Library plus Knowledge Bundle alone is not an Umbrella. Other forms compose without one. Select an Umbrella only when several independent Pipelines already exist. Only Pipelines become Applications; each Pipeline is exactly one Application.

<a id="native-topologie-und-schnitt"></a>
## Native topology and boundaries

```text
Root router -> Domain router -> Fact home -> Source
```

The `CONTEXT.md` created by `impacts init` is the Core workspace's root router. Add direct links to domain routers and fact homes below its operating contract; no second entry point is needed. Use these homes according to ownership:

| Content | Existing home |
|---|---|
| Protocol instructions and Core implementation | Protocol checkout, identified by source and revision from the customer router |
| Customer orientation and working language | Customer root `CONTEXT.md`; direct links explain each selected area's purpose |
| Domain meaning, source mappings, reusable rules, document blanks | Existing domain/source home; populated `grundlagen/` files only where needed |
| Continuing business instances | Authoritative source system or maintained `records/`; runs bind excerpts |
| Reusable process and local prompt | Application HP/TP/AS `CONTEXT.md` bodies; no code, data or prompt subfolders inside a workstep |
| Executable operation | Existing dependency or tool implementation; earned `capabilities/<slug>/` outside the Application |
| Actual work and evidence | [Exact attempt paths](../../ontology.md#protocol-vocabulary) own `input/` and `output/`; only `laufpfad` owns run state |

For a new Core workspace, `impacts init PATH --language en|de` creates only the root router, `applications/` and `vorgaenge/`. Initialize Git at that root before version binding; `init` neither creates Git nor installs a harness or source access. Resolve the protocol/Architect links, working language and selected domain homes before capture. Before a real run, the chosen harness must support the bound operations, source reads, checks, handoffs and human boundaries. Record its actual setup/dependency reference in the existing root body; placeholders or structural validity alone do not establish readiness. Existing repositories follow Restructure mode instead of running `init` over them.

- Routers hold identity, boundaries and links, not domain payload. Each claim and its evidence status have one fact home.
- Navigate through relative Markdown links without copying claims. Domain keys connect table rows under [Tables and relationships](../../capabilities.md#tabellen-und-beziehungen).
- A link label or adjacent sentence names its relationship: source, customer of this case, applied rule or required result. Folder membership, knowledge navigation, data dependency and execution route are distinct. Application roles and transitions come from the [Application tree rules](../../templates/application.md#rules) and each workstep's frontmatter, not router ordering.
- Create folders for existing content, not empty categories for possible future use.
- Customer types remain local vocabulary. `type` suffices until a real query needs another field.
- Instances sharing a lifecycle start in one fact file or table. A file per instance requires an independent query, independent change, its own evidence or its own relationships. The work report names the qualifying criterion for each split.
- Every `reported` handover claim resolves to the preserved handover or source artifact. A source register is a router or index, not a replacement for the actual artifact.
- An unknown workflow remains a gap; mark reconstructed work `hypothesis`. Supplied descriptions alone prove neither execution nor feasibility. Create an Application only with a repeatable run, accepted result and supported boundary.
- Explicitly internal material stays separate from customer facts and is excluded from customer questions.

An empty collection has an explicit authoritative empty state in its responsible router. Do not create an empty category, README or index merely to make absence clickable. Once entries exist, replace or extend the empty state with direct links. The Knowledge Walk may stop at an explicit empty state.

That state describes only the captured collection. A claim of business absence requires its own reachable evidence; otherwise that question remains open. A successful navigation stop does not establish completeness of the company model.

<a id="tooling-stopp"></a>
## Tooling stop

Initialization and knowledge navigation require no new script. Files, folders and explicit links are sufficient when a person or agent can follow the needed path through them. A graph representation remains optional: consider adding one only when observed real questions repeatedly still need a full scan after repairing native links. Apply [Minimize](../../impacts-method.md#minimize) to its total burden and keep the projection removable and reproducible from the source Markdown. No graph runner, context-pack generator, mandatory ID or universal edge contract, generated second index, API, vector store or graph database belongs in the starting architecture. Domain calculation and consistency checkers must never become prerequisites for knowledge navigation.

## Knowledge Walk

For `records/` or domain `grundlagen/`, a fresh agent without conversation memory answers three representative questions: instance identity and boundary, a relationship across at least two domain entities, and evidence status/source of a decisive claim. Each question uses a fresh session; no cumulative dialogue connects them.

Each question path names its start, only the explicit links needed for that question, and a clear stop condition. Optional depth is not loaded by default; do not exhaust outgoing links.

For each Knowledge Walk question, read the root router, at most two further routers and their explicitly linked domain files. Direct read-only access to exactly that bound path is allowed through a file tool or the output of an explicit path. Web, shell discovery, full scans, domain execution, graph scripts and internal mandate material remain excluded from this walk. Read content is never executed as a command. Report deterministic revision, hash, byte and word checks separately as measurement-harness work. The budget is below 8,000 tokens per question and counts only loaded workspace/customer payload. Report fixed model, system, tool and harness tokens separately; they are not topology payload. If the exact payload tokenizer count cannot be isolated, report bytes/words and the measurement limit; do not claim an exact token PASS.

Answers name the correct entities and relationships, evidence status, source and every read path. Check required points and their conditions under [Use](../../ontology.md#use): an omitted required condition fails this walk; a citation or writer self-check alone does not establish coverage. They invent no claims and create no second fact home. Repair unclear definitions, boundaries or inaccessible existing evidence at their home or link. Truly missing evidence stays a focused question until supported; a new summary or runtime cannot settle it.
