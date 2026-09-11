---
title: Complexity budget
evidence_status: reported
---

# Complexity budget

A deterministic gate against structural growth. `budget.yaml` holds limits and attribution; `check.py` measures the working tree. The human-confirmed V0.2 boundary `5/5/15` is the initial bootstrap. Afterward, the checker reads its comparison boundary from the latest reachable public release tag. It skips a tag at the current `HEAD`, so a post-tag check still compares against the preceding release.

An increase requires `approved_by: human:<id>` and a reason in the budget. This records attribution; it does not authenticate it. Protected `main` and release tags provide the baseline's protection against self-modification. See the simplicity contract in [AGENTS.md](../../AGENTS.md) for the rules and sources.
