---
type: vorgang
protocol: v0.4.0
id: vorgang:approval-001
hauptprozess_revision: git-tree:@HAUPTPROZESS_REVISION@
laufpfad:
- arbeitsschritt_ref: arbeitsschritt:start
  nummer: 1
  status: aktiv
  gelesen:
  - eingabe: input/auftrag.md
    pfad: vorgaenge/approval-001/_quellen/export.json
    revision: git-commit:@SOURCE_COMMIT@
    sha256: sha256:31a05711bcf05385b0f833f757b51af806272488509ca7289d2efb6e386dc15a
  - eingabe: input/auftrag.md
    pfad: vorgaenge/approval-001/_quellen/export-herkunft.md
    revision: git-commit:@SOURCE_COMMIT@
    sha256: sha256:a10098d9a6d23714d432cc54edc963304db5fc955280d97c062e27194c63444c
---

Synthetic external export capture.
