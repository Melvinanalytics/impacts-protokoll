# Zuschnitt: from observed work to the five objects

Read this at Perfect and Augment. Each rule names the test that decides a cut.

## Leistung

The valued end state that leaves the process. Test: someone pays for it, or an organisation's primary KPI moves when it arrives. `ergebnis` names the state, `kennzahl` its lagging indicator, `abnahme` the observable conditions under which it counts as reached. One Leistung per Hauptprozess. Two candidates that cannot be merged into one end state are two Applications.

## Hauptprozess

The complete path from `einstieg_ref` to the Leistung. Every terminal outcome gets its own `end:<slug>`, the negative ones included: `end:absage`, `end:ausser-scope`, `end:abgebrochen`. A path that can only end well is incomplete.

Bidding before delivery: when bids are specific to this Leistung, the Angebot is the first Teilprozess of the delivery Hauptprozess and a lost bid is a named end. It becomes its own Application only when one bid process serves several Leistungen in the same workspace.

## Teilprozess

A closed context section. Test: a person can describe its `ergebnis` without describing the other sections. Cut at the handoffs that survived Minimize, not at department borders. Each Teilprozess states its Beitrag zur Leistung and one Frühindikator; the indicator stays `hypothesis` until runs support it.

## Arbeitsschritt

One job. Cut a new step when the inputs change, the actor changes, or the tool changes. Declare:

- `eingaben`: paths under `input/` of the attempt; stable references from `grundlagen/` or `records/` are named in the body under Eingaben, never copied into the tree.
- `ausgaben`: paths under `output/`. Every output is a file a human can edit before the next step reads it.
- `pruefung`: one observable criterion. If it needs a paragraph, split the step.
- `routen`: named by the outcome of `pruefung`; targets are steps or ends.
- `gate: human` only where a person must carry authority, risk or a legal act. Then the routes are exactly `freigegeben` and `abgelehnt`.
- `customer_touchpoint`: `standard` when a person leads the interaction and the harness prepares it; `sacred` when the interaction is protected and a reclassification needs human review of the Application.

The body follows the template: Ein Job, Eingaben, Nicht laden, Verarbeitung, Ausgaben, Prüfung, Human Check.

## Waits

A wait is not a step. It is a `wartend` Laufpfad entry with `wiedereinstieg` (`ausloeser`, `continuation_ref`). A wait that carries its own work, chasing documents for example, is a step with `customer_touchpoint: standard` whose attempt goes `wartend`.

## Loops

A rejection routes back to the step that produced the rejected input, not to the entry. Every loop leaves through a `pruefung` outcome that reaches an end; the validator rejects a loop without exit.

## Automation boundary

Decide the execution form per step from these dimensions:

| Dimension | Points to code or Capability | Points to the model | Points to a human |
|---|---|---|---|
| Eingangsvarianz | low, structured | high, language | high, judgement |
| Ergebnistoleranz | tight, exact | wide | wide, but accountable |
| Häufigkeit × Dauer | high | medium | low |
| Schadenshöhe | low | low | high |
| Umkehrbarkeit | reversible | reversible | irreversible |
| Entdeckbarkeit | a check can see the error | a check can see the error | nobody would notice |
| Touchpoint | none | none | `standard` or `sacred` |

Rule of thumb: low variance, tight tolerance and high frequency mean code. High variance in language means the model, with `pruefung` in code. High harm, low reversibility or a sacred touchpoint mean a human gate. Universal thresholds do not exist; write the decision and its reason into the step body.

## Naming

Slugs match `[a-z0-9]+(-[a-z0-9]+)*`. Folder name equals slug. IDs are `hauptprozess:<slug>`, `teilprozess:<slug>`, `arbeitsschritt:<slug>`, `vorgang:<slug>`. Teilprozesse carry nouns (vorpruefung, entscheidung), Arbeitsschritte carry the verb (pruefen, entscheiden). Ends carry the outcome (entschieden, absage).

## Evidence

Every fact in an Application body is labelled: `verified` when a source or the customer confirms it, `reported` when a person said it, `hypothesis` when the architect inferred it, `open` when nobody knows yet. An Application with unlabelled facts is not finished.
