# Data handling in a workstep

This reference shows how a step names, reaches, binds, checks, hands off and writes back business data. It applies [Data Governance](../../capabilities.md#data-governance), [snapshot and provenance](../../capabilities.md#snapshot-und-herkunftsnachweis), [visible output and handoff](../../capabilities.md#sichtbare-ausgabe-und-übergabe) and [record writeback](../../capabilities.md#rückübertragung-in-geschäftsrecords); those sections stay authoritative. The kinds, facets and route names below are optional capture guidance. They are not Core types, required fields, parser labels or a closed taxonomy; a domain may rename them at its own home.

Three homes stay separate throughout:

| Home | Owns | Does not own |
|---|---|---|
| Domain home | Meaning, keys, units, source mappings, leading system per attribute, responsibility | Values of a case, credentials, a run |
| Workstep | Selection for this job: which identity, purpose, time, fields, reader, effect and check | Reusable meaning; a second copy of the source mapping |
| Harness | Access, credentials, execution of the bound operation, actual evidence | Business authority, meaning, permission for use |

A step references the domain home by link and anchor instead of maintaining its own mapping. In a selected Core attempt, also bind the needed description or sufficient excerpt under [snapshot and provenance](../../capabilities.md#snapshot-und-herkunftsnachweis). That preserved input is evidence of the cited revision, not a second maintained authority. Ten steps on one customer table then share one description while their runs preserve the definitions actually used.

## Data objects

Use only distinctions needed for the question. These are capture roles, not an exclusive classification of every file or object. Distinguish the definition, stored representation and case occurrence where their identity, meaning or evidence differs.

| Kind | What it is | Address, if independently cited | Typical confusion |
|---|---|---|---|
| Business object | Class of things the business keeps data about: customer, item, order, offer | none | The table that stores part of it |
| Attribute | Property of a business object; refers to a value domain | none | The field that carries it; two fields can carry one attribute |
| Value domain | Allowed values with meaning, type and unit: a code list or a rule | none | The code list and its maintained content (reference data) |
| Event | Occurrence in the world with a time that produces data: offer sent | none | The record about it: “offer created” is not “offer sent” |
| System | Application or channel that keeps or supplies data: ERP, CRM, shared mailbox, recurring manual input | `quelle:` | The table inside it |
| Data collection | Named set of rows with one structure: table, report, export, file or hand list | `quelle:` | A report or export taken as the originating maintained system |
| Field | Physical carrier of an attribute in a data collection | part of a source description | Entry date taken as event date |
| Key mapping | Evidenced link between keys of two systems or collections, with multiplicity and match rate | scoped mapping home | Equal names or numbers taken as the same identity |
| Lineage edge | Directed link: B derives from A, as designed flow or as actual run | none | The derivation rule: lineage says from where, the rule says how |
| Measure | Quantity that enters an aggregation, at the grain of an event or object | input variable of a rule | The metric; a price never aggregated is an attribute |
| Derivation rule | Rule that derives, filters, aggregates, converts or checks | `rechenweg:` | Its implementation (workbook, SQL) or one execution |
| Metric | Meaning of a quantity: what is counted, unit, population, grain, time basis | `kennzahl:` | Its value, target or threshold |
| Hierarchy | Ordered roll-up levels over attributes of a business object; several per object, each with validity | none | The is-a hierarchy of terms |

A concrete value, record or source state stays at its case/evidence home; a Core Run keeps its existing contract. A `beobachtung:` identifies a scoped claim, not the value or record itself. Composite terms combine these distinctions:

| Term | Composed of |
|---|---|
| Data model | Business objects, attributes, keys and relationships; physically, data collections and fields |
| Master data management | Leading system per attribute, key mappings, duplicates and responsibility |
| Golden record | A record derived from several systems by a key mapping and a rule; a hub that maintains it is a system |
| KPI | A metric with a target and a steering purpose; the role sits in the result contract |
| Data quality | Results of checking rules against an explicit requirement |
| Data contract or interface | Agreement about exchanged collections/fields, meaning, grain, keys, time, quality and responsibility; a derivation relationship is stated separately |
| Lineage | Lineage edges from a metric back to fields |

Each facet answers a separate question about a scoped definition or claim. Apply it where relevant; a mixed collection may contain several origins or value kinds. Distinguish those parts when the intended use depends on the difference. An event and a metric over it retain their own meanings:

| Facet | Question | Values |
|---|---|---|
| Level | Definition or occurrence? | definition · occurrence (value, record, state, run) |
| Data role | Which function in the business? | reference · master · transaction |
| Origin | How did it arise? | captured · copied (export, replica) · derived · set by decision |
| Time character | How does it relate to time? | point (event) · cut-off (stock) · period (flow) · timeless (value domain only) |
| Value kind | Which claim does a value make? | actual · plan · forecast · target · threshold · comparison · assumption |
| Aggregation | May it be summed? | additive · semi-additive (not across a named dimension, usually time) · non-additive |
| Evidence | How established? | [evidence labels](zuschnitt.md#evidence) per claim |

Record these details at the object's domain home where they apply: grain and complete key (including tenant and version); which [clock](../../ontology.md#domain-addresses-and-relationships) counts; population and filters; unit and conversion; location as system › collection › field; responsibility; leading system with valid-from date; validity of master data at event time.

## The data path through one step

Each station names the question, the existing contract slot that answers it and the evidence it leaves. Ordinary file work records the applicable selection, source state, checks and continuation at its existing case home. Attempt paths, `Quellenanforderung`, digests, `pruefung` and byte-identical routed handoff below apply to selected Core Runs; this sequence adds no mandatory stages or fields to other forms.

| Station | Question | Contract slot | Evidence left | Typical failure |
|---|---|---|---|---|
| Define | What does the input mean? | [Use](../../ontology.md#use) for an existing definition; [Author or change](../../ontology.md#author-or-change) for missing meaning | Definition with address and revision; needed meaning bound in a selected Core attempt | Live link treated as a bound definition |
| Locate | Which object in which system holds it, and which system leads? | [Source descriptions](../../capabilities.md#data-governance) | Source description with form, leading system, responsibility | Export or report named as the source |
| Reach | By which route can a reader get it, and may that route write? | Source description and tool line; [access routes](#access-routes) when reader, effect or permission is unresolved | The four separate access findings | Tool listed, therefore treated as usable |
| Bind | Which bounded excerpt does this attempt use? | [Quellenanforderung](../../capabilities.md#source-inputs-for-core-applications) and `*-herkunft.md` | Input bytes, provenance, digest | New live read used as an input during the same attempt |
| Check input | Is the excerpt usable for this job? | Required control in Quellenanforderung | Executed input checks | Missing values counted as zero |
| Process | Which transformation serves this job, by whom and under which rule? | Processing body: selection, extraction, join, conversion, calculation or interpretation; placement and executor under [Augment](../../impacts-method.md#augment); [calculation checks](#checks-before-calculating) when the job calculates | Input and rule revision, parameters, result, checks and any used model configuration | Interpretation claimed as a checked calculation |
| Check result | Is the result correct for its use? | `pruefung` | Executed checks and their outcome | Query that runs taken as correct |
| Hand off | What does the successor need first? | Handoff mapping and successor's first action under the [forward check](../../impacts-method.md#reverse-engineer-a-product-or-service) | Byte-identical handoff with provenance | Verdict without the affected content |
| Write back | Does the result change a continuing record? | [Record writeback](../../capabilities.md#rückübertragung-in-geschäftsrecords) | Target, version, confirmation | Draft or request taken as written |

## When which data is used

The attempt rows below apply to selected Core Runs; ordinary work keeps its source notes and checks at the existing case home without introducing attempts or digests.

| Moment | Data used | Rule |
|---|---|---|
| Design | Definitions, schemas, table metadata, a few inspected records | Reading metadata or samples informs the domain home; it binds no run |
| Before the attempt opens | The declared source excerpt and rules | Acquire, materialize and hash before opening; missing access leaves a specific blocker |
| During the attempt | Declared inputs and permitted tool operations | Transform bound inputs within the job. A permitted new read becomes output with provenance for a subsequent attempt; bound input/provenance bytes stay unchanged |
| After the result check | The result and actual check outcome | Follow its declared success, failure or recovery path. Failed-check evidence may be handed off for diagnosis; successful-use restrictions still apply |
| Next attempt | New evidence from the previous output | Bound as new input; earlier input bytes stay unchanged |

A versioned source is read at its bound revision. A mutable source is captured with its actual response and read time; the read time proves neither freshness nor completeness.

Fixed calculations and formal checks execute deterministically under the sanctioned rule. A model may supply declared parameters, extract content or interpret evidence within its assigned job; retain its used configuration and decision-relevant result. Inspect extracted values against their source before a dependent calculation. Interpretation and nondeterministic extraction do not establish source truth or deterministic reproducibility.

## Access routes

Source form says what a collection is; the access route says how a reader reaches it. Record both, and record the effect separately.

| Route | Reader reaches the data by | Effect | Record at the source home | Record in provenance | Typical failure |
|---|---|---|---|---|---|
| Versioned file | Path at a repository revision | read | Path, owner | Revision, path, digest | Working copy read instead of the bound revision |
| Shared or mutable file | Path on a drive or share | read; write possible | Path, owner, update rhythm | Read time, digest, selection | Later edits silently included |
| Export | File produced by a person or job from a system | read | Producing system, table, filters | Export time, producer, table, filters | Export treated as the system |
| Report | Saved view with its own filters and formulas | read | Underlying table, report filters | Report version, run time | Report filters inherited unseen |
| Manual input | A named person supplies values | read | Recurring channel, if maintained | Person, date, question, confirmation | One answer treated as a maintained source |
| API | Documented endpoint | read or write | Endpoint family, version, auth conditions | Endpoint, parameters, response, read time | Documentation taken as access |
| CLI | Command against a system or file | read or write | Command family, version | Command, version, arguments, output, read time | Write-capable command used without a declared effect |
| MCP server | Tool exposed by a configured server | read or write | Server identity and version, tool names | Server and tool, arguments, response, read time | Listed tool taken as permission |

The four findings stay separate, each with its own evidence:

| Finding | Established by | Does not establish |
|---|---|---|
| Documented | Reading the interface or export description | Access, values, permission |
| Access verified | One actual read with the configured reader | Completeness or freshness |
| Data acquired | Bound bytes with provenance | Authority or permission for this use |
| Use permitted | The applicable authority for this purpose, such as a processing agreement or owner decision | Correctness of values |

The step names route kind and operation in its tool line; credentials stay with the harness. A write-capable route grants no permission: the job declares the effect and establishes its required authority and checks. A missing finding blocks only the use that depends on it: without verified live-system access, an already acquired mutable export with provenance can still support one recalculation within its stated scope if use for that purpose is permitted.

## Writing it in the step

The Quellenanforderung keeps its stable labels. `Ursprung` names the actual file or external source to be read, with a link to its existing source description and use condition. The description locates meaning and selection; it does not replace acquisition origin in provenance. `Stand` carries the required source state, not the read time. The processing body names route, operation, timing and effect. Synthetic German fixture:

```markdown
### Quellenanforderung

- Quell-Eingabe: `input/materialbestand.csv`
- Herkunft: `Lesezugriff ERP-Materialbestand`
- Ursprung: `ERP, Materialbestand` ([Quellenbeschreibung](grundlagen/lieferzeit.md#quelle-erp-materialbestand): nur Bestand je Artikel und Lager; Preise nicht)
- Stand: `fachlicher Stand 2026-09-16 06:00`
- Erforderliche Kontrolle: `Schlüssel eindeutig; fehlende Bestände gezählt; für diesen Job keine Ersatzwerte`

### Quellenanforderung

- Quell-Eingabe: `input/kapazitaet.csv`
- Herkunft: `Lesezugriff Produktionsplanung`
- Ursprung: `Produktionsplanung, freie Kapazität` ([Quellenbeschreibung](grundlagen/lieferzeit.md#quelle-produktionsplanung): sechs Wochen ab Stichtag)
- Stand: `Planungsstand 2026-09-16 06:00`
- Erforderliche Kontrolle: `Wochen und Einheiten vollständig; fehlende Kapazität bleibt offen`

## Verarbeitung

3. Beschaffung vor Öffnen dieses Versuchs: ERP über CLI `erp-read` 4.2,
   Operation `bestand --artikel <ids> --stichtag <datum>`,
   nur lesend. Produktionsplanung über MCP-Server `planung` 1.3, Werkzeug `kapazitaet_lesen`,
   nur lesend. Antworten materialisieren; Argumente, Quellenstand, Lesezeit und tatsächliche
   Kontrolle in den beiden deklarierten Herkunftsdateien festhalten, bevor die Eingaben
   gebunden werden. Bei fehlendem Zugriff diesen Versuch nicht öffnen; konkreten Blocker
   und zulässige Beschaffung/Fortsetzung festhalten. Verarbeitung nutzt die gebundenen
   Eingaben; kein Ersatzwert und keine Änderung ihrer Herkunftsbytes.
```

The `*-herkunft.md` file follows the [stable-source provenance template](../../capabilities.md#provenance-file-example): source state, acquisition time, selection, reader, digest, and required versus actual control each keep their own field.

## Feeding back

Four ways a result leaves a step. Only the first changes a continuing business record.

Attempt paths, digests and byte-identical handoff mappings apply to selected Core Runs. Ordinary work retains the applicable source, check and effect evidence at its existing case home. A Core failure-route handoff needs its own declared producer mapping, just as a success-route handoff does.

| Way | When | How | Evidence |
|---|---|---|---|
| Permitted record writeback | After its required checks and any required gate are satisfied | Apply [Record writeback](../../capabilities.md#rückübertragung-in-geschäftsrecords): target, scope, authority, freshness, conflict and confirmation | Target, version, confirmed or unconfirmed |
| Handoff to a successor | On the declared route | Byte-identical output into the successor's input with provenance | Handoff mapping, digest |
| Visible output | With the attempt | Ordinary output file; a report or draft stays a run result | Output file and checks |
| Change of meaning | When a definition or mapping must change | [Author or change](../../ontology.md#author-or-change) at the domain home; not a run effect | New definition revision |

The source mapping selects the leading system for an authoritative attribute update. A permitted copy, export or downstream record does not become another fact authority. Use the existing writeback contract for confirmation and retry handling; a business key alone does not make a write repeat-safe.

## Checks before calculating

Select checks required by the calculation's grain, rule and intended use; these are examples, not universal admission criteria. Keep any missing premise and its dependent-use restriction explicit. When a provider such as the leading system, a calculation service or a Capability delivers a derived item, the applicable rows below are premises its provider must evidence; the consuming step checks that evidence for fit to its use and keeps an unevidenced premise `open`.

| Object | Check |
|---|---|
| Metric | A rule with unit, aggregation and population exists; a stated value is recalculated for one period and the difference explained or kept `open` |
| Derivation rule | Inputs, constants, parameters and assumptions have declared meaning and source or authority. For a combined ratio, calculate from the combined numerator and denominator; a mean of individual ratios is a different metric. Apply medians or other aggregations only under their stated definition |
| Measure | Identify the relevant event, stock/state, period or derived quantity and its source fields or rule. Count missing values and distinguish them from zero; any imputation requires an explicit applicable rule and retained evidence |
| Event | Compare event, validity and entry clocks where the calculation depends on them; test the declared ordering with its time-zone and correction rules |
| Field | Fill rate in the period is measured; type and unit are uniform |
| Data collection | Check the complete key against the declared row grain; count duplicates and required-period gaps. Trace report filters/formulas and export source/state; where needed, reconcile with the underlying data |
| Key mapping | Declare multiplicity and show unmatched and multiple matches. Before aggregation, check whether the join repeats a measure; aggregate the contributing side to the needed grain or apply an explicitly sanctioned allocation. A legitimate one-to-many relationship remains one-to-many, not a first-match lookup |
| Chain | A result's support is limited by each needed input and rule premise; retain their separate evidence and scope instead of inventing a combined confidence score |
| Comparison across cases or periods | Same definition and population on both sides, including cases that left; outcomes mature at the as-of time or the open share stated; composition checked before a difference is read as change |
| Segment, cluster or outlier | Enough cases per group; group assignment as of the event time; the number of groups scanned stated |
| Projection | History over several cycles under one definition; no input from after the as-of time; fit and sensitivity under [Scenario use](../../impacts-method.md#scenario-use); an expectation carries its range and base rate over a stated horizon. When the result steers who is acted on, later outcomes reflect that steering; retain who was acted on and why, so that [Test](../../impacts-method.md#test) can separate that effect |

## Worked example: estimated delivery time

Synthetic design continuation of the [ontology relationship example](../../ontology.md#example-rechenweg-lieferzeit-angebot). The proposed job `lieferzeit-schaetzen` would apply `rechenweg:lieferzeit-angebot` for one offer request and hand the estimate to offer preparation in the [offer pipeline](datenbezug.md#reusable-offer-pipeline). The parent example reports revision 3 but supplies no adoption decision; rule sanction, actual access and purpose-specific use permission remain `open` and block the dependent calculation and use. The table describes required preparation and intended processing, not completed stations.

| Station | In this step |
|---|---|
| Define | Resolve `kennzahl:geschaetzte-lieferzeit` and the proposed rule revision at `grundlagen/lieferzeit.md`; establish its sanction before dependent calculation and bind the required definitions as inputs |
| Locate | Intended mappings: `quelle:erp-materialbestand` for stock per item and warehouse; `quelle:produktionsplanung` for free capacity per week. Confirm their leading-system scope with the responsible source owner |
| Reach | Proposed ERP CLI and planning MCP readers, both read-only. Verify documentation, configured access and permission for this purpose; none is established by this example |
| Bind | Stock excerpt for the requested items at cut-off 06:00 and capacity for six weeks, each with `*-herkunft.md` |
| Check input | Keys unique; missing stock counted; capacity weeks complete |
| Process | Code applies the rule; the model only writes the explanation text |
| Check result | Estimate recalculated from bound inputs; the rule's assumptions listed |
| Hand off | To `vorbereiten`: first action, place the estimate on the offer positions; needed content, estimate in calendar days, rule revision, inputs' source state and stated limits |
| Write back | None in this step. The offer system leads the offer revision; the estimate reaches it only through the separately permitted writeback after offer approval |

The example records no executed read, check, approval or writeback.

## Limits

This reference adds no Core field, schema, parser label or command. Naming a route proves no access; a filled table proves no availability. Transport, credentials, isolation and execution remain with the harness.
