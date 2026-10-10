# Capability contract

A Capability is an optional reusable operation inside a workstep. Its domain contract, implementation and checks live together outside the Application tree. This file owns Capability authority, source binding and handoffs. [Meaning and valid inference](ontology.md#meaning-and-valid-inference), [evidence and obligations](ontology.md#evidence-and-obligations), and [enforcement and completion](ontology.md#enforcement-and-completion) stay in the ontology instruction; the [language contract](language.md#enforce-at-use-boundaries) owns customer-readable presentation.

## Responsibilities

| Concept | Responsibility |
|---|---|
| Capability definition | Reusable operation, parameters, rule and technical use conditions |
| Workstep | Local call, declared inputs/outputs, intended use, check and route |
| Harness | Execute the bound operation, collect actual evidence and enforce prerequisites; configured software, an agent session or a person fills this role and gains no authority from it |
| Source origin | Actual local file or external reference read by this run |
| Snapshot | Bytes actually used in the run |
| Data control | Procedure required for an intended use |
| Control evidence | Evidence of the control performed in this run |
| `pruefung` | Observable evaluation of the workstep output |
| Technical use condition | Condition under which an operation's result is applicable |
| Use restriction | Permitted business purpose of the output |

Verified, current, checked and authorized for use are distinct claims.

The configured harness declares the run-history retention and checking needed for the intended traceability claim at its existing setup home. It preserves bound attempts and completed evidence through that mechanism, subject to applicable access and retention rules. Git can retain transitions when compatible with those rules; it is not a requirement to commit personal run inputs. Current Core validation does not compare independently retained earlier run states, detect coordinated rewrites or authenticate decisions. A required history claim needs its configured evidence and actual check; otherwise it remains unproven.

<a id="wann-extrahieren"></a>
## When to extract

Every bound calculation references its sanctioned rule. Give processing its own Capability home only when at least one applies:

- Several worksteps or Applications need the same operation.
- It has an independent deterministic core.
- It has independent source, freshness or checking rules.
- It needs versioning independently of the workstep.

Otherwise keep it in the workstep. Use `capabilities/<slug>/` in the domain repository or workspace, outside Core and the Application.

<a id="rechen-capability"></a>
## Calculation Capability

Keep a compact revision-bound contract: operation/purpose; parameter shape with units, granularity and time; sanctioned method/formula; failure and blocking cases including data requirements per use; deterministic checker; visible evidence format; fixtures; sensitivity cases only where result tolerance matters.

Definition, formula, checker, evidence format and fixtures share one Capability revision. A Git tree OID binds files, not interpreter/library environments. State an environment as a technical use condition when it affects results.

<a id="capability-aufruf"></a>
## Capability call

The workstep binds its local call, without repeating the domain contract. These labels are stable parser vocabulary across languages:

```markdown
- Aufruf-ID: `liefertermin-1`
- Capability-Pfad: `capabilities/liefertermin/CONTEXT.md`
- Capability-Revision: `git-tree:<oid>`
- Operation: `liefertermin-berechnen`
```

For one call, its ID may derive as `<arbeitsschritt-slug>-1`; multiple calls need explicit IDs. The [cold walk](../06_evaluations/cold-walk/CONTEXT.md) reads this block and requires the derived value to be written before binding the revision. It supports one call in the example step; general multiple-call execution is not established.

Authority is the tuple of call ID, resolvable path, tree OID and operation in the bound Application. Before the run, the harness binds a reachable workspace revision, resolves the Capability's parent directory there and requires the same tree OID. It executes that tree and writes the workspace revision and tuple into the ordinary result evidence. The Capability does not attest its own origin.

The OID establishes identity, not trustworthiness. A production harness executes only domain-approved revisions. Isolation, permissions, secrets and runtime environment remain outside Core.

```text
Capability call -> Visible output -> pruefung -> Route
```

## Data Governance

### Source descriptions

Describe needed sources in their existing domain/source homes, including ordinary files without a selected Application or live connection. A documented source/interface, acquired data, verified access and permission for the intended use are separate findings; apply [ontology evidence and obligations](ontology.md#evidence-and-obligations).

For each relevant attribute/domain and effective period, identify its authoritative factual source, the responsible decision-maker for meaning and allowed changes, and the duties of its maintainer and data provider. One person may perform several duties; unknown actual owners stay `open`. Within existing descriptions and without new record types, distinguish the role of business data (reference codes, master data that transactions refer to, transaction or event records) from its origin: captured at the source, copied as an export or replica, derived by a rule, or set by a decision. Bounded observations and derived KPI values remain distinct from both. A transaction record does not by itself prove the real event. For data-derived metric inputs, trace reports and exports to the collection/fields that capture the relevant event or attribute; constants, decided parameters and case observations retain their own rule, authority or evidence origin.

Use [Tables and relationships](#tables-and-relationships) and [ontology inference](ontology.md#meaning-and-valid-inference) to describe units, row meaning/grain, selection/validity time, identity and namespace, relationships and source-field semantics needed for the intended result. Document sources need the same relevant distinctions without becoming tables.

Record the known source form: file, export, report, manual input or API. The form establishes neither the origin nor how a reader reaches the source. Record the access route (for example file, export, report, manual input, API, CLI or MCP server), whether it can write, and which of the separate findings above it has established; [data handling](impacts-architect/references/datenumgang.md#access-routes) shows the distinctions per step. Retain provenance and, for documentation actually read, its URL/path, version/date and read date; describe possible endpoints, schemas, authentication and access conditions only when known. Retrieve locally first; discover sources for explicit gaps. Unknown details remain questions, not fabricated interfaces.

An interface being publicly documented does not by itself establish customer-data access, current values, factual authority or permission for the intended use; retain applicable access/use terms when known. A source description requires no API probe, credentials or live integration. Reuse existing valid source/identity mappings and their fact/domain homes; clarify only mappings missing or conflicting for the intended use. Source equivalence or selection among competing masters needs evidence of their applicable scope/mapping. Preserve unresolved choices with their responsible decision-maker and unknown ownership at their homes, restricting only dependent uses.

### Source inputs for Core Applications

For selected Core Applications, the Application specifies expected origin, acquisition and minimum control for each source input, with or without a Capability call. The domain home owns the reusable source mapping. The workstep supplies the local selection: identity, purpose, time, needed fields/relationships, configured reader or responsible provider, and destination input. A tool name or URL alone is not an acquisition contract. Use the existing body and these stable parser labels:

```markdown
### Quellenanforderung

- Quell-Eingabe: `input/rezeptur.md`
- Herkunft: `freigegebene Rezeptur`
- Ursprung: `grundlagen/rezeptur.md`
- Stand: `git:<commit>`
- Erforderliche Kontrolle: `revisionsgebunden materialisieren`
```

Repeat the block for each stable source input, referring to its acquisition in Processing and marking that acquisition as preceding the designated attempt's opening. A processing-body declaration describes how to acquire the input; it does not authorize changing bound inputs during the attempt. Inputs from preceding steps in the same run instead use the producer's [handoff mapping](#sichtbare-ausgabe-und-übergabe). Another run's output is a declared source input: retain the producing workspace/source identity, run, selected attempt, output path and applicable revision/evidence, and acquire its bytes before the consuming attempt opens. A same-named run in another workspace is not the same origin. This binding supplies neither a cross-Application route nor missing acceptance, authority or fulfillment evidence. The harness resolves the declaration from the bound Application; implementation support for the selected reader must exist before execution. Missing access leaves a specific blocker, not an invented snapshot or competing source of truth.

Inputs carry claim evidence, source/origin, snapshot, revision and required/actual control. Capability results retain assumptions and technical conditions; workstep outputs retain business-use restrictions; routes record actual process progression.

Apply [evidence labels](impacts-architect/references/zuschnitt.md#evidence) per claim. A required manual check before commitment differs from evidence that a named person actually checked it. In a real run, that person supplies their own attribution.

Control strength follows volatility, repetition, harm, result tolerance, reproducibility and existing infrastructure. Revision binding, manual confirmation and automatic monitoring are practices, not maturity levels. Small businesses may use files and documented confirmations.

<a id="tabellen-und-beziehungen"></a>
### Tables and relationships

For needed tables, the domain description names row meaning, unique key, source/access and required relationships: source columns, target collection, target key and business meaning. Composite keys include every decision-relevant component, such as tenant or contract version. File path, business identity and source revision differ. A source row number or physical row position locates a record in that source; it is business identity only when a maintained source definition establishes that role. Existing schemas stay at their home; local structured metadata describes only missing meaning. Document-based facts have the same meaning/evidence obligations without requiring a table.

A document link reaches this description; actual rows join through keys, not similar names or shared folders. Automated processing executes needed type, uniqueness, reference and multiplicity checks. A matching foreign key alone establishes neither validity nor authority. No match requires sufficient coverage before claiming absence; multiple valid matches must not collapse to the first.

Selection names starting identity, purpose, time and required relationships/fields. The configured reader supplies the bounded excerpt with reproducible selection and provenance. Reuse source/relationship rules across calls. Metadata requires a reader and checker. Core implements neither table joins nor a general domain schema; see the [linked-data read path](impacts-architect/references/datenbezug.md#the-question-determines-the-read-path) and [offer/agreement evidence path](impacts-architect/references/datenbezug.md#from-catalog-through-pipeline-to-a-filled-offer).

<a id="bedeutung-und-zulässige-schlüsse"></a>
### Meaning and inference

Apply the appropriate [Author or change](ontology.md#author-or-change) or [Use](ontology.md#use) branch of the ontology. Its [inference rules](ontology.md#meaning-and-valid-inference) and [evidence/obligation rules](ontology.md#evidence-and-obligations) are authoritative.

<a id="fachliche-durchsetzung"></a>
### Domain enforcement

Check scope, evidence and completion follow [Enforcement and completion](ontology.md#enforcement-and-completion). The workstep and executing harness enforce those conditions; Core validation does not replace them.

<a id="snapshot-und-herkunftsnachweis"></a>
## Snapshot and provenance

1. **Declare paths before Application binding.** The workstep's `eingaben` names the source/projection file and its provenance file, normally separate `*-herkunft.md`. These declarations belong to the committed Application tree the run binds; adding one later changes that definition. Actual bytes must be acquired before the designated attempt opens.
2. **Acquire the attempt's data.** Resolve the declared source, permitted read operation, required source state and selection. **Versioned source:** read the bound immutable revision, such as `git show <commit>:<path>`. **Mutable source:** capture the actual returned response/excerpt and read time. Reading time alone proves neither freshness nor source completeness.
3. **Materialize the declared inputs.** Keep the smallest sufficient source or projection and its provenance at the declared paths. Provenance identifies actual origin, source revision or its absence, read time for mutable sources, selection/extraction, resulting Content-Digest and required/actual controls. A projection identifies source path/revision and digest and retains enough source evidence to inspect its derivation. Nondeterministic extraction records its human or Capability-specific confirmation.
4. **Check and open the attempt.** Verify declared inputs and the controls required for opening, then install the designated attempt files under `input/`, hash the declared surface and open the entry as one logical transition. Stage outside reached attempt folders; on failure, remove unbound staging and leave the prior `laufpfad` unchanged. This is not a claim of filesystem atomicity. A placeholder does not satisfy a missing prerequisite; evidence of a gap can support only the declared diagnostic or acquisition job.

Reading for design or navigation locates the applicable authority; it does not make every read file an execution input. Every operative external instruction actually followed by Processing or Check, including protocol instructions, must be retained in the bound body or materialized with provenance as a declared input. No protocol-path exemption applies.

The Application tree binds its own instructions only. Referenced rules, prompt fragments, document blanks and needed source meaning outside that tree must also be materialized as declared inputs; a pinned Capability follows its separate call contract. Bind no secret values in these files: configured access remains with the harness. New source evidence acquired after opening follows [Work from prerequisites](impacts-method.md#work-from-prerequisites), preserving the existing input set.

A declared shared provenance file may replace per-file provenance only under a configured reader/checker that supports its syntax. It has one uniquely keyed entry for each local input and retains the same applicable origin, source state, selection, digest, acquisition/provider/time evidence and required/actual controls. Missing entries, duplicate keys or contradictory recognized labels fail that local check. The [offer walk](../06_evaluations/offer-walk/CONTEXT.md) supplies the shared-provenance example in its fixture-local `herkunft.json`; its reader rejects duplicate JSON keys. Existing per-file formats remain valid. Changing declared provenance paths creates a new Application revision and new bound attempts.

`Content-Digest` is lowercase hexadecimal SHA-256 of raw file bytes, not the aggregate surface hash. The aggregate surface hash, which `impacts hash` prints and `eingabe_hash` and `ausgabe_hash` record, is computed this way: hash each regular file under the declared paths with SHA-256 over its raw bytes; sort the files by the UTF-8 bytes of their resolved attempt-relative POSIX paths, without Unicode normalization; encode the list of `{"path", "sha256"}` records, each `sha256` the file's lowercase hex digest without prefix, as UTF-8 JSON with keys sorted, non-ASCII characters unescaped and no space after `,` or `:`; append one LF; hash that payload with SHA-256 and prefix its lowercase hex with `sha256:`. Overlapping declarations include each path once. Binary content and zero-byte regular files are hashable. A symlinked surface fails as `structure.symlink`; every other unbindable surface (missing, containing no regular file, escaping, unreadable, a path not encodable as UTF-8, or non-regular) fails as `hash.mismatch`, as does a differing digest. File content need not be UTF-8.

<a id="provenance-file-example"></a>
### Copyable stable-source provenance file

For the default per-file form, declare each stable source input's actual input path, for example `input/rezeptur.md` or `input/messwerte.csv`, and its separate `input/<name>-herkunft.md` together under `eingaben`. Use the authoritative [stable-source provenance template](templates/herkunft.md), printed by `impacts template herkunft`; use `impacts template herkunft --language de` for German. Replace all nine field values with the actual evidence.

`Source state` describes the source revision or business state; `Acquired at` records when this local copy was obtained. They are not substitutes for one another. The digest covers the exact local input bytes, not an upstream file's claimed digest or the aggregate hash surface. Keep required control separate from evidence of actual control. If source state or actual control is unknown, leave it explicitly open. This is guidance for ordinary Markdown evidence, not a Core schema or a contract enforced by the general validator.

<a id="sichtbare-ausgabe-und-übergabe"></a>
## Visible output and handoff

Capability evidence is an ordinary `output/` file in the Capability's own format. It shows bound rule, used inputs, result, executed checks, assumptions and technical use conditions. A parameter table or equivalent block list is sufficient; no receipt schema is introduced.

A local handoff has two records: the Application's expected producer-output → consumer-input mapping per step route, declared once at the producer; and the run's byte-identical consumer file with declared provenance, attempt-qualified origin relative to the run, and matching Content-Digest. A later consumer in the same run is permitted only under a declared, supported handoff convention: before consumer opening, the harness selects an actually reached, completed producer attempt under that convention and checks its output and provenance. The selection must resolve rework ambiguity and any required intervening decision evidence. A mapping supplies data; it creates no route, bypasses no gate and never starts a consumer early. Already bound consumer inputs remain unchanged.

The cold walk reads this stable sentence syntax:

```markdown
Bei Route `bestanden`: `output/pruefbericht.md -> arbeitsschritt:entscheiden/input/pruefbericht.md`.
```

The mapping sentence is a parser-consumed label under [Preserve meaning](language.md#preserve-meaning): it keeps this exact form in every working language, German words included, while the surrounding instruction is translated. A workspace that declares a different sentence form supplies a harness that reads that form; translating the label breaks the cold walk's mapping check.

The output path is relative to the producer attempt; `arbeitsschritt:entscheiden` is a target ID, not a folder. The [cold walk](../06_evaluations/cold-walk/CONTEXT.md) supports exactly one mapping to the selected immediate successor and terminal human-gate routes. Its block/sentence syntax is a local reading convention, not Core schema. Multiple mappings, later consumers and gate routes to worksteps require a harness that implements those declared transitions.

Producer `ausgabe_hash` and consumer `eingabe_hash` bind different surfaces. Relative paths participate, so hashes are not compared and do not form a hash chain. A local harness verifies origin and digest claims where the use requires it.

<a id="rückübertragung-in-geschäftsrecords"></a>
## Record writeback

Writing a run result to a continuing record or source system is a separately permitted effect of the job. The body names target, change scope, required authority and check. The harness or authorized person uses the configured access. Description alone grants no permission. For an authoritative attribute update, use the leading system and scope declared by its source mapping; a permitted copy or export does not create another fact authority. Apply declared freshness/conflict checks before writing. Confirm the effect through the declared readback or authoritative operation confirmation, retaining the target record/version and confirmed or unconfirmed outcome in the existing output evidence. A request or draft does not establish writeback. Resolve an uncertain target state before retrying; use the declared update or idempotency mechanism where repetition could duplicate an effect. A business key alone guarantees no repeat-safe write. Bound definitions and historical run bytes remain unchanged. These rules also apply without an extracted Capability; Core provides no write service.

<a id="signale-und-human-gate"></a>
## Signals and human gates

`hypothesis` identifies an expected effect and its validation question. `open` retains a focused question without an invented replacement. A warning needs a use restriction, check, question or blocking consequence.

Before opening `gate: human` or preparing a declared action at a `sacred` customer touchpoint for its responsible human, the executing harness checks declared inputs, required control evidence and the body’s permitted effect and actor. A failed prerequisite leaves the previous run state unchanged. Touchpoint classification grants no execution authority. Changing a `sacred` classification separately requires the applicable human review of the Application; a technical success cannot supply it. After human work, `pruefung` evaluates the gate output. The responsible human supplies the actual `freigegeben`/`abgelehnt` decision and its attribution. The configured harness, including an agent session, may mechanically record an evidenced decision, including one given by voice or another message, for the identified object and revision, preserving its decision, identity and decision time without inventing missing values. Establish its origin from the applicable decision authority through the configured trusted execution path; a file merely claiming `human:<id>` is insufficient. Preserve the source evidence in the existing run evidence. The actual source and evidenced request or channel context must support the decision, object, revision, holder and decision time; the human need not dictate machine fields. Receipt or transcription time cannot substitute for decision time. Recording or formatting creates no authority and authenticates no person. Missing, ambiguous or contradictory decision evidence keeps the dependent transition unresolved; corrections preserve bound and completed history under the existing revision rules.

One packet or interaction may yield separate decisions at declared authority boundaries. Preserve each holder's right, scope and source evidence; record an applicable already received decision at its declared transition without asking again solely for bookkeeping. Recheck its coverage when the object, revision or relevant premises change. Each gate entry retains its responsible human's attribution; a shared interaction creates neither a joint `by` nor a concurrent Laufpfad. Processing and newly acquired evidence follow [Work from prerequisites](impacts-method.md#work-from-prerequisites).

Core validation neither enforces that preflight nor authenticates a person. A synthetic walk establishes only that opening writes no route/approval and completion consumes an external decision fixture.

<a id="retention-and-deletion"></a>
## Retention and deletion at the harness boundary

For each record home, its responsible operator declares the intended purpose, applicable legal basis, retention period and exceptions from the responsible authority's source. This declaration identifies the permitted scope; it does not itself establish that the basis or authority is valid. Keep an unknown basis, period, exception or owner open and restrict only the dependent deletion.

Before deletion, inventory the known source records and their known copies, projections, caches, search indexes, exports and backups, including affected run attempts and known Git histories, clones and remotes. Permission for one target does not authorize additional copies or remote history rewriting. State the inventory's sources, scope and search limits. Unknown consumers remain unknown; do not claim complete erasure or absence of copies beyond checked coverage.

Bind a deletion preview to the exact record identities and current source revisions or states. Show the stated purpose, basis, retention rule, exceptions, affected locations and expected effect. Obtain the required human approval for that scoped preview. Immediately before the effect, recheck that source state, approval and preview still match. Prevent a concurrent writer from changing the target between that recheck and deletion, using an effective lock, an exclusive maintenance window or equivalent control. If the harness cannot establish this race protection, do not execute the deletion.

Delete only the exact authorized targets and declared derivatives. Do not widen a path, query or identifier match at execution time. If part of the operation fails, stop dependent deletion, report confirmed and unconfirmed targets separately through a minimal receipt, and leave completion open. Do not recreate already deleted bytes merely to make the operation appear atomic.

After deletion, recheck each known copy and index in scope. Check backup and restore paths so deleted material is not silently reintroduced; where a restore is required, apply the same deletion control before restored data becomes available. Retain the bounded search method and unresolved copies as explicit gaps.

The receipt records only what is needed to show the authorized scope, decision reference, operator or authenticated system, time, checked inventory coverage and actual outcome, including partial failure and open gaps. It contains neither deleted content nor a content hash or other durable fingerprint that can be linked back to that content. Its record reference must be no more identifying than the record home requires.

Authorized deletion of bytes bound to an existing Run leaves `hash.mismatch`, indistinguishable from tampering to Core. Retain that mismatch, link the minimal non-content receipt and authorization from the existing run body, and restrict affected historical uses. Never rehash missing or replaced bound bytes to make the run pass. This procedure adds no Core deletion state; pseudonymization does not itself establish an exemption or deletion permission.

## Transport

Transport an Application alone if it has no Capability calls. Otherwise materialize each needed `capabilities/<slug>/` from the same source repository revision at the same relative path. Before the first run, `git rev-parse <workspace-revision>:capabilities/<slug>` must equal the bound tree OID. Missing or mismatching paths prevent execution. No package manifest or Core resolver is introduced.

Transporting an Application preserves its definition bytes; destination source applicability and authority follow [Data Governance](#data-governance), reusing valid local mappings and permissions while unresolved questions go to their responsible decision-maker.
Claim destination execution only after a destination `vorgang` has actually reached the stated test endpoint with its applicable prerequisites and checks; copying or checking links alone does not establish this, and independent permitted preparation remains useful while dependent execution is restricted.
Apply [Reviewed correction](impacts-method.md#reviewed-correction) at the changed home's revision boundary: changed Application definitions require a new Application binding, while changed external mappings stay at their source home and require the corresponding source binding and affected checks, preserving earlier bound inputs.

## Limits

The optional [computation example](../06_evaluations/computation-walk/CONTEXT.md) demonstrates parameters, partial results, blockers and scenario comparison. Domain formulas remain at their existing home. It defines no universal computation profile, registry, database, extractor, required API, monitoring service or automatic approval.
