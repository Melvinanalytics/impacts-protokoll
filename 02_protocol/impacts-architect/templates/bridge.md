# Reality and Leistungsstückliste bridge: <offering or result name>

Compact one-page analysis for `analyse/` before a stable process exists; for a deep capture of running multi-step work, use [ist-prozess.md](ist-prozess.md). It connects what the recipient receives (`Leistungsstückliste`, see `02_protocol/impacts-method.md#leistungsstückliste`) with backward-derived prerequisites and observed company reality (`A#`), before deciding what to delete, merge, keep as a job section in its owning file or build as a `hauptprozesse/` Pipeline. Mark every claim `verified`, `reported`, `hypothesis` or `open` with its source.

## 1. Result boundary

- **Unit:** `<subject> | <who owes whom> | <Auslöser event> | <ends, negative ones included>`
- **Commercial boundary:** `<Offering | Demand | Delivery | Supply or capacity>` (`02_protocol/impacts-architect/references/zuschnitt.md#commercial-boundary-cut`)
- **Acceptance (`abnahme`):** `<observable conditions under which the recipient accepts the result>`
- **Guardrail:** `<what must not be harmed: confidentiality, workspace separation, release gate, workload>`

## 2. Leistungsstückliste (what the recipient receives)

`C#` is a component, `J#` a joint between components.

| ID | Element | Acceptance / check | Evidence |
|---|---|---|---|
| C1 | `<deliverable part or frame>` | `<observable check>` | `reported` |
| C2 | `<deliverable part>` | `<observable check>` | `hypothesis` |
| J1 | `<C1 <-> C2: required consistency, shared number or transition>` | `<observable joint check>` | `open` |

## 3. Backward prerequisite trace

Trace each `C#` and `J#` backwards to its source, rule, resource or decision.

| Target | Required prerequisite | Home & workspace (Foundation / Provider record / Customer record / Decision) | Owner & access | Evidence |
|---|---|---|---|---|
| C1 | `<needed fact, calculation or blank>` | `<path, workspace or external system>` | `<owner; accessible or gap>` | `open` |
| J1 | `<rule reconciling C1 and C2>` | `<path or rule owner>` | `<owner>` | `open` |

## 4. Company reality overlay

Map observed activities (`A#`), waits and friction onto `C#`, `J#` and guardrails. An activity that serves none of them is a `Minimize` candidate.

| Activity | Observed work | Serves (`C#` / `J#` / guardrail / none) | Friction, bottleneck & counter-explanation | Evidence |
|---|---|---|---|---|
| A1 | `<what happens today>` | `C1` | `<wait, rework, copy, search; and what else could explain it>` | `reported` |
| A2 | `<what happens today>` | `none` | `<duplicate check or channel copy; and what else could explain it>` | `hypothesis` |

## 5. Minimize and home decision

Target home is one of: `entfaellt`, a job section in the existing owning file (`grundlagen/...#<section>`), `hauptprozesse/<slug>/`, `grundlagen/`, `records/`, or `open`.

| Item | Proposed move | Target home | Why (and open question) |
|---|---|---|---|
| A2 | `entfaellt` | `entfaellt` | `<serves no C#, J# or guardrail>` |
| A1 | Keep as one recurring job | `<owning file>#<job section>` | `<recurs in one pass; no multi-step state>` |
