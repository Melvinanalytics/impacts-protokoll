---
type: workspace
---

Working language: en

# IMPACTS Workspace

Before business capture, record the actual protocol source, revision and resolvable Architect entry (`02_protocol/impacts-architect/SKILL.md`). Every `02_protocol/` path in this workspace resolves against that recorded source/revision, not the generated customer tree. Its form selection identifies the smallest suitable domain home. Add direct links to those homes with their purpose; keep facts at their source. Given products/services, use the method's “Reverse-engineer a product or service” before assuming a Pipeline.

For domain meaning, use the applicable Author/change or Use branch of `02_protocol/ontology.md` in that protocol revision. Link the existing domain home. Executed domain checks are separate from `impacts validate`.

## Setup

`init` creates this router, `applications/` and `vorgaenge/`. Initialize Git at this root before binding revisions. Git omits empty directories; validation treats absent `applications/` or `vorgaenge/` collections as empty. Present collections must contain valid children; add no placeholder files. Add domain files only for actual content under the Architect's form selection. Before a real run, name the configured harness and its setup/dependency reference here; confirm support for the selected Application's operations, source access, checks, handoffs and human boundaries. Keep credentials in that execution environment. An empty valid workspace is not an executable process. The following Application/run rules apply only to a selected Pipeline.

## Operating contract

1. The workspace root is the Git root. Runs bind committed Application trees only.
2. Design an Application: `impacts template application` shows the layout; `impacts template <kind>` supplies each `CONTEXT.md`. Folders carry domain names: `applications/<hauptprozess>/<teilprozess>/<arbeitsschritt>/CONTEXT.md`; the role is `type`, the ID is `<type>:<folder-name>`. The tree contains only `CONTEXT.md` files. After commit, `git rev-parse HEAD:applications/<slug>` supplies the revision. Import another repository's Application as a byte copy of `applications/<slug>/` (`git archive | tar -x`), committed with source commit and tree OID in the commit message. Equal bytes preserve its tree OID; localization is a new revision.
3. Open a run: materialize and check the entry's declared inputs and provenance from their declared sources first, including needed rules/templates outside the Application. Then create `vorgaenge/<slug>/CONTEXT.md` from `impacts template vorgang` with `application_revision: git-tree:<oid>`. The first `laufpfad` entry is the Application entry, attempt `001`, status `aktiv`. Inputs belong under `<step>/001/input/`; `impacts hash <attempt-folder> <surface>...` supplies `eingabe_hash`. Failed preparation opens no attempt.
4. Complete an attempt with actual check evidence and the matching outcome: write declared outputs under `output/`, use `impacts hash` for `ausgabe_hash`, record `gewaehlte_route`, set `abgeschlossen`. A declared failure route carries the failed result; it grants no successful use. A step route requires the next entry with its bound inputs in the same logical transition; an `end:<slug>` route ends the run.
5. Human gate: the entry stays `aktiv` until the named human supplies `freigabe` with `by: human:<id>` and `at`. No agent writes `human:<id>`.
6. Wait: `wartend` with `wiedereinstieg` (`ausloeser`, `continuation_ref`). Permitted drafts in the current job may appear under `output/`; bound inputs, route and approval remain unchanged. Explain usable results, blocker and next permitted work in the run body, derived from `laufpfad` and files. Continuation completes this attempt through a route; bind new inputs in the next designated attempt. Core does not start parallel worksteps.
7. Run `impacts validate .` before each commit. Exit 1 blocks.
8. Core executes no workstep. The bound workstep body supplies the prompt and names tool operations, versions, parameters, permitted effects and checks. The configured harness loads declared inputs, executes permitted work and retains actual output evidence under `02_protocol/impacts-method.md`, “Compose an Arbeitsschritt”, and `02_protocol/capabilities.md` in the bound protocol revision.

## Working language

Customer work uses English: interviews, domain definitions, instructions, drafts, questions and decisions. Machine identifiers and source quotations retain their original form; explain their meaning and use consequences in English. Use `impacts template <kind> --language en`. Before customer use, the workstep checks the actual output, including inserted values, under `02_protocol/language.md` in the bound protocol revision. A missing or failed language/meaning check blocks its dependent use. Bind the language instruction and actual check evidence in the existing contract and declared run files.
