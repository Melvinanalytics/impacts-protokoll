# Calculation contract: bounded scenario comparison

Status: synthetic example. Operation authority: [run.py](run.py); behavior is checked through its CLI by [the tests](../../tests/test_computation_walk.py). This document defines interpretation and applicability, not a second independently editable calculator.

## What belongs where

| Responsibility | Existing home | Boundary |
|---|---|---|
| Meaning, method, parameters and applicability | Domain formula file or earned Capability | No customer-specific rule becomes a Core requirement. |
| Expected sources and minimum controls | Calling Arbeitsschritt | Do not repeat the formula implementation. |
| Actual values, origin and time basis | Input snapshot of one attempt | Unknown stays unknown; the snapshot is not the live source of truth. |
| Values, blockers and interpretation | Ordinary output file | Correct arithmetic does not release a commitment. |
| Next process action | Existing `pruefung` and route | A knowledge link is not an execution edge. |

An input's declared origin is not independent source verification. Revisions, manual checks or monitoring are bound by the calling Arbeitsschritt according to use and risk, under the [public governance rule](../../02_protocol/capabilities.md#data-governance). This example has no source connector: all data is explicitly synthetic. `as_of` records the scenario timestamp; it does not establish source freshness or a validity period. `verified` in a supplied snapshot cannot authenticate its author or make a result current.

## Selected operations

| Operation | Interpretation | Required scope |
|---|---|---|
| Demand | Distinct eligible buyers × reached share × buyer conversion × frequency | Buyer denominator, deduplicated reach and one common window; not already purchase occasions. |
| Resource capacity | Usable pool hours / effort per accepted case | Effort includes required review/rework. Hours belong to the same window. |
| Modeled volume | Minimum of demand and all declared resource bounds | Homogeneous comparable cases, non-overlapping pools and no omitted dominant constraints. |
| Unit contribution | Net price minus genuinely volume-variable cost | Explicit accounting boundary, EUR per case in this example. |
| Operating-result scenario | Modeled volume × unit contribution, less retained fixed and incremental operating cost | Complete period costs; retained payroll is not simultaneously claimed as avoided spend. |

Demand and economics are optional; each named resource requires hours and effort. Missing demand means there is no modeled total volume. Missing one required pool prevents a combined volume claim, while other resource capacities remain usable as conditional results. A known zero is not missing. Invalid units are not silently converted. No parameter defaults to zero.

The code declares supported parameter names, units and numeric domains and emits the question for each unusable input. The snapshot supplies values, evidence labels and origins. Results expose local dependency names under `inputs`; these are local calculation bindings, not global node IDs. UI tables or a graph may project those bindings instead of maintaining a second dependency list. Identifying a responsible person for a resulting question belongs to the concrete Arbeitsschritt; the demo does not invent a customer role.

## Partial, negative and changed outcomes

| Synthetic configuration | Modeled volume | Operating result/month | What it shows |
|---|---:|---:|---|
| Baseline | 80 | EUR 12,000 | Production limits this scenario. |
| Production effort halved; EUR 2,000 added cost | 120 | EUR 26,000 | The limit moves to demand/review. |
| More reach; total additional cost EUR 3,000 | 120 | EUR 25,000 | More demand alone adds no volume at this review limit. |
| Same scenario plus review capacity 160 | 160 | EUR 41,000 | Both constraints matter; this is not a causal prediction. |
| Lower-demand baseline | 60 | EUR 4,000 | Demand is limiting. |
| Faster production at the same low demand | 60 | EUR 2,000 | Local speed improvement can reduce the operating result. |
| Review hours unknown | unknown | unknown | Demand, production bound and contribution remain calculated; ask for review availability. |

The tests independently check these values and mutations. Compare complete configurations, not summed headline benefits of overlapping interventions. Changed input bytes change the input digest; the previous output is not rewritten. Cross-run change detection, comparison-window compatibility and invalidation are not implemented by this CLI.

## Limits that a caller must keep visible

- This is an aggregate continuous-volume model, not scheduling, queueing, product-mix optimization, a delivery promise or integer batch planning. Customer-specific thresholds, discounts, setup times and capacity reservations are out of scope.
- Declaring the four assumptions `true` makes the scenario evaluable; it does not prove those assumptions in reality. An unconfirmed assumption blocks the combined bound. Independent partial calculations remain conditional.
- Staff effort, elapsed customer time, actual accepted throughput, expenditure and cash are different measures. This example does not calculate lead-time improvement, actual output, working-capital release or causal ROI.
- A human, agent and deterministic system may contribute within the same Arbeitsschritt. The calculator replaces none of the remaining authority or interaction requirements.
- The complete input bytes and output evidence are visible. Do not supply secrets or unnecessary personal data. A production harness controls access, isolation and retention.
- Runtime: Python 3.11+ standard library, Decimal precision 28; finite nonnegative inputs, positive effort, shares in [0,1]. Results are decimal strings. This example performs no financial settlement rounding; a real financial calculation needs its own approved rounding rules.
- The local rule-file digest is diagnostic, not execution attestation or trust approval. Production reuse needs the Application-bound revision and host checks in the Capability contract.

## Transfer recipe

Start from a concrete decision or accepted result, not a list of every possible KPI. Follow its calculation to the needed inputs and their existing evidence. Keep ambiguity at that source home; do not turn an estimate into a confirmed rule. If repeated operations earn their own boundary, bind the existing Capability form rather than adding a generic computation engine.

For a folder such as `grundlagen/analyse/formeln/`, its router should answer: which question, which sanctioned operation, which variable/source bindings, which test and which missing-input question? Domain IDs or `edges` may help an existing local graph, but the protocol does not require one file per variable or a universal business ontology. If a retained graph and executable input list express the same dependency, derive one from the other or enforce parity.
