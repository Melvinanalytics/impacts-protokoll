# Capability contract

Owns: reusable operation contracts, extraction, calls, evidence and transport. Reader: author; harness for calls and transport. Does not own: universal source binding and execution, see [Binding and execution](binding.md).

A Capability is an optional reusable operation inside an Arbeitsschritt. It can return values, judgments, selections, proposals, decision results or evidence of a permitted effect. A Capability cannot make a decision reserved for a human. Received decision evidence keeps its actual origin. Gates, waits, customer touchpoints, routes and execution state belong to the Arbeitsschritt and its Vorgang under [Execution](binding.md#execution); the harness retains the actual result and enforces the declared use conditions. Its domain contract, implementation and checks live together outside the Hauptprozess tree. This file owns Capability contracts. Universal source binding and execution follow [Binding and execution](binding.md). [Meaning and valid inference](ontology.md#meaning-and-valid-inference), [evidence and obligations](ontology.md#evidence-and-obligations), and [enforcement and completion](ontology.md#enforcement-and-completion) stay in the ontology instruction; the [language contract](language.md#enforce-at-use-boundaries) owns customer-readable presentation.

For early workspace routing when connecting domain Capabilities, follow [Capability orientation](impacts-architect/references/formwahl.md#capability-orientation).

## Responsibilities

A technical use condition states when an operation's result is applicable. The Capability definition owns the reusable operation, parameters, link to the sanctioned rule and technical use conditions.

## When to extract

Every bound calculation references its sanctioned rule. Extract a Capability only when at least one applies:

- Several Arbeitsschritte or Hauptprozesse need the same operation.
- It has an independent deterministic core.
- It has independent source, freshness or checking rules.
- It needs versioning independently of the Arbeitsschritt.

Otherwise keep it in the Arbeitsschritt. Use `capabilities/<slug>/` in the Fachrepo or workspace, outside Core and the Hauptprozess.

## Calculation Capability

Keep a compact revision-bound contract: operation/purpose; parameter shape with units, granularity and time; link to the sanctioned rule and its revision at its [Foundations home](impacts-architect/references/formwahl.md#data-kinds); failure and blocking cases including data requirements per use; deterministic checker; visible evidence format; fixtures; sensitivity cases only where result tolerance matters.

Operation definition, rule link, implementation, checker, evidence format and fixtures share one Capability revision. A rule change is a Foundations revision. A Git tree OID binds files, not interpreter/library environments. Declare result-affecting environments as technical use conditions.

## Capability call

The Arbeitsschritt binds its local call without repeating the domain contract. These parser labels stay stable across languages:

```markdown
- Aufruf-ID: `liefertermin-1`
- Capability-Pfad: `capabilities/liefertermin/CONTEXT.md`
- Capability-Revision: `git-tree:<oid>`
- Operation: `liefertermin-berechnen`
```

For one call, its ID may derive as `<arbeitsschritt-slug>-1`; multiple calls need explicit IDs. The [cold walk](../06_evaluations/cold-walk/CONTEXT.md) reads this block and requires the derived value to be written before binding the revision. It supports one call in the example Arbeitsschritt; general multiple-call execution is not established.

The bound call identity is the tuple of call ID, resolvable path, tree OID and operation in the bound Hauptprozess. Before the call, the harness binds a reachable workspace revision, resolves the Capability's parent directory there and requires the same tree OID. It executes that tree and writes the workspace revision and tuple into the ordinary result evidence. The Capability does not attest its own origin.

The OID establishes identity, not trustworthiness. A production harness executes only domain-approved revisions. Isolation, permissions, secrets and runtime environment remain outside Core.

```text
Capability call -> Visible output -> pruefung -> Route
```

## Evidence

Capability evidence is an ordinary `output/` file in the Capability's own format. It shows bound rule, used inputs, result, executed checks, assumptions and technical use conditions. A parameter table or equivalent block list suffices; no receipt schema is introduced.

## Transport

Transport a Hauptprozess alone if it has no Capability calls. Otherwise materialize each needed `capabilities/<slug>/` from the same source repository revision at the same relative path. Commit the transported Capability trees before the first Vorgang uses them, then require `git rev-parse <workspace-revision>:capabilities/<slug>` to equal the bound tree OID. Missing or mismatching paths prevent execution. No package manifest or Core resolver is introduced.

## Limits

The optional [computation example](../06_evaluations/computation-walk/CONTEXT.md) demonstrates parameters, partial results, blockers and scenario comparison. Domain formulas remain at their existing home. It defines no universal computation profile, registry, database, extractor, required API, monitoring service or automatic approval.
