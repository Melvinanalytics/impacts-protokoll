# Process decomposition: from observed work to Leistung, Hauptprozess, Teilprozess and Arbeitsschritt

Owns: the Leistung test, the cut into Hauptprozess, Teilprozess and Arbeitsschritt, when a gate, wait, loop or check is declared, executor choice at the automation boundary, and folder naming. Reader: author. Does not own: what happens when a declared element runs, see [Execution](../../binding.md#execution).

Read this at the method's [Perfect](../../impacts-method.md#perfect) and [Augment](../../impacts-method.md#augment) phases. Each rule names its boundary test. Core fields, trees and attempt contracts apply when selected under [Tooling stop](formwahl.md#tooling-stop); source and evidence requirements apply to every form.

## Leistung

The valued state leaving the Hauptprozess. Test: an identified recipient can accept or use it under observable conditions. `ergebnis` names the state, `kennzahl` its readable result-metric statement and `abnahme` the conditions or thresholds under which it counts as reached. Link `kennzahl` to an independently maintained domain metric when one is cited, reused or changed; observed values remain case evidence. A metric without an established process remains domain knowledge and does not earn a Hauptprozess.

## Hauptprozess

The complete path from `einstieg_ref` to the Leistung. Each terminal state gets its own `end:<slug>`, including negative ends: `end:absage`, `end:ausser-scope`, `end:abgebrochen`. A path that can only end well is incomplete.

A Hauptprozess defines one kind of Leistung; each Vorgang owes one instance of it, from the Auslöser of its entry Arbeitsschritt to a terminal state an outsider could check, such as accepted, refused, cancelled, killed, or an owed condition met or missed by its deadline. A Vorgang achieves the Leistung when its result fulfills the acceptance and completion conditions, whether an internal or external party accepts it. Where `leistung.erreicht` is declared, it lists the ends that achieve the Leistung; every other end is negative. A later claim against a fulfilled obligation, such as a defect notice, is the Auslöser of another Vorgang; rule 3 decides whether its remedy needs another Hauptprozess.

1. **New Leistung.** Open another Vorgang when further work owes a Leistung beyond the scope the current Vorgang owes; it belongs to another Hauptprozess only when the existing result contract cannot represent it (rule 3). Exercising an option or amending the same obligation before its end stays in the current Vorgang; after that end it opens another Vorgang. Waiting for the reply to this obligation stays inside; the reply that discharges it is its end, even when it is also the Auslöser of the next Vorgang. A separately commissioned assessment or decision with its own Leistung and completion conditions requires a separate Vorgang; rule 3 decides whether the existing Hauptprozess can represent it. A choice required within the current obligation stays in its job or gate. Override rights decide authority, not the cut.
2. **Instance.** The subject (*Gegenstand*) is the domain object a Vorgang's Leistung is owed for. One Vorgang per subject that reaches its own terminal state. A period, round or batch is the subject when the Leistung is owed for it as a whole.
3. **Definition.** Another definition is needed when the existing result and control contract cannot represent the required work. Supported input-bound scope, acceptance parameters and routes are configuration; identical end labels alone do not establish equivalent contracts.
4. **Never alone.** A change of actor, tool, executor, document type, object count, recipient or duration does not cut.
5. **Tie.** Keep work together unless separating removes evidenced coordination, recovery or duplicate-definition work.

## Teilprozess

Group Arbeitsschritte under the [protocol meaning](../../ontology.md#protocol-vocabulary). Test: a person can describe its `ergebnis` without describing the other Teilprozesse. Cut by result; a department or person boundary signals a possible handoff but does not cut by itself. On its positive route, the grouped Arbeitsschritte produce or complete one required component of the [Leistungsstückliste](../../impacts-method.md#leistungsstückliste) with its joints, or establish an evidenced prerequisite for the remaining path. Its `ergebnis` names that contribution. A prerequisite alone does not justify a separate Teilprozess. Completing includes reaching required component states such as checked or released. A negative end does not claim successful completion of the Teilprozess; preserve evidence of components already produced, completed or delivered and effects already caused. Other work stays inside the Teilprozess it serves.

## Arbeitsschritt

One coherent job with a visible, verifiable result. Cut a new Arbeitsschritt when a separately needed result, route or authority boundary requires its own declared inputs, output and check. An actor or tool change alone does not earn a new Arbeitsschritt. Contributions of different executors may compose inside one job. Gate readiness still follows the [gate rules](../../binding.md#signals-and-human-gates). Declare:

- `eingaben`: declare only the inputs every case of the Leistung has; an input some cases lack is no prerequisite and is reached through a declared input such as an index or record. Declared inputs are referenced by source path and digest in the attempt's `gelesen`. Stable references keep their source home; apply [Snapshot and provenance](../../binding.md#snapshot-and-provenance).
- `ausgaben`: paths under `output/`; drafts remain editable, while bound or completed outputs require a traceable new revision. Every declared output surface contains at least one regular file when its attempt completes, on every selected route; directory surfaces and zero-byte regular files are allowed. Each file must satisfy the declared meaning of that output.
- `pruefung`: one observable verification rule; it may reference several relevant checks. A long explanation alone does not earn a new Arbeitsschritt.
- `routen`: named by the check result, the value `pruefung` returns; targets are Arbeitsschritte or ends.
- `gate: human` only where the applicable rule reserves an actual decision, approval or legal act for the responsible person. Then the routes are exactly `freigegeben` and `abgelehnt`, or solely `entschieden` under [Decision results and Auslöser](../../binding.md#decision-results-and-auslöser); the declared output preserves the actual decision and its evidence under [Signals and human gates](../../binding.md#signals-and-human-gates).
- `customer_touchpoint`: `standard` or `sacred` as [Identify](../../impacts-method.md#identify) defines them. Declare the effect and responsible human; apply the [execution preflight](../../binding.md#signals-and-human-gates).

For source mappings needed by this Arbeitsschritt, apply [Source descriptions](datenumgang.md#source-descriptions).

The body follows the template: one section per [step area](../../impacts-method.md#step-areas), with Excluded context as part of Inputs, plus Setup completion. [Arbeitsschritt composition](../../impacts-method.md#compose-an-arbeitsschritt) defines how its prompt, tools and data form one executable job; every input has a source/acquisition or producer handoff, every output a check and permitted use.

When the Arbeitsschritt calls reusable processing, apply the [Capability extraction criteria](../../capabilities.md#when-to-extract) and [local call contract](../../capabilities.md#capability-call). The Arbeitsschritt names only the local call tuple, inputs, expected output and minimum check, without duplicating the Capability contract.

For handoffs, follow [Visible output and handoff](../../binding.md#visible-output-and-handoff).

See [Signals and human gates](../../binding.md#signals-and-human-gates) for opening and recording a human gate.

See [Waits](../../binding.md#waits) for waiting attempts and expiry transitions.

### Synthetic example across levels

`hypothesis`: design example, not observed execution evidence.

| Level | Forecast example |
|---|---|
| Hauptprozess | Finanzielle Vorausschau (`finanzielle-vorausschau`) defines a period forecast and the path to it. |
| Leistung | A quantity and value forecast for the period; `kennzahl` measures the percentage of forecast-backed capacity decisions in the recipient's November planning review that cite this forecast within seven days of delivery; `abnahme` requires traceable offer and study assumptions and checked quantity and value calculations. |
| Teilprozess | Mengeneffekte (`mengeneffekte`) groups the Arbeitsschritte for forecast quantities; Werteffekte (`werteffekte`) groups those for forecast values. These are the two result components. |
| Arbeitsschritt | Under `mengeneffekte`, `angebotsmengen-ermitteln` and `studienmengen-ermitteln` produce the offer and study quantity components, then `mengengeruest-ziehen` checks their total. Under `werteffekte`, `mengen-bewerten` applies the declared prices and checks the value calculation. |
| Vorgang | The November forecast owes this Leistung for November as its whole subject under rule 2. It achieves the Leistung when the quantity and value outputs fulfill `abnahme`. |

Assume November has 10 forecast units from offers and 5 from studies, all at EUR 100 per unit. `mengengeruest-ziehen` checks `10 + 5 = 15` units; `mengen-bewerten` checks `15 * 100 = 1500` EUR under the rule forecast value = forecast quantity times unit price. These numbers are synthetic design premises. The EUR 1,500 is a calculated output; observing the recipient-use metric does not delay acceptance because this example's `abnahme` does not require it.

Missing study quantities leave the forecast incomplete under this acceptance contract; a checked offer component alone does not achieve the Leistung. Changing the person calculating values does not create another Teilprozess: the result boundary stays the same.

The same November subject continues into `kapazitaetsplanung`, a second Hauptprozess whose Leistung is a checked capacity plan. Its entry rule takes the delivered forecast end as Auslöser. `vorgang:kapazitaet-november` binds `vorgang:vorausschau-november`'s checked output as a source with `sha256`; it does not route back into that Hauptprozess. Both Subject sections link `records/perioden/november/CONTEXT.md`. The period-kind home declares `forecast-needed`, `forecast-delivered`, `capacity-planned` once. The record's `Stage: forecast-delivered` cites the delivery event and links both Vorgänge and their commitment.

Synthetic decision `entscheidung:planung-11` records the planning holder, 2026-11-10 decision date, source and revisions for November and December: "approve November capacity; defer December". Both period records cite that one decision. A gate requesting this selection uses `entschieden`; the selection is its readable output. Example derived due-list line: `November | capacity plan owed | planning holder | 2026-11-12T17:00:00+01:00 | decision planung-11 and forecast output | open capacity Vorgang when inputs pass`. This line coordinates; the record and bound outputs keep the facts. A missing forecast blocks only its dependent plan. An outside recipient's later response is a received source at the period record and does not reopen the delivered forecast Vorgang.

## Loops

For a declared rework loop, route to the producer or a separate rework Arbeitsschritt whose already-declared inputs carry the rejected result and the rejection details needed for that job. The rejecting Arbeitsschritt's output and handoff must supply that content, possibly together in one file, compatible with the inputs' bound meaning and shape. Every declared input must have applicable content on every attempt, including the first; do not add an input to the bound definition during a Vorgang. If the producer has no suitable declared input, define a separate rework Arbeitsschritt before binding the Hauptprozess. See [Loops](../../binding.md#loops) for executing a return route. Every loop has a check result that reaches an end; the validator rejects a loop without exit, but this does not prove that execution will take it. Declare each loop's bound before further repetition: a counted unit with a source-backed limit or, for a loop whose passes start only when an outside event arrives that the loop did not request, a source-backed deadline after which no further pass starts. For either bound, declare the responsible follow-up and the permitted limit handling: escalation or a stop. Apply the [time and counting evidence requirement](../../ontology.md#enforcement-and-completion) before selecting that check result. A continuing service bounds each activation or review interval, not the service lifetime. Technical retries have their own declared budget and uncertain-effect recovery; they neither consume nor reset a business-pass count unless its rule says so. A missing bound remains a design gap, not permission for unbounded repetition; a counter reset cannot bypass it.

## Automation boundary

An executor is who or what performs a contribution.

First apply Identify's independent [result-work and coordination questions](../../impacts-method.md#result-work-and-coordination) and Minimize the observed arrangement. Those answers expose contribution and dependency without selecting executors, conferring authority or creating exclusive Arbeitsschritt types.

Before selecting an executor, apply [Augment's point-of-use context](../../impacts-method.md#augment) requirements for each retained contribution.

Use the human constraints established in Identify to choose only the contributions needed for the resulting job:

| Executor | Suitable work | Boundary |
|---|---|---|
| Deterministic system | Explicit rules, calculations and reproducible checks | Requires valid rules, appropriate inputs and permission for any external action |
| Classifier | Recurring judgments whose answer is one value from a supplied set: a yes/no/open test, one category or an ordered rating | The set includes `open` or abstention; behavior must be evaluated on representative repeated cases before reliance; the answer is a typed judgment, not evidence of the classified fact, permission or a business metric |
| Agent | Variable language, interpretation and proposals | States uncertainty and stays within permitted actions |
| Human | Required interaction, accountable judgement or authorization | Decision scope and permitted consequence must be understandable |

Test each model contribution by its output. If its answer is a category from a supplied scheme, a yes, no or open, or a rating, no fixed rule decides it, and it recurs, design it as a classifier contribution. A smaller dedicated classifier may be evaluated for it as a lower-latency, lower-cost option than a general model; neither benefit nor quality is established until that evaluation covers this exact question. Keep a general model where the output is variable language. Independent judgments stay separate questions; choosing an action considers only currently eligible candidates.

These are not exclusive Arbeitsschritt classes. Result work may require a deterministic calculation, human authorization or physical operation; necessary routine coordination may be deterministic or agent-assisted. Frequency informs whether implementation effort is worthwhile, not who has authority. Record the executors in the existing processing body. For automatic extraction by a view, use one list item per contribution beginning with `Deterministic system:`, `Classifier:`, `Agent:` or `Human:`. Other wording remains source text; a view does not infer an executor from it. Gate and touchpoint semantics remain as declared above.

### Required checks and review

At design time, the responsible human uses the method's constraints to determine essential and optional checks and reviews for the intended result. Assess result tolerance together with input variation:

- What harm could a wrong result cause?
- Would the mistake be discovered before that harm occurs?
- Could the result or effect be reversed, and at what cost?

Consider how inputs can vary or violate the assumed premises; variable inputs need applicable source controls and exception handling. Declare the required conditions, permitted use and failure consequence in the existing criterion/body before execution. This qualitative decision adds no numerical score, field or mandatory form. Reuse an already authorized design decision or configuration for routine checks; no fresh approval ceremony is needed. If consequential premises change, the responsible human reassesses the design. For an uncalibrated recurring job, the design may declare temporary quality review: whether it is essential, its purpose, accountable reviewer, withdrawal evidence and reinstatement condition. A person checking quality does not by itself add `gate: human`. Withdrawing an essential review requires design reassessment. For changed bound work, withdrawal also requires a reviewed new definition revision. The executing agent applies the declared choice within assigned authority and cannot guess or demote essential checks. An undeclared consequence stays a design question; independent permitted preparation continues.

Low result tolerance does not automatically require Git. Fixed calculations need actual deterministic calculation checking; that establishes neither input truth nor permission. Variable inputs do not justify probabilistic money calculations. This assessment can underestimate harm; passing declared checks does not repair a mistaken assessment. Files declare the requirements and guide the agent; mechanical enforcement can be claimed only for conditions actually enforced by an available checker or harness.

## Naming

Below a stage folder, folders carry domain names; level names are types declared in each `CONTEXT.md` frontmatter, never folder names. The linked tree supplies the executing agent's context. Name Teilprozesse with nouns and Arbeitsschritte with verb phrases, as in the [synthetic forecast example](#synthetic-example-across-levels). Ends name terminal states. Slug and ID rules: [layout rules](../../binding.md#hauptprozess-tree-rules).
