# Zuschnitt: from observed work to the five objects

Read this at Perfect and Augment. Each rule names the test that decides a cut.

## Leistung

The valued end state that leaves the process. Test: an identified recipient can accept or use it under observable conditions. Payment or movement of an organisational KPI matters only where relevant. `ergebnis` names the state, `kennzahl` its lagging indicator, `abnahme` the conditions under which it counts as reached. One Leistung per Hauptprozess. Two candidates that cannot be merged into one end state are two Applications.

## Hauptprozess

The complete path from `einstieg_ref` to the Leistung. Every terminal outcome gets its own `end:<slug>`, the negative ones included: `end:absage`, `end:ausser-scope`, `end:abgebrochen`. A path that can only end well is incomplete.

Include preparation or an offer in the Hauptprozess when it belongs to the same accepted Leistung. A separately accepted, reusable offer process can have its own Leistung. Determine this from the actual result boundary, not a universal sales lifecycle.

## Teilprozess

A closed context section. Test: a person can describe its `ergebnis` without describing the other sections. Cut at the handoffs that survived Minimize, not at department borders. Each Teilprozess states its Beitrag zur Leistung and one Frühindikator; the indicator stays `hypothesis` until runs support it.

## Arbeitsschritt

One coherent job with a visible, verifiable result. Cut a new step when a separately needed result, route or authority boundary requires its own declared inputs, output and check. An actor or tool change alone does not earn a new step; human, agent and deterministic contributions may compose inside one job. Gate readiness still follows the Capability-Regel below. Declare:

- `eingaben`: paths under `input/` of the attempt. Stable references stay at their single home in `grundlagen/`, `records/` or an external system; the run materializes the smallest professionally sufficient source or projection plus a separate `*-herkunft.md` under attempt `input/`. Both declared inputs are hashed.
- `ausgaben`: paths under `output/`. Every output is a file a human can edit before the next step reads it.
- `pruefung`: one observable verification rule; it may reference several relevant checks. A long explanation alone does not earn a new step.
- `routen`: named by the outcome of `pruefung`; targets are steps or ends.
- `gate: human` only where a person must carry authority, risk or a legal act. Then the routes are exactly `freigegeben` and `abgelehnt`.
- `customer_touchpoint`: `standard` when a person leads the interaction and the harness prepares it; `sacred` when the interaction is protected and a reclassification needs human review of the Application.

The body follows the template: Ein Job, Eingaben, Nicht laden, Verarbeitung, Ausgaben, Prüfung, Human Check.

When the step calls reusable processing, follow the single public [Capability-Regel](../../capabilities.md). The workstep names only the local call tuple, inputs, expected output and minimum check; it does not duplicate the Capability contract.

For a step handoff, the Application declares `A/output/datei.md -> B/input/datei.md` exactly once in the producing workstep beside its output and route. The run copies bytes and adds `B/input/datei-herkunft.md` with a current-Vorgang-relative, three-digit-attempt origin such as `a/002/output/datei.md` and lowercase SHA-256 over raw file bytes. Producer `ausgabe_hash` and consumer `eingabe_hash` bind separate surfaces; they are not compared. The general validator does not verify origin or content-digest claims.

Before opening a `gate: human` step, the harness checks its proposed declared inputs and required control evidence without mutating the run. It then performs one logical producer-close/Gate-open transition; transactional filesystem atomicity is not claimed. The open Gate has neither route nor `freigabe`. The human produces the Gate output and decision; `pruefung` remains evaluation of that output. The general validator does not authenticate a person or enforce the preflight.

## Waits

A wait is not a step. It is a `wartend` Laufpfad entry with `wiedereinstieg` (`ausloeser`, `continuation_ref`). A wait that carries its own work, chasing documents for example, is a step with `customer_touchpoint: standard` whose attempt goes `wartend`.

## Loops

A rejection routes back to the step that produced the rejected input, not to the entry. Every loop leaves through a `pruefung` outcome that reaches an end; the validator rejects a loop without exit.

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

Every fact in an Application body is labelled: `verified` when a source or the customer confirms it, `reported` when a person said it, `hypothesis` when the architect inferred it, `open` when nobody knows yet. An Application with unlabelled facts is not finished.
