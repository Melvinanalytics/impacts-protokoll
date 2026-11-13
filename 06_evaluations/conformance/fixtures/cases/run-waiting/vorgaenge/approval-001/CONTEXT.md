---
type: vorgang
protocol: v0.5.0
id: vorgang:approval-001
hauptprozess_revision: git-tree:@HAUPTPROZESS_REVISION@
laufpfad:
- arbeitsschritt_ref: arbeitsschritt:start
  status: abgeschlossen
  gewaehlte_route: weiter
  nummer: 1
  gelesen:
  - eingabe: input/auftrag.md
    pfad: records/approval-001/start/001/auftrag.md
    revision: git-commit:@SOURCE_COMMIT@
    sha256: sha256:ac62571dcadb11f2406d2d4277de2ee1b567a998bc1bf2bc9f7130db57a75438
  geschrieben:
  - pfad: vorgaenge/approval-001/start/001/output/ergebnis.md
    sha256: sha256:7e32f8d5d966b6fc20727d012729337bb4b815d4b3932d187f4d29e4a1f26172
- arbeitsschritt_ref: arbeitsschritt:pruefen
  status: wartend
  wiedereinstieg:
    ausloeser: Supplier response
    continuation_ref: vorgaenge/approval-001/pruefen/001/output/draft.md
  nummer: 1
  gelesen:
  - eingabe: input/auftrag.md
    pfad: records/approval-001/pruefen/001/auftrag.md
    revision: git-commit:@SOURCE_COMMIT@
    sha256: sha256:4529668bbb2a094fd848dccc30487be6850c89145a11ed0f63b4730c588cbfda
---

# Waiting for response
