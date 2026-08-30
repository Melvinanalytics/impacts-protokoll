---
title: Komplexitätsbudget
evidence_status: reported
---

# Komplexitätsbudget

Deterministisches Gate gegen Komplexitätsausbruch. `budget.yaml` hält Grenzen und Attributionsdaten. `check.py` misst den Arbeitsbaum. Im privaten Verlauf hält der unveränderliche Commit `2c0aaa5d425cdd9a3daf9ffa9a5d800c84c625a5` die akzeptierten Ausgangsgrenzen. Eine saubere Public-Historie enthält diesen privaten Commit absichtlich nicht; dort verwendet derselbe Checker die fest codierte portable Baseline `6/7/20` und die Limits `6/9/21`.

Spätere Commits können `budget.yaml` nicht als eigene Baseline verwenden. Eine Erhöhung braucht `approved_by: human:<id>` samt Begründung im Budget. Das Feld dokumentiert die Attribution und authentifiziert sie nicht. Eine Änderung des gebundenen Commits, der portablen Baseline oder der portablen Limits ist eine sichtbare Änderung am Gate und braucht menschliche Prüfung. Regeln und Quellen stehen im Einfachheitsvertrag unter `AGENTS.md`.
