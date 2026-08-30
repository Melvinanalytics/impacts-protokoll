# IMPACTS Protocol

IMPACTS is a contract-only core for file-native customer workspaces. It defines process terms, folder conventions, schemas, static validation and an empty workspace template.

Start with [CONTEXT.md](CONTEXT.md). The current authority is [contract-only-core-design.md](docs/superpowers/specs/2026-08-26-contract-only-core-design.md).

## Core boundary

The Core owns two commands:

```bash
impacts init /tmp/impacts-demo --customer demo-kunde
impacts validate /tmp/impacts-demo
```

`init` creates an empty folder template. `validate` reads folders, IDs, references, hierarchy and schemas. Agent harnesses handle package checkout, tool calls and process execution.

Reference code lives in [`src/impacts_protocol/`](src/impacts_protocol/). Core checks live in [`06_evaluations/`](06_evaluations/).

Application, Expertise, Experience and Capability packages live in separate repositories. Customer workspaces contain customer-owned foundations, records, process provenance, concrete runs and derived views.

## Process model

- A `Leistung` is a repeatable owed result.
- One `Hauptprozess` produces exactly one `Leistung`.
- A `Teilprozess` belongs to one Hauptprozess.
- An `Arbeitsschritt` belongs to one Teilprozess.
- A `Vorgang` is one complete concrete Hauptprozess run.

The hierarchy is `Leistung 1:1 Hauptprozess → Teilprozess 1:n → Arbeitsschritt 1:n`.

## File graph

A file is a node. A stable ID supplies identity. A reference supplies an edge. Frontmatter supplies type. The enclosing folder supplies context. Obsidian, Graphviz and Neo4j exports under `99_ansichten/` remain derived views.

## Verification

```bash
python3 -m pytest -q
python3 06_evaluations/complexity-budget/check.py
PYTHONPATH=src python3 06_evaluations/cold-walk/check.py
```

Public distribution follows [public-release-gate.md](docs/release/public-release-gate.md).
