# Public-release gate

Publish only from a clean export of the sanitized working tree with fresh public history. Keep the existing private Git history private because superseded commits can retain removed operational material.

Before publication:

1. Run the full test suite and cold walk.
2. Scan tracked content for operational names, identifiers, authority assignments, pilot claims, and payload fragments.
3. Confirm every example is synthetic.
4. Create a fresh repository or source archive from the sanitized tree. Exclude the private `.git` directory.
5. Run the full test suite in the fresh public history. The complexity checker must use its reviewed portable baseline because the private baseline commit is absent by design.
6. Inspect the resulting public artifact and record release approval.

History rewriting is outside this gate. The clean export provides the publication boundary.
