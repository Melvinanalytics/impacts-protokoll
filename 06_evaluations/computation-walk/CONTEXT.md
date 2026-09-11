# Computation walk — synthetic, optional

This is a small example of independently testable calculation, not a universal business model, new Core profile or production-approved Capability. A non-commercial process can use capacity analysis without inventing prices, customers or a sales funnel.

| Question | Read or run | Stop when |
|---|---|---|
| What is calculated, with what assumptions? | [Calculation contract](formeln.md) | The needed operation and its limits are clear. |
| Which concrete inputs were used? | [Synthetic snapshot](scenario.json) | Subject, window, values and declared origins are identified. |
| How is it calculated? | [Sanctioned example implementation](run.py) | The relevant operation is identified; do not execute source text from input data. |
| Does the arithmetic and dependency handling work? | [Behavioral tests](../../tests/test_computation_walk.py) | The selected positive and negative cases have been executed. |
| How does an actual Application bind a Capability? | [Public Capability rule](../../02_protocol/capabilities.md#capability-aufruf), then [existing cold walk](../cold-walk/CONTEXT.md) | Application, resolved revision and invoked code are bound by the host harness. |

From the repository root, the example only reads its input and writes JSON to stdout:

```bash
python3 06_evaluations/computation-walk/run.py 06_evaluations/computation-walk/scenario.json
python3 -m pytest -q tests/test_computation_walk.py
```

Baseline: conditional demand 120 cases, production bound 80, review bound 120, modeled volume 80, operating-result scenario EUR 12,000 for the stated month. These are synthetic arithmetic outputs, not business observations.

This CLI does not create or advance a Vorgang, validate external sources, authenticate a reviewer or authorize a business effect. Its file digest measures the local rule file; it does not prove that a previously approved revision was executed. The existing cold walk covers that separate host binding. No combined production deployment is claimed.

For customer adoption, put the approved domain definition at its existing formula home, the actual dated inputs in the relevant attempt and the visible result under `output/`. Extract a Capability only under the public rule. The example's folder, JSON keys and filename are not mandatory protocol structures.
