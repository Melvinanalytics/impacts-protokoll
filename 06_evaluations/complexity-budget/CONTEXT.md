---
title: Komplexitätsbudget
evidence_status: reported
---

# Komplexitätsbudget

Deterministisches Gate gegen Komplexitätsausbruch. `budget.yaml` hält Grenzen und Attributionsdaten. `check.py` misst den Arbeitsbaum. Die menschlich bestätigte V0.2-Grenze `5/5/15` bildet den einmaligen Bootstrap. Danach liest der Checker seine Vergleichsgrenze aus dem letzten erreichbaren öffentlichen Release-Tag. Ein Tag am aktuellen `HEAD` wird übersprungen, damit auch der Post-Tag-Check gegen den vorherigen Stand prüft.

Eine Erhöhung braucht `approved_by: human:<id>` samt Begründung im Budget. Das Feld dokumentiert die Attribution und authentifiziert sie nicht. Geschütztes `main` und geschützte Release-Tags sichern die Baseline gegen Selbständerung. Regeln und Quellen stehen im Einfachheitsvertrag unter `AGENTS.md`.
