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
    sha256: sha256:31f7d20687173e164c82e760340e60004b23a3b21c477157eee52382e08e67cf
- arbeitsschritt_ref: arbeitsschritt:pruefen
  status: aktiv
  nummer: 1
  gelesen:
  - eingabe: input/auftrag.md
    pfad: records/approval-001/pruefen/001/auftrag.md
    revision: git-commit:@SOURCE_COMMIT@
    sha256: sha256:6cab8f01aa06d5534e9bca751a46f952dc65cb44612610520ed742cd70d3758b
---

# Pending gate

Synthetic fixture identity: run-owner-end-continues.
