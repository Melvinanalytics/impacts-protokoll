---
type: vorgang
protocol: v0.4.0
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
    sha256: sha256:4c628ca5445dfec15da046b3b96735df47950fb01b2c33c17050db8978c0174f
  geschrieben:
  - pfad: vorgaenge/approval-001/start/001/output/ergebnis.md
    sha256: sha256:7e32f8d5d966b6fc20727d012729337bb4b815d4b3932d187f4d29e4a1f26172
- arbeitsschritt_ref: arbeitsschritt:pruefen
  status: abgeschlossen
  gewaehlte_route: freigegeben
  freigabe:
    by: human:fixture-reviewer
    at: '2026-08-30T10:00:00+02:00'
  nummer: 1
  gelesen:
  - eingabe: input/auftrag.md
    pfad: records/approval-001/pruefen/001/auftrag.md
    revision: git-commit:@SOURCE_COMMIT@
    sha256: sha256:4529668bbb2a094fd848dccc30487be6850c89145a11ed0f63b4730c588cbfda
  geschrieben:
  - pfad: vorgaenge/approval-001/pruefen/001/output/ergebnis.md
    sha256: sha256:396c29fd1351799146e59b7a4dfffb3df8929bbc74a36a0f9687193d1908b7bf
---

# Coordinated file and record rewrite
