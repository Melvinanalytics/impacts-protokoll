# ICM form selection

Owns: ICM form selection with its work report, composition, native file homes, data kinds and analysis placement, Capability orientation, tooling selection and the Knowledge Walk. Reader: author. Does not own: process decomposition, see [Process decomposition](zuschnitt.md).

Start with the unit that grows or repeats, or the bounded result whose steps can be declared. For business intake, use [Capture business meaning](../../impacts-method.md#capture-business-meaning). Given an offering or finished result, or when work is being set up or materially redesigned from an intended result, use [Reverse-engineer a product or service](../../impacts-method.md#reverse-engineer-a-product-or-service) before selecting a form or executor. This derivation can precede an established repeatable result. Refine form and populated home as evidence arrives; a provisional form confirms no process boundary.

Apply [Author or change](../../ontology.md#author-or-change) for missing or changing meaning and [Use](../../ontology.md#use) for existing definitions. This covers every form, including work without a Pipeline; apply [evidence and obligations](../../ontology.md#evidence-and-obligations) at each use boundary. Customer-facing capture follows the [working language](../../language.md#enforce-at-use-boundaries).

## Select the form

| ICM form | Home | Takes | Refuses, and why |
|---|---|---|---|
| Pipeline | [Data kinds](#data-kinds): Work for the run, Foundations (Definition) for the factory | Declared Inputs and Excluded context; a check after every Arbeitsschritt; editable output before expensive downstream work where a gate is declared | Human decisions at every stage boundary: only `gate: human` reserves a decision for a person ([gate rules](../../binding.md#signals-and-human-gates)); output inside the definition would change its bound OID; status from output-folder scans conflicts with `laufpfad`; reading whatever is present conflicts with input references and digests |
| Record Library | [Data kinds](#data-kinds): Subject record and its named records | One stated shape per record kind; status in the record's stage line; the name as identity | A record carrying its own Pipeline: link record and Vorgang by reference; template trees per record: folders need existing content; stored generated indexes: derive views |
| Knowledge Bundle | [Data kinds](#data-kinds): Foundations outside a Definition; received sources retain their kind | Layered loading; typed addresses (`quelle:`, `kennzahl:`, `rechenweg:`); navigation by links | Stub notes for planned content: no placeholder files; access tiers in frontmatter: the right-holder decides permission and records it under [Authority](../../ontology.md#authority) |
| Context Map | [Data kinds](#data-kinds): Work, for observed organization, work and data handoffs, as links between records and `analyse/` files | Captures of observed work in `analyse/`; patterns from repeated occurrence | Required scoring fields: customer types stay local and `type` suffices; stored dashboards: derive views |
| System Map | A repository that agents modify: its existing routers and files, across [data kinds](#data-kinds) | Existing routers for any repository whose code agents change, including the protocol, a Fachrepo or a customer workspace with `tools/` and `src/` | A unit kind: this is a property of the repository root |
| Umbrella | Several independent Pipelines: a small router to the process homes selected by [data kind](#data-kinds) | A root router over several Hauptprozesse | A unit kind: this is a router over independent processes |

When several open decisions need coordination, use a dated list in the existing case or record home linking each question to its responsible decider, needed inputs and consequence until decided; it coordinates, is not a fact home, and derives any execution status from `laufpfad`. Record each decision under [Decision record](#data-kinds), retaining its evidence and the revision it was given on; the coordination entry links there.

## Work report before proposing a tree

Before any tree proposal, briefly state:

For work being set up or materially redesigned, first apply [Reverse-engineer a product or service](../../impacts-method.md#reverse-engineer-a-product-or-service) to derive a provisional result boundary and necessary contributions. Use that derivation in the report below before selecting a form; it may establish that no repeatable process form exists yet.

1. Observed units that grow or repeat, and bounded results whose steps can be declared.
2. [Selected existing forms](#select-the-form) and their rationale.
3. Explicitly deferred forms.
4. Smallest populated starting home.

These orientation questions apply existing rules without adding duties:

- **Home:** Is there [one authoritative home](datenumgang.md#data-handling-in-an-arbeitsschritt), with bound snapshots distinguished from competing maintained copies?
- **Control:** Is the [control structure fixed before binding](../../binding.md#snapshot-and-provenance)? Forecasts and calendars are not frozen by it.
- **Worth:** Does the chosen form earn its burden under [Tooling stop](#tooling-stop) and [Minimize](../../impacts-method.md#minimize)?
- **Enforcement:** Does a [configured harness](../../ontology.md#enforcement-and-completion) enforce the selected execution checks?
- **Authority:** Does the right-holder or an [owned delegation rule](../../impacts-method.md#step-areas) authorize the decision or effect, without manufacturing a human decision under [Signals and human gates](../../binding.md#signals-and-human-gates)?

This report is conversational, not a repository artifact, file or frontmatter field.

## Composition

Forms compose while retaining their responsibilities. A Record Library plus Knowledge Bundle alone is not an Umbrella. Other forms compose without one. Select an Umbrella only when several independent Pipelines already exist. When Core contracts are selected, only Pipelines become Hauptprozesse; each selected Pipeline is exactly one Hauptprozess.

### Separation of Concerns

**Separation of Concerns:** Keep distinct responsibilities understandable at their existing homes and declare their necessary dependencies. Ontology and classification distinguish meanings and categories; a distinction alone does not require its own Arbeitsschritt, file or skill.

Process boundaries, reusable implementation/module boundaries and organizational or runtime deployment boundaries answer different questions. One intended use can connect several jobs or processes. A shared tool or interface alone establishes neither a shared domain contract nor a common runtime. Compare the actual consumers' meaning, inputs, checks, access and operating needs before selecting what to share.

For example, presentation content and PPTX or PDF rendering have different responsibilities. Keep shared claims and sources at one content home; specify each recipient's required format, editability, standalone explanation and other applicable checks under the existing output and acceptance contract. One coherent job may produce both formats. Format changes may also change required content: a PDF read without a speaker must contain its required explanation. Recheck affected exports after a shared content change; a format correction retains the content's meaning and required checks.

Apply the existing [Arbeitsschritt boundary criterion](zuschnitt.md#arbeitsschritt) when a separate result, route or authority boundary requires a split. Declare sending or publishing the rendered file as a separate permitted effect under [record writeback](../../binding.md#record-writeback).

## Native topology and boundaries

When assigning shared content or output variants to homes, apply [Separation of Concerns](#separation-of-concerns).

```text
Root router -> Domain router -> Fact home -> Source
```

`impacts init` creates the Core workspace's root `CONTEXT.md` router. Link domain routers and fact homes under its Domain homes line; no second entry point is needed. Use these homes according to ownership:

| Content | Existing home |
|---|---|
| Protocol instructions and Core implementation | Protocol checkout, identified by source and revision from the customer router |
| Customer orientation and working language | Customer root `CONTEXT.md`; direct links explain each selected area's purpose |
| Reusable process and local prompt | [Data kinds](#data-kinds): Foundations, including Definition |
| Executable operation | Existing dependency or tool implementation; earned `capabilities/<slug>/` outside the Hauptprozess |
| Data | The home its [data kind](#data-kinds) names |

<a id="data-kinds"></a>

Place and link after the [process cut](zuschnitt.md#hauptprozess); no Definition folder exists before [Minimize](../../impacts-method.md#minimize), while analysis, records and received sources may already exist.

Cut data by what it is: who changes it, how, and what checks it. Topic, folder and how widely it is used do not set its kind; how many steps use a foundation only picks its home. Each datum has one kind, judged by the business that holds it: what its own Vorgänge or reviews produce is work; what another party issues whole is a received source, even when that party produced it in its own Vorgang:

Ask the questions in Decided by in their numbered order; the first yes places the item. If none applies, use a derived view or a dated coordination list at the existing case or record home, not a new fact home.

| Data kind | Holds | Changed by | Check | Home | Decided by | ICM form |
|---|---|---|---|---|---|---|
| Work | What work and review produce: a Vorgang's drafts, check reports and offer; observations and findings with their evidence | The Arbeitsschritt or review that writes it | Hashes, routes and gates in a Vorgang; outside one, source and evidence label beside each claim | [Analysis placement](#analysis-placement) for analysis; [Tooling stop](#tooling-stop) for ordinary work; [exact attempt paths](../../binding.md#hauptprozess-tree-rules) for Core execution. Selected Core runs live in `vorgaenge/`; ordinary work stays at the existing process home | 1. Is it a selected Core Vorgang's run, or that Vorgang's work and review output? 9. Is it analysis, or other work and review output? | Pipeline run for a selected Core Vorgang; Context Map for analysis; none for ordinary work under [Tooling stop](#tooling-stop) |
| Foundations | How work is done: domain meaning, source mappings, rules, calculation rules with their decided parameters, document blanks, examples and style, standing preferences and pre-filters | Its responsible decision-maker, by decision, as a new revision; for a rule in an Arbeitsschritt body, that is a Hauptprozess revision | Authority and revision; each use names the revision it applied | The Arbeitsschritt body when only that Arbeitsschritt applies it and it fits as text; otherwise the existing domain/source home, with populated `grundlagen/` files only where needed. A Capability only implements a calculation; its rule stays here. A Definition uses the existing process/domain home; selected Core definitions live in `hauptprozesse/` and use HP/TP/AS `CONTEXT.md` bodies with no code, data or prompt subfolders inside an Arbeitsschritt | 2. Does it define how work is done, including a process Definition? Definition is the named case that declares a Hauptprozess: its whole tree is bound by tree OID; other foundations are bound at use by revision | Pipeline factory for Definition; Knowledge Bundle for other foundations |
| Population | Rows of a bulk source nobody has decided about yet, keyed by their source, such as all public tenders | Source updates | Source scope and identity | Outside Git, described by `quelle:`; promotion to a subject record follows [Record writeback](../../binding.md#record-writeback) | 3. Is it a row of a bulk source that nobody has decided about yet? | none |
| Received source | A document or message an outside issuer issues as a whole: one version of a tender with its documents, a signed contract, a customer email | Never edited in place: a change arrives as a new version or a signed amendment beside the others; see [snapshot step 2](../../binding.md#snapshot-and-provenance) | Digest | The record home it belongs to, such as the customer's case file (*Akte*), or the source system | 4. Did an outside issuer issue it whole? | none |
| Commitment | A named record: offer, order, project or mandate; parties, agreed scope and version, validity, acceptance or cancellation | Evidenced agreement or permitted change | Coverage and remaining obligations | `records/`, linked from its subjects | 5. Is it an offer, order, project or mandate? | Record Library |
| Subject record | Continuing business data about one domain object: a reference project, an expert profile, an address, insurance, capacity, a candidate's status | Its maintainer, a Vorgang through permitted [writeback](../../binding.md#record-writeback), or a declared job outside a Vorgang, on an evidenced event or correction, such as a decision about that object by the party it concerns | Evidence, as-of time, [retention and deletion](../../binding.md#retention-and-deletion); a value a rule computed names the rule revision and source versions it applied | Authoritative source system, or maintained `records/` only when real content needs it; use the [record shape](../templates/subject-record.md) and [stage/writeback rule](../../binding.md#record-writeback); Vorgänge bind excerpts | 6. Is it continuing data about one domain object that somebody has decided to keep? | Record Library |
| Decision record | One holder's readable decision over named subjects and revisions, with ID, date and source evidence | Fixed once decided; corrections supersede it | Authority, coverage and evidence | `records/`; each covered subject's record cites this one record | 7. Is it an independently identified decision over named subjects? | Record Library |
| Run record | Dated product of a tool or agent run outside any Vorgang, including a preselection round | Fixed once written | Inputs as references with `sha256`, actual run and output | Own record kind in `records/`, one entry per round; includes every candidate, rejected ones and lines sent | 8. Is it the dated product of a tool or agent run outside any Vorgang? | Record Library |

- One folder may hold several kinds, and one document may carry several; a folder name such as `grundlagen/` or `records/` does not prove a kind. A case file holds received sources and the case's status. Each datum keeps its own kind's check.
- Facts a received source states that later cases or steps rely on, such as contract terms or listed prices with their validity, are records that cite it, and their freshness lives on the record. A rule that applies such a term, such as a contract-fixed rate, reads it as a declared input value, so the term steers the result without becoming an instruction. A step's extract for its own case is work: a projection under [snapshot step 3](../../binding.md#snapshot-and-provenance). A blank or style a received source prescribes stays bound as that version and governs form like a foundation, without moving to `grundlagen/`.
- A preference for one case stays in that case's record. A standing preference, including one about a single counterpart such as a preferred client, belongs to the foundations and binds at its revision. A target or threshold set by decision belongs to the foundations; a measured value is work where a step computes it and a record once written back.
- A copy keeps its original's kind: a bound input or an export is evidence of the cited revision, not a second home. Work stays work when another Vorgang of the same business binds it as a [declared source input](../../binding.md#source-inputs-for-core-hauptprozesse). When it serves as evidence of a current state, the consuming job checks its as-of time against its own need; a state that later work keeps relying on is written back to its record.
- Any datum that holds personal data follows [Retention and deletion](../../binding.md#retention-and-deletion), whatever its kind.

A project is a commitment that stays open until acceptance or cancellation; an agreed change can alter its scope without ending it. It is a [domain object](../../ontology.md#protocol-vocabulary), not a form; its identity and state can outlast any Vorgang. Its plan, open questions and progress stay at its case home under [Tooling stop](#tooling-stop), including in Markdown. Its work can be a Pipeline covering even its whole result. When its work spans several Vorgänge, apply the [cut rules](zuschnitt.md#hauptprozess); each Vorgang keeps only its own execution state in its `laufpfad`. A changed Hauptprozess definition binds new Vorgänge only. Continuing after a restart explicitly selects, acquires and checks the predecessor's outputs as [declared source inputs](../../binding.md#source-inputs-for-core-hauptprozesse).

A mandate or standing agreement is a continuing commitment with parties, scope, validity, termination and coverage at its record home. A call-off is the bounded request under that agreement; its source and covered obligation open the applicable case or period Vorgang. The mandate has no execution state of its own. Record acceptance, cancellation and remaining obligations at the commitment, with links to its subjects and Vorgänge.

<a id="analysis-placement"></a>

- Analysis lives under `analyse/`: captures of today's work, backward traces and proposed Minimize moves are work outside a Vorgang, with source and evidence label beside each claim. Use `type: ist-prozess` for process captures; other analysis notes are plain Markdown. These are source material for [Identify](../../impacts-method.md#identify). No Arbeitsschritt binds analysis as a rule; a Vorgang may reference it as evidence. Candidate Hauptprozesse stay here as `hypothesis` until the owner confirms them by a commit moving them to `hauptprozesse/`, or by a recorded instruction naming the trees, date and owner’s words for that move. A migration move alone confirms nothing. An activity removed by its owner's decision stays visible here as `entfaellt` and never enters the definition tree.

For a new Core workspace, run `impacts init PATH --language en|de` ([what it writes](../../../README.md#optional-technical-use)). Before binding a Core Vorgang, initialize Git at that root; `init` neither creates Git nor installs a harness or source access. Resolve the protocol/Architect links, working language and selected domain homes before capture. Before a real Vorgang, the chosen harness must support the bound operations, source reads, checks, handoffs and human boundaries. Record its actual setup/dependency reference in the existing root body; placeholders or structural validity alone do not establish readiness. Existing repositories follow Restructure mode instead of running `init` over them.

- Routers hold identity, boundaries and links, not domain payload. Each claim and its evidence status have one fact home.
- Navigate through relative Markdown links without copying claims. Apply [domain addresses and relationships](../../ontology.md#domain-addresses-and-relationships) when a definition, derivation, source description or observation is independently cited, reused or changed. Domain keys connect table rows under [Tables and relationships](datenumgang.md#tables-and-relationships).
- A link label, compact table or adjacent sentence may state a relationship under [Domain addresses and relationships](../../ontology.md#domain-addresses-and-relationships); other surfaces link to its maintained home. Apply [Use](../../ontology.md#use) to distinguish folder membership, knowledge navigation, data dependency and execution route. Hauptprozess roles and transitions come from the [Hauptprozess tree rules](../../binding.md#hauptprozess-tree-rules) and each Arbeitsschritt's frontmatter, not router ordering.
- Create folders for existing content, not empty categories for possible future use.
- Customer types remain local vocabulary. `type` suffices until a real query needs another field.
- Instances sharing a lifecycle start in one fact file or table. A file per instance requires an independent query, independent change, its own evidence or its own relationships. The work report names the qualifying criterion for each split.
- Every `reported` handover claim resolves to the preserved handover or source artifact. A source register is a router or index, not a replacement for the actual artifact.
- An unknown workflow remains a gap; mark reconstructed work `hypothesis`. Supplied descriptions alone prove neither execution nor feasibility. Create a Hauptprozess only for work that fits [selected Core contracts](#select-the-form), with a bounded result and supported boundary.
- Explicitly internal material stays separate from customer facts and is excluded from customer questions.

An empty collection has an explicit authoritative empty state in its responsible router. Do not create an empty category, README or index merely to make absence clickable. Once entries exist, replace or extend the empty state with direct links. The Knowledge Walk may stop at an explicit empty state.

That state describes only the captured collection. A claim of business absence requires its own reachable evidence; otherwise that question remains open. A successful navigation stop does not establish completeness of the company model.

### Capability orientation

Where a workspace uses Capabilities from a Fachrepo or another domain home, its root `CONTEXT.md` links the early responsible router. That router identifies their supported local uses and directly links the existing source/adoption, setup and domain-contract homes needed for those uses. Use existing bindings to distinguish locally adopted revisions, historical use and candidates. Keep domain payload at its authoritative home.

Select the needed branch under [local context selection](../../impacts-method.md#load-context-locally-first). When that use combines domain meanings or relationships, apply [scoped harmonization](../../ontology.md#domain-addresses-and-relationships). The selected process explains the Capability's contribution to its Leistung; the Arbeitsschritt binds its operation under the [Capability call contract](../../capabilities.md#capability-call).

Orientation is complete when the selected path from the actually loaded repository instructions or declared entry resolves the local use, applicable source/revision, required domain meanings and operation/check contract, or retains a specific gap and its dependent-use restriction. Before adopting a changed route, exercise a supported use, a missing or incompatible source, and a nearby task that does not need that Capability. Record the actual read path and result. Finding the contract establishes navigation; execution and domain-use checks follow [enforcement and completion](../../ontology.md#enforcement-and-completion).

## Tooling stop

Selected Core Pipeline contracts fit bounded work whose next permitted Arbeitsschritt can be expressed through declared inputs, visible outputs, checks and routes, whether it runs once or recurs. Use [Tooling stop](#tooling-stop) and [Minimize](../../impacts-method.md#minimize) to compare the particular supported bindings/checks needed with native work. Repetition, seriousness or tool availability alone does not require Core. Human decision boundaries follow [Arbeitsschritt](zuschnitt.md#arbeitsschritt); required quality checking remains distinct from a human decision gate.

Core has one sequential `laufpfad`. It does not supply concurrent-user queues, runtime state isolation, real-time multi-agent messaging, deployment or undeclared model-selected branching. Keep those operations in their existing external system or configured harness and describe only the bounded interfaces, results and evidence needed by the selected form. If the intended runtime depends on those capabilities and no declared sequential boundary exists, do not present a folder pipeline as its orchestrator.

Ordinary files, folders and readable instructions support complete useful method use, including process guidance. Reuse existing domain, process, case and record homes for supported work, sources, open questions and continuation. This use needs neither Git, Python nor a harness and does not claim machine-validated Core Vorgang conformance. Choosing a particular check selects only its actual contract: Structural validation of a Hauptprozess without a Vorgang and hashing need Python without Git; Core Vorgang validation additionally requires its Git-bound Hauptprozess and attempt surfaces. Git binding preserves a definition revision; it proves neither execution nor authenticated approval.

Select each check for the condition required by the task, changed surface or intended claim. For ordinary file work with no history, repository-change or revision-binding claim, check the saved result, its required sources and continuation links directly. Use Git when history, a repository change or a declared revision binding is relevant, with the intended repository and comparison endpoints established. Invoke machine validation only when the task needs its specific condition and a capable checker is available for the known scope and inputs. Existing task authorization or configuration can select that check; routine authorized read-only checks need no fresh human approval. Tool availability creates no new gate or installation obligation. The [design-time check decision](zuschnitt.md#required-checks-and-review) fixes essential checks and their consequences before execution; the writer cannot demote a binding check to advisory.

A check with missing tools or execution errors counts as **missing** under [enforcement and completion](../../ontology.md#enforcement-and-completion). Make that status visible where the result matters. Preserve the technical diagnostic. A failed check retains its actual finding. Independent permitted preparation remains usable and resumable. Passing establishes only the checked condition on those inputs. Explain results to the user in order: progress made, consequence for the intended use, next action. Retain actual calculation, truth and authority requirements under [ontology enforcement](../../ontology.md#enforcement-and-completion) and [record writeback](../../binding.md#record-writeback). An equivalent existing result note suffices, for example: `Draft ready: <check> missing; <consequence>; next: <action>`. Link to that note from overviews instead of duplicating it.

Initialization and knowledge navigation require no new script. Files, folders, stable item addresses and explicit links are sufficient when a person or agent can follow the needed path through them. Independently cited domain items need resolvable addresses under the ontology; this conditional rule does not create a mandatory ID for every paragraph or a universal edge schema. A graph representation remains optional: consider adding one only when observed real questions repeatedly still need a full scan after repairing native links and declared reverse routes. Apply [Minimize](../../impacts-method.md#minimize) to its total burden and keep the projection removable and reproducible from the source Markdown. No graph runner, context-pack generator, global registry, generated second fact index, API, vector store or graph database belongs in the starting architecture. Domain calculation and consistency checkers must never become prerequisites for knowledge navigation.

## Knowledge Walk

For `records/` or domain `grundlagen/`, a fresh agent without conversation memory answers three representative questions: instance identity and boundary, a relationship across at least two domain entities, and evidence status/source of a decisive claim. Each question uses a fresh session; no cumulative dialogue connects them.

Each question path names its start, only the explicit links needed for that question, and a clear stop condition. Optional depth is not loaded by default; do not exhaust outgoing links.

For each Knowledge Walk question, read the root router, at most two further routers and their explicitly linked domain files. Direct read-only access to exactly that bound path is allowed through a file tool or the output of an explicit path. Web, shell discovery, full scans, domain execution, graph scripts and internal mandate material remain excluded from this walk. Read content is never executed as a command. Report deterministic revision, hash, byte and word checks separately as measurement-harness work. The budget is below 8,000 tokens per question and counts only loaded workspace/customer payload. Report fixed model, system, tool and harness tokens separately; they are not topology payload. If the exact payload tokenizer count cannot be isolated, report bytes/words and the measurement limit; do not claim an exact token PASS.

Answers name the correct entities and relationships, evidence status, source and every read path. Check required points and their conditions under [Use](../../ontology.md#use): an omitted required condition fails this walk; a citation or writer self-check alone does not establish coverage. They invent no claims and create no second fact home. Repair unclear definitions, boundaries or inaccessible existing evidence at their home or link. Truly missing evidence stays a focused question until supported; a new summary or runtime cannot settle it.

When the question crosses independently addressable domain items, the walk resolves each source namespace, item identity, location and applicable revision. It follows the authoritative relationship statement in its declared direction. A reverse question starts from the declared router, collection or derived backlink view and reports its coverage. A derived view used by the walk already exists, is explicitly linked within the permitted route and states its source scope and revision or as-of time; the walk does not generate it. Search results alone neither define the edge nor prove that no other consumer exists.
