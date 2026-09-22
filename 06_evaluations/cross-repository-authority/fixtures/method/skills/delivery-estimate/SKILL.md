---
name: delivery-estimate
description: Estimate a delivery date from a dispatch date and transit days.
---

# Delivery estimator

At `method@m4`, this file owns the reusable calculation: dispatch date plus transit days yields an estimated delivery date. Its declared inputs are dispatch date and transit days; its output is an estimate. A reported result says `status: ok`. That status covers this calculation on supplied inputs; it does not check availability or authorize a promise. The [availability check](../availability-check/SKILL.md) has a separate result contract.
