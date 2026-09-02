# Protocol routing

This area owns five static schemas, one template per object, the complete-path invariant and the architect skill that turns observed work into Applications.

## Language

**Leistung** is the embedded, ID-less result contract of one Hauptprozess. It names the valued end state, metric and acceptance conditions.

**Hauptprozess** is the Aggregate Root of one Application. It ends when its Leistung is achieved.

**Teilprozess** is one closed context section of its Hauptprozess.

**Arbeitsschritt** is one ICM stage. It declares inputs, outputs, verification and routes. Its Markdown body explains processing.

**Vorgang** is one concrete run of the Application revision named by its Git tree. Its Laufpfad is the only run-state authority.

Use [impacts-method.md](impacts-method.md) to turn observed work into an optimized Application. Start every `CONTEXT.md` from its template in [templates/](templates/) or `impacts template <kind>`; the frontmatter names every schema field, the body carries the method context. Read [complete-process-paths.md](invariants/complete-process-paths.md) before changing process topology. Normative architecture: [minimal-core-design.md](../docs/superpowers/specs/2026-08-30-minimal-core-design.md).

To ingest an observed process, restructure an existing customer folder or import an Application from a Fachrepo, use the skill in [impacts-architect/SKILL.md](impacts-architect/SKILL.md).
