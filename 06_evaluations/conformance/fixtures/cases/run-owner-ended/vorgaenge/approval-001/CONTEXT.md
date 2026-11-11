---
type: vorgang
protocol: v0.4.0
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
    sha256: sha256:df2bd5ef09c69054ed780e24041fa9fbd20c9c2708c5fc8ca5782e88871e286e
---

Synthetic closed producer with unopened successor.

Synthetic fixture identity: run-owner-ended.
