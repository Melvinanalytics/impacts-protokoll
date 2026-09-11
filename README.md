# IMPACTS Protocol

IMPACTS is a small public contract for file-native customer work. It designs work from the prerequisites of an accepted result, then represents it as human-readable Applications and revision-bound runs. HP/TP/AS keeps scope and handoffs visible; permitted preparation can proceed when its inputs and authority are available. See [Work from prerequisites](02_protocol/impacts-method.md#work-from-prerequisites) for the boundary between useful initiative, declared routes and human decisions.

Start with the [protocol router](02_protocol/CONTEXT.md). The [five schemas](02_protocol/schemas/) define machine contracts; the [complete-path invariant](02_protocol/invariants/complete-process-paths.md) defines route closure. The [method](02_protocol/impacts-method.md) and [Capability contract](02_protocol/capabilities.md) own work design and execution boundaries.

## Start with your task

| You have… | Start here | Expected next result |
|---|---|---|
| Notes, files or an undocumented business | [Form selection](02_protocol/impacts-architect/references/formwahl.md) | Place known facts and open questions; do not invent a confirmed process. |
| A bounded, repeatable result to deliver | [Build method](02_protocol/impacts-method.md) | One HP/TP/AS definition with inputs, checks and routes. |
| An existing run to continue | Its `vorgaenge/<id>/CONTEXT.md`, then its bound Application and current step | Required input, permitted next action or a specific blocker; no redesign of history. |
| A runnable, inspectable offer example | [Offer walk](06_evaluations/offer-walk/CONTEXT.md) | Checked draft, retained files and a pending human decision; optional downstream-capacity comparison. |
| A numerical decision or missing input | [Computation example](06_evaluations/computation-walk/CONTEXT.md) | A conditional result or focused question, not an invented business rule. |

For a new developer checkout, use Python 3.11+ and Git on `PATH`. Local checks cover Python 3.11 and 3.14 on macOS; other platforms require their own verification. Use an isolated environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e . pytest
```

The commands below inspect or initialize files; they do not execute customer work.

## Working language

The active protocol and technical reference are English-first. German customer work uses German instructions, drafts and decisions with the same machine keys. Start with the [German operator guide](02_protocol/translations/de.md) or the [language contract](02_protocol/language.md).

```bash
impacts init ../impacts-demo-de --language de
impacts template arbeitsschritt --language de
```

English is the default for newly generated material. Existing workspaces keep their agreed language. A language marker is an instruction; actual checks at the customer-use boundary establish the supported output. The [paired offer walk](06_evaluations/offer-walk/CONTEXT.md) demonstrates fixed German/English output and rejection before a human gate.

## Try one bounded result

```bash
python3 06_evaluations/offer-walk/run.py --language en --discovery --keep ../impacts-offer-demo
```

Expected final status: `PASS: handoff checked; human decision pending.` The `Artifacts:` line names the retained workspace. Open its `CONTEXT.md`, then `vorgaenge/angebot-001/CONTEXT.md` and the linked draft/report. The optional discovery case shows why increasing preparation from 6 to 18 cases per day can leave reviewed output at 6 and grow the downstream queue. Its assumptions, sensitivity and simulated decision stay in `grundlagen/discovery.md`; they establish no real approval or business improvement.

Use a new `--keep` path for each run. For takeover, follow the [Process Walk](02_protocol/impacts-architect/SKILL.md#walk-test); the [cold-walk writer](06_evaluations/cold-walk/check.py) is the executable reference for attempts and `laufpfad`. Real execution still needs the domain’s sources, configured harness and decision authority.

## Core boundary

```bash
impacts init ../impacts-demo
impacts validate ../impacts-demo
impacts template arbeitsschritt
impacts template application
```

Run these commands from the protocol checkout; the demo is created beside it so the checkout keeps its root-directory budget. Run `init` only for a new target: it refuses an existing directory. It creates no Git repository; initialize Git at the workspace root before versioning an Application. The initialized workspace is empty, not a runnable sample. Use the [cold walk](06_evaluations/cold-walk/CONTEXT.md) for an executed synthetic case, including real attempt files and their hashes.

`init` creates `CONTEXT.md`, `applications/` and `vorgaenge/`; the router body carries the operating contract for humans and harnesses. `validate` reads these files without changing them. Absent `applications/` or `vorgaenge/` collections count as empty, so an empty or Application-only workspace survives a Git clone. Present collections must be directories containing valid children; placeholder files such as `.gitkeep` are invalid. `template` prints the `CONTEXT.md` template of one core object with every schema field and the method context; `template application` prints the layout of the whole tree. `hash` computes the surface hash of one attempt, the same bytes the validator recomputes. Agent Harnesses execute work. Git versions Applications. Optional [Capabilities](02_protocol/capabilities.md) own bounded reusable research, analysis, transformation or calculation inside an Arbeitsschritt; they remain outside the Core.

## Model

The [Application template](02_protocol/templates/application.md#baum) owns the directory layout; `impacts template application` prints that same packaged source.

An Application is one Hauptprozess; its folder is the process name, its subfolders are the Teilprozesse and their subfolders the Arbeitsschritte. The role of every `CONTEXT.md` is its `type`; the generic role names appear only in the layout. Leistung is its embedded result contract. Arbeitsschritte own routes. A Vorgang derives its process and current step from the bound Application tree and Laufpfad. The workspace root is the Git repository root; a Vorgang binds only a committed Application tree.

## Design time

The skill in [02_protocol/impacts-architect](02_protocol/impacts-architect/SKILL.md) turns an observed customer process into an Application (Identify to Scale), restructures an existing customer folder into a workspace, or imports an approved Application from a Fachrepo. Use `02_protocol/impacts-architect/SKILL.md` from this protocol checkout. Keep the checkout and its sibling references together; a standalone copy into a skill directory is not a complete installation. If a skill directory exposes this checkout through a symlink, resolve the real skill path before following its relative links.

## Example

[06_evaluations/cold-walk/beispiel](06_evaluations/cold-walk/beispiel/applications/prueffall/) holds a synthetic Application with a loop, a wait, a human gate and a small calculation Capability. The cold walk runs it through one complete Vorgang with the public API and locally proves Application-driven source and handoff resolution, revision-bound Capability execution, Gate preflight and executable transport into a second repository while preserving the Core boundary.

## Verification

```bash
python3 -m pytest -q
python3 06_evaluations/complexity-budget/check.py
PYTHONPATH=src python3 06_evaluations/cold-walk/check.py
python3 06_evaluations/offer-walk/run.py --language de
python3 06_evaluations/offer-walk/run.py --language en
```

The public repository contains the protocol, examples, implementation and tests. Private planning, specifications, research, audits and handovers are excluded from distribution.

## Contributing

Use [Issues](https://github.com/Melvinanalytics/impacts-protokoll/issues) for reproducible problems or bounded proposals, and [pull requests](https://github.com/Melvinanalytics/impacts-protokoll/pulls) for changes. Include the source revision, expected behavior, actual result and a small synthetic example. Keep customer records, credentials and private working notes out of public submissions.

Read [AGENTS.md](AGENTS.md) and the nearest `CONTEXT.md`, then run the verification commands above. Keep the Core small, preserve machine identifiers and update a rule at its existing home. English is authoritative; changes affecting German working surfaces must update their translations and pass the paired checks in [language.md](02_protocol/language.md). Report unexecuted checks explicitly. Passing tests is separate from the release decision.

The Python distribution supplies the CLI, schemas and working templates. Use the complete GitHub checkout for the Architect, method, examples and repository tests.

## License

Licensed under the [Apache License 2.0](LICENSE).
