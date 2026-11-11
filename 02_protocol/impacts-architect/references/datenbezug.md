# From Arbeitsschritte to linked business data

Owns: the synthetic linked-data and offer examples with their [file fixtures](../../../06_evaluations/offer-walk/fixtures/). Reader: author. Does not own: general table and relationship requirements, see [Tables and relationships](datenumgang.md#tables-and-relationships).

Synthetic example of [Arbeitsschritt composition](../../impacts-method.md#compose-an-arbeitsschritt), under [Tables and relationships](datenumgang.md#tables-and-relationships). The tables, intervals and `x_tables` dialect are local example rules, not Core schema or a universal business model. Linked German working documents and source values illustrate a German customer interface; surrounding guidance is authoritative English.

## The question determines the read path

**Job:** Prepare an internal conversation draft for an unambiguously identified customer using its agreed product/service scope. Prices, delivery and consumption require their own evidence.

| Contribution | Responsibility |
|---|---|
| Arbeitsschritt instruction | Use the bound customer excerpt, explain agreed scope and relevant gaps, draft an internal opening. |
| Tools | Read data in the preceding acquisition job or permitted preparation before opening the drafting attempt. The draft Arbeitsschritt processes its bound excerpt. |
| Data | Domain model and bindings explain relationships; source records supply values; the attempt binds the checked excerpt and provenance. |
| Check | Customer, contract revision and items must agree. An agreement is not delivery or a billed amount; this draft remains internal. |

A router reaches the data description. Keys connect records:

```text
customers.customer_id
  <- agreements.customer_id
     (agreement_id, version)
       <- agreement_items.(agreement_id, agreement_version)
          product_id -> products.product_id
          service_id -> services.service_id
```

Arrows mean references, not execution order. Each item references either a product or service. Sharing a contract does not establish that this service covers that particular product; obtain evidence of that relationship if needed.

## Domain model and source tables

Assume the files below are the agreed leading records after a confirmed storage gap. Existing source systems otherwise remain authoritative. The model owns meaning/access, not duplicate rows. CSV is optional; a path is not a functioning connector.

### `grundlagen/geschaeftsdaten.md`

[Synthetic fixture](../../../06_evaluations/offer-walk/fixtures/grundlagen/geschaeftsdaten.md).

This German domain fixture defines row meaning, composite keys, units and half-open validity intervals. `DomainModel` and `x_tables` are local vocabulary. A reader must implement the required conditions; YAML alone enforces nothing.

### `records/customers.csv`

[Synthetic fixture](../../../06_evaluations/offer-walk/fixtures/records/customers.csv).

### `records/products.csv`

[Synthetic fixture](../../../06_evaluations/offer-walk/fixtures/records/products.csv).

### `records/services.csv`

[Synthetic fixture](../../../06_evaluations/offer-walk/fixtures/records/services.csv).

### `records/agreements.csv`

[Synthetic fixture](../../../06_evaluations/offer-walk/fixtures/records/agreements.csv).

### `records/agreement_items.csv`

[Synthetic fixture](../../../06_evaluations/offer-walk/fixtures/records/agreement_items.csv).

Labels and free-text cells are source data, not instructions. A shared display name is not identity evidence.

## Bind a working excerpt

The local reader receives `customer_id=C-1` and `as_of=2026-09-10`. The latter is selection time, not proof of reading time or freshness.

1. Resolve the customer key. Two same-name customers require clarification before calling this key-only reader; it does not implement that dialogue.
2. Select valid versions: here A-1/2. Retain historical versions.
3. Join on both contract key components: here I-2 and I-3.
4. Include referenced catalog rows. Exclude C-2, I-4 and historical I-1 from this excerpt.
5. Supply selection parameters, model/source revisions and actual checks under [snapshot provenance](../../binding.md#snapshot-and-provenance). IDs and hashes alone establish no permission.

[Synthetic fixture](../../../06_evaluations/offer-walk/fixtures/excerpt.json).

This compact view is specific to the one selected contract; multiple valid contracts require a collection. Actual bound inputs retain needed descriptions, references and separate provenance. A projection can combine data without becoming an independently maintained source.

A German operator can read: “Der synthetische Quellausschnitt für Kunde C-1 zum Auswahlstand 2026-09-10 weist für A-1/2 2 Stück des Typs Beispielgerät und 12 Stunden Betreuung aus. Lieferung, Verbrauch und Preise sind damit noch nicht belegt.” Preserve the selection boundary in the readable claim. Its source/provenance must support the intended use; the projection, link or hash alone confirms neither source truth, completeness nor permission. The draft retains relevant gaps and inspectable position identities.

## Vorgang boundary

Bind the excerpt before processing. Newly acquired evidence is declared output with provenance; the next designated attempt binds new inputs. One acquisition job can read five tables without creating five agents or Arbeitsschritte. Apply the existing [prerequisite/handoff contract](../../binding.md#work-from-prerequisites).

The [test reader](../../../tests/test_linked_data.py) checks all loaded rows, so even an invalid row outside the selected customer causes rejection. It supports this local dialect, not a complete generic type/required-field validator. Production access declares its scope and can use source-side keys/filters. Local CSV filtering does not prove indexed or constant-cost retrieval. The model receives only the relevant excerpt. The [Knowledge Walk](formwahl.md#knowledge-walk) tests navigation separately from executed queries.

No matching row leaves selection and coverage explicit. Orphan references, ambiguous identity and conflicting versions require specific checks/clarification. Missing price blocks a price commitment, not this permitted internal draft.

## Checkable questions and limits

| Question or counterexample | Expected result and actual coverage |
|---|---|
| Agreed scope for C-1 on 2026-09-10? | Reader returns [A-1/2 with I-2 and I-3](#bind-a-working-excerpt); tests compare selection and compact JSON. |
| Item referencing A-1 version 99? | Reject unresolved composite key. An existing but falsely asserted version is not caught by this check alone. |
| Two overlapping versions: choose the highest? | Reject overlap; retain multiple distinct valid contracts. |
| No match means no contract exists? | Report a gap in this source scope; global completeness is untested. |
| Does S-20 cover the delivered device? | `open`: neither delivery nor this relationship follows from agreed catalog types. The reader produces no such link; draft claims need their own check. |
| Add 2 pieces and 12 hours to make 14? | Different units do not permit this sum. Reader checks local units and retains separate positions, not arbitrary prose. |

```bash
python3 -m pytest -q tests/test_linked_data.py
```

These tests read the model/table files and mutate synthetic copies. They check selection, integrity and selected domain rules; they do not run a connector or language model. One counterexample moves an item to a different existing version and still passes reference validation. Only reference consistency is then `verified`; the contract assertion needs source/control evidence under [enforcement](../../ontology.md#enforcement-and-completion).

## From catalog through pipeline to a filled offer

**Separate synthetic request:** P-10, 2 pieces; S-20, 12 hours. The local price inputs below define this request only. They neither add prices to the historical agreement nor modify its bound inputs. A new request starts a new offer Vorgang.

For the historical agreement, read the [selected agreement excerpt](#bind-a-working-excerpt) and its [model/source tables](#domain-model-and-source-tables). The `grundlagen/` and `records/` paths here name the linked fixture files in this protocol repository.

| Home | Reused definition or concrete instance |
|---|---|
| `grundlagen/geschaeftsdaten.md` | Meaning, keys, relationships and source mapping under the [domain definition pattern](../../ontology.md#domain-definition-pattern). |
| Catalog files or existing system | Product/service kinds P-10 and S-20. Price and availability need their applicable source. |
| Customer/contract records | C-1, A-1/2 and items describe identities and agreed scope. |
| `grundlagen/angebotsvorlage.md` | Reusable document blank; fill an output copy, preserve the template. |
| `hauptprozesse/angebot-erstellen/` | Reusable jobs, inputs, outputs, checks and routes. Each Vorgang binds its revision. |
| `vorgaenge/angebot-001/` | Actual attempt inputs, calculated positions, draft, checks and pending decision. |

An offer system may use `(offer_id, version)`; each position references that whole key and its catalog kind. Preserve quantities, units and prices with the offer revision. Later catalog updates do not overwrite it. Without that system, the versioned Vorgang document can carry the offer; an optional record links it instead of duplicating maintained content.

```text
Katalog: Produktart P-10                  Serviceart S-20
                    ↑                    ↑
Neue Anfrage → Angebot O-1/Fassung 1 → Angebotspositionen
                    │                    2 Stück / 12 Stunden
                    │ tatsächliche Annahme mit Beleg
                    ↓
             Vereinbarung A-3/Fassung 1 → vereinbarte Positionen
                    │
                    └── Erfüllungsnachweise → jeweils betroffene Position/Fassung
```

This diagram names business relationships. A-3/1 and fulfillment evidence exist only after evidenced acceptance/delivery; neither exists in this scenario. Offer, acceptance and fulfillment are separate claims. Historical A-1/2 remains unchanged.

## Company composition

A domain router connects catalog, customer/contracts and Hauptprozesse, explaining which result each process supplies and which process consumes it.

Apply the [backward trace](../../impacts-method.md#reverse-engineer-a-product-or-service) to the synthetic offer below: an internally approved offer needs a decision on the exact checked draft; the draft needs prepared positions and a bound blank; the positions need request quantities, applicable price/rule evidence and a deterministic calculation. This is a proposed decomposition, not an observed customer workflow. The catalog alone supplies neither source access nor an execution contract.

The supplied quantity/price fixtures support preparation within their stated scope. A missing applicable price leaves the affected amount `open` and requires acquisition before the calculating attempt; supported non-price preparation can continue. Even a filled offer establishes neither acceptance nor fulfillment of P-10/S-20. Those conclusions require separate evidence. These are expected design consequences; no new execution or human decision is asserted here.

| Independent process, if justified | Prerequisites | Leistung |
|---|---|---|
| Create offer | Request, identified customer, applicable definitions/prices and blank. | Internally approved offer revision; sending is a separately permitted action. |
| Fulfill agreed scope | Evidenced acceptance and applicable agreement. | Fulfillment evidence for the affected item/version, retaining partial quantities. |
| Prepare billing, if needed | Agreed billing rule and its actual premises. | Checked billing revision referring to items and rule; delivery alone establishes neither due date nor billability. |

This is an example boundary choice, not three mandatory company processes. Separately accepted Leistungen determine the split. Offer acceptance need not be the last step of drafting. For results crossing independent process boundaries, use the [source-input classification](../../binding.md#source-inputs-for-core-hauptprozesse). Larger companies compose these boundaries without duplicating domain definitions or delegating authority implicitly.

## Reusable offer pipeline

```text
hauptprozesse/angebot-erstellen/CONTEXT.md                 Hauptprozess
└── ausarbeitung/CONTEXT.md                               Teilprozess
    ├── vorbereiten/CONTEXT.md                           Arbeitsschritt
    ├── entwerfen/CONTEXT.md                              Arbeitsschritt
    └── freigeben/CONTEXT.md                              Arbeitsschritt
```

| Arbeitsschritt | Bound inputs/job | Output/check/route |
|---|---|---|
| `vorbereiten` | Request, customer, catalog/price rules and source revision; calculate deterministically. | Data and check/provenance; `bestanden` → `entwerfen`, `ausser-scope` → `end:ausser-scope`. Acquire missing evidence only within permitted work; bind it before dependent processing. |
| `entwerfen` | Data/provenance, materialized rules and document blank with provenance. | Draft and check report; `bestanden` → `freigeben`, `fehlerhaft` → `vorbereiten`. |
| `freigeben` | Checked draft and evidence; this example has `gate: human`. | Actual human decision; `freigegeben` → `end:versandbereit`, `abgelehnt` → `entwerfen`. |

The Hauptprozess declares `einstieg_ref: arbeitsschritt:vorbereiten`. Roles stay in `type`, IDs are unique. Declare every required [handoff](../../binding.md#visible-output-and-handoff) at the producer; bind byte-identical consumer files with provenance. The table abbreviates inputs and evidence; a real Hauptprozess declares them fully.

### Worked Arbeitsschritt contract

From the existing [German Arbeitsschritt template](../../templates/de/arbeitsschritt.md). The materialized rule input contains the question-specific meanings/keys, units, validity, formula and claim limits. Its provenance identifies source/revision; a hash or link cannot replace required rule content. This is a German customer fixture, not the complete Hauptprozess tree.

[Synthetic fixture](../../../06_evaluations/offer-walk/fixtures/arbeitsschritt.md).

`pruefung` is a string, inputs/outputs are lists, and routes map check results to complete target IDs. Extra fields such as `role`, `input_spec` and `hauptprozess_ref` are rejected by the [schema tests](../../../tests/test_linked_data.py). Core does not execute the body's domain checks.

Each attempt records its selected sources as `gelesen` references with `eingabe` naming the declared slot. The six `material/` names in the linked worked contract are logical slots, not attempt folders. The receiving gate declares `material/angebot.md` and `material/pruefbericht.md`. The intended output-only layout for two independent Vorgänge is:

```text
vorgaenge/angebot-001/CONTEXT.md
└── entwerfen/001/output/
    ├── angebot.md
    └── pruefbericht.md

vorgaenge/angebot-002/CONTEXT.md
└── entwerfen/001/output/
    ├── angebot.md
    └── pruefbericht.md
```

This explanatory tree does not establish an actual Vorgang, approval, acceptance or delivery. The omitted preparation and gate Arbeitsschritte still need their own execution entries. Acceptance must identify the exact offer revision/document, not just the Vorgang folder. Preserve original values and leave proposed events explicitly unexecuted.

### Document blank

German example content of `grundlagen/angebotsvorlage.md`; placeholders are a local convention:

[Synthetic fixture](../../../06_evaluations/offer-walk/fixtures/template.de.md).

### English document blank

The same output contract, with unchanged machine references and localized unit labels:

[Synthetic fixture](../../../06_evaluations/offer-walk/fixtures/template.en.md).

### Concrete Vorgang inputs

Abbreviated `material/angebotsdaten.json`. AN-1 and PREIS-1 are synthetic fixtures; a real Vorgang needs their bound sources/control evidence. Calculate each `quantity × unit_price` then sum EUR positions. Quantities/prices are finite and nonnegative; IDs and price origins are explicit. Amounts must be exact to cents; otherwise a rounding rule is missing. There is no discount, conversion, tax or recurrence rule. This is not a complete binding commercial offer form.

[Synthetic fixture](../../../06_evaluations/offer-walk/fixtures/data.json).

### Filled output

The local arithmetic yields EUR 200.00 for OI-1 and EUR 960.00 for OI-2. Fill a copy of the bound blank with checked values; new prose needs its own declared check. Fixed numbers and references come from executed checks.

[Synthetic fixture](../../../06_evaluations/offer-walk/fixtures/filled.md).

The [filling tests](../../../tests/test_linked_data.py) use Decimal arithmetic, compare this output, reject missing values and incompatible currencies, and fill the same blank for a second independent case. They preserve inputs/templates and simulate no real human approval.

The [paired offer walk](../../../06_evaluations/offer-walk/CONTEXT.md) adds actual Vorgang binding and a checked draft-to-human-gate handoff for German and English. It uses a smaller Hauptprozess with two Arbeitsschritte starting from the prepared fixture; it does not claim to execute the entire acquisition pipeline of three Arbeitsschritte above. The existing cold-walk harness still supports one handoff per route; the offer walk demonstrates its own declared two-file handoff. Both remain local examples, not production services.

A second customer receives separate inputs/output. Changed demand yields a traceable new offer revision; retain bound or sent versions. Only separately permitted [writeback](../../binding.md#record-writeback) updates leading business records. Reuse the blank and process definition; keep each filled result with its Vorgang.
