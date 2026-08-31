# IMPACTS Protocol

IMPACTS is a small public contract for file-native customer work. It turns an optimized process definition into human-readable Applications and revision-bound runs.

Current authority: [Minimaler IMPACTS-Core V1](docs/superpowers/specs/2026-08-30-minimal-core-design.md).

## Core boundary

```bash
impacts init /tmp/impacts-demo
impacts validate /tmp/impacts-demo
```

`init` creates `CONTEXT.md`, `applications/` and `vorgaenge/`. `validate` reads these files without changing them. Agent Harnesses execute work. Git versions Applications. Capabilities own tools and deterministic calculations.

## Model

```text
Application
└── Hauptprozess { Leistung }
    └── Teilprozess
        └── Arbeitsschritt

Vorgang
├── application_revision
└── laufpfad
```

One Application contains one Hauptprozess. Leistung is its embedded result contract. Arbeitsschritte own routes. A Vorgang derives its process and current step from the bound Application tree and Laufpfad.

## Verification

```bash
python3 -m pytest -q
python3 06_evaluations/complexity-budget/check.py
PYTHONPATH=src python3 06_evaluations/cold-walk/check.py
```

Public distribution follows [public-release-gate.md](docs/release/public-release-gate.md).

## License

Licensed under the [Apache License 2.0](LICENSE).
