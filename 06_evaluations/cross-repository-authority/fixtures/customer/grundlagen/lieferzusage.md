# Delivery promise

## Definition

Address: [source namespace `urn:impacts:example:cross-repository:customer`](../CONTEXT.md); stable local item key `delivery-promise`; location this `definition` anchor; applicable revision `c8`.

This file owns the local meaning of a delivery promise: the date communicated to the customer as a commitment. Case inputs are `reported`; availability for the case is `open`.

<a id="relationship-delivery-promise-uses-estimator"></a>

| Direction | Target endpoint | Applicable scope | Relationship evidence |
|---|---|---|---|
| uses estimate from | [`urn:impacts:example:cross-repository:method` / `delivery-estimate`](../../method/skills/delivery-estimate/SKILL.md) at revision `m4` | Delivery promises under revision `c8`; no real case or validity period established | `reported`: synthetic maintained declaration; link and execution not checked |

This relationship locates a reusable calculation. It does not transfer this definition's authority or establish a commitment.
