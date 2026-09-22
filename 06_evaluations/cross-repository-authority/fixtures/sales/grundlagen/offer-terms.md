# Offer terms

## Delivery

Address: [source namespace `urn:impacts:example:cross-repository:sales`](../CONTEXT.md); stable local item key `offer-delivery-commitment`; location this `delivery` anchor; applicable revision `s3`.

This rule owns the conditions for a delivery commitment in an offer.

<a id="relationship-offer-delivery-inputs"></a>

| Direction | Target endpoint | Applicable scope | Relationship evidence |
|---|---|---|---|
| uses estimate from | [`urn:impacts:example:cross-repository:method` / `delivery-estimate`](../../method/skills/delivery-estimate/SKILL.md) at revision `m4` | Delivery commitments in offers under revision `s3` | `reported`: synthetic maintained declaration; link and execution not checked |
| requires evidence from | [`urn:impacts:example:cross-repository:method` / `availability-check`](../../method/skills/availability-check/SKILL.md) at revision `m4` | Same offer case and estimated date | `reported`: synthetic maintained declaration; no result established |
| interprets commitment using | [`urn:impacts:example:cross-repository:customer` / `delivery-promise`](../../customer/grundlagen/lieferzusage.md#definition) at revision `c8` | Customer-local promise meaning for the affected offer | `reported`: synthetic maintained declaration; applicability not checked |

The rule also requires the applicable human decision. No availability evidence or human decision is established in this fixture. The accepted result is therefore a stated blocker, not a delivery commitment.
