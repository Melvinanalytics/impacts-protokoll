# Prepare a useful offer draft from ordinary files

Produce an internal offer draft with cited scope, explicit gaps and a named next action. Use any folder, text editor or file-capable agent. No Git, Python, installer or YAML is needed.

**Flexible in how it thinks. Uncompromising in what counts.** Drafting may be fallible; calculations require deterministic checks, and human decisions remain human.

## Give the work a home

For real work, save the draft in that case's existing folder with its sources, open questions and next action.

To practice, create these six synthetic Markdown files in a separate folder. They reuse the catalog, customer, inquiry and offer-blank roles from the [synthetic company example](02_protocol/impacts-architect/references/datenbezug.md#from-catalog-through-pipeline-to-a-filled-offer). P-10, S-20, C-1 and O-1 are synthetic; no price, delivery date or approval is supplied.

`CONTEXT.md` (its `Form:` lines declare both folders so `impacts validate` accepts the layout later):

```markdown
# Offer preparation exercise
Working language: en

Form: grundlagen/ Knowledge Bundle per foundation
Form: records/ Record Library per offer

Synthetic training material; no real customer commitment.
- [Foundations](grundlagen/CONTEXT.md): catalog and offer blank.
- [Offers](records/CONTEXT.md): one folder per offer.
- [Inquiry AN-1](records/offer-o1/inquiry.md): requested scope for C-1.

Prepare Offer O-1 / Version 1 in records/offer-o1/draft.md.
Use only linked sources. Keep missing facts open. Do not send or approve.
When the draft exists, add a direct link here so a fresh session can continue.
```

`grundlagen/CONTEXT.md`:

```markdown
# Foundations
## What to load
For an offer, load the catalog and the offer blank; nothing else lives here.
## Overview
- [Catalog](catalog.md): product/service kinds and source limits.
- [Offer blank](angebotsvorlage.md): reusable internal document.
```

`grundlagen/catalog.md`:

```markdown
# Synthetic catalog
- P-10 is a product kind.
- S-20 is a service kind.
Source: synthetic company example, “From catalog through pipeline to a filled offer”.
Evidence: reported fixture descriptions; no real-world verification.
No price or availability source is supplied. Catalog kinds establish neither delivery nor service coverage.
```

`records/CONTEXT.md`:

```markdown
# Offers
## What to load
Open only the offer the task names.
## Overview
- [Offer O-1](offer-o1/): inquiry, and later the draft.
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

> Read CONTEXT.md and its linked files. Fill a copy of the offer blank at records/offer-o1/draft.md. Preserve identities, quantities and units. Cite the source file for each claim. Leave price, total and delivery date open. Name the question, responsible decision-maker and next action beside the draft. Add a draft link to CONTEXT.md. Do not calculate unsupported amounts, claim a performed check, approve, send or invent delivery evidence.

The draft should state that C-1 requests P-10 (2 pieces) and S-20 (12 hours), citing `inquiry.md`, and that both are catalog kinds, citing `catalog.md`. Keep price and total `open` until a price source and sanctioned rule exist and a deterministic check runs. Keep delivery date `open` until the responsible owner decides. Sending and acceptance remain unconfirmed.

Record this handoff in the draft:

> Draft ready for internal review: price and delivery date remain open, so no priced delivery promise is established. Next: obtain price/rule evidence and the owner's delivery decision; retain their sources beside this draft. Sending requires separate permission.

Reading sources supports a draft; it does not verify business facts.

## Continue in a fresh session

Close the conversation. Give a fresh agent only the folder and this task:

> Start at CONTEXT.md. Find the draft and its sources. State what is still open and the next action. Continue permitted preparation without inventing a price, date, check result, approval or sent offer.

The router and draft make work recoverable without a separate summary or state engine. If a link or source is missing, repair it at its home.

Keep this first use file based and optional-tool free. For a reproducible technical example with a deterministic delivery calculation, see the [delivery replay](06_evaluations/delivery-replay/CONTEXT.md), an optional next proof, not a prerequisite.

## When Git binding cannot be checked

If an owner requests a Git-bound Vorgang but Git is unavailable, keep the draft, sources and open questions in place and record:

> Preparation retained; unbound. Git-bound Vorgang validation did not run because Git is unavailable. Next: on a machine with Git and the CLI, commit the Hauptprozess at the Core workspace root, bind the Vorgang using the Vorgang template, run `impacts validate`, and retain the actual result.

Follow [Construct](02_protocol/impacts-method.md#construct) and the [Vorgang template](02_protocol/templates/vorgang.md). Never invent a tree ID, hash or approval. Structural validation proves neither executed work nor checked business facts.

See [optional technical use](README.md#optional-technical-use) for the CLI and [Tooling stop](02_protocol/impacts-architect/references/formwahl.md#tooling-stop) for the ordinary-files boundary.
