# Agent contract

Read [CONTEXT.md](CONTEXT.md) before repository work. It routes each intent to its authority and completion check; follow the closest `CONTEXT.md` for the affected surface and only the links needed by that branch.

For `AGENTS.md`, `CONTEXT.md`, workstep prompts or prompt fragments, apply [Maintain agent instructions](02_protocol/impacts-method.md#maintain-agent-instructions). Put each rule at one authoritative home and delete superseded wording instead of appending a patch elsewhere.

Before capturing, changing or applying domain meaning, follow the applicable completion path in [ontology.md](02_protocol/ontology.md).

Keep claims in definitions, records and reviews with their source and [evidence label](02_protocol/impacts-architect/references/zuschnitt.md#evidence). Keep method examples synthetic and customer-specific material in its customer repository.

## Simplicity contract (binding; grounded in ICM/OKF)

`06_evaluations/complexity-budget/check.py` checks three structural metrics against [budget.yaml](06_evaluations/complexity-budget/budget.yaml). Agents never raise a limit. An increase requires `approved_by: human:<id>` and rationale; this attribution does not authenticate the person. Passing proves only the measured bounds.

1. **Folders and Markdown are the architecture.** Extend an existing home before creating a system. (ICM folder-directed work; OKF directory bundles.)
2. **Keep Core minimal.** OKF requires `type`; justify each additional required Core field in its commit.
3. **Keep the interface fixed.** Core owns files, IDs and references; Git and harnesses own transport and execution.
4. **Separate factory and run.** Runs preserve bound definitions; work and evidence live in the run. Continuing records change only through permitted [writeback](02_protocol/capabilities.md#rückübertragung-in-geschäftsrecords).
5. **Load declared context.** Bound-input or completed-result changes create traceable revisions. Declared gates and permissions, not readability, govern human stops.
6. **Keep review and authentication separate.** A `human:<id>` string proves neither identity nor approval. Agents do not produce human decisions.
7. **Bind calculations.** Models may supply declared parameters; the sanctioned rule and deterministic check execute in the workstep or an earned [Capability](02_protocol/capabilities.md#wann-extrahieren).
8. **Retrieve locally first.** Repair routing to an existing fact. Research only for an evidenced gap, requested freshness or explicit request.

Before adding a term, schema, role, object or file kind, name and reuse the existing structure. If it is insufficient, record the concrete gap and smallest extension. Keep one name per meaning.

English owns the active protocol. Apply the [language contract](02_protocol/language.md) to customer work; German-only work uses German readable surfaces and unchanged machine tokens.

Sources: [ICM, arXiv 2603.16021](https://arxiv.org/abs/2603.16021) · [OKF v0.2 SPEC](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md)
