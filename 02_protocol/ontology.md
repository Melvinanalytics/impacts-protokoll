# Ontology, semantics and logic

This is the authoritative instruction for defining and applying domain meaning in IMPACTS. Choose [Author or change](#author-or-change) when meaning is missing or changing; choose [Use](#use) for an existing definition. Formatting corrections do not require model capture. Customer work follows the [language contract](language.md#enforce-at-use-boundaries).

**Ontology** identifies the kinds of things and relationships a domain distinguishes. **Semantics** states what a term, value or relationship means in context. **Logic** states which conclusion follows from which premises. A **schema** specifies checkable structural conditions. Schema conformance establishes those conditions, not the truth or completeness of a world model.

## Protocol vocabulary

These meanings remain stable across domains and languages. The existing [five schemas](schemas/) own their machine contracts.

| Machine term | English meaning | Boundary |
|---|---|---|
| `workspace` | Customer work and its root router | Git-root home for selected Applications and runs; domain knowledge and continuing records keep their own homes. The protocol repository supplies the method and Core, not customer facts. |
| `leistung` | Accepted process result | Embedded, ID-less result contract: end state, metric and acceptance. A commercial offering has its own domain definition. |
| `hauptprozess` | Main process | Root of one Application at `applications/<slug>/CONTEXT.md`; positive completion achieves its result. |
| `teilprozess` | Subprocess | A coherent context section of that main process, in a domain-named subfolder. |
| `arbeitsschritt` | Workstep | One coherent job with declared inputs, visible outputs, `pruefung` and routes. [Instructions, tools and data](impacts-method.md#compose-an-arbeitsschritt) contribute within this contract. |
| `vorgang` | Run | One execution bound to an Application Git tree. Its `laufpfad` alone owns execution state. |
| Capability | Reusable operation | Optional processing used by a workstep; the [Capability contract](capabilities.md#capability-contract) alone owns its contract and authority boundaries. No additional Core type. |

An **Application** is the reusable main-process tree, not an additional object above it. An **attempt** is one `laufpfad` entry with its bound input set; revisiting a workstep creates its next attempt. A domain object's identity and state can span several runs. Completing a run changes that object only through an evidenced, permitted domain action.

Folder containment means **membership**; `einstieg_ref` and `routen` mean **execution order**; a Markdown link provides **knowledge navigation**; a domain key connects **record instances**. Each reference retains its stated meaning. A knowledge link alone establishes neither an execution route nor a business relationship.

Definitions live at `applications/<hauptprozess>/<teilprozess>/<arbeitsschritt>/CONTEXT.md`. Run files live at `vorgaenge/<vorgang>/<arbeitsschritt>/<versuch>/input/` or `output/`; attempts start at `001`. Reference the actual file and revision carrying a claim, not just its run folder. Use the [run template](templates/vorgang.md).

Generate Core files from existing [templates](templates/) through `impacts template <kind>`. Preserve field names, types and ID prefixes; domain details belong in the body. Without template or validator access, provide an explicitly unvalidated sketch. Before adoption, run `impacts validate` on the resulting tree and correct failures. A model's assertion of validity cannot replace execution.

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

`pruefung` names the observable criterion. The body references the actual checker or accountable person and failure route. The existing declared output or bound upstream input carries **input/rule/output revision, checked condition and scope, observed result, remaining gap and use consequence**. The harness executes the check or validates an applicable result from its trusted execution path; model-written success text is insufficient. A failed, missing, stale or inapplicable required check blocks the transition/effect that requires it to pass. A declared failure route can carry that finding into recovery or a negative end; otherwise retain the appropriate wait. Independent permitted work continues. Check output and action authority remain separate.

The Core does not interpret this Markdown convention. Implement only checks needed by the application, at its existing boundaries; no universal ontology engine is required. A bound snapshot supports reproducibility. An external write also needs the declared current-state/conflict check at the action boundary, as specified in [record writeback](capabilities.md#rückübertragung-in-geschäftsrecords).

## Examples and learning

The [linked-data example](impacts-architect/references/datenbezug.md#prüfbare-fragen-und-grenzen) separates agreed quantities from delivery and device-specific service coverage. The [company walkthrough](impacts-architect/references/datenbezug.md#vom-katalog-über-die-pipeline-zum-ausgefüllten-angebot) connects products, services, independent processes and a reusable offer blank with separate runs. All supplied example values remain synthetic; proposed checks, acceptance and delivery stay explicitly unexecuted or unevidenced unless a real test supplies their narrowly scoped evidence.

A run records observations and correction proposals. [Reviewed correction](impacts-method.md#reviewed-correction) exercise the counterexample, a related new question and affected uses before a new definition revision. Earlier runs retain their definitions. Reuse meaning, access and tests within their premises; bind sources, language and authority for the destination. Better answers or lower token cost require measured results, not additional labels.
