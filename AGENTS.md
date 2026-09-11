# Agent guidance

Read [CONTEXT.md](CONTEXT.md) before repository work. Follow its routing and the protocol documents for the affected surface.

Before capturing, changing or applying domain concepts, relationships or inference rules, read and apply [ontology.md](02_protocol/ontology.md), including its completion conditions. Reuse the existing domain home and its evidence.

For claims in definitions, records and reviews, use the [evidence labels](02_protocol/impacts-architect/references/zuschnitt.md#evidence).

Keep each claim with its source and review state. Keep method examples synthetic. Store customer-specific material in its customer repository.

## Simplicity contract (binding; grounded in ICM/OKF)

`06_evaluations/complexity-budget/check.py` checks three structural metrics against [budget.yaml](06_evaluations/complexity-budget/budget.yaml). Raising a limit requires a nonempty `approved_by: human:<id>` attribution with rationale. The checker validates metrics, baseline and attribution format, not the person's identity. Agents never raise the budget themselves. Passing a size budget does not establish low coupling or business effectiveness.

1. **Folders and Markdown are the architecture.** Start a concept in an existing folder, not a new system. (ICM folder-directed work; OKF directory bundles.)
2. **The minimum contract is one field.** OKF requires `type`. Justify every additional required Core field in its commit. (OKF: minimally opinionated.)
3. **Fix the interface.** Core owns files, IDs and references; Git and harnesses own transport and execution. (OKF non-goals.)
4. **Separate factory and run.** Runs preserve their bound definitions. Work and evidence live in the run. Updating continuing business records requires explicitly permitted [writeback](02_protocol/capabilities.md#rückübertragung-in-geschäftsrecords). New evidence alone changes neither rules nor authority. (ICM layers 3/4.)
5. **Load the workstep's declared context.** Drafts are readable edit surfaces. Changes to bound inputs, completed results or sent documents create traceable revisions. Readability does not require a human stop after every step; declared gates and permitted actions govern. (ICM edit surfaces; IMPACTS historical binding.)
6. **Declared review is not authentication.** `human-reviewed` requires OKF `verified.by: human:<id>`, but that text alone proves neither identity nor domain approval. Agent consensus and delegated review never produce a human decision. (OKF trust signals; IMPACTS gate boundary.)
7. **Models supply parameters to bound calculations.** The sanctioned calculation and deterministic check execute in the workstep or an earned [Capability](02_protocol/capabilities.md#wann-extrahieren), with declared parameters. The model does not change the bound rule. (OKF attested computations.)
8. **Local retrieval before ingestion.** Follow the nearest `CONTEXT.md` through existing links to the fact home and source. Repair an inaccessible fact's router/link at that home. Research begins only for an evidenced gap, requested freshness or explicit user request. (ICM layered loading, edit-source principle, one home per fact.)

**Before adding a term, schema, role, object or file kind:** name the existing structure that already serves it and use that structure. If insufficient, identify the concrete gap and smallest extension. Budget increases need the human decision above. Keep one name per meaning.

English owns the active protocol. Apply the [language contract](02_protocol/language.md) to customer work; German-only work uses German readable surfaces and unchanged machine tokens.

Sources: [ICM, arXiv 2603.16021](https://arxiv.org/abs/2603.16021) · [OKF v0.2 SPEC](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md)
