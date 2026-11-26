---
type: vorgang
protocol: v0.8.0
id: vorgang:reader
hauptprozess_revision: git-tree:@HAUPTPROZESS_REVISION@
laufpfad:
- arbeitsschritt_ref: arbeitsschritt:start
  status: aktiv
  nummer: 1
  gelesen:
  - eingabe: input/auftrag.md
    pfad: records/approval-001/start/001/auftrag.md
    revision: git-commit:@SOURCE_COMMIT@
    sha256: sha256:ac62571dcadb11f2406d2d4277de2ee1b567a998bc1bf2bc9f7130db57a75438
  - eingabe: input/auftrag.md
    pfad: vorgaenge/retired/start/001/output/ergebnis.md
    sha256: sha256:7e32f8d5d966b6fc20727d012729337bb4b815d4b3932d187f4d29e4a1f26172
---

Synthetic reader whose producer Vorgang `retired` left the working tree.

Synthetic fixture identity: run-producer-vorgang-removed.
