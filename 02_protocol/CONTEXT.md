# Protocol routing

This area owns static method contracts, schemas and invariants.

## Language

**Leistung** is one repeatable owed result. It has a reciprocal 1:1 reference to one Hauptprozess.

**Hauptprozess** is the reusable process definition that produces one Leistung. It owns its Teilprozesse and complete process paths.

**Teilprozess** is a closed section of one Hauptprozess. It owns its Arbeitsschritte.

**Arbeitsschritt** is one ICM stage with declared inputs, processing, outputs, verification and gate.

**Vorgang** is one complete concrete execution of one Hauptprozess. Its customer files live under `06_vorgaenge/<id>/`.

Read [complete-process-paths.md](invariants/complete-process-paths.md) before changing process topology. The current architecture is [contract-only-core-design.md](../docs/superpowers/specs/2026-08-26-contract-only-core-design.md).
