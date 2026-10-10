---
type: workspace
---

Working language: en

# IMPACTS Workspace

Before business capture, follow the complete protocol source's root `README.md`, “Version and entry points”, to record its actual source, revision and resolvable Architect entry (`02_protocol/impacts-architect/SKILL.md`) under Source, harness and homes. If that source is missing after `init`, identify the generating package with `python -m pip show impacts-protocol` in its Python environment and obtain the corresponding complete source from [releases](https://github.com/Melvinanalytics/impacts-protokoll/releases). The package version alone does not identify an exact source revision. On resumption, follow the source/revision and working language already recorded here.

Every `02_protocol/` path in this workspace resolves against that recorded source/revision, not the generated customer tree. Its form selection identifies the smallest suitable domain home. Link those homes with their purpose under Domain homes; keep facts at their source. Given products/services, use `02_protocol/impacts-method.md#reverse-engineer-a-product-or-service` before assuming a Pipeline.

To capture or change domain meaning, use `02_protocol/ontology.md#author-or-change`; to apply it, use `02_protocol/ontology.md#use`. Link the existing domain home.

## Source, harness and homes

Record configured facts here and preserve the operating contract. Changes to instructions or working language follow the applicable reviewed revision path under `02_protocol/impacts-method.md#maintain-agent-instructions`.

- Protocol source: `<complete source used>`
- Revision and local changes: `<tag or commit, and each local change>`
- Architect entry: `<resolvable path of 02_protocol/impacts-architect/SKILL.md>`
- Harness and setup reference, when Core Run execution is selected: `<configured harness and its setup reference, or not selected>`
- Domain homes: `<link and purpose of each home>`

## Setup

`init` creates this router, `applications/`, `vorgaenge/` and `.gitattributes` (`* -text`, so a checkout keeps bound bytes and their hashes unchanged). Before a Core Run binds a revision, initialize Git at this root. Git omits empty directories; validation treats absent `applications/` or `vorgaenge/` collections as empty. Present collections must contain valid children; add no placeholder files. Add domain files only for actual content under the Architect's form selection. Before a Core Run, name the configured harness (`02_protocol/capabilities.md#responsibilities`) and its setup/dependency reference under Source, harness and homes; confirm support for the selected Application's operations, source access, checks, handoffs and human boundaries, including required history retention/checking under that responsibilities contract. Keep credentials in that execution environment. An empty valid workspace is not an executable process. The following rules apply to selected Core Application/Run contracts under `02_protocol/impacts-architect/references/formwahl.md#tooling-stopp`.

## Operating contract

1. For Core Runs, the workspace root is the Git root. Runs bind committed Application trees reachable from branch, tag or remote-tracking history or the current worktree’s resolvable commit at `HEAD`, including detached HEAD. Stash-only and auxiliary-ref-only trees are excluded; shallow history covers only reachable commits within its boundary. This reachability establishes no approval or authenticity.
2. Design an Application: `impacts template application` shows the layout; `impacts template <kind>` supplies each `CONTEXT.md`. Folders carry domain names: `applications/<hauptprozess>/<teilprozess>/<arbeitsschritt>/CONTEXT.md`; the role is `type`, the ID is `<type>:<folder-name>`. The tree contains only `CONTEXT.md` files. After commit, `git rev-parse HEAD:applications/<slug>` supplies the revision. Import another repository's Application only by the procedure in `02_protocol/impacts-method.md#scale`; localization is a new revision.
3. Open a run: materialize and check the entry's declared inputs and provenance from their declared sources first, including needed rules/templates outside the Application. Then create `vorgaenge/<vorgang>/CONTEXT.md` from `impacts template vorgang` with `application_revision: git-tree:<oid>`. The first `laufpfad` entry is the Application entry, attempt `001`, status `aktiv`. Inputs belong under `<arbeitsschritt>/001/input/`; `impacts hash <attempt-folder> <each eingaben path>...` supplies `eingabe_hash`. Failed preparation opens no attempt.
4. Complete an attempt with actual check evidence and the matching outcome: write declared outputs under `output/`, use `impacts hash <attempt-folder> <each ausgaben path>...` for `ausgabe_hash`, record the `routen` key of the actual `pruefung` outcome as `gewaehlte_route`, set `abgeschlossen`. A declared failure route carries the failed result; it grants no successful use. A step route requires the next entry with its bound inputs in the same logical transition; an `end:<slug>` route ends the run.
5. Human gate: the unresolved entry may stay `aktiv` or be `wartend` with its declared continuation, carrying neither route nor approval, until the named human's decision closes it under item 4, with `freigabe` (`by: human:<id>` and `at: "<YYYY-MM-DD>T<hh:mm:ss>+<hh:mm>"`, quoted, with offset) beside `gewaehlte_route` and `ausgabe_hash`. Record evidenced human decisions only under `02_protocol/capabilities.md#signale-und-human-gate`.
6. Wait: `wartend` with `wiedereinstieg` (`ausloeser`, `continuation_ref`). Permitted drafts in the current job may appear under `output/`; bound inputs, route and approval remain unchanged. Explain usable results, blocker and next permitted work in the run body, derived from `laufpfad` and files. Continuation completes this attempt through a route; bind new inputs in the next designated attempt. Core does not start parallel worksteps.
7. For required Core conformance, run `impacts validate` on the selected scope. It checks Core structure only (`02_protocol/ontology.md#enforcement-and-completion`), so exit 0 proves nothing more, not even that `gewaehlte_route` matches the actual `pruefung` outcome; the checker named under each step's Check and the configured harness own the rest. A failed or unperformed required check restricts its dependent claim or action.
8. Core executes no workstep. The bound workstep body supplies the prompt and names tool operations, versions, parameters, permitted effects and checks. The configured harness loads declared inputs, executes permitted work and retains actual output evidence under `02_protocol/impacts-method.md#compose-an-arbeitsschritt` and `02_protocol/capabilities.md`.

## Working language

Customer work uses English: interviews, domain definitions, instructions, drafts, questions and decisions; a workstep binds another language only as `02_protocol/language.md` allows. Machine identifiers and source quotations retain their original form; explain their meaning and use consequences in English. Use `impacts template <kind> --language en`. Before customer use, the workstep checks the actual output, including inserted values, under `02_protocol/language.md#enforce-at-use-boundaries`. A missing or failed language/meaning check blocks its dependent use. Bind the language instruction and actual check evidence in the existing contract and declared run files.
