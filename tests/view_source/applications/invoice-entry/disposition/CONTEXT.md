---
type: teilprozess
id: teilprozess:disposition
ergebnis: Confirmed scheduled-or-pending disposition and inspectable entry acceptance evidence
---

# Invoice disposition

`hypothesis`: candidate contribution based on the [SOP result and approval exception](../../../grundlagen/invoice-source.md#supplied-procedure).

## Contribution to the result

Give the proposed recipient Accounting usable evidence that the recorded invoice is scheduled under applicable approval or confirmed marked for approval, with the entry acceptance checks and follow-up visible. This concludes invoice entry, not payment or a monitoring service.

## Inputs and boundaries

The entry section's case packet supplies confirmed bill and original identities, source comparison, check evidence and unresolved restrictions. The bound [definition](../../../grundlagen/invoice-definition.md) supplies decision scope and gaps. A scheduling decision needs the final bill, authorized holder and current applicability. A pending record does not require inventing a positive scheduling decision.

## Workstep composition

[Decide scheduling](decide-scheduling/CONTEXT.md) is used only when a new human decision is actually requested within this case. It sends its external decision evidence through its declared handoff. [Confirm disposition](confirm-disposition/CONTEXT.md) consumes either that decision or the record job's checked pending/previously-approved packet, applies the covered disposition and checks final acceptance. The terminal recipient is Accounting (proposed, G1); only accepted scheduled/pending ends achieve this section. Incomplete ends preserve partial effects without acceptance.

## Setup completion

The declared mappings let each receiving job start with the actual object and evidence. The gate's pending state supplies no approval. The author report covers E1/E5, rejection, changed bill and missing authority. All necessary adoption, holder, checker and follow-up setup remains explicit in G1–G8. No human decision or actual disposition has been obtained.
