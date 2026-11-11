# Binding and execution

Scope: selected Core Hauptprozesse and their Vorgänge. Owns: the committed tree a Vorgang binds, source inputs and provenance, file references, handoff, the execution state of a Vorgang and its attempts including recorded human decisions, writeback, retention and deletion at the harness boundary, destination execution, with or without a Capability, and the validation issue codes. Reader: harness; author for source requirements. Does not own: when a gate, wait or loop is declared, see [Arbeitsschritt](impacts-architect/references/zuschnitt.md#arbeitsschritt); reusable operations, see [Capability contract](capabilities.md).

## Hauptprozess tree rules

```text
hauptprozesse/<hauptprozess>/
├── CONTEXT.md                  # type: hauptprozess    impacts template hauptprozess
└── <teilprozess>/
    ├── CONTEXT.md              # type: teilprozess     impacts template teilprozess
    └── <NN-><arbeitsschritt>/
        └── CONTEXT.md          # type: arbeitsschritt  impacts template arbeitsschritt

vorgaenge/<vorgang>/
├── CONTEXT.md                  # type: vorgang         impacts template vorgang
├── _quellen/                   # committed captures and provenance
└── <arbeitsschritt>/<nnn>/
    └── output/
```


- A frontmatter block-scalar value must not contain a bare `---` line.
- Placeholders and `routen` keys are slugs matching `[a-z0-9]+(?:-[a-z0-9]+)*`. Each definition ID is `<type>:<folder name without an optional prefix>`. A display prefix is exactly two ASCII digits followed by `-` (`NN-`); siblings may share its number. Every other numeric first segment belongs to the slug, so `2024-video`, `3-video` and `007-video` remain valid slugs and IDs. A slug cannot begin with a two-digit segment: in `24-x`, `24-` is a display prefix and the ID must omit it (`<type>:x`). Equal names after removing the prefix are duplicate IDs (`structure.duplicate_id`). Prefixes change no route or `laufpfad` reference.
- A Hauptprozess contains only `CONTEXT.md` files and folders. Each Hauptprozess has at least one Teilprozess, each Teilprozess at least one Arbeitsschritt; Arbeitsschritte have no subfolders.
- Present collections must contain valid children; add no placeholder files.
- Arbeitsschritt IDs are unique across the Hauptprozess. `einstieg_ref` and every Arbeitsschritt route target resolve inside the same Hauptprozess; every Arbeitsschritt is reachable from the entry. Each Arbeitsschritt has at least one route. Routes target `arbeitsschritt:<slug>` or `end:<slug>`; every Arbeitsschritt can reach an end, so every loop has an exit.
- For human gates, apply [Arbeitsschritt](impacts-architect/references/zuschnitt.md#arbeitsschritt); for waiting attempts, apply [Waits](#waits).
- `<nnn>` has three digits; attempts start at `nummer: 1`, which means `001`. Only Arbeitsschritte and attempts reached by `laufpfad` have folders in the Vorgang.

Use the recorded protocol's `impacts-method.md`, “Compose an Arbeitsschritt”, and the Arbeitsschritt template to fill the Arbeitsschritt contract.

## History retention

At its existing setup home, the configured harness declares retention and checking of Vorgang history for the intended traceability claim. That mechanism preserves bound attempts and completed evidence under applicable access and retention rules. Git can retain transitions subject to [Retention and deletion](#retention-and-deletion). Apply the [Core boundary](ontology.md#enforcement-and-completion). A required history claim remains unproven without its configured evidence and actual check.

## Source inputs for Core Hauptprozesse

The Hauptprozess specifies expected origin, acquisition and minimum control for each source input, with or without a Capability call. The domain home owns reusable source mappings; the Arbeitsschritt supplies local selection: identity, purpose, time, needed fields/relationships, configured reader or responsible provider, and destination input. A tool name or URL alone is not an acquisition contract. Use the existing body and these stable parser labels:

```markdown
### Quellenanforderung

- Quell-Eingabe: `grundlagen/rezeptur.md`
- Datenart: `Foundations`
- Herkunft: `freigegebene Rezeptur`
- Ursprung: `grundlagen/rezeptur.md`
- Stand: `git:<commit>`
- Erforderliche Kontrolle: `revisionsgebunden referenzieren`
```

Among a step's inputs, only foundations instruct; records, received sources and work are material to process. A blank or style prescribed by a received source governs form only.

`Datenart` names the input's [data kind](impacts-architect/references/formwahl.md#data-kinds), using that table's exact English value; handoff inputs are work by definition and need no label.

The Quellenanforderung keeps its stable labels. `Ursprung` names the actual file or external source to be read, with a link to [its existing source description](impacts-architect/references/datenumgang.md#source-descriptions) and use condition. The description locates meaning and selection; it does not replace acquisition origin in provenance. `Stand` carries the required source state, not the read time.

Repeat the block for each stable source input, referring to its acquisition in Processing and marking that acquisition as preceding the designated attempt's opening. A processing-body declaration describes how to acquire the input; it does not authorize changing bound inputs during the attempt. Inputs from preceding Arbeitsschritte in the same Vorgang instead use the producer's [handoff mapping](#visible-output-and-handoff). Another Vorgang's output is a declared source input: retain the producing workspace/source identity, Vorgang, selected attempt, output path and applicable revision/evidence, and acquire its bytes before the consuming attempt opens. A same-named Vorgang in another workspace is not the same origin. Separate Vorgänge exchange results through these declared inputs and checked handoffs; this establishes neither scheduling of Vorgänge nor deadlock freedom. This binding supplies neither a cross-Hauptprozess route nor missing acceptance, authority or fulfillment evidence. The harness resolves the bound Hauptprozess's declaration; execution requires implementation support for the selected reader. Missing access leaves a specific blocker, not an invented snapshot or competing source of truth.

Inputs carry claim evidence, source/origin, snapshot, revision and required/actual control. Capability results retain assumptions and technical conditions; Arbeitsschritt outputs retain business-use restrictions; routes record actual process progression.

When a result selects or recommends subsequent work, apply [Decision results and Auslöser](#decision-results-and-auslöser) for the receiving obligation and its readiness. Source binding alone supplies no Auslöser rule or scheduling rule.

Apply [evidence labels](ontology.md#evidence-and-obligations) per claim. A required manual check before commitment differs from evidence of its execution by a named person. In a real Vorgang, that person supplies their own attribution.

Control strength follows volatility, repetition, harm, result tolerance, reproducibility and existing infrastructure. Revision binding, manual confirmation and automatic monitoring are practices, not maturity levels. Small businesses may use files and documented confirmations.

## Snapshot and provenance

A snapshot is the bytes a Vorgang actually used.

The workspace root router pins the release tag for new work in `protocol`. Before moving the pin, ask the [cut questions](impacts-architect/references/zuschnitt.md#hauptprozess) of every Hauptprozess in the workspace. If its major.minor differs from the validator, the workspace and everything under it are not judged; the output states `workspace not judged under <validator release>: pinned <value>` and exits 0. A missing workspace pin produces one `protocol pin missing; add protocol: <release> to the frontmatter` issue.
Each new Vorgang records that pin in its own `protocol` field. A Vorgang release newer in major.minor than the workspace pin produces `binding.revision`, even when that Vorgang is otherwise not judged.
Core does not judge a Vorgang whose recorded release differs in major or minor from the validator, or whose missing `protocol` accompanies `eingabe_hash` in any `laufpfad` item; a missing version without that marker produces `protocol pin missing; add protocol: <release> to the frontmatter`.

1. **Declare inputs before Hauptprozess binding.** `eingaben` names the required sources or projections and provenance. These declarations belong to the committed definition. Acquire the actual bytes before opening the attempt.
2. **Capture mutable or external sources.** Store only captures of mutable or external sources (such as API responses or exports) in the flat `vorgaenge/<vorgang>/_quellen/`, with `<name>-herkunft.md` beside each capture and no step or attempt subfolders. Commit both before opening. An underscore-prefixed child of a Vorgang other than `_quellen` is rejected; `quellen` is an ordinary Arbeitsschritt slug. Stable sources stay at their `grundlagen/`, `records/` or source-system home. A [received source](impacts-architect/references/formwahl.md#data-kinds) read from a mailbox or another source system is mutable until stored at its record home; there, bind its exact version at that home, rather than copying it to `_quellen/`. Repository sources use a `git-commit` revision; sources outside Git use the external-store reference below. Deletion follows [Retention and deletion](#retention-and-deletion). Provenance retains actual origin, source state or its absence, read time, selection/extraction, Content-Digest and required/actual controls. A projection identifies the exact source path, revision and digest and retains evidence of its derivation. A projection of a received source names the exact version it read; a new version gets a new projection, and the old one stays unchanged. Correct a wrong or incomplete copy of the same received version by a new revision with its reason; preserve the issuer's version identity. Record required human or Capability-specific confirmation for nondeterministic extraction. Reading time proves neither freshness nor completeness.
3. **Record file references.** Each `versuch` records `gelesen`, a list of the files actually read. When the bound Arbeitsschritt declares at least one `eingaben` slot, `gelesen` requires at least one reference (`minItems: 1`). Every attempt covers every declared slot when it opens, including as `aktiv` or `wartend`, and retains that coverage through completion. A reference names its slot with `eingabe`; omit it only when `pfad` equals the declared path or lies under its declared directory. Several files may cover one slot. Unknown explicit slots and uncovered slots produce `binding.reference_missing`. A valid result shows that each declared slot has a recorded, reachable, digest-bound reference; the step's own check judges source applicability under the [Core boundary](ontology.md#enforcement-and-completion). Use one of these shapes:
   - Predecessor output: `pfad`, a workspace-relative file path under an attempt's `output/`, and `sha256`. Core reads working-tree bytes and requires a preceding completed producer. The producer may belong to another Vorgang, including an old one that Core does not judge.
   - Versioned source: `pfad`, `revision: git-commit:<oid>` and `sha256`. Core reads the blob at that commit and requires the commit to be reachable under the same history rule as Hauptprozess trees below. Later edits or removal from the working tree leave the bound bytes unchanged. Captures in `_quellen/` use this shape.
   - External store (for example, personal data): `ablage`, `schluessel` and `sha256`. `ablage` names a store declared in the workspace root router; an undeclared store is rejected; a file in the working tree or in Git is never an `ablage` reference. Core checks shape and rejects a relative `schluessel` resolving to an existing file in the working tree; apply the [Core boundary](ontology.md#enforcement-and-completion). The harness checks the store's bytes and digest under its access and retention rules.
4. **Check and open.** Verify source references, provenance and required controls, then open the attempt under [Execution](#execution) as one logical transition; completed attempts require their output files. The attempt holds only `output/`; `input/` is rejected. Failed preparation opens no attempt. Stage outside reached attempt folders; on failure, remove unbound staging and leave the prior `laufpfad` unchanged. This does not claim filesystem atomicity. A gap supports only the declared diagnostic or acquisition job.

A file reference uses `sha256:<64 lowercase hex>`, the SHA-256 of raw file bytes. `geschrieben` lists every output file of a completed attempt with its workspace-relative `pfad` and `sha256`. Core checks each against the working tree and checks that the inventory is complete. `impacts hash <root> <file-or-directory>...` prints these per-file references relative to the supplied root; use the workspace root for recorded references. Overlapping declarations include each path once. It emits no aggregate digest.

Reading for design or navigation locates the applicable authority; it does not make every read file an execution input. The Vorgang's recorded protocol release binds its protocol execution rules. Retain every other operative external instruction followed by Processing or Check in the bound Hauptprozess body or reference it with provenance as a declared input.

The Hauptprozess tree binds its own instructions only. Other referenced rules, prompt fragments, document blanks and needed source meaning outside that tree must also be referenced as declared inputs; a pinned Capability follows its separate call contract. Bind no secret values in these files: configured access remains with the harness. New source evidence acquired after opening follows [Work from prerequisites](#work-from-prerequisites), preserving the existing input set.

Bind every operation a step names by revision, [Capability](capabilities.md#capability-call) or tool alike.

A v0.4 Vorgang binds only a tree found under `hauptprozesse/` in reachable history. A tree found only under `analyse/` or the retired collection is not bindable. A byte-identical move into `hauptprozesse/` keeps its OID and becomes bindable once reachable there.

Vorgänge bind committed Hauptprozess trees reachable from branch, tag or remote-tracking history or the current worktree’s resolvable commit at `HEAD`, including detached HEAD. Stash-only and auxiliary-ref-only trees are excluded; shallow history covers only reachable commits within its boundary.

A declared shared provenance file may replace per-file provenance only under a configured reader/checker that supports its syntax. It has one uniquely keyed entry for each local input and retains the same applicable origin, source state, selection, digest, acquisition/provider/time evidence and required/actual controls. Missing entries, duplicate keys or contradictory recognized labels fail that local check. The [offer walk](../06_evaluations/offer-walk/CONTEXT.md) supplies the shared-provenance example in its fixture-local `herkunft.json`; its reader rejects duplicate JSON keys. Existing per-file formats remain valid. Changing declared provenance paths creates a new Hauptprozess revision and new bound attempts.

Missing or unreadable referenced bytes produce `binding.reference_missing`; a differing digest produces `binding.reference_digest`. Symlinks produce `structure.symlink`. Binary and zero-byte regular files are supported. The caller keeps bytes and directory entries stable while enumerating and reading through an actual stable-read control appropriate to the harness. Core does not synchronize writers or prove a concurrent filesystem transaction. Without an actual stable-read control, a digest does not establish that a concurrently changing tree stayed confined or represented one consistent state.

### Provenance file example

For the default per-file form, declare each stable source input's actual input path, for example `grundlagen/rezeptur.md` or `records/messwerte.csv`, and its separate `<name>-herkunft.md` at the same home together under `eingaben`. Use the authoritative [stable-source provenance template](templates/herkunft.md), printed by `impacts template herkunft`; use `impacts template herkunft --language de` for German. Replace all nine field values with the actual evidence.

`Source state` describes the source revision or business state; `Acquired at` records when this local copy was obtained. They are not substitutes for one another. The digest covers the exact local input bytes, not an upstream file's claimed digest or another file. Keep required control separate from evidence of actual control. If source state or actual control is unknown, leave it explicitly open. This is guidance for ordinary Markdown evidence, not a Core schema or a contract enforced by the general validator.

## Visible output and handoff

A local handoff has two parts: the declared producer-output → consumer-input mapping, and the consumer's `gelesen` reference to the selected producer output with its digest and provenance. No consumer copy is needed. A later consumer in the same Vorgang is permitted only under a declared, supported handoff convention: before consumer opening, the harness selects an actually reached, completed producer attempt under that convention and checks its output and provenance. The selection must resolve rework ambiguity and any required intervening decision evidence. A mapping supplies data; it creates no route, bypasses no gate and never starts a consumer early. Already bound consumer inputs remain unchanged.

Failed-check evidence may be handed off for diagnosis; successful-use restrictions still apply. A Core failure-route handoff needs its own declared producer mapping, just as a success-route handoff does.

A normally routed new attempt may reuse earlier evidence as a declared operation: bind current inputs, explicitly select the earlier output, establish its continued applicability, run the declared check and retain its origin. Reuse does not replay effects or reuse a human approval beyond the [received-decision rule](#signals-and-human-gates).

The cold walk reads this stable sentence syntax:

```markdown
Bei Route `bestanden`: `output/pruefbericht.md -> arbeitsschritt:entscheiden:material/pruefbericht.md`.
```

The mapping sentence is a parser-consumed label under [Preserve meaning](language.md#preserve-meaning): it keeps this exact form in every working language, German words included, while the surrounding instruction is translated. A workspace that declares a different sentence form supplies a harness that reads that form; translating the label breaks the cold walk's mapping check.

The right side uses `arbeitsschritt:<slug>:<slot>`, where `<slot>` exactly names the consumer's declared `eingaben` slot, here `material/pruefbericht.md`. The middle part `<slug>` names no folder in an attempt; the whole token is a label, not an ID. The output path is relative to the producer attempt; `arbeitsschritt:entscheiden` is a target ID, not a folder. The [cold walk](../06_evaluations/cold-walk/CONTEXT.md) supports exactly one mapping to the selected immediate successor and terminal human-gate routes. Its block/sentence syntax is a local reading convention, not Core schema. Multiple mappings, later consumers and gate routes to Arbeitsschritte require a harness that implements those declared transitions.

The consumer references the selected producer's output file and digest. A mapping supplies neither a route nor permission to open a consumer before its producer completes.

## Record writeback

Writing a Vorgang result to a continuing record or source system is a separately permitted effect of the job. The body names target, change scope, required authority and check. The harness or authorized person uses the configured access. For an authoritative attribute update, use the leading system and scope declared by its source mapping; a permitted copy or export does not create another fact authority. Apply declared freshness/conflict checks before writing. Declare the time or interval at which each required condition must hold. For a condition required at the write or throughout a declared operation interval, establish that it holds for that operation or interval through a target condition or other control covering relevant concurrent changes and expiry; otherwise leave the dependent write unresolved. A prior read, private lock or stored intention alone does not establish that coverage. Confirm the effect through the declared readback or authoritative operation confirmation, retaining the target record/version and confirmed or unconfirmed result in the existing output evidence. A request or draft does not establish writeback. Resolve an uncertain target state before retrying; use the declared update or idempotency mechanism where repetition could duplicate an effect. A business key alone guarantees no repeat-safe write. Bound definitions and historical Vorgang bytes remain unchanged. These rules also apply without an extracted Capability, under the [Core boundary](ontology.md#enforcement-and-completion).

**Synthetic example: expected behavior, not an executed result.** An authorized update requires the currently approved price to remain 100 at the write. A worker checks r7/100; another authorized writer approves r8/120 before an unconditional update. The earlier check does not support that effect. A configured target condition can enforce the required price and approval at the write; its coverage and actual result need evidence. An authorized observation append may continue under its own checks where that operation is independent of the price and approval condition. The [record-effect reading cases](../06_evaluations/nontechnical-reconstruction/result-work-coordination.md#supplementary-record-effect-cases) exercise this boundary and its exceptions.

One subject keeps one authoritative record across Hauptprozesse. Each record kind declares its identity rule, stage words and readable shape once at its record-kind home. Use one `CONTEXT.md` per earned instance folder or one table row, with identity, one `Stage:` line or Stage column, links to Vorgänge, commitments and decisions, outcome and deadlines. A stage records the subject's business position; a second execution status or hand-kept progress summary duplicates `laufpfad` and must be removed. The evidenced event that changes a stage writes it in the same permitted writeback. The viewer reads the single Subject link's `Stage:` line, or its anchored table row's Stage column. A table row uses `<a id="<identity>"></a>` in its identity cell. Missing or ambiguous stage text remains `open`. Until a Vorgang opens, a view shows the row's business state and any stage for it; the row has no execution state.

A population row becomes a subject record at the first decision made about it alone. One workspace serves one company; a subject shared by departments lives with the department that owes its first commitment. Other departments reference it. A Fachrepo holds no customer subject records.

## Execution

1. **Open.** For a new Vorgang, create its router from `impacts template vorgang` with `protocol` and `hauptprozess_revision`. Check declared inputs, provenance and controls, then open the attempt as `aktiv` with `nummer` and `gelesen` (an open attempt, `aktiv` or `wartend`, accepts both `geschrieben: []` and absent `geschrieben` and needs no folder while it has no output; its `output/` folder appears with its first output file) under [Snapshot and provenance](#snapshot-and-provenance): at the entry, or at the predecessor's position through `vorgaenger`. Failed preparation opens nothing.
2. **Complete.** Run the declared check. Record every output file in `geschrieben` (`impacts hash <workspace> <output-path>...` supplies the references), the check result's `routen` key as `gewaehlte_route`, and `abgeschlossen`. A failure route grants no successful use. At a human gate add `freigabe` (`by: human:<id>`, `at: "<YYYY-MM-DD>T<hh:mm:ss>+<hh:mm>"`, quoted) under [Signals and human gates](#signals-and-human-gates). Position and status then follow [Vorgang progress](#vorgang-progress).
3. **Wait.** Record `wartend` and its evidenced continuation only under [Waits](#waits), including the next timed check; an unsent request remains `aktiv`.
4. **Stop.** On a protocol break, stop dependent work and record Friction under [Waits](#waits); record an owner's end with `abgebrochen`, `freigabe` and `geschrieben` under [Vorgang progress](#vorgang-progress).

At every transition, the harness sets `status_seit` and commits the Vorgang file so that an attempt's timeline can be rebuilt from that file's Git history. `status_seit` remains optional in the schema, so no check enforces its presence.

Each `laufpfad` item is a `versuch`. Its `nummer` starts at 1 and rises by 1 per Arbeitsschritt without gaps or duplicates, through 999. Folders use three digits, `001` through `999`. An empty `laufpfad` is forbidden.

The first attempt starts at `einstieg_ref`. With optional `vorgaenger: vorgaenge/<slug>/CONTEXT.md`, it may start where that predecessor stands. An active or waiting predecessor stands at its last Arbeitsschritt. A completed predecessor with an Arbeitsschritt route stands at its selected successor. An owner-stopped (`abgebrochen`) or ended Vorgang has no position to continue from and cannot be named as `vorgaenger`. Core reads that position even for a not-judged predecessor. Work from the predecessor's open attempt is no output a successor can bind; store it at the subject record with provenance and bind it as a versioned source. The path must resolve to another Vorgang; it grants no source permission or approval. The predecessor’s last step ID must exist in the successor’s bound definition, as must the continuing start position. One predecessor may be named by at most one judged successor; a second successor is rejected with `execution.attempt`. A Vorgang named as `vorgaenger` by a judged successor is superseded: the due list derives that and does not show it as open.

Readable-body labels and their readers are inventoried in the [parser-label inventory](impacts-architect/references/parser-labels.md).

### Vorgang progress

Display position, status and Leistung achievement derived from the following table; do not maintain a separate progress summary. Read the last attempt in `laufpfad` and resolve its selected route against the bound Hauptprozess.

| Last attempt and bound route | Position | Vorgang status | Leistung achieved |
|---|---|---|---|
| `aktiv` | Its Arbeitsschritt and `versuch` | `aktiv` | Not yet established |
| `wartend` with `wiedereinstieg` | Its Arbeitsschritt and `versuch` | `wartend` | Not yet established |
| `abgeschlossen`, selected route reaches `end:<slug>` | Last Arbeitsschritt and reached `end:<slug>` | `beendet` | Whether that end is in `leistung.erreicht`; `open` if the list is absent |
| `abgeschlossen`, selected route targets an unopened Arbeitsschritt | Selected successor, no attempt yet | `zwischen` | Not yet established |
| `abgebrochen`, owner's recorded decision | Last Arbeitsschritt and attempt, no successor | `abgebrochen` | No |
| Named as `vorgaenger` by a judged successor | Retained historical position, no current work | `superseded` | No claim for this superseded Vorgang |
| Missing or contradictory derivation inputs | `open` for each value that cannot be derived | `open` if not derivable | `open` if not derivable |

The owner may end any current attempt with `status: abgebrochen`, `freigabe` identifying that owner and decision time, and `geschrieben` referencing the recorded decision. It carries neither `gewaehlte_route` nor `wiedereinstieg` and must be last. The recorded decision replaces normal completion requirements; unfinished job outputs need not exist. Inventory every file that was produced. This establishes no Leistung achievement; write the true outcome to the subject record. An end cannot continue. A route back to an Arbeitsschritt opens a new attempt under [Loops](#loops). A closed attempt alone establishes no acceptance; a reached end alone establishes no success. The Core function `derive_progress` in `impacts_protocol.model` implements this table for validator and viewer. Display the subject's stage from its record, separately from execution status. Progress weights belong in analysis.

### Work from prerequisites

For target timing and handoff design, apply [Minimize](impacts-method.md#minimize).

Within the current declared job, perform useful permitted work as soon as its prerequisites hold. If a contribution is blocked, preserve usable results; name the missing evidence or decision, responsible party and next allowed action. The existing processing body defines permitted preparation, acquisition and effects. Apply [Record writeback](#record-writeback) for subject records and their linked Vorgänge, [Vorgang progress](#vorgang-progress) for execution state, and [Signals and human gates](#signals-and-human-gates) for early decision requests and recording received decisions.

When a Vorgang's subject splits, such as one lot awarded and another rejected, the Vorgang continues for the part its route serves; the other part keeps its state at its record home or continues in a new Vorgang that selects the predecessor's outputs as [declared source inputs](binding.md#source-inputs-for-core-hauptprozesse). A new Vorgang binds any required row excerpt under [Snapshot and provenance](#snapshot-and-provenance).

For example, prepare an offer's supported content and calculate its price while delivery confirmation is outstanding, if the price rule and sufficient available inputs establish that calculation independently of delivery. Keep a delivery-dependent surcharge or final price open until its required evidence is available. Mark the missing confirmation and retain any required review before a commitment. Preparation needs sufficient inputs for that contribution; a file recording an unknown value proves the gap, not the missing value.

If a declared input file cannot yet be referenced, acquire it through the preceding job or a permitted preparation path before opening that attempt. Intermediate transformations of bound inputs stay within the job; they need no extra Arbeitsschritt merely because a tool was called. Newly acquired source evidence becomes declared output with provenance and then input to the next designated attempt before dependent processing. Never replace already bound input bytes. A relevant change requires rechecking the drafts and downstream results that declare or demonstrably depend on it. Unrelated work stays valid without evidence of a dependency. A new input set belongs to a new routed attempt, which may reuse earlier evidence under [Visible output and handoff](binding.md#visible-output-and-handoff). If the required return route is absent, restart in a new Vorgang with `vorgaenger` under [Execution](#execution). The reference identifies the old obligation; it does not grant new authority.

The current Core has one sequential `laufpfad`; [Vorgang progress](#vorgang-progress) derives its position, including between steps and after an end. Within the current job, the harness may organize independent operations; the Core does not. An `aktiv` or `wartend` attempt may hold permitted, uncompleted drafts under its declared `output/`; those produced outputs establish no acceptance, select no route, complete no attempt and release no Gate. Resume follows the declared route. Starting another Arbeitsschritt early, bypassing a Gate or opening concurrent Laufpfad branches is not implied. Recurring waits may justify a reviewed change to future Hauptprozesse, not a silent rewrite of a bound definition.

#### Decision results and Auslöser

A decision is a readable value, including a selection such as "yes for three of six". Keep one decision record with its own identity, holder, decision date, covered subject IDs, object revisions and source evidence. Each covered subject references that record; it does not copy the decision. A human gate may use `entschieden` as its sole route when the check establishes that a decision exists; binary gates retain `freigegeben` and `abgelehnt`. The decision's content lives in the recorded output, not in the route key.

Outside decisions, including awards, client approval and acceptance, arrive as received sources at the subject record. `gate: human` is reserved for a right-holder the workspace asks. A Vorgang waits for an outside decision only while its own obligation is open: the `abnahme` of its Leistung names that decision, or the decision can return work to it. After its end, a later outside decision arrives as a received source, changes the subject's outcome at its record, and opens another Vorgang only where an entry Arbeitsschritt declares it as Auslöser. The next entry binds the predecessor output and received source as declared inputs. An end may itself be the next Hauptprozess's Auslöser under its entry rule. No route crosses Hauptprozesse. Cost and lead time roll up by the subject's linked Vorgänge under the declared calculation rule.

Interpretation, comparison, filtering and prioritization can be substantive results. Their relation to a Leistung follows [Protocol vocabulary](ontology.md#protocol-vocabulary). Declare the applicable criteria, source scope, uncertainty handling and checks in the existing job; preserve reserved decisions and the [Capability authority boundary](capabilities.md#capability-contract).

An Auslöser is an outside event, such as a decision, a delivery or a date, that opens a Vorgang with the first attempt of its Hauptprozess entry or continues a waiting attempt.

- **Declaration.** A Hauptprozess does no work; its Auslöser is that of its entry Arbeitsschritt, whose later attempts start through incoming routes. The entry Arbeitsschritt's Flow declares each event that is its Auslöser, one line per event: the event, the result, subject and scope it carries, its rule and the remaining prerequisites; an upstream home links to it. Every declared event opens the same Leistung. If two events need different first work, that is a route inside the entry step; if they lead to different Leistungen, they are two Hauptprozesse. The declared rule decides that the event opens the obligation and permits its start: an undeclared event opens nothing, and a decision needs its holder's authority.
- **Schedule.** A retained schedule is timing under [Minimize](impacts-method.md#minimize), not an Auslöser; it delays opening or provision. A date is the Auslöser only when it opens the obligation, such as a period close.
- **Input.** The Auslöser is not an input. The entry Arbeitsschritt, like every Arbeitsschritt, [declares only the inputs every case has](impacts-architect/references/zuschnitt.md#arbeitsschritt). Where an event carries content the work needs, such as scope or a contract, the receiving job [binds that result revision](binding.md#source-inputs-for-core-hauptprozesse) as a declared input and checks its intended use.
- **Missing input.** If preparation cannot bind the declared input references, no attempt opens; the subject's record home keeps the owed opening with the missing input, its owner and next action until preparation succeeds.
- **Multiplicity.** Whether an event continues the current obligation or opens another follows from the [Leistung](impacts-architect/references/zuschnitt.md#hauptprozess), not from the event; one event can do both. One Auslöser may open several Vorgänge, one per Hauptprozess and [subject](impacts-architect/references/zuschnitt.md#hauptprozess); preserve the source-to-target mapping, declared multiplicity and handling of partial, rejected, unresolved, revised or repeated results. One evidenced decision may satisfy the rule's condition; reuse its applicable scope without requesting a duplicate decision. Reconcile uncertain effects under [writeback](binding.md#record-writeback) before repeating them.
- **Dispatch.** Dispatch belongs to the configured harness, not a cross-Hauptprozess Arbeitsschritt route.

The mapping identifies the obligation the Auslöser opens and the intended action separately from the evidence revision. A revised judgment about the same request is not automatically a new obligation or permission to repeat an effect.

For priority, eligibility and scheduling, apply [Augment](impacts-method.md#augment).

### Waits

A wait is a `wartend` attempt with `wiedereinstieg` (`ausloeser`, `continuation_ref`). An attempt becomes `wartend` only when its remaining work awaits a declared `ausloeser` and the request is recorded as sent or the awaited outside event is recorded as having begun, with that evidence referenced in `wiedereinstieg`; otherwise it remains `aktiv`. A drafted, unsent request remains output of the `aktiv` attempt, with the blocker named in the Vorgang body. At a human gate, preparing the decision packet is `aktiv`; only a request recorded as sent makes it `wartend`. The responsible human supplies the decision and the harness only records it. A holder's decision after a protocol break is also an awaited event. When the agent cannot follow the bound definition, including a conflict with an always-loaded rule, it stops dependent work, records the failure in Friction and names the blocker in the Vorgang body. The attempt remains `aktiv` until the request for the owner's decision is recorded as sent; then it becomes `wartend` with that decision as `wiedereinstieg.ausloeser`. Failed preparation opens no attempt under [Snapshot and provenance](#snapshot-and-provenance).

`continuation_ref` is a workspace-relative path to an existing working-tree file. By default, use the waiting attempt's own output file naming what is awaited and recording the sent request or begun outside event. Core checks that the path resolves to a regular file inside the workspace, without symlinks; the harness checks the evidence and actual dispatch or event start. No new Core field records dispatch. Work such as acquiring missing documents belongs to the current declared job; required human interaction gets its applicable touchpoint. The waiting attempt remains current until its declared continuation; no separate wait node is needed. For permitted preparation, processing and newly acquired evidence, apply [Work from prerequisites](#work-from-prerequisites).

Each wait declares, in Flow, its timing source, the due time of the expected event or the next timed review when arrival cannot be committed, the responsible follow-up and permitted non-arrival handling under the table below. Record the next time the harness must check the wait as `wiedereinstieg.faellig`, a quoted timestamp with offset; the Flow declaration says whether it is the expected event's due time or a timed review. A `faellig` earlier than the attempt's `status_seit` means the check is due at once; it is no contradiction. Review triggered only by the missing event cannot cover its absence. Missing timing, responsibility or permission remains an explicit gap with a clarification owner or unresolved ownership and a next action; the dependent continuation is not execution-ready, while independent permitted work continues. The configured harness must actually check the declared time and surface the non-arrival; a written rule alone establishes no monitoring.

| Current wait and event | Required check and permission | Permitted transition |
|---|---|---|
| Any wait, `faellig` reached | Harness checks for the declared event and continuation conditions | The check becomes due; expiry alone selects no route and supplies no decision or approval |
| Ordinary wait, check finds no event | Apply declared non-arrival handling within its authority | Remain `wartend` and escalate, or complete through a declared fallback route or negative end after applicable output and check requirements pass; if still waiting, record the next `faellig` |
| Human gate, check finds no decision | Apply declared escalation within its authority | Remain `wartend`, escalate and record the next `faellig`; expiry supplies no `freigabe` and selects neither `freigegeben` nor `abgelehnt` |
| Any wait, event received | Check declared continuation conditions and applicable evidence; for a human gate apply [Signals and human gates](binding.md#signals-and-human-gates) | Continue the waiting attempt only when permitted; otherwise retain the wait and record the next `faellig` |

### Loops

A route back opens a new attempt with the complete declared input set; earlier attempt bytes remain unchanged. Every loop declares one readable `Loop bound:` line in its returning step's Flow: counted unit and limit or outside-event deadline, source, responsible follow-up and permitted escalation or stop. The cold walk checks that each cycle has a nonempty bound line; the harness checks its meaning and observes the limit. Passes made in a `vorgaenger` count toward its successor's bound; a restart does not reset it. An Arbeitsschritt reached again may reuse its earlier evidence under [Visible output and handoff](binding.md#visible-output-and-handoff). Within the consumer, perform only its declared corrections and preserve the handed-off input bytes. For a defect requiring work outside that job, record its location and follow the declared return route. A declared final rejection follows its negative end.

### Signals and human gates

Warnings need a use restriction, check, question or blocking consequence.

Producer-close/Gate-open is one logical transition, without claimed filesystem atomicity. Opening grants neither route nor `freigabe`. Apply [Waits](#waits) to distinguish an `aktiv` packet or unsent request from a `wartend` gate whose request is recorded as sent.

Before opening `gate: human` or preparing a declared action at a `sacred` customer touchpoint for its responsible human, the executing harness checks declared inputs, required control evidence and the body’s permitted effect and actor. A failed prerequisite leaves the previous execution state unchanged. Touchpoint classification grants no execution authority. After human work, the gate output is checked against `pruefung`. The configured harness, including an agent session, may mechanically record an evidenced decision, including one given by voice or another message, for the identified object and revision, preserving its decision, identity and decision time without inventing missing values. Establish its origin from the applicable decision authority through the configured trusted execution path; a file merely claiming `human:<id>` is insufficient. Preserve the source evidence in the existing Vorgang evidence. The actual source and evidenced request or channel context must support the decision, object, revision, holder and decision time; the human need not dictate machine fields. Receipt or transcription time cannot substitute for decision time. Recording or formatting authenticates no person. Missing, ambiguous or contradictory decision evidence keeps the dependent transition unresolved. Corrections preserve bound and completed history under the existing revision rules.

Within an already permitted job or preparation path, a decision may be requested once its object, required evidence and authority are ready. This does not start an attempt of the later Arbeitsschritt early. One packet or interaction may yield separate decisions at declared authority boundaries. Preserve each holder's right, scope and source evidence. Record an applicable already received decision at its declared transition without asking again solely for bookkeeping. For a gated decision, record it when the declared gate opens. Recheck its coverage when the object, revision or relevant premises change. Each gate entry retains its responsible human's attribution; a shared interaction creates neither a joint `by` nor a concurrent Laufpfad. Processing and newly acquired evidence follow [Work from prerequisites](#work-from-prerequisites).

Apply the [Core boundary](ontology.md#enforcement-and-completion). A synthetic walk establishes only that opening writes no route/approval and completion consumes an external decision fixture.


### Validation issue codes

| Code family | Check and next action |
|---|---|
| `format.*` | Repair the reported text or YAML syntax. |
| `schema.*` | Supply or correct the named contract field. |
| `routing.*` | Restore the router and its expected type. |
| `structure.*` | Correct the named layout, identity or unsafe filesystem entry. |
| `reference.*` | Resolve the named definition reference within its scope. |
| `process.*` | Correct the named gate, end or reachable route. |
| `binding.*` | Restore the declared revision or referenced evidence without rewriting bound history. |
| `execution.*` | Correct the named attempt or Laufpfad condition while preserving completed history. |
| `trust.*` | Obtain the responsible human's evidenced decision and correct its serialization without inventing approval. |

## Retention and deletion

Personal data must not enter Git history. Keep it in a deletable store outside Git; the repository retains a reference and digest under the existing input and provenance mechanics.

For each record home, its responsible operator declares the intended purpose, applicable legal basis, retention period and exceptions from the responsible authority's source. This declaration identifies permitted scope without establishing basis or authority validity. Keep an unknown basis, period, exception or owner open and restrict only the dependent deletion.

Before deletion, inventory the known source records and their known copies, projections, caches, search indexes, exports and backups, including affected attempts and known Git histories, clones and remotes. Permission for one target does not authorize additional copies or remote history rewriting. State the inventory's sources, scope and search limits. Unknown consumers remain unknown; do not claim complete erasure or absence of copies beyond checked coverage.

Bind a deletion preview to the exact record identities and current source revisions or states. Show the stated purpose, basis, retention rule, exceptions, affected locations and expected effect. Obtain the required human approval for that scoped preview. Immediately before the effect, recheck that source state, approval and preview still match. Prevent a concurrent writer from changing the target between that recheck and deletion, using an effective lock, an exclusive maintenance window or equivalent control. If the harness cannot establish this race protection, do not execute the deletion.

Delete only the exact authorized targets and declared derivatives. Do not widen a path, query or identifier match at execution time. If part of the operation fails, stop dependent deletion, report confirmed and unconfirmed targets separately through a minimal receipt, and leave completion open. Do not recreate already deleted bytes merely to make the operation appear atomic.

After deletion, recheck known copies and indexes in scope. Check backup and restore paths so deleted material is not silently reintroduced; where a restore is required, apply the same deletion control before restored data becomes available. Retain the bounded search method and unresolved copies as explicit gaps.

The receipt records only what is needed to show the authorized scope, decision reference, operator or authenticated system, time, checked inventory coverage and actual result, including partial failure and open gaps. It contains neither deleted content nor a content hash or other durable fingerprint that can be linked back to that content. Its record reference must be no more identifying than the record home requires.

Authorized deletion of a referenced working-tree output, or loss of a recorded source blob from Git history, leaves `binding.reference_missing` or `binding.reference_digest`. Apply the [Core boundary](ontology.md#enforcement-and-completion). For external stores, the harness records missing or changed bytes. Retain that finding, link the minimal non-content receipt and authorization from the existing Vorgang body, and restrict affected historical uses. Never rehash missing or replaced bound bytes to make validation pass. Pseudonymization does not itself establish an exemption or deletion permission.

## Destination execution

Transporting a Hauptprozess preserves its definition bytes; destination source applicability and authority follow [Source descriptions](impacts-architect/references/datenumgang.md#source-descriptions), reusing valid local mappings and permissions while unresolved questions go to their responsible decision-maker.
Claim destination execution only after a destination `vorgang` has actually reached the stated test endpoint with its applicable prerequisites and checks; copying or checking links alone does not establish this, and independent permitted preparation remains useful while dependent execution is restricted.
Apply [Reviewed correction](impacts-method.md#reviewed-correction) at the changed home's revision boundary: changed Hauptprozess definitions require a new Hauptprozess binding, while changed external mappings stay at their source home and require the corresponding source binding and affected checks, preserving earlier bound inputs.


