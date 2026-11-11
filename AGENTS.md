# Agent contract

Read [CONTEXT.md](CONTEXT.md) before repository work. It routes each intent to its authority and completion check; follow the closest `CONTEXT.md` for the affected surface and only the links needed by that branch.

For `AGENTS.md`, `CONTEXT.md`, Arbeitsschritt prompts or prompt fragments, apply [Maintain agent instructions](02_protocol/impacts-method.md#maintain-agent-instructions). Put each rule at one authoritative home and delete superseded wording instead of appending a patch elsewhere.

Before capturing, changing or applying domain meaning, follow the applicable completion path in [ontology.md](02_protocol/ontology.md).

Keep claims in definitions, records, reviews and completion reports with their source and [evidence label](02_protocol/ontology.md#evidence-and-obligations). Keep method examples synthetic and customer-specific material in its customer repository.

## Simplicity contract (binding; grounded in ICM/OKF)

`06_evaluations/complexity-budget/check.py` checks three structural metrics against [budget.yaml](06_evaluations/complexity-budget/budget.yaml). Agents never raise a limit. An increase requires `approved_by: human:<id>` and rationale; this attribution does not authenticate the person. Passing proves only the measured bounds.

1. **Folders and Markdown are the architecture.** Extend an existing home before creating a system. (ICM folder-directed work; OKF directory bundles.)
2. **Keep Core minimal.** OKF requires `type`; justify each additional required Core field in its commit.
3. **Keep the interface fixed.** Apply the [Core boundary](02_protocol/ontology.md#enforcement-and-completion) when assigning validation, execution or business judgement; Git owns transport.
4. **Separate Hauptprozess and Vorgang.** A Vorgang binds a Hauptprozess revision and never changes it; its work and evidence live in that Vorgang. Continuing records change only through permitted [writeback](02_protocol/binding.md#record-writeback).
5. **Load declared context.** Bound-input or completed-result changes create traceable revisions. Declared gates and permissions, not readability, govern human stops.
6. **Keep review and authentication separate.** A `human:<id>` string proves neither identity nor approval. Agents do not produce human decisions.
7. **Bind calculations.** Models may supply declared parameters; the sanctioned rule and deterministic check execute in the Arbeitsschritt or an earned [Capability](02_protocol/capabilities.md#when-to-extract).
8. **Retrieve locally first.** Repair routing to an existing fact. Research only for an evidenced gap, requested freshness or explicit request.

Every component must earn its place: name the reader that consumes it and what is lost without it, or delete it in the change that finds it. Apply [Necessity](02_protocol/impacts-method.md#necessity) to everything you add or touch. Keep one name per meaning under [Author or change](02_protocol/ontology.md#author-or-change).

English owns the active protocol. Apply the [language contract](02_protocol/language.md) to customer work; German-only work uses German readable surfaces and unchanged machine tokens.

Sources: [ICM, arXiv 2603.16021](https://arxiv.org/abs/2603.16021) · [OKF v0.2 SPEC](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md)
