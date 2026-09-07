# Protocol routing

This area owns five static schemas, one template per object, the complete-path invariant and the architect skill that turns observed work into Applications.

## Language

**Leistung** is the embedded, ID-less result contract of one Hauptprozess. It names the valued end state, metric and acceptance conditions.

**Hauptprozess** is the Aggregate Root of one Application and its root `CONTEXT.md` (`applications/<slug>/CONTEXT.md`). It ends when its Leistung is achieved.

**Teilprozess** is one closed context section of its Hauptprozess, a subfolder named after it.

**Arbeitsschritt** is one ICM stage, a subfolder of its Teilprozess named after it. It declares inputs, outputs, verification and routes. Its Markdown body explains processing.

**Vorgang** is one concrete run of the Application revision named by its Git tree. Its Laufpfad is the only run-state authority.

**Capability** is optional, reusable processing inside an Arbeitsschritt. Public authority: [capabilities.md](capabilities.md).

Use [impacts-method.md](impacts-method.md) to turn observed work into an optimized Application. See the tree with `impacts template application` (the Schablone) and start every `CONTEXT.md` from its template in [templates/](templates/) or `impacts template <kind>`; the frontmatter names every schema field, the body carries the method context. Read [complete-process-paths.md](invariants/complete-process-paths.md) before changing process topology. Normative architecture: [minimal-core-design.md](../docs/superpowers/specs/2026-08-30-minimal-core-design.md).

For customer initialization or knowledge topology, start with the [Architect's form selection](impacts-architect/SKILL.md#form-selection). Use that skill also to ingest an observed process, restructure an existing customer folder or import an Application from a Fachrepo. It enters the seven-phase Application method only after selecting a Pipeline.
