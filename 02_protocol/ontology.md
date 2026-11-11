# Ontology, semantics and logic

Owns: protocol vocabulary, domain meaning, evidence labels, inference, authority for decisions and effects, and enforcement boundaries. Reader: everyone. Does not own: execution of a Vorgang, see [Binding and execution](binding.md).

This is the authoritative instruction for defining and applying domain meaning in IMPACTS. Choose [Author or change](#author-or-change) when meaning is missing or changing; choose [Use](#use) for an existing definition. Formatting corrections do not require model capture. Customer work follows the [language contract](language.md#enforce-at-use-boundaries).

**Ontology** identifies the kinds of things and relationships a domain distinguishes. **Semantics** states what a term, value or relationship means in context. **Logic** states which conclusion follows from which premises. A **taxonomy** orders kinds into levels or classes; every level owns a property of its own. A **schema** specifies checkable structural conditions. Schema conformance establishes those conditions, not the truth or completeness of a world model.

## Protocol vocabulary

These meanings remain stable across domains and languages. The existing [five schemas](schemas/) own their machine contracts.

| Machine term | English meaning | Boundary |
|---|---|---|
| `protocol` | Protocol release tag `vMAJOR.MINOR.PATCH`: the workspace pin for new work and the release recorded by each Vorgang. | Core requires its shape and uses the workspace and Vorgang values to select judgment by matching major and minor; without it, the legacy marker distinguishes not judged from `protocol pin missing; add protocol: <release> to the frontmatter`. [Snapshot and provenance](binding.md#snapshot-and-provenance). |
| `workspace` | Customer work and its root router | Domain knowledge and continuing records keep their own homes; selected Core Vorgänge require a Git-root workspace. The protocol repository supplies the method and Core, not customer facts. |
| `leistung` | Process result | The kind of result a Hauptprozess defines, as an embedded, ID-less contract: `ergebnis`, `kennzahl`, `abnahme` and optional `erreicht`. Each Vorgang owes one instance for its [subject](impacts-architect/references/zuschnitt.md#hauptprozess). A commercial offering (*Leistungsangebot*), a kind of product or service a business offers or plans to offer, has its own domain definition. |
| `hauptprozess` | Main process | Defines one kind of Leistung and the path to it under the [cut rules](impacts-architect/references/zuschnitt.md#hauptprozess); its folders follow the [layout](binding.md#hauptprozess-tree-rules). |
| `teilprozess` | Subprocess | Does no work itself; groups Arbeitsschritte to one `ergebnis`, one Leistungsstückliste component, in a domain-named subfolder with `CONTEXT.md`. The [layout rules](binding.md#hauptprozess-tree-rules) require this level even for a small Hauptprozess. |
| `arbeitsschritt` | Workstep | One coherent job with declared inputs, visible outputs, `pruefung` and routes. [Instructions, tools and data](impacts-method.md#compose-an-arbeitsschritt) contribute within this contract. |
| `ausloeser` | Trigger | The outside event that opens a Vorgang or continues a waiting attempt; [Decision results and Auslöser](binding.md#decision-results-and-auslöser) owns its rule. Core records the token only in a wait's `wiedereinstieg`; the entry Arbeitsschritt's Flow declares the opening one. |
| `hauptprozess_revision` | Bound Hauptprozess tree | A Vorgang binds a reachable `hauptprozesse/` tree as `git-tree:<oid>`. [Snapshot and provenance](binding.md#snapshot-and-provenance). |
| `vorgang` | Process instance | One instance of a Hauptprozess, bound to its Git tree. Its `laufpfad` alone owns execution state. |
| `versuch` | Attempt | One execution of one Arbeitsschritt, recorded in `laufpfad`. Its folder `<arbeitsschritt>/<nnn>/` holds only `output/`. [Execution](binding.md#execution). |
| `nummer` | Attempt number | Core checks consecutive numbers per Arbeitsschritt from 1 through 999 and three-digit folders. [Execution](binding.md#execution). |
| `gelesen` | Recorded input references | Core checks the recorded references and coverage of every declared input slot from opening onward. It resolves each file and checks its digest, or checks external-store reference shape. [Snapshot and provenance](binding.md#snapshot-and-provenance). |
| `geschrieben` | Recorded output references | Core checks every completed output file and its digest. [Snapshot and provenance](binding.md#snapshot-and-provenance). |
| `pfad` | Reference file path | Workspace-relative file address; Core reads working-tree output bytes or a recorded Git blob. [Snapshot and provenance](binding.md#snapshot-and-provenance). |
| `revision` | Source commit | On a file reference, `git-commit:<oid>` selects the immutable source blob. Core resolves it. [Snapshot and provenance](binding.md#snapshot-and-provenance). |
| `sha256` | File digest | Core compares `sha256:<64 hex>` with raw file bytes; external-store verification belongs to the harness. [Snapshot and provenance](binding.md#snapshot-and-provenance). |
| `ablage`, `schluessel` | External store and key | Core checks nonempty strings and the store name against the root router's `Ablage:` lines. The harness resolves personal data outside Git. [Snapshot and provenance](binding.md#snapshot-and-provenance). |
| `vorgaenger` | Predecessor Vorgang | Optional path to another Vorgang's `CONTEXT.md`; Core uses its position for a permitted restart. [Execution](binding.md#execution). |
| Capability | Reusable operation | Optional processing used by an Arbeitsschritt under the [Capability contract](capabilities.md#capability-contract). No additional Core type. |
| Harness | Whoever executes the bound operation, collects actual evidence and enforces prerequisites: configured software, an agent session or a person. The role grants no authority. | Core does not check this role. [History retention](binding.md#history-retention). |
| `pruefung` | Names the observable criterion that the Arbeitsschritt output is evaluated against. | Core checks the string's schema shape. [Arbeitsschritt](impacts-architect/references/zuschnitt.md#arbeitsschritt). |
| `routen` | A mapping from result names to Arbeitsschritte or ends. | Core checks route structure and transitions. [Declared](impacts-architect/references/zuschnitt.md#arbeitsschritt), [run](binding.md#execution). |
| `einstieg_ref` | The first Arbeitsschritt of a Hauptprozess. | Core checks that it resolves inside the Hauptprozess. [Layout rules](binding.md#hauptprozess-tree-rules). |
| `end:` | A terminal state of the Hauptprozess. | Core checks terminal route targets. [Hauptprozess](impacts-architect/references/zuschnitt.md#hauptprozess). |
| `gate` | A decision reserved for the responsible person. | Core checks human-gate structure. [Declared](impacts-architect/references/zuschnitt.md#arbeitsschritt), [run](binding.md#signals-and-human-gates). |
| `customer_touchpoint` | A customer interaction that creates trust, advice, commitment or experience. | Core checks only that the value is `standard` or `sacred`; no Core rule depends on it. The viewer displays it. [Identify](impacts-method.md#identify). |
| `freigabe` | Attribution of the responsible human's decision. | Core checks decision-attribution structure. [Signals and human gates](binding.md#signals-and-human-gates). |
| `wiedereinstieg` | The declared continuation of a waiting attempt. | Core checks waiting-attempt structure. [Waits](binding.md#waits). |
| `continuation_ref` | Inside `wiedereinstieg`: a workspace-relative path to an existing working-tree file describing continuation. | Core checks that it resolves to a regular file inside the workspace without symlinks. [Waits](binding.md#waits). |
| `faellig` | Inside `wiedereinstieg`: the next time the harness checks the wait, a quoted timestamp with offset. | Core checks the timestamp shape. [Waits](binding.md#waits). |
| `abgebrochen` | Owner-stopped attempt and derived Vorgang status; replaces the former owner-stop attempt token `beendet`. | Distinct from a normal routed end, whose derived Vorgang status remains `beendet`. [Vorgang progress](binding.md#vorgang-progress). |
| `status_seit` | When an attempt received its current status, a quoted timestamp with offset; a commit time records the file change, not the status start. | Core checks the timestamp shape. [Vorgang progress](binding.md#vorgang-progress). |
| `abnahme` | The conditions or thresholds under which the Leistung counts as reached. | Core checks the list's schema shape. [Leistung](impacts-architect/references/zuschnitt.md#leistung). |
| `erreicht` | The ends that achieve the Leistung. | Core checks achieving-end references. [Vorgang progress](binding.md#vorgang-progress). |

<a id="retired-names"></a>Retired names and their replacements are kept in [tests/retired_names.md](../tests/retired_names.md), read by [test_necessity.py](../tests/test_necessity.py) to reject plain occurrences outside inline code and paths in protocol Markdown and the root guides.

`leistung` names a role, not a format or content kind. Assessments, selections, permitted decisions, documents, artifacts and evidenced effects are overlapping examples of what may fulfill it under its acceptance conditions. Keep a result's conclusion, fulfillment of the obligation and permission for subsequent work distinct under [Evidence and obligations](#evidence-and-obligations). A supported negative conclusion can fulfill an assessment. A positive result establishes only its evidenced scope; any remaining conditions for subsequent work still apply.

The result kinds are output, Leistung, check result and end. An Arbeitsschritt output records what was produced; when it fulfills the Hauptprozess's acceptance and completion conditions, the Vorgang achieves the Leistung. An intermediate output leaves remaining obligations open. The delivered result fulfills the obligation, whether an internal or external party accepts it, and can remain an input to another process. The Hauptprozess's result metric measures the recipient's later use or change. That use or change completes a Vorgang only when `abnahme` names it as an observable condition; declare the time/window when that condition requires one. Otherwise measure it across Vorgänge and route evidenced findings to [Reviewed correction](impacts-method.md#reviewed-correction). Causal attribution requires more than the output's existence.

A Vorgang binds the Hauptprozess's definition tree: its folder with its Teilprozesse and Arbeitsschritte. A domain object's identity and state can span several Vorgänge. Completing a Vorgang changes that object only through an evidenced, permitted domain action. A run is one harness execution, such as one pipeline execution or one agent session. It belongs to the harness, is not a Vorgang and may serve ordinary work as well as several Vorgänge. The conformance cases `run-*` test Vorgänge; `laufpfad` is a Vorgang's path.

Apply [Use](#use) for the meaning and effect of every reference. Folder placement, a Markdown link, a domain key, a declared input or handoff and a Core route are not interchangeable.

The [Hauptprozess layout](binding.md#hauptprozess-tree-rules) and its [rules](binding.md#hauptprozess-tree-rules) own definition and Vorgang paths. Reference the actual file and revision carrying a claim, not just its Vorgang folder. Use the [Vorgang template](templates/vorgang.md).

For selected Core contracts, use the existing [templates](templates/) and preserve field names, types and ID prefixes; domain details belong in the body. Apply the [Tooling stop](impacts-architect/references/formwahl.md#tooling-stop). Core conformance requires actual applicable validation; a model's assertion cannot replace execution.

## Author or change

1. **Bound the question.** State the needed result, recipient and intended use. Identify the claims and actions the result must support.
2. **Find its home.** Follow the nearest `CONTEXT.md` to the existing definition and source. Repair an unreachable existing link. Extend that home only for missing meaning; create a populated Markdown file under `grundlagen/` only when no home exists.
3. **Define the necessary distinctions.** Use the [domain definition pattern](#domain-definition-pattern) or equivalent existing sections, applying [meaning and valid inference](#meaning-and-valid-inference) and [evidence and obligations](#evidence-and-obligations). Define terms and attributes once; let each consuming operation specify what it requires. A classification axis earns a field only when a check reads it. Retain source identity, scope and evidence. Keep missing information `open` with its question and dependent use. Give each kind one name, and review the name itself, not only the claims it carries. Run these checks when you add, rename or retire a name, change what it means, or find two names for one kind or one name in two senses:
   1. **Uses.** Search the definitions, schemas, code and tests the name reaches within the [permitted read set](impacts-method.md#load-context-locally-first), and list each use with file and line. State what you did not search. For a new name, also list the existing names for the same kind.
   2. **Meanings.** Group the uses by what the name refers to in each sentence. Compare definitions, not instance values or revisions. A name qualified by its owner or namespace is a name of its own.
   3. **Name test.** Two names that occur 1:1 with no field, constraint, lifecycle, owner, cardinality or end state that one lacks are one term; one name whose uses differ in any of these is two terms; a level that owns nothing goes; a term without a checkable definition gets one or goes.
   4. **Hierarchy test.** No use may merge two levels (Hauptprozess, Teilprozess, Arbeitsschritt), a kind with its instance (Hauptprozess with Vorgang, Arbeitsschritt with attempt), a harness run with a Vorgang, or an observation, its definition or its execution.
   5. **Link test.** The meaning has one home, and other maintained surfaces link it instead of restating it. A translation, a source-specific synonym at its domain home and a bound snapshot keep their declared source.
   6. **Loss.** Apply [Necessity](impacts-method.md#necessity) to each name you keep or delete. The number of files a change touches is no function.
   7. **Attack.** Search for the use that breaks your verdict. A sentence that explains why two names mean one thing is a finding, not a resolution.
   8. **Close.** Keep one current name and delete the others in the same change. Preserve quoted sources and historical bindings unchanged. Keep machine tokens until a release renames them, and map each renamed machine token once under [Protocol vocabulary](#protocol-vocabulary). For a protocol name, add each retired name to [Retired names](#retired-names); [test_necessity.py](../tests/test_necessity.py) then rejects a new plain occurrence in the files it scans. Qualify an ordinary word with a second legitimate sense where it is ambiguous; do not retire it. Record uses, meanings, verdict, loss and attack in the commit body or review record.
4. **Exercise the change.** Check a valid case, a missing or contradictory premise, and a plausible forbidden inference relevant to the changed rule. Reuse existing cases. Record expected results and actual checks separately. Include executable counterexamples for implemented technical conditions.

Capture is complete when the needed meanings resolve and each case has either a supported answer or an explicit gap, next action and use restriction. This does not establish that the missing fact exists or that an action is authorized.

## Use

1. **Resolve and bind.** Derive the needed answer points and conditions from the question and existing definition. For each, retain a compact source note: point → actually read path/section → scoped finding or gap. Keep identity/version, selection or validity time, units, rule conditions and provenance with the finding. Before reading sources for these points, follow [Load context locally first](impacts-method.md#load-context-locally-first) to select the permitted material. In a Vorgang, bind the relevant definition, excerpt and provenance as [declared inputs](binding.md#snapshot-and-provenance); a live link only locates the source. Folder containment means membership; `einstieg_ref` and `routen` mean execution order; a router link makes a responsible home navigable; a domain relationship states business meaning and scope; a domain key connects record instances; a declared input or handoff binds material for a job; a route governs execution; source authority follows its own evidence and revision. A hyperlink can locate any of them but establishes none of the other conditions.
2. **Apply.** Use rules whose premises hold for this excerpt under [Meaning and valid inference](#meaning-and-valid-inference). Preserve [evidence labels](#evidence-and-obligations); for required actions, apply [evidence and obligations](#evidence-and-obligations). Complete independent permitted work while dependent claims or actions remain blocked.
3. **Check the intended use.** The question, applicable definitions and declared output contract fix the required points and conditions before drafting; the writer cannot narrow that scope to fit its answer. For each condition, retain its source passage and matching passage in the checked answer revision, or a specific gap, next action and use restriction, in the existing check output. Check each stated claim against its source as well. A matching topic, citation or number does not cover a changed predicate, identity, time or scope. Correct omissions and unsupported claims, then recheck affected conditions before returning the answer. Cite the actual source/section. Execute the applicable [Enforcement and completion](#enforcement-and-completion) checks; a written check instruction is not evidence of execution.

An ordinary use does not refill the model or redesign its tests. Missing or conflicting meaning follows [Reviewed correction](impacts-method.md#reviewed-correction) at the existing home. Bound definitions and inputs remain unchanged; new evidence becomes declared output and, when needed, input to a subsequent attempt.

## Domain definition pattern

Use the existing domain schema and body sections. This is a writing aid, not a new type or Core schema. Include only distinctions required by the question; an irrelevant section needs no placeholder or justification ritual.

| Content | Record at its authoritative home |
|---|---|
| Question | Needed answer, scope and intended use. |
| Terms | Meaning; kind versus instance; source identity/key and revision where relevant; evidence. |
| Relationships | Named direction and endpoints; source/target keys or document references; required multiplicity, time and units; evidence for that relationship. |
| Inference | Premises → conclusion; rule source and scope; forbidden inference; executable calculation/check where applicable. |
| Obligations | Operation and scope → required condition; authority/source; check and failure consequence. Reference shared rules rather than copying them. |
| Cases | Relevant valid, missing/conflicting and forbidden-inference cases; expected result; actual result or explicitly not executed. |

## Domain addresses and relationships

Domain knowledge can exist before or outside a Hauptprozess. Give every definition, derivation, source description or observation that is independently cited, reused or changed one resolvable address at its authoritative home. Do not assign identifiers to prose that has no independent identity or relationship.

An address retains four distinct parts: **source namespace, item identity, resolvable location and applicable revision**. The source namespace is the stable identity or URI of the authoritative domain/source root, declared once at its existing router; a checkout path, repository display name or revision is not that identity. Reuse an existing business key or canonical source URI. If the root has no stable identity, keep cross-root identity open or assign one local customer-owned identity at that router before publishing references. Where an item has no existing key, a customer domain may use these readable local tokens:

| Token | Identifies | Does not identify |
|---|---|---|
| `kennzahl:<slug>` | One scoped metric definition: what is counted or assessed, unit, population or grain, time basis, and any source-selection or comparison basis that changes the meaning | A concrete source read or value, target, threshold or every similarly named metric |
| `rechenweg:<slug>` | One scoped derivation rule: required inputs or premises, method or formula, and applicability | Its spreadsheet/code implementation, one execution occurrence, its result or permission to use it |
| `quelle:<slug>` | One scoped description of where information comes from or is maintained: a system, collection, document, maintained table or recurring manual input channel | A record or value, a concrete acquisition, a revision, or the person who happened to provide or calculate it |
| `beobachtung:<slug>` | One bounded claim about a subject or case, recorded from a direct observation, source read, report or measurement | The evidence artifact, verified truth, an interpretation or causal conclusion, a calculation occurrence or a later Arbeitsschritt |

`<slug>` follows the Core lexical rule: lowercase ASCII letters and digits separated by single hyphens. These tokens are domain address identities, not Core types, required frontmatter fields or a closed protocol taxonomy. They are unique only within their declared source namespace. A cross-namespace reference retains that namespace; equal tokens never establish equal identity.

In plain use, `quelle:` answers where information comes from, `beobachtung:` what was found in a bounded case or source, `rechenweg:` how a value is derived, `kennzahl:` what that value means, and `arbeitsschritt:` which bounded job processes declared inputs and produces a visible, checkable output. A concrete value, source read and calculation occurrence stay in their case, business record or Vorgang evidence; they do not receive another definition identity merely because they are linked.

`leistung.kennzahl` remains the embedded, readable result-metric statement in the Core result contract. It is ID-less and does not create a `kennzahl:<slug>`. Link it to a domain metric only when that definition is independently cited, reused or changed; observed values remain case evidence. Local objectives, guardrails and acceptance thresholds stay in their consuming contract, including `abnahme` where applicable. Referencing them does not create another metric identity.

A `rechenweg:` states a rule or observed derivation description. Prescription, observed use, proposal and adoption are separate scoped claims with their own evidence; the same formula can be both prescribed and observed. Materially different concurrent formulas are distinct derivation descriptions. Give an observed formula another `rechenweg:` address only when it is independently cited, reused or changed; otherwise retain it under the case-local calculation occurrence. A workbook remains an implementation or evidence artifact, and an observation can record the bounded claim that its formula was used. None of these claims verifies a concrete calculation result or grants permission to use it.

A source description may be reported or open. It does not by itself establish authority, freshness, access or permission for use. A one-off human answer remains case evidence and the person remains its provider; the answer or person receives no `quelle:` address unless a maintained information source or recurring channel is independently cited, reused or changed.

An unqualified token refers only to the citing item's declared source namespace. Conflicting declarations of the same qualified identity remain unresolved until distinguished or reconciled; never select the first match. Identity follows the domain's stated identity rule, while revision identifies the cited definition state. A versioned evolution may retain identity; distinct concurrent scopes or new instances require distinct identities. A physical move preserves identity only with evidenced namespace continuity. Record location changes separately from identity mappings and preserve historical bindings. Splits and merges state which identities continue and which are new. A shared identity does not establish semantic equivalence across revisions.

Use a stable explicit anchor for an item inside a Markdown file. The readable link label may carry its token, for example `rechenweg:lieferzeit-angebot` linked to `grundlagen/lieferzeit.md#rechenweg-lieferzeit-angebot`. The link locates the current description; a historical claim or Vorgang also retains the cited revision or preserved snapshot. A rename repairs current references. A copy or fork establishes no unchanged authority or equivalence without an explicit mapping.

Write each maintained relationship once at the dependent item's home or at one scoped mapping home. Other surfaces link to that statement instead of maintaining another one. Name its direction, endpoints, applicable scope and evidence, plus time or validity conditions where they affect identity or permitted use. A date does not substitute for departmental, tenant, geographic or other applicable scope. A calculation can reference several definitions and sources; several processes can reference the same calculation rule; observations and later Arbeitsschritte relate many to many. Names, folder proximity, actors and matching tokens imply none of these edges. Backlinks and indexes are derived navigation: they may list known referring homes but do not become a second relationship authority or prove complete discovery. A reverse question uses a declared collection, router or derived view and states its coverage.

`arbeitsschritt:<slug>` remains a Core work contract. References to `beobachtung:`, `quelle:`, `rechenweg:` and `kennzahl:` belong in the Arbeitsschritt body, declared input/output provenance or an existing domain mapping home; they are not additional Core frontmatter fields. An Arbeitsschritt may use a source, apply a calculation rule, produce a value conforming to a metric definition and be supported by an observation only when the relationship, scope and evidence are stated.

An observation records the claim and subject or case. Retain each relevant clock under its own meaning: event or validity time; source issue/as-of time or revision; actual observation, acquisition or read time; and recording time. Distinguish them whenever they differ, keep an unknown required time `open`, and never substitute one clock for another. The evidence itself stays at its own source. A source-derived observation may restate or paraphrase what the source says, but it must not silently turn that statement into a claim about actual behaviour, cause, rule validity or authority. Retain the evidence origin and label, relevant domain links and remaining gaps. The reporter, data provider, calculator, maintainer, rule owner and decision authority remain distinct roles even when evidence shows that one person performs several; support each assignment separately. Split observations when case, time, evidence origin or evidence status differs materially. An observation needs no process assignment; later process design cites it without converting it into an `arbeitsschritt`.

Across departments or repositories, keep definitions distinct until a scoped mapping establishes their relationship. A harmonization note compares meaning, unit, population or grain, time basis, rule and intended use; it retains both addresses, evidence, unresolved differences, responsible authority and affected consumers. It may record scoped equivalence, broader/narrower meaning, conflict or an open relationship. A shared definition is adopted only by its applicable authority, and each consumer rebinds explicitly; authority over one scope does not substitute for a required decision in another affected scope. Prior citations remain unchanged.

Synthetic relationship example. Source namespace: `urn:impacts:example:delivery`; cited snapshot: `example-r3`. The example illustrates filing and links; it records no executed check, adopted customer rule, delivery promise or permission.

<a id="example-kennzahl-geschaetzte-lieferzeit"></a>
### `kennzahl:geschaetzte-lieferzeit`

Synthetic estimated calendar days for one offer case; this definition establishes no delivery promise.

<a id="example-quelle-erp-materialbestand"></a>
### `quelle:erp-materialbestand`

Synthetic governed description of a material-availability source.

<a id="example-quelle-produktionsplanung"></a>
### `quelle:produktionsplanung`

Synthetic governed description of a capacity-planning source.

<a id="example-rechenweg-lieferzeit-angebot"></a>
### `rechenweg:lieferzeit-angebot`

Within this synthetic scenario, revision 3 is **reported** as the prescribed rule for offer estimates. No rule owner or adoption decision is evidenced.

| Relationship | Target | Applicable scope/time | Relationship evidence |
|---|---|---|---|
| calculates | [`kennzahl:geschaetzte-lieferzeit`](#example-kennzahl-geschaetzte-lieferzeit) | Offer estimates; rule revision 3 | `reported`: synthetic scenario statement; formula execution untested |
| uses | [`quelle:erp-materialbestand`](#example-quelle-erp-materialbestand) | Material availability input under source mapping revision 2 | `hypothesis`: no concrete source read |
| uses | [`quelle:produktionsplanung`](#example-quelle-produktionsplanung) | Capacity input under source mapping revision 5 | `hypothesis`: no concrete source read |

<a id="example-evidence-note-o17"></a>
### Synthetic evidence excerpt `case-note-o17`

> On 2026-09-18, a case worker reported that a personal workbook displayed an estimated delivery time of 12 calendar days for synthetic offer O-17 as of 2026-09-16. The workbook formula was not inspected.

This excerpt is the evidence artifact for the report below. It does not establish the formula, input truth, compliance, acceptance or actual use.

<a id="example-beobachtung-lieferzeit-workbook-o17"></a>
### `beobachtung:lieferzeit-workbook-o17`

| Item | Recorded meaning |
|---|---|
| Subject/case | Synthetic offer O-17 |
| Claim | A case worker reported that a personal workbook displayed 12 calendar days. |
| Calculation occurrence | Case-local key `O-17/C-02`; not another `rechenweg:` identity |
| Event/validity time | Workbook display concerned the offer state on 2026-09-16. |
| Source issue/as-of | Workbook revision and formula are `open`. |
| Observation/acquisition time | Conversation recorded on 2026-09-18; workbook not acquired. |
| Recording time | Observation entered on 2026-09-21. |
| Evidence origin and label | [`case-note-o17`](#example-evidence-note-o17); `reported` for the person's statement |
| Roles | Reporter: case worker. Data provider, calculator, maintainer, rule owner and decision authority: `open`. |
| Rule relationship | Comparison candidate: [`rechenweg:lieferzeit-angebot`](#example-rechenweg-lieferzeit-angebot). Whether the workbook used or complied with that rule is `open`. |
| Metric relationship | Comparison candidate: [`kennzahl:geschaetzte-lieferzeit`](#example-kennzahl-geschaetzte-lieferzeit). Whether the displayed field conforms to that definition is `open`; the value is not a delivery promise. |
| Check, acceptance and use | `open`; none follows from the report. |

The observation may later inform more than one process boundary, such as determining an estimate and preparing an offer. This example defines no Hauptprozess, so those candidate jobs remain open descriptions rather than invented `arbeitsschritt:` addresses. Conversely, a later resolved Arbeitsschritt may cite several observations. This many-to-many mapping does not convert an observation into an Arbeitsschritt.

The relationship tables record declared claims, not a calculation execution, source read, acceptance or permission. The concrete displayed value and occurrence stay in case evidence; the observation claim, occurrence and supporting evidence retain separate identities.

## Evidence and obligations

Claims in definitions, records and reviews carry their source and one label, listed from weakest to strongest:

- `open`: an unanswered question or missing input.
- `hypothesis`: an interpretation or proposal awaiting validation.
- `reported`: a source or person states the claim; its factual content has not been verified.
- `verified`: the specific claim is supported by an inspectable check or a confirmed decision within the decision-maker's authority. Name what was checked or decided and for which scope.

A claim carries no stronger label than its evidence supports. An answer carries the weakest label of its premises. Inspecting a brochure can verify its wording while its delivery promise remains `reported`. A confirmed decision establishes its scoped rule, not an external fact. Keep contradictory evidence reachable and the unresolved conclusion `open`. Labels do not confer freshness, business permission or authenticated human approval. A document-level label applies only where it fits; qualify differing claims inline. A Hauptprozess with unlabelled facts is not finished.

**`MUST` describes an obligation within an explicitly named scope.** It is not an evidence label or a new Core field. Use this form in the existing rule or Arbeitsschritt body:

```text
MUST: Before <operation/use>, <condition> must hold within <scope>.
Basis: <authoritative rule or decision, with revision and applicable authority>.
Check: <actual checker or responsible decision-maker, inputs and evidence>.
Failure: <existing route, wait or restriction on the dependent use>.
```

Reference an existing basis or check instead of repeating it. State an operation's needed conditions at its boundary; a product can be recorded without a price even when a priced offer requires one. Conflicting obligations leave the affected action unresolved until the applicable authority settles the conflict. An agent cannot invent precedence or promote a proposal by marking it `MUST`. When an always-loaded rule and the bound Arbeitsschritt disagree, the agent blocks; it does not pick a winner.

Keep these claims distinct: a policy **was adopted**; its predicted benefit **is supported**; this Vorgang **complied**. An adopted policy may be binding while its expected benefit remains `hypothesis`. A source report remains `reported` until the particular claim has appropriate verification. A check on reference consistency verifies only that condition on those inputs, not a delivery promise or sending permission.

## Meaning and valid inference

- **Identity:** Names are labels. Apply the stated identity rule, including source system, tenant and version where needed. Matching IDs from different systems require an evidenced mapping. Define source-specific synonyms at the domain home.
- **Kind and instance:** A product type is not a delivered item. Requested, offered, agreed, delivered and consumed are distinct claims with distinct evidence. A commercial service describes a business offering; a tool or Capability supplies an operation. Their relationship must be stated, not inferred from the shared word “service”.
- **Relationship:** Preserve direction, endpoints and evidence. `A → B → C` establishes no arbitrary A–C relationship. Inversion, transitivity and causality need their own premises.
- **Scope:** Check relevant units, periods, state, multiplicity and coverage. Missing is neither zero nor false. No result means `open` unless the source is sufficiently complete for the question.
- **Derivation:** Retain premises and rule. Execute fixed calculations and automated formal deductions deterministically. A correct calculation remains conditional on its inputs; free interpretation retains its own evidence status. A result cannot supply its own missing premise: acquire independent evidence or leave the conclusion `open`.

## Authority

A right to decide, permit or bind belongs to its holder: whoever the applicable rule, contract or ownership names, or a delegate under a rule the holder owns. Only the holder's decision confers authority, evidenced for its object, scope and revision. Nothing else does: not a role, tool or data availability, a passing check, a hash or validation result, a draft or proposal, an attribution string, an expiry or an agent's confidence. On its declared path, an attempt needs a human decision only where the Arbeitsschritt declares `gate: human`.

| Act | Holder | Record |
|---|---|---|
| Decide at a declared human gate | The responsible human the Arbeitsschritt names | `freigabe` beside the chosen route in the Vorgang ([Signals and human gates](binding.md#signals-and-human-gates)) |
| Permit access, use or an effect | The holder of that right | Holder and basis in the Arbeitsschritt's Authority section |
| Adopt or change a rule or definition | Its decision-maker, within that scope | The decision and a new revision at the rule's home |
| Confirm a Hauptprozess definition | Its owner | The commit that places the tree in the [definition home](impacts-architect/references/formwahl.md#select-the-form) |
| Clear a confirmed definition for real work | The responsible customer | A line in the workspace root `CONTEXT.md`: who, when, which tree, which test Vorgänge |

## Enforcement and completion

| Boundary | Actual check | Limit |
|---|---|---|
| Core structure | `impacts validate` checks only that files, IDs and references resolve and match their digest under the implemented schemas, process paths and bound Vorgang surfaces. | Core causes no effect and makes no business judgement. |
| Domain use | Arbeitsschritt's named checker executes required identity, relationship, validity, unit and calculation checks. | Does not establish untested conditions or source truth. |
| Action | Executing harness checks required results and applicable authority before the dependent transition/effect. | A label, document hash or agent consensus does not authenticate a decision. |

Core validation does not compare independently retained earlier execution states or detect coordinated rewrites. It neither enforces the [gate and touchpoint preflight](binding.md#signals-and-human-gates) nor authenticates a person or decision; the harness supplies the actual checks and trusted decision evidence.

Declared input coverage and digest checks establish reachable, bound references, not that the selected file is the right source; the Arbeitsschritt's own check judges that. For `ablage` references, Core checks shape and the declared store name, not the store's bytes. It counts these references as not verified; lack of byte verification is never an error. The harness verifies those bytes and their digest.

Core provides no write service, including writing or renumbering display prefixes. Authorized deletion of bound bytes yields the same missing-reference or digest findings as tampering; Core cannot distinguish them and has no deletion state. The harness retains the authorization and minimal receipt under [Retention and deletion](binding.md#retention-and-deletion).

`pruefung` names the observable criterion. The body references the actual checker or accountable person and failure route. The existing declared output or bound upstream input carries **input/rule/output revision, checked condition and scope, observed result, remaining gap and use consequence**. For time-dependent conditions, retain the actual judged/as-of time, its source and applicable rule, keeping acquisition and recording times distinct. A loop's pass limit requires its declared counted unit and complete bound counting evidence; a count of attempts alone does not establish it. For harness-executed operations, the harness executes the check or validates an applicable result from its trusted execution path; model-written success text is insufficient. A failed, missing, stale or inapplicable required check blocks the transition/effect that requires it to pass. A declared failure route can carry that finding into recovery or a negative end; otherwise retain the appropriate wait. Independent permitted work continues.

Implement only checks the intended use needs, at its existing boundaries; no universal ontology engine is required. A bound snapshot supports reproducibility. An external write also needs the declared current-state/conflict check at the action boundary, as specified in [record writeback](binding.md#record-writeback).

## Examples and learning

The [linked-data example](impacts-architect/references/datenbezug.md#checkable-questions-and-limits) separates agreed quantities from delivery and device-specific service coverage. The [company walkthrough](impacts-architect/references/datenbezug.md#from-catalog-through-pipeline-to-a-filled-offer) connects products, services, independent processes and a reusable offer blank with separate Vorgänge. All supplied example values remain synthetic; proposed checks, acceptance and delivery stay explicitly unexecuted or unevidenced unless a real test supplies their narrowly scoped evidence.

For observed defects and correction proposals, follow [Reviewed correction](impacts-method.md#reviewed-correction).
