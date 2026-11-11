---
type: arbeitsschritt
id: arbeitsschritt:pruefen
eingaben:
  - input/auftrag.md
ausgaben:
  - output/ergebnis.md
gate: human
routen:
  freigegeben: end:freigegeben
  abgelehnt: arbeitsschritt:start
---

# Review request

Synthetic W6 case: w6-second-atomic-error; hauptprozesse/approval/produktion/pruefen/CONTEXT.md.
