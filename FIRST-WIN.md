# Prepare a useful offer draft from ordinary files

The contribution is an internal draft with supported scope, source references, missing information and a next action. Work in an ordinary folder using a text editor or a file-capable agent with permission to read the sources and write the draft. No Git, Python, installer or YAML is needed.

**Flexible in how it thinks. Uncompromising in what counts.** Interpretation and drafting may be fallible; checked calculations require actual deterministic checks, and human decisions remain human.

## Give the work a home

Use existing domain and case files in your business. For this exercise, create the four Markdown files below in a separate folder. They reuse the catalog, customer, inquiry and offer-blank roles from the [synthetic company example](02_protocol/impacts-architect/references/datenbezug.md#from-catalog-through-pipeline-to-a-filled-offer). P-10, S-20, C-1 and O-1 are synthetic identifiers. This exercise deliberately supplies no applicable price or delivery date; it changes no historical agreement or Run.

`CONTEXT.md` is the entry point:

```markdown
# Offer preparation exercise
Working language: en

Synthetic training material; no real customer commitment.
- [Catalog](grundlagen/catalog.md): product/service kinds and source limits.
- [Offer blank](grundlagen/angebotsvorlage.md): reusable internal document.
- [Inquiry AN-1](records/offer-o1/inquiry.md): requested scope for C-1.

Prepare Offer O-1 / Version 1 in records/offer-o1/draft.md.
Use only linked sources. Keep missing facts open. Do not send or approve.
When the draft exists, add a direct link here so a fresh session can continue.
```

`grundlagen/catalog.md`:

```markdown
# Synthetic catalog
- P-10 is a product kind.
- S-20 is a service kind.
Source: synthetic company example, “From catalog through pipeline to a filled offer”.
Evidence: reported fixture descriptions; no real-world verification.
No applicable price or availability source is supplied here.
Catalog kinds establish neither delivery nor service coverage of a specific item.
```

`records/offer-o1/inquiry.md`:

```markdown
# Inquiry AN-1
Customer: C-1. Offer to prepare: O-1 / Version 1.
Requested scope: P-10, 2 pieces; S-20, 12 hours.
Source: synthetic company example, separate synthetic request.
Evidence: reported fixture request; not an agreement or delivery record.
Delivery date: open; the responsible owner has not decided.
No sending permission or approval is recorded.
```

`grundlagen/angebotsvorlage.md`:

```markdown
# Offer {{offer_id}} / Version {{version}}
Customer: {{customer_id}}
Request: {{request_ref}}

Scope:
Price and total:
Delivery date:
Sources and evidence:
Missing information and next action:
Use: internal draft; sending and acceptance are not confirmed.
```

## Ask for the contribution

Give your agent this task, or follow it yourself:

> Read CONTEXT.md and its three linked files. Fill a copy of the offer blank at records/offer-o1/draft.md. Preserve the requested identities, quantities and units. Cite the source file for each claim. Leave price, total and delivery date open. Name the question, responsible decision-maker and next action beside the draft. Add a draft link to CONTEXT.md. Do not calculate unsupported amounts, claim a performed check, approve, send or invent delivery evidence.

The useful draft should say that C-1 requests P-10, 2 pieces, and S-20, 12 hours, citing `inquiry.md`; these are catalog kinds, citing `catalog.md`. Price and total stay `open`: obtain an applicable price source and sanctioned calculation rule, then perform the actual deterministic calculation/check before claiming a checked amount. Delivery date stays `open`: ask the responsible owner to decide after checking availability. Sending and acceptance remain unconfirmed.

Record this handoff in the draft, using the actual progress:

> Draft ready for internal review — price and delivery date are still open, so no priced delivery promise is established. Next: obtain applicable price/rule evidence and the owner's delivery decision; retain their sources beside this draft. Sending requires its own permission.

This is an expected output, not a claim that an agent has already produced or checked it. Reading source statements supports a draft; it does not verify the business facts.

## Continue in a fresh session

Close the conversation. Give a fresh agent only the folder and this task:

> Start at CONTEXT.md. Find the draft and the sources supporting its requested scope. State what is still open and the exact next action. Continue permitted preparation without inventing a price, date, check result, approval or sent offer.

The existing router and draft should make the work recoverable. If the draft link or a source is missing, repair that path at its existing home. No second summary or state engine is needed. A consumer check must observe this recovery; the programmed technical examples do not prove it.

## If the requested Git binding cannot be checked

Suppose the owner now asks to prepare a Git-bound Run and validate its historical binding, but Git is unavailable. Keep the draft, sources, questions and any candidate definition at their existing homes. Record beside the preparation:

> Preparation retained — Git-bound historical Run validation was not performed because Git is unavailable. This preparation is unbound; it is not a validated Run. Next: on a machine with Git and the Python CLI, complete the Application contract and required setup cases, commit that Application at the Core workspace root, bind the Run to its actual committed tree using the Run template, and run `impacts validate` on that workspace. Retain the actual result and correct any reported failure before claiming validated binding.

Follow [Construct](02_protocol/impacts-method.md#construct) and the [Run template](02_protocol/templates/vorgang.md) for those steps. Do not invent a tree ID, hash, execution entry or approval. Resume from the preserved draft when tooling becomes available. Structural validation alone proves neither executed work nor a checked business result; required domain checks and human decisions still need their own evidence.

The [optional technical use](README.md#optional-technical-use) links the installer and existing programmed evaluations. [Form selection](02_protocol/impacts-architect/references/formwahl.md#tooling-stopp) owns the ordinary-files and machine-validation boundary. [Deutsch](02_protocol/translations/de.md) explains the same entry path in German.
