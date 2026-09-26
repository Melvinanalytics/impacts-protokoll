---
type: vorgang
id: vorgang:approval-001
application_revision: git-tree:@APPLICATION_REVISION@
laufpfad:
  - arbeitsschritt_ref: arbeitsschritt:start
    versuch: 1
    status: abgeschlossen
    eingabe_hash: sha256:986ffc4749acc3e8105df9a9f03282cacd035ad7740e2b96d4c3b5120d5067a0
    gewaehlte_route: weiter
    ausgabe_hash: sha256:2a18b135c295b71c3eb69bef077867478e489dc3bc1af7058b47d467ff96a5c5
  - arbeitsschritt_ref: arbeitsschritt:pruefen
    versuch: 1
    status: wartend
    eingabe_hash: sha256:35ea69cce8b2b5027f0d124dc08e5081f097a42b73e2b040f9899722c07a85a2
    wiedereinstieg:
      ausloeser: Supplier response
      continuation_ref: event:reply-001
---

# Waiting for response
