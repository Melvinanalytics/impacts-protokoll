# Process decomposition: from observed work to the five objects

Read this at the method's [Perfect](../../impacts-method.md#perfect) and [Augment](../../impacts-method.md#augment) phases. Each rule names the test that decides a cut.

## Leistung

The valued end state that leaves the process. Test: an identified recipient can accept or use it under observable conditions. Payment or movement of an organisational KPI matters only where relevant. `ergebnis` names the state, `kennzahl` its lagging indicator, `abnahme` the conditions under which it counts as reached. One Leistung per Hauptprozess. Two candidates that cannot be merged into one end state are two Applications.

## Hauptprozess

The complete path from `einstieg_ref` to the Leistung. Every terminal outcome gets its own `end:<slug>`, the negative ones included: `end:absage`, `end:ausser-scope`, `end:abgebrochen`. A path that can only end well is incomplete.

Include preparation or an offer in the Hauptprozess when it belongs to the same accepted Leistung. A separately accepted, reusable offer process can have its own Leistung. Determine this from the actual result boundary, not a universal sales lifecycle.

## Teilprozess

A closed context section. Test: a person can describe its `ergebnis` without describing the other sections. Cut at the handoffs that survived Minimize, not at department borders. Each Teilprozess states its contribution to the accepted result. Include a leading indicator only when it supports a concrete steering decision under [Identify](../../impacts-method.md#identify); its relation to the result remains `hypothesis` until supported by observed runs.

## Arbeitsschritt

One coherent job with a visible, verifiable result. Cut a new step when a separately needed result, route or authority boundary requires its own declared inputs, output and check. An actor or tool change alone does not earn a new step; human, agent and deterministic contributions may compose inside one job. Gate readiness still follows the Capability contract below. Declare:

- `eingaben`: paths under `input/` of the attempt. Stable references stay at their single home in `grundlagen/`, `records/` or an external system; the run materializes the smallest professionally sufficient source or projection plus a separate `*-herkunft.md` under attempt `input/`. Apply [Snapshot and provenance](../../capabilities.md#snapshot-und-herkunftsnachweis) for materialization, binding and hashing.
- `ausgaben`: paths under `output/`; drafts remain editable, while bound or completed outputs require a traceable new revision.
- `pruefung`: one observable verification rule; it may reference several relevant checks. A long explanation alone does not earn a new step.
- `routen`: named by the outcome of `pruefung`; targets are steps or ends.
- `gate: human` only where a person must carry authority, risk or a legal act. Then the routes are exactly `freigegeben` and `abgelehnt`.
- `customer_touchpoint`: `standard` when a person leads the interaction and the harness prepares it; `sacred` when the interaction is protected and a reclassification needs human review of the Application. Declare the effect and responsible human; apply the [execution preflight](../../capabilities.md#signale-und-human-gate).

The body follows the template: One job, Inputs, Excluded context, Processing, Outputs, Check, Human check. [Workstep composition](../../impacts-method.md#compose-an-arbeitsschritt) defines how its prompt, tools and data form one executable job; every input has a source/acquisition or producer handoff, every output a check and permitted use.

When the Arbeitsschritt calls reusable processing, apply the [Capability extraction criteria](../../capabilities.md#wann-extrahieren) and [local call contract](../../capabilities.md#capability-aufruf). The Arbeitsschritt names only the local call tuple, inputs, expected output and minimum check; it does not duplicate the Capability contract.

For handoffs, follow [Visible output and handoff](../../capabilities.md#sichtbare-ausgabe-und-übergabe). The producer declares the mapping once; the run creates byte-identical consumer input plus provenance. The general validator does not verify provenance claims.

Before opening a Human Gate, apply [Signals and Human Gate](../../capabilities.md#signale-und-human-gate). Producer-close/Gate-open is one logical transition, without claimed filesystem atomicity. Opening grants neither route nor `freigabe`; `pruefung` evaluates the later human output. The general validator neither enforces preflight nor authenticates a person.

## Waits

A wait is a `wartend` Laufpfad entry with `wiedereinstieg` (`ausloeser`, `continuation_ref`). Work such as acquiring missing documents belongs to the current declared job; required human interaction gets its applicable touchpoint. Permitted preparation can continue within that job under [Work from prerequisites](../../impacts-method.md#work-from-prerequisites). The waiting entry remains current until its declared continuation; no separate wait node is needed.

## Loops

For a declared rework loop, route rejection to the step that produced the rejected input. A declared final rejection follows its negative end. Every loop leaves through a `pruefung` outcome that reaches an end; the validator rejects a loop without exit.

## Automation boundary

Use the human constraints established in [Identify](../../impacts-method.md#identify) to choose only the contributions needed for this job:

| Contribution | Suitable work | Boundary |
|---|---|---|
| Deterministic system | Explicit rules, calculations and reproducible checks | Requires valid rules, appropriate inputs and permission for any external action |
| Agent | Variable language, interpretation and proposals | States uncertainty and stays within permitted actions; a proposal is not authority |
| Human | Required interaction, accountable judgement or authorization | Decision scope and permitted consequence must be understandable |

These are not exclusive step classes. Input variance, tolerance, harm, reversibility and detectability inform the mix and required checks; frequency informs whether implementation effort is worthwhile, not who has authority. Record the choice in the existing processing body. Gate and touchpoint semantics remain as declared above.

## Naming

Slugs match `[a-z0-9]+(-[a-z0-9]+)*`. Folder name equals slug. IDs are `hauptprozess:<slug>`, `teilprozess:<slug>`, `arbeitsschritt:<slug>`, `vorgang:<slug>`. Teilprozesse carry nouns (vorpruefung, entscheidung), Arbeitsschritte carry the verb (pruefen, entscheiden). Ends carry the outcome (entschieden, absage).

## Evidence

Claims in definitions, records and reviews carry their source and one label:

- `verified`: the specific claim is supported by an inspectable check or a confirmed decision within the decision-maker's authority. Name what was checked or decided and for which scope.
- `reported`: a source or person states the claim; its factual content has not been verified.
- `hypothesis`: an interpretation or proposal awaiting validation.
- `open`: an unanswered question or missing input.

Inspecting a brochure can verify its wording while its delivery promise remains `reported`. A confirmed decision establishes the chosen rule within its scope; it does not verify an external fact. Keep contradictory evidence reachable and the unresolved conclusion `open`. Labels do not confer freshness, business permission or authenticated human approval. A document-level label applies only where it fits; qualify differing claims inline. An Application with unlabelled facts is not finished.
