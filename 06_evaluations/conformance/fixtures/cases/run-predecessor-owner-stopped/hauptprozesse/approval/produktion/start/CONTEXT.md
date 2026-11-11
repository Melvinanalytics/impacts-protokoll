---
type: arbeitsschritt
id: arbeitsschritt:start
eingaben:
  - input/auftrag.md
ausgaben:
  - output/owed-result.md
pruefung: Request fields are recorded
routen:
  weiter: arbeitsschritt:pruefen
  abbrechen: end:abgebrochen
---

# Record request

Synthetic owner termination before the owed job result exists.

Synthetic fixture identity: run-predecessor-owner-stopped.
