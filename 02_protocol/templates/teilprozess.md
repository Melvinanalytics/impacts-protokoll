---
type: teilprozess
id: teilprozess:vorpruefung
ergebnis: Reviewable check report
---

# Preliminary review

A subprocess is a coherent domain section of the main process. Its worksteps are subfolders; its folder name is its ID slug. Replace example values in the customer's working language.

## Contribution to the result

State one coherent result this section contributes, its recipient or consuming section and its permitted use. Explain how `ergebnis` contributes to the main process's accepted result; do not restate the main process or child worksteps.

## Inputs and boundaries

Name the upstream results, domain definitions, rules, resources and authority required across this section. State the relevant exclusions and the conditions under which the section cannot claim its result. Point to each source home; do not copy its content into this subprocess contract.

## Workstep composition

Map every required component of `ergebnis` to the workstep that produces it. For an internal handoff, reference the producer's declared handoff and applicable check without restating its paths or maintaining a second route table. At a terminal boundary, name the final recipient, accepted result and applicable end instead of inventing a downstream consumer. Every child workstep must contribute to this section result.

## Setup completion

Definition setup is complete when every result component has a producing workstep, visible output and applicable check; each internal result references its consuming boundary, while each terminal result names its final recipient and end. Every required input is obtainable or explicitly open with a next action and use restriction, and no child job or claim sits outside this section's contribution. Before the candidate commit, review a supported case, a missing or conflicting prerequisite and a plausible forbidden inference across this section; record premises, expected outcomes and open gaps. After commit, the Test phase supplies observed harness evidence against that revision. Structural validity and design review do not establish execution readiness or `ergebnis`.

## Leading indicator

Include only when an early observation supports a concrete steering decision: name the indicator, proposed relationship to the result metric and possible action. The relationship remains `hypothesis` until observed runs support it. Otherwise omit this section; contribution and section result remain required.
