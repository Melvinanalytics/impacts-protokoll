# IMPACTS Protocol — ultracode coherence handover

Date: 2026-09-09
Tree scored: `main` @ `1a0cf9c` (`v0.2.0`)
Local tree named by Melvin (`~/Projects/IMPACTS-PROTOKOLL`): **UNKNOWN** — not present on this agent
Authoring constraint: analysis only; no product-file deletes

Evidence labels used in this report (Melvin's request):

- **VERIFIED**: inspectable in this clone (file, git object, or command output)
- **INFERRED**: interpretation of those sources
- **UNKNOWN**: missing tree, missing human decision, or unrun check

AGENTS.md uses a different vocabulary (`verified` / `reported` / `hypothesis` / `open`). That split is itself a finding.

Score axes (1–5):

| Axis | 1 | 5 |
|---|---|---|
| Coherence | claims ≠ content, orphan, mixed jobs | one job; claims match bytes |
| Consistency | fights V1 / AGENTS / sibling files | same terms, same boundary |
| Compressibility | already tight | ~half the words/LOC would keep meaning |
| Bloat | none | duplication, stale research, dead plans, commented corpses |

---

## 1. One-page executive

`main` is already the compressed public core. v0.1.0 → v0.2.0 deleted charter, two extra schemas, gutachten fixtures, a Neo4j research note, and ~3.2k test/validator lines (**VERIFIED** `git diff --stat v0.1.0 v0.2.0`). What remains is a 40-file, ~3.3k-LOC contract: five schemas, `init`/`validate`, two eval gates, one human-verified spec.

The live problem is not leftover research on `main`. It is **three public lineages plus a missing local tree**:

1. Tag `v0.1.0` still contains `00_charter/`, `paketaktivierungen`/`wiedervorlage` schemas, `docs/research/2026-08-29-graph-intelligence-layer.md`, and `tests/fixtures/**/gutachten/**` (**VERIFIED** `git ls-tree v0.1.0`).
2. `main` / tag `v0.2.0` is the tree scored below: nested `hauptprozess/teilprozesse/arbeitsschritte` layout, two CLI commands, empty cold walk.
3. `origin/release/v0.3.0` is a later Melvin-attributed export: `hash`+`template`, domain-named Application tree, architect skill, capability example, cold-walk `beispiel/`, and in-place amendments to the V1 spec (**VERIFIED** `git log --oneline origin/release/v0.3.0`).
4. Melvin's local `~/Projects/IMPACTS-PROTOKOLL` was **UNKNOWN** here. `release/v0.3.0` commit messages claim it was cut from private `main`. Treat that as **INFERRED** until the local tree is diffed.

A next owner who “cleans `main`” without a lineage decision will either rewrite a tree v0.3 already replaced, or silently fork the public contract.

Inside `main` itself, the strongest *file* issues are duplication, not corpses:

- The 301-line V1 spec restates the five JSON schemas, the graph invariant, and the hash contract. `02_protocol/invariants/complete-process-paths.md` restates spec §5 in English under an orphan title `I4` (no I1–I3 in the tree).
- Path `docs/superpowers/specs/` is a planning-tool leftover. The file it holds is sacred (`verified.by: human:melvin`).
- Tests still mutate `PORTABLE_BASELINE` / `PORTABLE_LIMITS` that `check.py` no longer defines.
- Spec examples still say `verkehrswertermittlung` / `gutachten-001` while tests and the release gate demand synthetic examples.
- `customer_touchpoint: sacred` is stored but not enforced. AGENTS Trust-Trias (`human-reviewed` vs `machine-confirmed`) is not a Core schema. Method overclaims relative to `impacts validate`.

Do not split `validator.py`, do not add a sixth schema, do not restore v0.1 research, do not raise `budget.yaml` without Melvin.

---

## 2. How to execute this report

1. Get the lineage decision from Melvin (cut list item 1). Until then, change no product file.
2. If the live product is private-main / `release/v0.3.0`, **stop using this file-by-file table as a delete list for that tree**. Re-score v0.3; several `main` “gaps” are already filled there, and v0.3 introduces new bloat (`cold-walk/check.py` 1148 LOC vs validator 664).
3. If `main`/`v0.2.0` remains the public contract, execute cut list items 2–9 in order. Each item is a single existing file or a rename. No new protocol object.
4. Keep the sacred list untouched without Melvin.
5. `docs/audits/` is a new nested folder under existing `docs/`, created only for this handover. Flatten into `docs/` if Melvin wants zero new directories. It does not change `root_dirs` (still 5).

---

## 3. Inventory (`main` @ `1a0cf9c`)

Excluded: `.git`, caches, egg-info, build, `.coverage`, `.venv` (none present).

**VERIFIED** `find` of the working tree: 40 meaningful files, 3280 lines including `LICENSE`.

| Area | Files | LOC |
|---|---|---|
| Root md + license + gitignore + pyproject | 6 | 322 |
| `02_protocol/**` | 8 | 219 |
| `06_evaluations/**` | 6 | 306 |
| `docs/**` (before this report) | 2 | 315 |
| `src/impacts_protocol/**` | 7 | 966 |
| `tests/**` | 11 | 1152 |

Root directories counted by the budget checker: `02_protocol`, `06_evaluations`, `docs`, `src`, `tests` = 5.

57 test functions (**VERIFIED** `^def test_` plus two `unittest` methods). One is parametrized (`body` empty vs whitespace).

---

## 4. Ranked cut list (strongest first)

Execute only after item 1. “Delete” here means a later, explicit Melvin-approved edit — this PR deletes nothing.

### 1. Decide the live lineage — process, not a file

**Why:** Three published trees disagree on the Application folder layout and on the CLI surface. v0.3 amended V1 in place (nested `hauptprozess/` folders removed; `impacts hash` / `impacts template` added).

**VERIFIED** `origin/release/v0.3.0` `CONTEXT.md` routes to three specs; `main` `CONTEXT.md` routes to one.

**Do:** Melvin names one of: freeze `v0.2.0` as public core; promote `release/v0.3.0`; or wait for local-tree export. Record it in the V1 spec frontmatter or a one-line README note.

**Do not:** Implement v0.3 features onto `main` from this audit. Do not merge `release/v0.3.0` as a drive-by cleanup.

### 2. Stop treating the V1 spec as a second schema book

File: `docs/superpowers/specs/2026-08-30-minimal-core-design.md` (§4 YAML copies of JSON schemas; §5 copy of I4; §7 copy of `validator._surface_hash`; §11 completed migration checklist).

**Compressibility 4 / Bloat 4.** ~half of the 301 lines are restatements.

**Do (on a freeze-v0.2 decision):** Keep §1–3, §8–10, §12 as the unique prose. Replace §4 with links to `02_protocol/schemas/*.json`. Replace §5 with a link to `complete-process-paths.md`. Move §11 to a short “done in v0.2.0” note. Keep one YAML example, not five.

**Do not:** Edit this file's `verified.by: human:melvin` block, nor its status, without Melvin. On a v0.3-live decision, this file was already amended; re-score there.

### 3. Retire or explain `I4`

File: `02_protocol/invariants/complete-process-paths.md`

**VERIFIED** title is `# I4: Complete process paths`. **VERIFIED** `02_protocol/invariants/` contains only this file. v0.1 I4 text described yaml graphs, wait nodes, handoffs — current I4 matches V1 §5.

**Do:** Drop the `I4:` prefix, or restore I1–I3 as real invariant files. Do not invent I1–I3 for symmetry.

### 4. Relocate `docs/superpowers/` (path only)

**VERIFIED** `06_evaluations/complexity-budget/check.py` still ignores a `.superpowers` directory that does not exist on `main`. The spec lives under a Superpowers planning path. Four routers point at it (`CONTEXT.md`, `README.md`, `02_protocol/CONTEXT.md`, this report).

**Do:** After Melvin: move to `docs/release/` or `docs/specs/` and update the four links in one commit. Do not rewrite the body in that commit.

**Do not:** Create `docs/research/` again. v0.1's Neo4j note is gone from `main` and must stay gone.

### 5. Delete dead portable-baseline mutations

File: `tests/test_complexity_budget.py` lines that set `check.PORTABLE_BASELINE` and `check.PORTABLE_LIMITS`.

**VERIFIED** those names do not exist in `06_evaluations/complexity-budget/check.py`. The test still fails closed because `accepted_limits()` reads the fake git tag. The assignments are a commented corpse by another name.

**Do:** Remove the two assignments. Keep the test.

### 6. Merge duplicate init tests

Files: `tests/test_cli.py` (unittest) and `tests/test_minimal_init.py` (pytest) both prove `init` + existing-target.

**Do:** Keep pytest. Move the stderr/`exists` assertion into `test_minimal_init.py`. Delete `tests/test_cli.py`.

### 7. Kill the English alias `workstep`

**VERIFIED** in `tests/support.py` (`write_workstep`), `tests/test_minimal_application.py`, `tests/test_minimal_schemas.py`, and one validator message `"Invalid workstep run directory"`. Domain term is `Arbeitsschritt`.

**Do:** Rename helpers and the one message. No schema change.

### 8. Replace residual domain examples in the V1 spec

**VERIFIED** spec still uses `hauptprozess:verkehrswertermittlung` and `vorgang:gutachten-001`. Tests use synthetic `video`. `docs/release/public-release-gate.md` requires synthetic examples. v0.1 fixtures were literally `gutachten/`.

**Do:** Copy the test video example into the spec. One commit, examples only.

### 9. Cosmetic leftovers (batch)

- `IGNORED_ROOT` entry `.superpowers` in `complexity-budget/check.py`
- `generator.py` docstring “Stamp a contract-only IMPACTS customer workspace”
- `complexity-budget/CONTEXT.md` frontmatter `evidence_status: reported` on a machine-enforced gate
- `load_frontmatter` thin wrapper in `io.py` (keep if CLI/tests stay; otherwise inline)
- `WORKSPACE_TEMPLATE_FILES` lives in `workspace_contract.py` only for cold-walk

None of these are product behavior. Batch them; do not spend a design discussion.

### Explicitly not a cut

| Temptation | Why not |
|---|---|
| Split `validator.py` (761 LOC, 23 callables) | One job: read-only validation. v0.3 already extracted `hashing.py` on another lineage. Splitting on `main` forks both. |
| Delete cold-walk because it only checks emptiness | It is the D-04 lock: init stays a skeleton. v0.3 *replaced* this check with a full Vorgang walk — that is a lineage change. |
| Delete `test_core_boundary.py` 00_charter assertion | Cheap regression against v0.1 resurrection. |
| Restore graph-intelligence / charter / 7 schemas | v0.2 deleted them on purpose. |
| Add a Trust or Capability schema | AGENTS rule 1–2 and budget `protocol_schemas: 5`. |
| Raise `budget.yaml` | Needs `approved_by: human:<id>`. Agents must not. |

---

## 5. Sacred keep list (do not touch without Melvin)

1. **The five schemas** in `02_protocol/schemas/`. Field set, URNs `v1`, `additionalProperties: false`. v0.3 commit text says schemas are unchanged. Required-field rationale is already in commit `90c3a11` (**VERIFIED**).
2. **`verified.by: human:melvin` on the V1 spec** and **`approved_by: human:melvin` in `budget.yaml`**. AGENTS rule 6: agents never mint `human-reviewed`.
3. **Einfachheitsvertrag** in `AGENTS.md` and the checker pair `budget.yaml` + `check.py`. Limits `5/5/15`.
4. **Public API** `{init_workspace, validate, Issue, ValidationReport}` and CLI `init` / `validate` on this lineage. Adding commands is a V0.3 decision.
5. **Trust on Human Gates:** `freigabe.by` must be `human:<id>`. No agent attribution. `customer_touchpoint: sacred` semantics beyond storage need a human rule, not a silent validator feature.
6. **Factory ≠ product.** This repo does not hold customer Applications. `06_evaluations/CONTEXT.md` already says customer regression stays in the customer repository.
7. **`docs/release/public-release-gate.md`.** Clean export; private history stays private; examples synthetic.
8. **Closed Application tree + open workspace extras.** Validator rejects unknown files *inside* an Application and ignores customer folders at workspace root. That is the Core/Application boundary.
9. **Git-tree revision binding.** `application_revision: git-tree:<oid>` is the run-meaning lock. Do not reintroduce `hauptprozess_ref` / `current_arbeitsschritt_ref` / receipts.
10. **No sixth schema, no Wiedervorlage object, no wait node.** Waiting is a Laufpfad status. I4 already says so.

---

## 6. Cross-cutting findings

### 6.1 Naming

| Term | Home | Drift |
|---|---|---|
| Application | README, spec, folders `applications/` | v0.3: Application root `type` becomes `hauptprozess`; `type: application` router deleted |
| Arbeitsschritt | schemas, spec | Tests/validator: `workstep` |
| Leistung | embedded, ID-less | v0.1 CONTEXT said reciprocal 1:1 file; **gone from `main`**, still in tag `v0.1.0` |
| Human Gate / `gate: human` | spec + I4 + schema | consistent |
| Customer-Touchpoint / `customer_touchpoint` | method + schema | not in validator |
| Capability / Harness | README, AGENTS, method | **not in this repo on `main`** — by design (OKF: interface ≠ packaging) |
| I4 | one invariant file | I1–I3 missing |
| ICM / OKF | AGENTS.md | not operationalized in schemas |

German domain names + English CLI/messages + German spec + English protocol CONTEXT. **INFERRED:** bilingual on purpose; the inconsistency is the spec vs routers, not the product terms.

### 6.2 Duplicated MECE

The five-object model is defined in all of: `README.md` (tree ASCII), `CONTEXT.md` (link only), `02_protocol/CONTEXT.md` (definitions), V1 spec §2–4, five JSON schemas, `impacts-method.md` “Where the context lives”, and `tests/support.py` (the only example Application).

**INFERRED:** keep schemas + one prose glossary (`02_protocol/CONTEXT.md`) + spec for rules that are not in JSON (hash serialization, git-tree reachability, error classes). Everything else should point, not re-list.

### 6.3 Protocol vs apps/evals

On `main`, evals match the protocol: cold-walk expects the empty three-surface template; complexity budget measures five schemas and five root dirs.

Contradiction appears **across lineages**, not inside `main`:

- `main` cold-walk: empty template is success.
- v0.3 cold-walk: empty template is the *problem statement*; success is a synthetic Vorgang with loop, wait, human gate, hash.mismatch, and tree transport.

**VERIFIED** quote, `origin/release/v0.3.0` `docs/superpowers/specs/2026-09-02-executable-core-design.md` §1:

> `impacts init` schreibt drei Flächen und zwei Sätze. Der Cold Walk erzeugt eine leere Vorlage und prüft, dass sie leer ist.

That sentence is a diagnosis of **this** `main` tree.

### 6.4 Research vs executable core

On `main`, research is gone. AGENTS.md still imports ICM/OKF Trust-Trias and Attested Computations. Those rules bind *agents working in this repo*. They are not checked by `impacts validate`.

**INFERRED risk:** a next owner adds `verified.by` to workspace routers or a capability schema “because AGENTS says so”. That would violate sacred items 1 and 4.

v0.1 research (`graph-intelligence-layer.md`) talked Neo4j, Records, `99_ansichten/`, `datenautoritaet.yaml`. **VERIFIED** absent from `main`. **VERIFIED** still in tag `v0.1.0`. Public-release-gate wanted fresh history; this GitHub repo still serves that tag.

### 6.5 Method vs Core (sacred overclaim)

`02_protocol/impacts-method.md` says `sacred` “protects the interaction until a human approves a changed classification”.

**VERIFIED** `validator.py` never mentions `customer_touchpoint`. Schema only enums `standard`|`sacred`.

Core stores the marker. Method narrates a workflow the validator will not fail closed on. Say that out loud in the method file, or it will be implemented as a sixth concern.

### 6.6 Evidence vocabulary

| Surface | Labels |
|---|---|
| AGENTS.md | verified / reported / hypothesis / open |
| V1 spec frontmatter | `evidence_status: verified`, `verified.by: human:melvin` |
| complexity CONTEXT | `evidence_status: reported` |
| This handover (requested) | VERIFIED / INFERRED / UNKNOWN |

Three names for review state. AGENTS stop-question applies.

---

## 7. File scores (`main`)

Grouped where the role is identical.

### 7.1 Root contract

| File | Coh. | Cons. | Comp. | Bloat | One job? |
|---|---|---|---|---|---|
| `CONTEXT.md` | 5 | 4 | 1 | 1 | Router. Four links, no prose dump. Cons. 4: does not mention AGENTS or the v0.3 branch. |
| `AGENTS.md` | 5 | 3 | 2 | 2 | Agent operating contract. Cons. 3: Trust-Trias/OKF not in schemas; extra required fields *are* justified in `90c3a11`, so rule 2 holds. |
| `README.md` | 5 | 4 | 2 | 2 | Public face. Repeats the model tree and verification commands already in CONTEXT/evals. |
| `pyproject.toml` | 5 | 5 | 1 | 1 | Package 0.2.0, two packages, CLI `impacts`. Matches `__init__.py` and schemas path. |
| `LICENSE` | 5 | 5 | 1 | 1 | Apache-2.0. Do not touch. |
| `.gitignore` | 5 | 4 | 1 | 1 | Misses `.ruff_cache` / `.superpowers` that the budget checker ignores. Harmless. |

### 7.2 Protocol

| File | Coh. | Cons. | Comp. | Bloat | One job? |
|---|---|---|---|---|---|
| `02_protocol/CONTEXT.md` | 5 | 5 | 1 | 1 | Glossary + links. Best MECE home. |
| `02_protocol/impacts-method.md` | 4 | 3 | 3 | 2 | Authoring method; no schema. Identify list is long. Sacred-overclaim (see 6.5). |
| `02_protocol/invariants/complete-process-paths.md` | 4 | 3 | 3 | 3 | Same rules as spec §5; orphan `I4`; English vs German spec. |
| `leistung.schema.json` | 5 | 5 | 1 | 1 | ID-less embedded contract. 3 required. |
| `hauptprozess.schema.json` | 5 | 5 | 1 | 1 | `$ref` to Leistung. 4 required. |
| `teilprozess.schema.json` | 5 | 5 | 1 | 1 | `ergebnis` only. Leading indicator lives in Markdown, as method says. |
| `arbeitsschritt.schema.json` | 5 | 5 | 1 | 1 | Routes, gate, touchpoint. 6 required. Tight path regexes. |
| `vorgang.schema.json` | 5 | 5 | 1 | 1 | Highest required-count (12 nested, budget 15). Laufpfad is the state machine. |

### 7.3 Executable core

| File | Coh. | Cons. | Comp. | Bloat | One job? |
|---|---|---|---|---|---|
| `src/impacts_protocol/__init__.py` | 5 | 5 | 1 | 1 | Public surface lock. |
| `cli.py` | 5 | 5 | 1 | 1 | Two commands. Help text German; messages English. |
| `generator.py` | 5 | 5 | 1 | 1 | Atomic init. Docstring slightly stale (“Stamp…”). |
| `workspace_contract.py` | 5 | 5 | 1 | 1 | Two tuples. Could live in generator; not worth a debate. |
| `model.py` | 5 | 5 | 1 | 1 | `Issue` + `ValidationReport`. |
| `io.py` | 5 | 5 | 2 | 1 | Frontmatter reader. `DuplicateKeyError` is a `ValueError` subclass so validator maps it to `format.invalid`; **UNKNOWN** whether a test hits duplicate keys. `load_frontmatter` used only by `test_minimal_init.py`. |
| `validator.py` | 4 | 5 | 2 | 2 | One *product* job, five *internal* jobs (schema registry, graph, vorgang, git-tree, hash). 761 LOC. Matches spec §4–10. Do not split on this lineage. |

### 7.4 Evaluations

| File | Coh. | Cons. | Comp. | Bloat | One job? |
|---|---|---|---|---|---|
| `06_evaluations/CONTEXT.md` | 5 | 5 | 1 | 1 | Two-check router. |
| `cold-walk/CONTEXT.md` | 5 | 5 | 2 | 2 | Repeats README verification. |
| `cold-walk/check.py` | 5 | 5 | 1 | 1 | Asserts emptiness. Correct for v0.2 D-04. |
| `complexity-budget/CONTEXT.md` | 4 | 4 | 2 | 2 | Stale `evidence_status: reported`. Body is accurate. |
| `complexity-budget/budget.yaml` | 5 | 5 | 1 | 0 | Sacred numbers + human bootstrap. |
| `complexity-budget/check.py` | 5 | 4 | 2 | 2 | Real gate. Ignores `.superpowers` leftover. Release-tag baseline logic is the whole point; do not “simplify” it. |

### 7.5 Docs (pre-report)

| File | Coh. | Cons. | Comp. | Bloat | One job? |
|---|---|---|---|---|---|
| `docs/superpowers/specs/2026-08-30-minimal-core-design.md` | 4 | 4 | 4 | 4 | Normative V1 + schema reprint + finished migration + gutachten examples. Path is tooling leftover. Content is sacred. |
| `docs/release/public-release-gate.md` | 5 | 3 | 1 | 1 | Cons. 3: this repo's `v0.1.0` tag still holds operational-looking fixtures the gate says to keep out of public history. |

### 7.6 Tests

| File | Coh. | Cons. | Comp. | Bloat | One job? |
|---|---|---|---|---|---|
| `tests/__init__.py` | 5 | 5 | 1 | 1 | Package marker. |
| `tests/support.py` | 5 | 4 | 1 | 1 | Only Application in the product surface. `workstep` alias. Video example is the synthetic canon. |
| `test_cli.py` | 5 | 2 | 3 | 4 | unittest duplicate of init tests. |
| `test_minimal_init.py` | 5 | 5 | 1 | 1 | Keep. |
| `test_cold_walk.py` | 5 | 5 | 1 | 1 | Imports check.py via file path. Fine. |
| `test_complexity_budget.py` | 4 | 3 | 2 | 3 | PORTABLE_* corpse. Otherwise the right tests. |
| `test_core_boundary.py` | 5 | 5 | 2 | 2 | Public API + retired-surface absence + fail-closed. Keep the tombstones. |
| `test_minimal_application.py` | 5 | 5 | 1 | 1 | Graph/schema mutation tests. |
| `test_minimal_schemas.py` | 5 | 5 | 1 | 1 | Five-schema lock + anti-`hauptprozess_ref`. |
| `test_minimal_vorgang.py` | 5 | 5 | 2 | 2 | Copies `_surface_hash`. That copy is the v0.3 “one hash” motive. On `main`, acceptable. |
| `test_packaging.py` | 5 | 5 | 1 | 1 | Install-from-elsewhere. Skip if no pip. |

Error-class coverage vs spec §10 (**VERIFIED** by test string search): all 15 codes appear in tests (`routing.missing/type`, `format.invalid`, `structure.symlink/invalid`, `schema.invalid`, `reference.duplicate/unresolved`, `process.unreachable/no_end/gate`, `revision.invalid`, `run.invalid`, `hash.mismatch`, `trust.invalid`). Depth is uneven: `format.invalid` has one YAML case; duplicate keys **UNKNOWN**.

---

## 8. Appendix — VERIFIED quotes

### 8.1 Scope of this clone

```
main 1a0cf9c [origin/main] test: gate packaging suite on pip
tags: v0.1.0, v0.2.0
remote: Melvinanalytics/impacts-protokoll
```

`git branch -a` also has `origin/release/v0.2.0` (parallel v0.2 cut) and `origin/release/v0.3.0`.

### 8.2 V1 authority and human attribution

`docs/superpowers/specs/2026-08-30-minimal-core-design.md`:

```yaml
status: user-confirmed
review_state: implemented
evidence_status: verified
normative: true
date: 2026-08-30
verified:
  by: human:melvin
  at: 2026-08-30
```

`CONTEXT.md` line 5: “Normative V1 design” → that file.

`90c3a11` body (required-field rationale, AGENTS rule 2):

> Required-field rationale: type selects the applicable object contract. id provides stable references. Leistung.ergebnis names the valued end state, kennzahl names its success measure, and abnahme makes completion testable. …

### 8.3 What v0.2 removed (do not restore)

V1 spec §11:

> Entfernt werden: `00_charter/`; Paketaktivierungs- und Wiedervorlage-Schema; … `--customer`, `validate_workspace`, `validate_application` und `generate_workspace` als öffentliche Interfaces; … Ältere Specs bleiben als `superseded` historische Evidenz oder verlassen aktive Router.

**VERIFIED** `main` has no `superseded` specs. They left the active tree. Tag `v0.1.0` still has them.

v0.1 `02_protocol/CONTEXT.md` (contradicts current Leistung):

> **Leistung** is one repeatable owed result. It has a reciprocal 1:1 reference to one Hauptprozess.
> **Vorgang** … files live under `06_vorgaenge/<id>/`.

Current `02_protocol/CONTEXT.md`:

> **Leistung** is the embedded, ID-less result contract of one Hauptprozess.
> **Vorgang** is one concrete run of the Application revision named by its Git tree.

### 8.4 Orphan I4

Current file first line: `# I4: Complete process paths`

v0.1 I4 (same path, different contract):

> Every Hauptprozess declares its process graph in its canonical `hauptprozess.yaml`. … A node reference resolves within the same Hauptprozess.

Current I4:

> One Application contains one Hauptprozess. … No separate wait node or Wiedervorlage object exists.

### 8.5 Sacred overclaim vs validator

Method:

> `sacred` protects the interaction until a human approves a changed classification.

`arbeitsschritt.schema.json` property only:

```json
"customer_touchpoint": {"enum": ["standard", "sacred"]}
```

`rg customer_touchpoint src/` → no matches.

### 8.6 Residual domain example vs synthetic tests

Spec §4.2: `id: hauptprozess:verkehrswertermittlung`  
Spec §4.5: `id: vorgang:gutachten-001`  
`tests/support.py`: `id: hauptprozess:video`, body `# Video-Produktion`

Release gate:

> Confirm every example is synthetic.

### 8.7 Dead portable baseline

`tests/test_complexity_budget.py`:

```python
check.PORTABLE_BASELINE = {**getattr(check, "PORTABLE_BASELINE", {}), "root_dirs": 6}
check.PORTABLE_LIMITS = {**getattr(check, "PORTABLE_LIMITS", {}), "root_dirs": 6}
```

`rg PORTABLE_ 06_evaluations/` → no matches.

### 8.8 Empty cold walk (v0.2 job)

`06_evaluations/cold-walk/CONTEXT.md`:

> It expects two empty workspace folders plus one file:
> CONTEXT.md / applications/ / vorgaenge/

`generator.py` writes exactly that plus two German sentences.

### 8.9 Budget and root dirs

`budget.yaml`: `limits: {root_dirs: 5, protocol_schemas: 5, max_total_required_fields_per_schema: 15}`  
`initial_release.approved_by: human:melvin`

Measured on this tree (**VERIFIED** running the same counter as `check.py`):

| Schema | nested required |
|---|---|
| arbeitsschritt | 6 |
| hauptprozess | 4 |
| leistung | 3 |
| teilprozess | 3 |
| vorgang | 12 |

Max 12 ≤ 15.

### 8.10 v0.3 lineage (not scored file-by-file)

`origin/release/v0.3.0` `pyproject.toml`: `version = "0.3.0"` plus package `impacts_protocol.templates`.

`591714b` subject: `feat: executable core v0.3.0`  
`4d22fe7` subject: `feat: domain-named Application tree and capability method`

v0.3 README model (breaking vs `main`):

```text
applications/<hauptprozess>/CONTEXT.md                     Hauptprozess { Leistung }
applications/<hauptprozess>/<teilprozess>/CONTEXT.md        Teilprozess
applications/<hauptprozess>/<teilprozess>/<schritt>/CONTEXT.md   Arbeitsschritt
```

v0.3 `cold-walk/check.py`: **1148** lines (**VERIFIED** `git show … | wc -l`). `main` validator: **761**. v0.3 validator: **664**.

New files on that branch (not on `main`): `hashing.py`, `02_protocol/templates/*`, `02_protocol/impacts-architect/**`, `02_protocol/capabilities.md`, `06_evaluations/cold-walk/beispiel/**`, specs `2026-09-02`, `2026-09-04`, `2026-09-07`, tests `test_hash.py`, `test_templates.py`, `test_architect.py`.

Domain-named-tree spec frontmatter (**VERIFIED** `git show origin/release/v0.3.0:docs/superpowers/specs/2026-09-07-domain-named-tree-design.md`):

```yaml
status: draft
review_state: ready-for-human-review
evidence_status: verified where marked
normative: true
source: decision by Melvin Voigtländer on 2026-09-07 (reported, recorded by the agent); attribution documents, it does not authenticate
```

No `verified.by: human:melvin` block on that file. The V0.3 executable-core spec *does* have `verified.by: human:melvin` at 2026-09-02. **INFERRED:** next owner must not treat both amendments as the same trust level.

### 8.11 Local tree

Path `~/Projects/IMPACTS-PROTOKOLL`: **UNKNOWN** on this agent (`find` over `/home/ubuntu` found no such tree). Commit messages on `release/v0.3.0` claim export from private `main@c4bc29b` and `main@39e07e6`. Diff that local path against `1a0cf9c` and against `4d22fe7` before any cleanup PR.

---

## 9. Suggested first conversation with Melvin

1. Is public `main` frozen at v0.2.0 while private/local + `release/v0.3.0` is the live factory?
2. May the V1 spec be shortened to unique prose, or is the YAML reprint the human-readable contract on purpose?
3. Should `I4` lose its number, or are I1–I3 sitting only in the local tree?
4. Is `docs/superpowers/` an allowed historical path, or should the spec move now that Superpowers is not in the product?
5. Confirm sacred list item 5: `sacred` remains a stored marker, not a validator workflow.

Until those five answers exist, the executable next step is: **read this report, do not edit product files.**
