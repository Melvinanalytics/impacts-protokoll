---
type: arbeitsschritt
id: arbeitsschritt:pruefen
eingaben:
  - input/revised-request.md
ausgaben:
  - output/ergebnis.md
pruefung: Decision follows the revised request
gate: human
routen:
  freigegeben: end:freigegeben
  abgelehnt: arbeitsschritt:start
---

# Updated current Application definition
