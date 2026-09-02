# Public-release gate

Publish only from a clean export of the sanitized working tree with fresh public history. Keep the existing private Git history private because superseded commits can retain removed operational material.

Before publication:

1. Run the full test suite and cold walk.
2. Scan tracked content for operational names, identifiers, authority assignments, pilot claims, and payload fragments.
3. Confirm every example is synthetic.
4. Create a fresh repository or source archive from the sanitized tree. Exclude the private `.git` directory.
5. Run the full test suite in the fresh public history. For V0.2, the complexity checker uses the human-attributed bootstrap in `budget.yaml`. Later releases read the prior public release tag.
6. Inspect the resulting public artifact and record release approval.

History rewriting is outside this gate. The clean export provides the publication boundary.

## Export allowlist

The public tree consists of exactly these paths from `main`:

```text
.gitignore  AGENTS.md  CONTEXT.md  LICENSE  README.md  pyproject.toml
02_protocol/  06_evaluations/  src/  tests/
docs/release/
docs/superpowers/specs/2026-08-30-minimal-core-design.md
docs/superpowers/specs/2026-09-02-executable-core-design.md
```

Everything else under `docs/` stays private: audits, research, plans, superseded specs and `docs/CONTEXT.md`. The root `CONTEXT.md` row that routes to the design record is dropped from the export. The export lands as one commit on a `release/v<version>` branch from `origin/main`; its message names the `main` commit it was cut from.
