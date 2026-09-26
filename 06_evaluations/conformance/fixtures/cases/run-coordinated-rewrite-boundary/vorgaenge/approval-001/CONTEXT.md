---
type: vorgang
id: vorgang:approval-001
application_revision: git-tree:@APPLICATION_REVISION@
laufpfad:
  - arbeitsschritt_ref: arbeitsschritt:start
    versuch: 1
    status: abgeschlossen
    eingabe_hash: sha256:61884fae76e221a4f3ea6056bd8a034328e87c5ce0cb7e83b86dc7c82f952ff8
    gewaehlte_route: weiter
    ausgabe_hash: sha256:2a18b135c295b71c3eb69bef077867478e489dc3bc1af7058b47d467ff96a5c5
  - arbeitsschritt_ref: arbeitsschritt:pruefen
    versuch: 1
    status: abgeschlossen
    eingabe_hash: sha256:35ea69cce8b2b5027f0d124dc08e5081f097a42b73e2b040f9899722c07a85a2
    gewaehlte_route: freigegeben
    ausgabe_hash: sha256:cc3fa1f4b85da095a2e06a1d619e544c5bbe7bf0d85a9d1f92e5d9e51f4c3b2e
    freigabe:
      by: human:fixture-reviewer
      at: "2026-08-30T10:00:00+02:00"
---

# Coordinated file and record rewrite
