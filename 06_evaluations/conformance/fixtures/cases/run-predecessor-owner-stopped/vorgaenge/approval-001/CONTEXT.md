---
type: vorgang
protocol: v0.5.0
id: vorgang:approval-001
hauptprozess_revision: git-tree:@HAUPTPROZESS_REVISION@
laufpfad:
- arbeitsschritt_ref: arbeitsschritt:start
  status: abgebrochen
  freigabe:
    by: human:fixture-owner
    at: "2026-11-10T10:00:00+01:00"
  nummer: 1
  gelesen:
  - eingabe: input/auftrag.md
    pfad: records/approval-001/start/001/auftrag.md
    revision: git-commit:@SOURCE_COMMIT@
    sha256: sha256:ac62571dcadb11f2406d2d4277de2ee1b567a998bc1bf2bc9f7130db57a75438
  geschrieben:
  - pfad: vorgaenge/approval-001/start/001/output/ergebnis.md
    sha256: sha256:3033bc5da0922c70f25ac692462939c4414fa573ac999280ecba3460347b7b8f
---

Synthetic owner-stopped predecessor; a successor naming it must be rejected.

Synthetic fixture identity: run-predecessor-owner-stopped.
