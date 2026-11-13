---
type: vorgang
protocol: v0.5.0
id: vorgang:restart
hauptprozess_revision: git-tree:@HAUPTPROZESS_REVISION@
vorgaenger: vorgaenge/approval-001/CONTEXT.md
laufpfad:
- arbeitsschritt_ref: arbeitsschritt:pruefen
  nummer: 1
  status: aktiv
  gelesen:
  - eingabe: input/auftrag.md
    pfad: records/approval-001/start/001/auftrag.md
    revision: git-commit:@SOURCE_COMMIT@
    sha256: sha256:ac62571dcadb11f2406d2d4277de2ee1b567a998bc1bf2bc9f7130db57a75438
---

Synthetic restart.

Synthetic fixture identity: run-predecessor-ended.
