---
type: vorgang
protocol: v0.5.0
id: vorgang:approval-001
hauptprozess_revision: git-tree:@HAUPTPROZESS_REVISION@
laufpfad:
- arbeitsschritt_ref: arbeitsschritt:start
  status: aktiv
  nummer: 1
  gelesen:
  - eingabe: input/auftrag.md
    ablage: synthetic-external-store
    schluessel: external-object-one
    sha256: sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  - eingabe: input/auftrag.md
    ablage: another-synthetic-store
    schluessel: external-object-two
    sha256: sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
---

Synthetic external-store boundary: run-external-two-unverified.
