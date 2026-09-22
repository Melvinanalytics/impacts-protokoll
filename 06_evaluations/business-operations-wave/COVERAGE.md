# Coverage and execution record

This file maps the complete v0.3.5 product delta and the v0.3.6 business-design delta to the frozen cases. It does not replace the authorities linked from the repository router. Read it only after completing the first-pass answers in [CONTEXT.md](CONTEXT.md).

## Coverage rule

“All parts of v0.3.5” means every shipped feature cluster and executable behavior change from v0.3.4 to v0.3.5 is covered. Pure test refactoring is covered by the full regression suite rather than a fictional business scenario. Each semantic cluster receives:

- a valid or supported case;
- a missing, conflicting or stale case;
- a plausible forbidden inference or authority overreach;
- an existing deterministic check where the product has a machine-enforced boundary.

## v0.3.5 feature coverage

| Shipped cluster | Primary shipped surfaces | Valid/supported | Missing or conflicting | Forbidden inference/adversarial | Deterministic regression |
|---|---|---|---|---|---|
| Public version and entry identity | `README.md`, `FIRST-WIN.md`, root `CONTEXT.md`, German guide, `pyproject.toml` | E07 with one aligned edition | E07 asset/version mismatch | One checked asset is presented as complete release proof | `tests/test_public_release.py`, packaging tests |
| Complete source identity and entry resolution | README entry path, root router and Architect dependency declaration | E15–E16 with complete exact source | E15 missing parent protocol; E16 dirty source | Edition string or successfully opened skill substitutes for actual bytes | public-release and link tests plus E reading |
| Trust and security boundaries | README and German operator guide | E09, E11–E13 | E10, E13 | Source content or credentials expand instruction authority | public path checks plus E reading |
| Enterprise knowledge-only intake | README and German operator guide | E09 | E10 | Router links are assumed to be retrieved; public release is called tenant attestation | E reading; deployment remains outside protocol |
| Executable enterprise dependency intake | README and German operator guide | E11 | E11 unresolved dependencies | Wheel checksum is claimed to cover dependencies | packaging/release tests plus E reading |
| Customer/public repository boundary | README trust table and root agent contract | E14 | E14 proposed customer-data publication | A reusable example justifies publishing customer facts | private-path/public-export checks plus E reading |
| Cross-repository task routing | protocol router and Architect description/mode selection | C01, C09, C12 | C07, C10–C11 | Import mode is used for arbitrary knowledge or skills | architect/link tests plus C-wave reading |
| Source ownership and consumer dependency kinds | Architect Restructure steps 1–9 | C01–C06 | C07, C11 | Matching owner name, bytes or newer revision establishes authority | cross-repository fixture and public link checks |
| Bounded discovery, retirement and recovery | Architect Restructure steps 4, 6 and 7 | C01, C11, C12 | C07 | Residual possibility of unknown consumers blocks forever, or bounded search proves none exist | cross-repository reading fixture |
| Explicit consumer rebinding and historical preservation | Architect Restructure step 8, Import mode | C02, C10–C12, B12 | C11 | Later definition silently rewrites prior Run | Core Run/history tests |
| Domain addresses | `ontology.md`, formwahl native topology, German guide | A01–A08, B01–B02 | A03, A05–A08 | Every paragraph needs an ID, or same label means same item | linked-data and localization tests |
| Scoped domain relationships | ontology relationship requirements and reconciliation note | A03–A05, A08 | A03, A05 | Link proximity implies direction, inversion, transitivity or causality | linked-data tests plus A-wave reading |
| Namespace and identity | ontology meaning/inference | A04, A06 | A06 | Same bare ID across systems is one entity | linked-data tests |
| Observation boundary and clocks | ontology and both Ist templates | A07–A08, B08 | B03, B07 | Evidence artifact is the observation; recording verifies it; one timestamp substitutes for all clocks | localization/source-hash tests plus A/B reading |
| Roles around facts and calculations | ontology and Ist templates | B08, A12 | B01, B08 | Reporter or calculator automatically owns the rule | A/B adversarial pass |
| Calculation capture and provenance | both Ist templates and ontology worked example | B01–B04, B08–B10 | B03–B05, B11 | Correct arithmetic supplies input truth, acceptance or authority | computation walk plus B-wave reading |
| Calculation check, acceptance and use | Ist template additions | B02, B06 | B05–B07, B11 | Calculated means accepted, used or permitted | computation walk plus B-wave reading |
| Metric meaning separate from values and thresholds | ontology and method | A01–A05, B02–B04 | A05, B04 | Equal values or units merge definitions | A/B reading |
| Transactions/events separate from bounded observations | `capabilities.md` data governance | A06–A08 | A07 | A transaction record proves the real event | A-wave reading |
| Customer-language meaning | German guide and localized Ist template | A11, E01–E04 | E01, E03 | Translation changes machine vocabulary or becomes authority | `tests/test_localization.py` |
| Cold-walk implementation source identity | cold-walk script and regression | E08 | E08 wrong installed source | Happy-path equivalence proves correct checkout binding | `tests/test_cold_walk.py` |
| Hash error families | `src/impacts_protocol/hashing.py` | E05 | E05 | Hash success proves truth or permission | hash and Run tests |
| Workspace issue paths | `src/impacts_protocol/validator.py` | E06 | E06 nested defect | Application-relative path is sufficient at workspace boundary | validator/Run tests |
| Historical invalid-definition guidance | validator rejection message | E06, B12 | E06 | Repair by rewriting or rebinding old Runs | `tests/test_minimal_vorgang.py` |
| Export closure and private-path exclusion | release allowlist and public tests | E07 | E07 incomplete asset set | Local/private path is acceptable in public artifact | `tests/test_public_release.py` |
| Full executable behavior retained | shared pytest fixtures/refactors and existing Core contracts | all applicable mechanical cases | negative fixtures in existing tests | Passing a reading case substitutes for machine checks | full Python 3.11 and 3.14 suites |

## v0.3.6 delta coverage

| Shipped cluster | Cases | Required distinction |
|---|---|---|
| Result work and coordination are independent questions | D01–D07, D12 | Four combinations plus `open`; labels do not pick the answer |
| Coordination is minimized before assigning an executor | D01, D04, D06 | Remove or redesign the dependency before automating it |
| Result boundary is relative and does not quantify economic value | A09–A10, D02–D05 | Accepted result/condition versus project, department or claimed value |
| Aggregation avoids double counting and keeps waits separate | D06–D07 | Fixed boundary/population/period/unit; mixed/open effort separate |
| Augment supplies minimum sufficient point-of-use context | B03–B11, D08–D10 | Recipient, use, source, revision/time, trigger, check, destination, missing route |
| Derived context preserves provenance and cannot create authority | A11, B11, D09–D10 | Summary, translation or estimate remains derived |
| Supply form is earned by observed need | B09–B10 | Direct read versus maintained deterministic service; no graph by default |
| Execution mix follows rules, variance, interaction, authority and effects | D02–D05, D11–D12 | Deterministic, agent and human contributions compose inside work |
| Physical and external effects need permitted operations and evidence | D03, D11–D12 | Preparation is not execution |
| Updated capture and workstep templates preserve these distinctions | A09–A10, B01–B12, D01–D12 | No new Core field or exclusive step class |
| Public edition identity moved to 0.3.6 | E07 | Tag, metadata, guides and assets agree |

## Wave execution design

Use the prior audit discipline without importing its old business facts or verdicts:

1. **Freeze:** preserve `CONTEXT.md` and `EXPECTED.md` bytes before the first run.
2. **Operate:** fresh reader answers all cases from the public tag under test without `EXPECTED.md`.
3. **Contradict:** another fresh reader applies the seven adversarial mutations in `EXPECTED.md` and reports kills only; it does not repair answers.
4. **Regress:** run deterministic suites on exact v0.3.5 and v0.3.6 trees with documented Python/package prerequisites.
5. **Converge:** classify every failure as reader error, case defect, protocol defect or unperformed environment check. Never move an oracle to manufacture a pass.

No run may claim customer adoption, business improvement, production-harness behavior or human approval. A simulated harness remains labeled. A later run gets a new evidence directory; frozen cases and earlier evidence remain unchanged.

## Execution record

| Target | Check | Result |
|---|---|---|
| v0.3.5 tag `2cd1fde` | Full deterministic suite, CPython 3.11.15, pytest 9.1.1, editable install with declared runtime dependencies and setuptools | 546 passed, 6 skipped in 68.30 s |
| v0.3.5 tag `2cd1fde` | Full deterministic suite, CPython 3.14.6, pytest 9.1.1, same installation conditions | 546 passed, 6 skipped in 69.72 s |
| v0.3.5 tag `2cd1fde` | Complexity budget; direct cold walk; direct computation; German and English offer walks; focused computation/cold/offer/public-release tests | budget 4/5 roots, 5/5 schemas, 12/15 required fields; all direct walks passed; 184 focused tests passed in 51.38 s |
| v0.3.6 tag `5ad90cd` plus this uncommitted wave | Full deterministic suite, CPython 3.11.15, pytest 9.1.1, editable install with declared runtime dependencies and setuptools | 546 passed, 6 skipped in 69.72 s |
| v0.3.6 tag `5ad90cd` plus this uncommitted wave | Full deterministic suite, CPython 3.14.6, pytest 9.1.1, same installation conditions | 546 passed, 6 skipped in 69.72 s |
| v0.3.6 tag `5ad90cd` plus this uncommitted wave | Complexity budget; direct cold walk; direct computation; German and English offer walks; focused computation/cold/offer/public-release tests | budget 4/5 roots, 5/5 schemas, 12/15 required fields; all direct walks passed; 184 focused tests passed in 51.38 s |
| Candidate `ae80b0a` | Blind semantic first pass, 64 cases; readers did not open this file or `EXPECTED.md` | Strict first-pass score 61/64. B02 reached a safe conditional result but incorrectly called the identity question a protocol/case gap; C10 omitted Capability, destination-source, language and affected-use compatibility checks; E08 diagnosed checkout B instead of requiring checkout A. |
| Candidate `ae80b0a` | Fresh case-specific follow-ups for B02, C10 and E08 | 3/3 substantive pass. Cumulative result: 64/64 after follow-ups, not a clean first-pass 64/64. B02 requires one case note minimum, one occurrence key and no new metric or reusable-derivation identity merely because one execution returned three outputs. C10 retained every compatibility/source boundary. E08 required checkout A and the discriminating negative fixture. |
| Candidate `ae80b0a` | Independent adversarial pass over all seven mutation kinds | 7/7 retained identity, evidence, authority, process and permission boundaries; no protocol or case gap found. |
| Candidate `ae80b0a` | Independent adjudication of the normative delta and reading results | No normative defect found; version-bump preparation may continue. The review is agent evidence, not human approval or release readiness. |

The historical v0.3.6 working-tree entries include only the three initial wave files and their router link on top of the named tag. The later `ae80b0a` rows bind the first normative routing candidate. Reader results establish interpretation of synthetic cases, not customer adoption, human approval, production execution or a measured reduction in context tokens. Preserve the first-pass errors when reporting the corrected cumulative result. Update this table only with exact revision, environment and observed output; do not infer a pass from a nearby tree.
