# IMPACTS Protocol

IMPACTS is a small public contract for file-native customer work. It turns an optimized process definition into human-readable Applications and revision-bound runs.

Current authority: [Minimaler IMPACTS-Core V1](docs/superpowers/specs/2026-08-30-minimal-core-design.md), extended by [Ausführbarer IMPACTS-Core V0.3](docs/superpowers/specs/2026-09-02-executable-core-design.md).

## Core boundary

```bash
impacts init /tmp/impacts-demo
impacts validate /tmp/impacts-demo
impacts template arbeitsschritt
impacts template application
impacts hash /tmp/impacts-demo/vorgaenge/demo-001/start/001 input/auftrag.md
```

`init` creates `CONTEXT.md`, `applications/` and `vorgaenge/`; the router body carries the operating contract for humans and harnesses. `validate` reads these files without changing them. `template` prints the `CONTEXT.md` template of one core object with every schema field and the method context; `template application` prints the Schablone of the whole tree. `hash` computes the surface hash of one attempt, the same bytes the validator recomputes. Agent Harnesses execute work. Git versions Applications. Optional [Capabilities](02_protocol/capabilities.md) own bounded reusable research, analysis, transformation or calculation inside a workstep; they remain outside the Core.

## Model

```text
applications/<hauptprozess>/CONTEXT.md                     Hauptprozess { Leistung }
applications/<hauptprozess>/<teilprozess>/CONTEXT.md        Teilprozess
applications/<hauptprozess>/<teilprozess>/<schritt>/CONTEXT.md   Arbeitsschritt

vorgaenge/<vorgang>/CONTEXT.md                             application_revision, laufpfad
vorgaenge/<vorgang>/<schritt>/<versuch>/input|output       one attempt
```

An Application is one Hauptprozess; its folder is the process name, its subfolders are the Teilprozesse and their subfolders the Arbeitsschritte. The role of every `CONTEXT.md` is its `type`; the generic role names appear only in the Schablone. Leistung is its embedded result contract. Arbeitsschritte own routes. A Vorgang derives its process and current step from the bound Application tree and Laufpfad. The workspace root is the Git repository root; a Vorgang binds only a committed Application tree.

## Design time

The skill in [02_protocol/impacts-architect](02_protocol/impacts-architect/SKILL.md) turns an observed customer process into an Application (Identify to Scale), restructures an existing customer folder into a workspace, or imports an approved Application from a Fachrepo. Copy the folder to `.claude/skills/impacts-architect/` to install it.

## Example

[06_evaluations/cold-walk/beispiel](06_evaluations/cold-walk/beispiel/applications/prueffall/) holds a synthetic Application with a loop, a wait, a human gate and a small calculation Capability. The cold walk runs it through one complete Vorgang with the public API and locally proves Application-driven source and handoff resolution, revision-bound Capability execution, Gate preflight and executable transport into a second repository while preserving the Core boundary.

## Verification

```bash
python3 -m pytest -q
python3 06_evaluations/complexity-budget/check.py
PYTHONPATH=src python3 06_evaluations/cold-walk/check.py
```

Public distribution follows [public-release-gate.md](docs/release/public-release-gate.md).

## License

Licensed under the [Apache License 2.0](LICENSE).
