# IMPACTS Protocol

**Make your business easier for people and AI to work in.**

IMPACTS helps small and medium-sized businesses understand their business, simplify work, and use AI and data science without becoming specialists. Use your files to clarify a result, find sources, prepare work and name the next decision.

**Ordinary files and folders are a complete way to use IMPACTS.** It is a manual, an execution protocol and a structure; its framework is not a runtime. An agent needs file access and appropriate read/write permissions. Give it a task: “Clarify this offer from these sources; show what is missing and what I need to decide.”

[Prepare your first useful contribution](FIRST-WIN.md): an internal offer draft, its sources, an unresolved delivery question and a next action a session can recover. No installation needed.

**Flexible in how it thinks. Uncompromising in what counts.** Agents may interpret and draft; checked calculations need actual deterministic checks, and human decisions remain human. Missing facts stay missing. A hash, Git history or structural check supplies neither business truth nor authenticated approval. The mission describes intended benefit; examples establish only their stated conditions, with no acceleration, usability or universal harness compatibility claim.

## Follow your task

| You have… | Start here |
|---|---|
| Notes or an undocumented business | [Form selection](02_protocol/impacts-architect/references/formwahl.md) |
| An offer to clarify | [First contribution](FIRST-WIN.md) |
| A bounded, repeatable result | [Build method](02_protocol/impacts-method.md) |
| An existing bound Run | Its `vorgaenge/<id>/CONTEXT.md` and linked inputs |
| A calculation to check | [Computation example](06_evaluations/computation-walk/CONTEXT.md) |

The [root router](CONTEXT.md) locates authorities; knowledge and records keep their homes. English owns the protocol. German customer work stays German: [operator guide](02_protocol/translations/de.md) · [language contract](02_protocol/language.md).

## Optional technical use

Call machine validation for a needed check when a suitable checker is available. An unavailable or failed check leaves its condition unestablished: preparation continues while the dependent claim or action waits. Explain progress, consequence and next action; retain raw diagnostics for maintainers. [Form selection](02_protocol/impacts-architect/references/formwahl.md#tooling-stopp) owns this boundary.

The CLI supplies `init`, `template`, `validate` and `hash`. Application-only validation checks implemented structure, references and paths without Git. Current historical Run validation needs Git and committed Application binding. Neither establishes definition completeness or execution; a configured harness executes structured Runs.

Get the complete protocol at a published tag so the method, Architect references and examples share one revision:

```bash
git clone --branch v0.3.4 --depth 1 https://github.com/Melvinanalytics/impacts-protokoll.git
cd impacts-protokoll
```

For file-only use, the matching source archive on the [release page](https://github.com/Melvinanalytics/impacts-protokoll/releases/tag/v0.3.4) also supplies the complete protocol. Keep its files together and start at `CONTEXT.md`. For CLI-only use, the release wheel and `SHA256SUMS` supply the installable package; the wheel omits the method and examples.

For the CLI, use Python 3.11+ in the protocol checkout:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
impacts init ../impacts-demo
impacts validate ../impacts-demo
impacts template arbeitsschritt
```

`init` creates an empty Core workspace (`CONTEXT.md`, `applications/`, `vorgaenge/`), refuses an existing target and creates no Git repository or runnable process. Keep it beside the checkout. Add `--language de` to `init` or `template` for German. Initialize Git at the Core root before committing an Application for Run binding.

Explore the [Application template](02_protocol/templates/application.md), [schemas](02_protocol/schemas/), [Capabilities](02_protocol/capabilities.md) and [Architect skill](02_protocol/impacts-architect/SKILL.md); keep the skill's sibling references together. The programmed [offer walk](06_evaluations/offer-walk/CONTEXT.md) retains checked synthetic preparation at a pending human gate; the [cold walk](06_evaluations/cold-walk/CONTEXT.md) exercises loops, waits, synthetic gates and transport.

## Develop and contribute

Read [AGENTS.md](AGENTS.md) and the nearest `CONTEXT.md`; update rules at their existing homes.

```bash
python -m pip install -e . pytest setuptools
python -m pytest -q
python3 06_evaluations/complexity-budget/check.py
```

`setuptools` is needed for development packaging tests using `--no-build-isolation`. Run evaluations from their linked guides. Local checks cover Python 3.11/3.14 on macOS. The distribution supplies CLI, schemas and templates; use the complete checkout for method, Architect, examples and tests.

Submit [issues](https://github.com/Melvinanalytics/impacts-protokoll/issues) or [pull requests](https://github.com/Melvinanalytics/impacts-protokoll/pulls) with revision, expected/observed behavior and a synthetic case. Exclude private customer material; update affected German surfaces and report checks not performed. Tests, files-only consumer checks and release decisions are separate.

[Apache License 2.0](LICENSE).
