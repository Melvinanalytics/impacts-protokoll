# Ontology, semantics and logic

This is the authoritative instruction for defining and applying domain meaning in IMPACTS. Choose [Author or change](#author-or-change) when meaning is missing or changing; choose [Use](#use) for an existing definition. Formatting corrections do not require model capture. Customer work follows the [language contract](language.md#enforce-at-use-boundaries).

**Ontology** identifies the kinds of things and relationships a domain distinguishes. **Semantics** states what a term, value or relationship means in context. **Logic** states which conclusion follows from which premises. A **schema** specifies checkable structural conditions. Schema conformance establishes those conditions, not the truth or completeness of a world model.

## Protocol vocabulary

These meanings remain stable across domains and languages. The existing [five schemas](schemas/) own their machine contracts.

| Machine term | English meaning | Boundary |
|---|---|---|
| `workspace` | Customer work and its root router | Domain knowledge and continuing records keep their own homes; selected Core Runs require a Git-root workspace. The protocol repository supplies the method and Core, not customer facts. |
| `leistung` | Accepted process result | Embedded, ID-less result contract: end state, metric and acceptance. A commercial offering has its own domain definition. |
| `hauptprozess` | Main process | Root of one Application at `applications/<slug>/CONTEXT.md`; positive completion achieves its result. |
| `teilprozess` | Subprocess | A coherent context section of that main process, in a domain-named subfolder. |
| `arbeitsschritt` | Workstep | One coherent job with declared inputs, visible outputs, `pruefung` and routes. [Instructions, tools and data](impacts-method.md#compose-an-arbeitsschritt) contribute within this contract. |
| `vorgang` | Run | One execution bound to an Application Git tree. Its `laufpfad` alone owns execution state. |
| Capability | Reusable operation | Optional processing used by a workstep; the [Capability contract](capabilities.md#capability-contract) alone owns its contract and authority boundaries. No additional Core type. |

An **Application** is the reusable main-process tree, not an additional object above it. An **attempt** is one `laufpfad` entry with its bound input set; revisiting a workstep creates its next attempt. A domain object's identity and state can span several runs. Completing a run changes that object only through an evidenced, permitted domain action.

Folder containment means **membership**; `einstieg_ref` and `routen` mean **execution order**; a Markdown link provides **knowledge navigation**; a domain key connects **record instances**. Each reference retains its stated meaning. A knowledge link alone establishes neither an execution route nor a business relationship.

Selected Core definitions live at `applications/<hauptprozess>/<teilprozess>/<arbeitsschritt>/CONTEXT.md`. Run files live at `vorgaenge/<vorgang>/<arbeitsschritt>/<versuch>/input/` or `output/`; attempts start at `001`. Reference the actual file and revision carrying a claim, not just its run folder. Use the [run template](templates/vorgang.md).

For selected Core contracts, use the existing [templates](templates/) and preserve field names, types and ID prefixes; domain details belong in the body. Apply the [ordinary-use and machine-validation boundary](impacts-architect/references/formwahl.md#tooling-stopp). Core conformance requires actual applicable validation; a model's assertion cannot replace execution.

## Author or change

1. **Bound the question.** State the needed result, recipient and intended use. Identify the claims and actions the result must support.
2. **Find its home.** Follow the nearest `CONTEXT.md` to the existing definition and source. Repair an unreachable existing link. Extend that home only for missing meaning; create a populated Markdown file under `grundlagen/` only when no home exists.
3. **Define the necessary distinctions.** Use the [domain definition pattern](#domain-definition-pattern) or equivalent existing sections, applying [meaning and valid inference](#meaning-and-valid-inference) and [evidence and obligations](#evidence-and-obligations). Define terms and attributes once; let each consuming operation specify what it requires. Retain source identity, scope and evidence. Keep missing information `open` with its question and dependent use.
4. **Exercise the change.** Check a valid case, a missing or contradictory premise, and a plausible forbidden inference relevant to the changed rule. Reuse existing cases. Record expected outcomes and actual checks separately. Include executable counterexamples for implemented technical conditions.

Capture is complete when the needed meanings resolve and each case has either a supported answer or an explicit gap, next action and use restriction. This does not establish that the missing fact exists or that an action is authorized.

## Use

1. **Resolve and bind.** Derive the needed answer points and conditions from the question and existing definition. For each, retain a compact source note: point → actually read path/section → scoped finding or gap. Keep identity/version, selection or validity time, units, rule conditions and provenance with the finding. Load only the sources needed to close those points. In a run, bind the relevant definition, excerpt and provenance as [declared inputs](capabilities.md#snapshot-und-herkunftsnachweis); a live link only locates the source.
2. **Apply.** Use rules whose premises hold for this excerpt under [Meaning and valid inference](#meaning-and-valid-inference). Preserve [evidence labels](impacts-architect/references/zuschnitt.md#evidence); for required actions, apply [evidence and obligations](#evidence-and-obligations). Keep unresolved contradictions reachable. Complete independent permitted work while dependent claims or actions remain blocked.
3. **Check the intended use.** The question, applicable definitions and declared output contract fix the required points and conditions before drafting; the writer cannot narrow that scope to fit its answer. For each condition, retain its source passage and matching passage in the checked answer revision, or a specific gap, next action and use restriction, in the existing check output. Check each stated claim against its source as well. A matching topic, citation or number does not cover a changed predicate, identity, time or scope. Correct omissions and unsupported claims, then recheck affected conditions before returning the answer. Cite the actual source/section. Execute the applicable [Enforcement and completion](#enforcement-and-completion) checks; a written check instruction is not evidence of execution. Successful checks do not supply missing authority.

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

Domain knowledge can exist before or outside an Application. Give every definition, derivation, source description or observation that is independently cited, reused or changed one resolvable address at its authoritative home. Do not assign identifiers to prose that has no independent identity or relationship.

An address retains four distinct parts: **source namespace, item identity, resolvable location and applicable revision**. The source namespace is the stable identity or URI of the authoritative domain/source root, declared once at its existing router; a checkout path, repository display name or revision is not that identity. Reuse an existing business key or canonical source URI. If the root has no stable identity, keep cross-root identity open or assign one local customer-owned identity at that router before publishing references. Where an item has no existing key, a customer domain may use these readable local tokens:

| Token | Identifies | Does not identify |
|---|---|---|
| `kennzahl:<slug>` | One scoped metric definition: what is counted or assessed, unit, population or grain, time basis, and any source-selection or comparison basis that changes the meaning | A concrete source read or value, target, threshold or every similarly named metric |
| `rechenweg:<slug>` | One scoped derivation rule: required inputs or premises, method or formula, and applicability | Its spreadsheet/code implementation, one execution occurrence, its result or permission to use it |
| `quelle:<slug>` | One scoped description of where information comes from or is maintained: a system, collection, document, maintained table or recurring manual input channel | A record or value, a concrete acquisition, a revision, or the person who happened to provide or calculate it |
| `beobachtung:<slug>` | One bounded claim about a subject or case, recorded from a direct observation, source read, report or measurement | The evidence artifact, verified truth, an interpretation or causal conclusion, a calculation occurrence or a later workstep |

`<slug>` follows the Core lexical rule: lowercase ASCII letters and digits separated by single hyphens. These tokens are customer-foundation identities, not Core types, required frontmatter fields or a closed protocol taxonomy. They are unique only within their declared source namespace. A cross-namespace reference retains that namespace; equal tokens never establish equal identity.

In plain use, `quelle:` answers where information comes from, `beobachtung:` what was found in a bounded case or source, `rechenweg:` how a value is derived, `kennzahl:` what that value means, and `arbeitsschritt:` which bounded job processes declared inputs and produces a visible, checkable output. A concrete value, source read and calculation occurrence stay in their case, business record or Run evidence; they do not receive another definition identity merely because they are linked.

`leistung.kennzahl` remains the embedded, readable result-metric statement in the Core result contract. It is ID-less and does not create a `kennzahl:<slug>`. Link it to a domain metric only when that definition is independently cited, reused or changed; observed values remain case evidence. Local objectives, guardrails and acceptance thresholds stay in their consuming contract, including `abnahme` where applicable. Referencing them does not create another metric identity.

A `rechenweg:` states a rule or observed derivation description. Prescription, observed use, proposal and adoption are separate scoped claims with their own evidence; the same formula can be both prescribed and observed. Materially different concurrent formulas are distinct derivation descriptions. Give an observed formula another `rechenweg:` address only when it is independently cited, reused or changed; otherwise retain it under the case-local calculation occurrence. A workbook remains an implementation or evidence artifact, and an observation can record the bounded claim that its formula was used. None of these claims verifies a concrete calculation result or grants permission to use it.

A source description may be reported or open. It does not by itself establish authority, freshness, access or permission for use. A one-off human answer remains case evidence and the person remains its provider; the answer or person receives no `quelle:` address unless a maintained information source or recurring channel is independently cited, reused or changed.

An unqualified token refers only to the citing item's declared source namespace. Conflicting declarations of the same qualified identity remain unresolved until distinguished or reconciled; never select the first match. Identity follows the domain's stated identity rule, while revision identifies the cited definition state. A versioned evolution may retain identity; distinct concurrent scopes or new instances require distinct identities. A physical move preserves identity only with evidenced namespace continuity. Record location changes separately from identity mappings and preserve historical bindings. Splits and merges state which identities continue and which are new. A shared identity does not establish semantic equivalence across revisions.

Use a stable explicit anchor for an item inside a Markdown file. The readable link label may carry its token, for example `rechenweg:lieferzeit-angebot` linked to `grundlagen/lieferzeit.md#rechenweg-lieferzeit-angebot`. The link locates the current description; a historical claim or Run also retains the cited revision or preserved snapshot. A rename repairs current references. A copy or fork establishes no unchanged authority or equivalence without an explicit mapping.

Write each maintained relationship once at the dependent item's home or at one scoped mapping home. Other surfaces link to that statement instead of maintaining another one. Name its direction, endpoints, applicable scope and evidence, plus time or validity conditions where they affect identity or permitted use. A date does not substitute for departmental, tenant, geographic or other applicable scope. A calculation can reference several definitions and sources; several processes can reference the same calculation rule; observations and later worksteps relate many to many. Names, folder proximity, actors and matching tokens imply none of these edges. Backlinks and indexes are derived navigation: they may list known referring homes but do not become a second relationship authority or prove complete discovery. A reverse question uses a declared collection, router or derived view and states its coverage.

`arbeitsschritt:<slug>` remains a Core work contract. References to `beobachtung:`, `quelle:`, `rechenweg:` and `kennzahl:` belong in the workstep body, declared input/output provenance or an existing domain mapping home; they are not additional Core frontmatter fields. A workstep may use a source, apply a calculation rule, produce a value conforming to a metric definition and be supported by an observation only when the relationship, scope and evidence are stated.

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

The observation may later inform more than one process boundary, such as determining an estimate and preparing an offer. This example defines no Application, so those candidate jobs remain open descriptions rather than invented `arbeitsschritt:` addresses. Conversely, a later resolved workstep may cite several observations. This many-to-many mapping does not convert an observation into a workstep.

The relationship tables record declared claims, not a calculation execution, source read, acceptance or permission. The concrete displayed value and occurrence stay in case evidence; the observation claim, occurrence and supporting evidence retain separate identities.

## Evidence and obligations

The [evidence labels](impacts-architect/references/zuschnitt.md#evidence) describe support for individual claims. **`MUST` describes an obligation within an explicitly named scope.** It is not an evidence label or a new Core field. Use this form in the existing rule or workstep body:

```text
MUST: Before <operation/use>, <condition> must hold within <scope>.
Basis: <authoritative rule or decision, with revision and applicable authority>.
Check: <actual checker or responsible decision-maker, inputs and evidence>.
Failure: <existing route, wait or restriction on the dependent use>.
```

Reference an existing basis or check instead of repeating it. State an operation's needed conditions at its boundary; a product can be recorded without a price even when a priced offer requires one. Conflicting obligations leave the affected action unresolved until the applicable authority settles the conflict. An agent cannot invent precedence or promote a proposal by marking it `MUST`.

Keep these claims distinct: a policy **was adopted**; its predicted benefit **is supported**; this run **complied**. An adopted policy may be binding while its expected benefit remains `hypothesis`. A source report remains `reported` until the particular claim has appropriate verification. A check on reference consistency verifies only that condition on those inputs, not a delivery promise or sending permission.

<a id="bedeutung-und-zulässige-schlüsse"></a>
## Meaning and valid inference

- **Identity:** Names are labels. Apply the stated identity rule, including source system, tenant and version where needed. Matching IDs from different systems require an evidenced mapping. Define source-specific synonyms at the domain home.
- **Kind and instance:** A product type is not a delivered item. Requested, offered, agreed, delivered and consumed are distinct claims with distinct evidence. A commercial service describes a business offering; a tool or Capability supplies an operation. Their relationship must be stated, not inferred from the shared word “service”.
- **Relationship:** Preserve direction, endpoints and evidence. `A → B → C` establishes no arbitrary A–C relationship. Inversion, transitivity and causality need their own premises.
- **Scope:** Check relevant units, periods, state, multiplicity and coverage. Missing is neither zero nor false. No result means `open` unless the source is sufficiently complete for the question. Keep contradictory evidence reachable.
- **Derivation:** Retain premises and rule. Execute fixed calculations and automated formal deductions deterministically. A correct calculation remains conditional on its inputs; free interpretation retains its own evidence status. A result cannot supply its own missing premise: acquire independent evidence or leave the conclusion `open`.

<a id="durchsetzung-und-abschluss"></a>
## Enforcement and completion

| Boundary | Actual check | Limit |
|---|---|---|
| Core structure | `impacts validate`: implemented schemas, references, process paths and bound run surfaces. | Does not validate arbitrary domain claims, language or permissions. |
| Domain use | Workstep's named checker executes required identity, relationship, validity, unit and calculation checks. | Does not establish untested conditions or source truth. |
| Action | Executing harness checks required results and applicable authority before the dependent transition/effect. | A label, document hash or agent consensus does not authenticate a decision. |

`pruefung` names the observable criterion. The body references the actual checker or accountable person and failure route. The existing declared output or bound upstream input carries **input/rule/output revision, checked condition and scope, observed result, remaining gap and use consequence**. For harness-executed operations, the harness executes the check or validates an applicable result from its trusted execution path; model-written success text is insufficient. A failed, missing, stale or inapplicable required check blocks the transition/effect that requires it to pass. A declared failure route can carry that finding into recovery or a negative end; otherwise retain the appropriate wait. Independent permitted work continues. Check output and action authority remain separate.

The Core does not interpret this Markdown convention. Implement only checks needed by the application, at its existing boundaries; no universal ontology engine is required. A bound snapshot supports reproducibility. An external write also needs the declared current-state/conflict check at the action boundary, as specified in [record writeback](capabilities.md#rückübertragung-in-geschäftsrecords).

## Examples and learning

The [linked-data example](impacts-architect/references/datenbezug.md#prüfbare-fragen-und-grenzen) separates agreed quantities from delivery and device-specific service coverage. The [company walkthrough](impacts-architect/references/datenbezug.md#vom-katalog-über-die-pipeline-zum-ausgefüllten-angebot) connects products, services, independent processes and a reusable offer blank with separate runs. All supplied example values remain synthetic; proposed checks, acceptance and delivery stay explicitly unexecuted or unevidenced unless a real test supplies their narrowly scoped evidence.

A run records observations and correction proposals. [Reviewed correction](impacts-method.md#reviewed-correction) exercise the counterexample, a related new question and affected uses before a new definition revision. Earlier runs retain their definitions. Reuse meaning, access and tests within their premises; bind sources, language and authority for the destination. Better answers or lower token cost require measured results, not additional labels.
