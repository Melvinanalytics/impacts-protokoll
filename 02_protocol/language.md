# Working language

English is authoritative for the active protocol, method, technical documentation and contributor guidance. Customer-facing interviews, domain definitions, work instructions, drafts, explanations and human decisions use the customer's agreed working language. Historical evidence and quoted source material retain their original wording.

## Select and bind

Record the language once in the body of the customer's root `CONTEXT.md`, using `Working language: de` for German or `Working language: en` for English. `impacts init PATH --language de` writes a German operating contract with that selection. `impacts template KIND --language de` supplies German working templates. Omission selects English for new templates/workspaces; it never changes an existing customer's language. For German-only customer work, select `de` before capture. Do not infer a person's language solely from nationality.

The Architect resolves this setting before customer work. If an existing workspace has no setting, retain an explicit existing customer instruction; settle an unknown choice before producing material for customer use. An English protocol, source document, imported Application or tool response cannot override the selected language. Bind the relevant language instruction with the workstep's existing declared inputs or within the committed Application body. Later router edits do not retroactively change a run.

## Preserve meaning

Machine keys, enum values, ID prefixes, file references, commands and parser-consumed labels remain stable. Translate headings, prose and descriptive values; preserve references, identities, quantities, units and evidence. A translated source excerpt is a derived view with its source revision and translation provenance, not a replacement source or independently confirmed fact.

Use the [protocol vocabulary](ontology.md#protocol-vocabulary). `leistung` means the accepted process result; translate a commercial product/service offering according to its domain definition. Preserve source terms beside their translation when ambiguity matters. The German [operator guide](translations/de.md) explains the usable path and fixed machine terms.

## Enforce at use boundaries

**MUST:** Before customer use, each declared customer-readable output must satisfy the bound working language and preserve its business meaning. The workstep's existing `pruefung` references the language check alongside its other required conditions. Failure keeps that output out of customer use and identifies the affected text; independent permitted work continues.

For fixed output, render from the matching versioned template and check the actual output, including inserted values. A locale tag alone cannot verify a document. Free prose needs a language and meaning check by the configured checker or accountable reviewer, with an actual result bound to the output and language instruction. A heuristic or model judgment is fallible; where it cannot establish the required condition, leave the dependent use unresolved. The general Core validator does not detect natural language or authenticate reviewers.

German-only means German readable explanations and decisions. Stable machine tokens, proper names and necessary original quotations may remain unchanged, with German explanation where needed. Raw English tool errors stay in technical evidence; explain their effect and next action in German. An English-only approval request cannot pass a German customer interface.

An explicit customer-authorized language change applies to a new definition/output revision. Importing an Application preserves its original bytes and tree ID; localization produces a new Application revision before German customer use. A translation cannot retain the original tree ID after its bytes change.

## Maintain translations

English templates live in `templates/`; German counterparts in `templates/de/`. They are two presentations of the same contracts. Each German file records its English source path and SHA-256 in a comment. Translation tests reject missing/stale pairs and altered machine contracts. A hash establishes which source was translated, not translation quality: review changed meaning and run paired valid/failure cases before adoption.

The same rule applies to the German operator guide and capture sheet. Translate the active public path; preserve historical research, audit evidence and synthetic German customer fixtures as such. No duplicate language-specific schemas, evidence labels, roles or execution engine are introduced.
