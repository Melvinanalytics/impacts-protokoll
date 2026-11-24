---
type: workspace
protocol: v0.7.0
---

Working language: en

# IMPACTS Workspace

Customer work uses this working language under `02_protocol/language.md`. Every `02_protocol/` path here resolves against the protocol source and revision recorded below, not against this customer tree.

## Source, harness and homes

Before applying a protocol route, record the source, revision and Architect entry by the source's root `README.md`, “Version and entry points”. Missing after `init`? Identify the package with `python -m pip show impacts-protocol` and fetch the complete source from [releases](https://github.com/Melvinanalytics/impacts-protokoll/releases); the package version alone names no exact revision. On resumption, use what is recorded here. Changes to instructions or working language follow `02_protocol/impacts-method.md#maintain-agent-instructions`.

- Complete source location (release pin is in frontmatter): `<path or URL>`
- Source commit and local changes: `<commit and each local change>`
- Architect entry: `<resolvable path of 02_protocol/impacts-architect/SKILL.md>`
- Harness and setup reference, when Core execution is selected: `<harness and setup reference, or not selected>`
- Domain homes: `<link and purpose of each home>`
- Value chain, with more than one Hauptprozess (`02_protocol/impacts-architect/references/formwahl.md#composition`): `<per Hauptprozess: Leistung and Auslöser links, unit, what opens it, who uses its end>`

`Ablage: <name> <location or system>, <access rule home>`: one unindented body line per external store.

`Form: <folder>/ <form> per <unit>`: one unindented body line per top-level folder (`02_protocol/impacts-architect/references/formwahl.md#folder-structure-by-form`).

Select each home by form selection; keep facts at their source. Given products or services, apply `02_protocol/impacts-method.md#reverse-engineer-a-product-or-service` before assuming a Pipeline. Capture or change domain meaning under `02_protocol/ontology.md#author-or-change`; apply it under `02_protocol/ontology.md#use`. For Capabilities from a Fachrepo or another home, link its responsible router under Domain homes and apply `02_protocol/impacts-architect/references/formwahl.md#capability-orientation`.

## Routing

Separate work from read-only questions (`02_protocol/impacts-method.md#load-context-locally-first`). Replace placeholder rows only with populated links; leave unpopulated areas out.

### Work (creates or changes output)

| Intent | Open | Additional, only when triggered | Output and target | Check |
|---|---|---|---|---|
| `<recurring job without Core Arbeitsschritt>` | `<link to owning file#job-section>` | `<when <observable trigger>: <link to the source then needed>>` | `<artifact and target path>` | `<observable check>` |
| `<selected Core Pipeline>` | `<link to hauptprozesse/<slug>/CONTEXT.md>` | — | `<Vorgang output>` | `impacts validate` |

The standard case reads only Open; "Additional" names a trigger and the source it then needs, so whoever works the standard case knows what to skip. Each level router follows `impacts template ebene`.

### Read-only questions

| Question about | Open | Stop condition |
|---|---|---|
| `<foundations, rules, offerings>` | `<link to grundlagen/CONTEXT.md>` | `<cited rule and evidence status>` |
| `<cases, commitments, subjects>` | `<link to records/CONTEXT.md>` | `<cited record and as-of time>` |
| `<captures, candidates>` | `<link to analyse/CONTEXT.md>` | `<cited analysis and open gaps>` |

## Setup

`init` creates `AGENTS.md`, this router, `hauptprozesse/`, `vorgaenge/`, `.gitattributes` (`* -text`, so a checkout keeps bound bytes and hashes) and a `.gitignore` for system and office leftovers. Absent `hauptprozesse/` or `vorgaenge/` count as empty. An empty valid workspace is not an executable process.

Add `analyse/`, `capabilities/`, `grundlagen/` and `records/` only with content. Place new or moved files by `02_protocol/impacts-architect/references/formwahl.md#folder-structure-by-form` and `02_protocol/impacts-architect/references/formwahl.md#data-kinds`. Name domain folders by `02_protocol/impacts-architect/references/zuschnitt.md#naming`; Core layouts, slugs and identities follow `02_protocol/binding.md#hauptprozess-tree-rules`.

## Tree clearance and imports

Clearance line shape:

`hauptprozess:<slug> cleared for real work: human:<id>, <YYYY-MM-DD>, git-tree:<oid>, tested by vorgang:<id>[, ...]`

Only the responsible person writes it, in their own commit or by dictating and confirming it. Strike through a superseded line. The line authenticates nobody; Core does not check it.

One import line per imported tree, outside that tree; first import and reviewed takeover follow `02_protocol/impacts-method.md#scale`:

`Imported <hauptprozess|capability>:<slug>: source repository <repository>, commit <commit>, tree git-tree:<oid>, source protocol <Fachrepo protocol pin>`

## Operating contract

1. For Core Vorgänge, the workspace root is the Git root.
2. Design a Hauptprozess at its selected home; `impacts template <kind>` supplies each `CONTEXT.md`. Import from another repository only by `02_protocol/impacts-method.md#scale`; localization is a new revision.
3. Before opening a real Vorgang, find a clearance line naming the current Hauptprozess tree. Without one, ask the responsible customer and open nothing. Mark a synthetic test subject "synthetic test case".
4. Run Vorgänge under `02_protocol/binding.md#execution` of the pinned release.
5. Run `impacts validate` for required Core conformance. It checks structure only (`02_protocol/ontology.md#enforcement-and-completion`) and replaces no domain check or human decision.
6. The bound Arbeitsschritt body supplies the prompt, operations, permitted effects and checks; the configured harness loads declared inputs and retains actual output evidence (`02_protocol/impacts-method.md#compose-an-arbeitsschritt`).
7. Keep each recurring job without a Core Arbeitsschritt in one section of its owning file (`02_protocol/impacts-method.md#maintain-agent-instructions`).
8. Agents never invent an `Ablage`, write a clearance line or create a human decision.
9. When ordinary work shows a demonstrated defect or consequential repeated friction, open the recorded Architect entry (`Choose a mode`) and apply `02_protocol/impacts-method.md#reviewed-correction`.
