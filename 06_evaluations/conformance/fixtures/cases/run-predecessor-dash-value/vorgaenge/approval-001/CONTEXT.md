---
type: vorgang
protocol: v0.8.0
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
    sha256: sha256:cac877058c5c187f8f1f62a1a4c9aed4a0f0f3b6b9ccb0ac25a1215eb7b89b31
---

Synthetic completed predecessor whose bound Arbeitsschritt holds `---` inside a frontmatter value; its successor must read the route.

Synthetic fixture identity: run-predecessor-dash-value.
