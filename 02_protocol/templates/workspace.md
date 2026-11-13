---
type: workspace
protocol: v0.5.0
---

Working language: en

Customer work uses this working language under `02_protocol/language.md`.

# IMPACTS Workspace

Before business capture, follow the complete protocol source's root `README.md`, “Version and entry points”, to record its actual source, revision and resolvable Architect entry (`02_protocol/impacts-architect/SKILL.md`) under Source, harness and homes. If that source is missing after `init`, identify the generating package with `python -m pip show impacts-protocol` in its Python environment and obtain the corresponding complete source from [releases](https://github.com/Melvinanalytics/impacts-protokoll/releases). The package version alone does not identify an exact source revision. On resumption, follow the source/revision and working language already recorded here.

Every `02_protocol/` path in this workspace resolves against that recorded source/revision, not the generated customer tree. Its form selection identifies the smallest suitable domain home. Link those homes with their purpose under Domain homes; keep facts at their source. Given products/services, use `02_protocol/impacts-method.md#reverse-engineer-a-product-or-service` before assuming a Pipeline.

To capture or change domain meaning, use `02_protocol/ontology.md#author-or-change`; to apply it, use `02_protocol/ontology.md#use`.

## Source, harness and homes

Record configured facts here and preserve the operating contract. Changes to instructions or working language follow the applicable reviewed revision path under `02_protocol/impacts-method.md#maintain-agent-instructions`.

- Complete source location (provenance; release pin is in frontmatter): `<path or URL>`
- Source commit and local changes: `<commit and each local change>`
- Architect entry: `<resolvable path of 02_protocol/impacts-architect/SKILL.md>`
- Harness and setup reference, when Core execution is selected: `<configured harness and its setup reference, or not selected>`
- Domain homes: `<link and purpose of each home>`
- Value chain, with more than one Hauptprozess (`02_protocol/impacts-architect/references/formwahl.md#composition`): `<one row per Hauptprozess: links to its Leistung and Auslöser lines; its unit, linked to the record kind; which end or outside event opens it; every Hauptprozess or recipient that uses its end, upstream ones included>`

`Ablage: <name> <location or system>, <access rule home>`: declare each external store on its own unindented body line; agents never invent a store.

`Form: <folder>/ <form> per <unit>`: one unindented body line per top-level folder (forms: `02_protocol/impacts-architect/references/formwahl.md#folder-structure-by-form`).

When using Capabilities from a Fachrepo or another domain home, link their early responsible router under Domain homes and apply `02_protocol/impacts-architect/references/formwahl.md#capability-orientation` from the recorded protocol source.

## Setup

`init` creates this router, `hauptprozesse/`, `vorgaenge/`, `.gitattributes` (`* -text`, so a checkout keeps bound bytes and their hashes unchanged) and a `.gitignore` for system and office leftovers (`Thumbs.db`, `desktop.ini`, `~$*`), which the level check skips. Git omits empty directories; validation treats absent `hauptprozesse/` or `vorgaenge/` collections as empty. Use `02_protocol/impacts-architect/references/formwahl.md#data-kinds` for stage authority and candidate placement. An empty valid workspace is not an executable process. The following rules apply to selected Core Hauptprozess/Vorgang contracts under `02_protocol/impacts-architect/references/formwahl.md#tooling-stop`.

Hauptprozess and Vorgang layouts live in `02_protocol/binding.md#hauptprozess-tree-rules`. `analyse/`, `capabilities/`, `grundlagen/` and `records/` appear only with content.

```text
<workspace>/
├── CONTEXT.md                         # init: router and protocol pin
├── hauptprozesse/                      # init
├── vorgaenge/                          # init
├── analyse/                           # first capture
├── capabilities/                      # earned reusable operation
├── grundlagen/                        # foundations no single step owns
└── records/                           # first record
```

`analyse/` appears with the first capture; `init` does not create it. Each record kind has its own folder under `records/` and starts as one table; once a subject earns its own folder, the table moves into the kind's `CONTEXT.md`; a workspace with one record kind may keep its table directly in `records/` (`02_protocol/impacts-architect/references/formwahl.md#folder-structure-by-form`). Use `grundlagen/` only for foundations no single step owns.

## Tree clearance and imports

Clearance line shape:

`hauptprozess:<slug> cleared for real work: human:<id>, <YYYY-MM-DD>, git-tree:<oid>, tested by vorgang:<id>[, ...]`

Keep a superseded line struck through. Agents never write a clearance line. The responsible person writes it in their own commit or dictates and confirms it. The line authenticates nobody; Core does not check it.

Keep one import line per imported tree here, beside its clearance lines:

`Imported <hauptprozess|capability>:<slug>: source repository <repository>, commit <commit>, tree git-tree:<oid>, source protocol <Fachrepo protocol pin>`

Apply `02_protocol/impacts-method.md#scale` for first import or reviewed takeover. This record stays outside the imported tree; Core does not check it.

## Operating contract

1. For Core Vorgänge, the workspace root is the Git root.
2. Design a Hauptprozess at the home selected by `02_protocol/impacts-architect/references/formwahl.md#data-kinds`: `02_protocol/binding.md#hauptprozess-tree-rules` supplies the layout and its rules; `impacts template <kind>` supplies each `CONTEXT.md`. Import another repository's Hauptprozess only by the procedure in `02_protocol/impacts-method.md#scale`; localization is a new revision.
3. Before opening a real Vorgang, find a clearance line below naming the current Hauptprozess tree. Without one, ask the responsible customer and open nothing. Mark a synthetic test subject "synthetic test case".
4. Run Vorgänge under `02_protocol/binding.md#execution` of the pinned release.

5. For required Core conformance, run `impacts validate` on the selected scope. Apply the Core boundary (`02_protocol/ontology.md#enforcement-and-completion`).
6. Under the Core boundary in item 5, the bound Arbeitsschritt body supplies the prompt and names tool operations, versions, parameters, permitted effects and checks. The configured harness loads declared inputs, executes permitted work and retains actual output evidence under `02_protocol/impacts-method.md#compose-an-arbeitsschritt` and `02_protocol/binding.md`.
