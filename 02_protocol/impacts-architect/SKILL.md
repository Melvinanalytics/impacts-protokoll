---
name: impacts-architect
description: Turn an observed customer process into an IMPACTS Application (one Hauptprozess with embedded Leistung, Teilprozesse, Arbeitsschritte with routes and human gates), restructure an existing customer folder or repository into an IMPACTS workspace, or import an approved Application from a Fachrepo. Use when someone wants to ingest, map, allocate or declare a process, "apply IMPACTS", "make this an Application", migrate a repo into a workspace, or onboard a customer. Every result must pass impacts validate.
---

# IMPACTS Architect

This skill produces files the core validates: an Application tree of `CONTEXT.md` files, a workspace router, and where needed `grundlagen/` and `records/`. It never executes an Arbeitsschritt, never writes `human:<id>`, and never introduces a schema, field or folder kind the core does not have.

Read the core before designing: `impacts template <kind>` prints the contract of every object, [impacts-method.md](../impacts-method.md) names the phases, [zuschnitt.md](references/zuschnitt.md) holds the cutting rules. Install: copy this folder to `.claude/skills/impacts-architect/`.

## Invariants

1. One Application holds one Hauptprozess with one embedded Leistung. Two Leistungen mean two Applications.
2. Arbeitsschritte own their routes, the Hauptprozess owns the entry, every step reaches a named end.
3. The Application tree holds only `CONTEXT.md` files. Reference material lives in `grundlagen/`, customer instances in `records/`, code in dependencies.
4. The workspace root is the git root. A Vorgang binds a committed Application tree.
5. `gate: human` marks an authority, risk or legal boundary and nothing else. `customer_touchpoint` marks where the customer is in the interaction.
6. Factory and run stay apart: no Vorgang changes the Application.
7. Every observed claim carries an evidence label and stays `reported` until the customer confirms it.
8. `impacts validate .` runs before every commit.

## Choose a mode

- A process described in conversation, no folder yet: Build mode.
- An existing customer folder, repository or vault: Restructure mode, then Build mode for each Application it hides.
- An approved Application in a Fachrepo: Import mode.

## Build mode

Identify → Minimize → Perfect → Augment → Construct → Test → Scale, as a procedure.

**Identify.** Interview a few questions at a time and write one [ist-prozess.md](templates/ist-prozess.md) per observed process into `grundlagen/ist-prozesse/`:

- What leaves the process, and who pays for it? That is the Leistung: `ergebnis`, `kennzahl`, `abnahme`.
- Walk me through one run. Where do you stop and check before you continue? Those pauses are human gates and Teilprozess boundaries.
- What stays the same every run, and what is new each time? Stable material goes to `grundlagen/`, the rest is Vorgang input.
- Who outside the firm is in the room? Those are customer touchpoints, `standard` or `sacred`.
- What breaks if this step is wrong, and would you notice? That feeds the automation boundary.

Then fill the Application body from its template: Markttopologie, Wertfluss, Zielgröße und Guardrails, Touchpoints, Automationsgrenze. Name the constraint, the step with the lowest throughput, and what would falsify that claim.

**Minimize.** Strike every observed step that moves neither the Kennzahl of the Leistung nor a guardrail: handoffs between departments, waits that exist for the calendar, duplicate capture, org-chart roles, working-hour logic. List what you struck under Wertfluss in the Application body; the customer sees what changed.

**Perfect.** Cut with [zuschnitt.md](references/zuschnitt.md): Teilprozesse at closed context sections, Arbeitsschritte at one job each, routes named by the outcome of `pruefung`, one `end:<slug>` per terminal outcome including the negative ones, waits as `wartend` states, loops with an exit.

**Augment.** Decide the execution form per Arbeitsschritt: deterministic transformation goes to code or a Capability and is named in the body as a dependency; variable language and context go to the model; judgement, authority and customer interaction stay human, as gate or touchpoint. The boundary table in zuschnitt.md decides.

**Construct.** `impacts template <kind>` for every object, filled from the captures, under `applications/<slug>/`. `impacts validate applications/<slug>` until exit 0. Commit. `git rev-parse HEAD:applications/<slug>` is the revision new Vorgänge bind.

**Test.** Run one representative Vorgang with the harness the way the core's cold walk does: open the entry step, `impacts hash` the inputs, advance, stop at the gate. Compare against the observed baseline: Kennzahl, guardrails, failure cases. A leading indicator stays `hypothesis` until observed runs support it.

**Scale.** Commit the tested revision. New Vorgänge bind it; running Vorgänge keep theirs.

## Restructure mode

1. Inventory, touch nothing. List the tree. Per area: what it is, when last touched, what refers to it.
2. Find the hidden Applications. What is the repeating unit, where does work enter, where does it leave. Interview the folder the way you would interview the person.
3. Classify every file into one role and its home:

| Role | Home |
|---|---|
| Router: identity and routing | root `CONTEXT.md`, the body `impacts init` writes |
| Application: how a step works | `applications/<slug>/…/CONTEXT.md` |
| Grundlage: stable reference, rules, assets, rights | `grundlagen/` |
| Vorgang-Artefakt: input or output of one run | `vorgaenge/<slug>/arbeitsschritte/<step>/<versuch>/input` or `output` |
| Werkzeug: code that produces artefacts | `tools/` or `src/` as a foreign dir; an external tool becomes a pinned dependency |
| Tot: superseded, duplicate, unreferenced | delete after step 4; git history keeps it, no archive folder |

4. Reference check before any move: in-repo links, sibling paths, symlinks, and consumers outside the repo such as scripts, jobs and other repositories. Ask the owner for the outside ones. A file with a live referrer is held, or moved together with its referrers in one change.
5. Migration map for human approval: old path, new path, role, referrers found.
6. Migrate by copy, verify, remove: copy, compare file count and hashes, only then remove. Check case-folded destination collisions first.
7. Build mode for every Application found, then `impacts validate .` and the walk test.

## Import mode

An approved Application arrives as a byte copy, as stated under Scale in impacts-method.md:

```bash
git -C <fachrepo> archive <commit>:applications/<slug> | tar -x -C applications/<slug>
git commit -m "import applications/<slug> from <fachrepo>@<commit> (tree <oid>)"
```

`git rev-parse HEAD:applications/<slug>` must equal the Fachrepo's oid; that is the proof of origin. Never edit the imported tree; customer overrides go to `grundlagen/`. Pin the Fachrepo's package at the same commit in the customer's dependency manifest, so process and code share one revision.

## Walk test

A cold agent with no memory:

1. Open the root `CONTEXT.md`. Can it say where it is and how to advance a Vorgang from this one file?
2. `impacts validate .` returns 0.
3. Open `vorgaenge/<slug>/CONTEXT.md`. The current step is the last Laufpfad entry. Open that step's `CONTEXT.md`: inputs, outputs, `pruefung`, routes and human check are all named.
4. Every Application body section holds the customer's facts, each labelled `verified`, `reported`, `hypothesis` or `open`.
5. Token check: router plus one Arbeitsschritt plus its inputs stay within 2k to 8k tokens.

If a step fails, move or split files. Do not explain more.

## Guardrails

- No Application for a process done twice. The ladder runs chat, saved prompt, Application.
- Three independent occurrences make a Teilprozess pattern. One complaint is a gripe.
- Stopp-Frage before any new term, field, folder kind or schema: name the existing structure that already does it.
- Never write `human:<id>`. The human writes `freigabe`; the agent prepares the evidence.
- The customer confirms the Application before its first real Vorgang. Until then every claim in it is `reported`.
