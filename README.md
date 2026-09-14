# IMPACTS Protocol

**Make your business easier for people and AI to work in.**

IMPACTS helps small and medium-sized businesses understand their business, simplify work, and use AI and data science without becoming specialists. Use your files to clarify a result, find sources, prepare work and name the next decision.

**Ordinary files and folders are a complete way to use IMPACTS.** It is a manual, an execution protocol and a structure; its framework is not a runtime. An agent needs file access and appropriate read/write permissions. Give it a task: “Clarify this offer from these sources; show what is missing and what I need to decide.”

[Prepare your first useful contribution](FIRST-WIN.md): an internal offer draft, its sources, an unresolved delivery question and a next action a session can recover. No installation needed.

**Flexible in how it thinks. Uncompromising in what counts.** Agents may interpret and draft; checked calculations need actual deterministic checks, and human decisions remain human. Missing facts stay missing. A hash, Git history or structural check supplies neither business truth nor authenticated approval. The mission describes intended benefit; examples establish only their stated conditions, with no acceleration, usability or universal harness compatibility claim.

## Get the protocol

For new work, get the complete source archive from the [v0.3.4 release](https://github.com/Melvinanalytics/impacts-protokoll/releases/tag/v0.3.4), or clone that tag:

```bash
git clone --branch v0.3.4 --depth 1 https://github.com/Melvinanalytics/impacts-protokoll.git
cd impacts-protokoll
```

Keep the complete source together: method, Architect, references, templates and examples. Reading the archive needs no installation. A copied Architect folder is incomplete even when its `references/` folder is present: it also depends on parent protocol files and root guidance. The wheel contains the CLI, schemas and templates; using its generated workspace with the method requires the matching complete source.

## Version and entry points

The source edition is `[project].version` in the root [pyproject.toml](pyproject.toml). For an installed package, run `python -m pip show impacts-protocol` in the Python environment that supplies `impacts` and read `Version`. Published package version `X` corresponds to release tag `vX`. This identifies the package edition; it does not identify an exact source revision or establish compatibility.

Record the actual source location and identity in the customer's existing root `CONTEXT.md`. In a Git checkout, use `git rev-parse HEAD` and `git status --short` to record the commit and any local changes; retain a release tag only when it identifies that source. Without Git, record the archive's actual origin, tag or filename and local source location; retain an available checksum and describe local changes. An archive filename alone is not proof of its contents. Keep unavailable identity or conflicting versions explicit; obtain the corresponding source before applying a rule whose version cannot be resolved. A checkout beyond a release or modified files must be identified as such, even if the edition in `pyproject.toml` is unchanged.

| Starting surface | Entry and completion |
|---|---|
| Complete protocol source | Read this protocol's root [CONTEXT.md](CONTEXT.md), then the selected task route. Keep customer work in its own folder. |
| New or existing customer folder | Read that folder's `CONTEXT.md`; record or follow its actual protocol source/revision and working language. Resolve `02_protocol/` paths against that source. |
| Existing Core Run | Start at its `vorgaenge/<id>/CONTEXT.md` and declared inputs. Preserve its bound Application, sources and language; a newer installed package or protocol does not upgrade them. |
| Wheel or copied skill with missing source | Recover the source/revision from provenance: published versions from [releases](https://github.com/Melvinanalytics/impacts-protokoll/releases), unreleased revisions from the recorded original repository or file snapshot. Resolve the needed links there before applying their rules. |

Entry is resolved when the task's router, source identity and required links are reachable without substituting `main`, another release or model memory. If something is missing, retain the gap and next action; independent permitted preparation can continue. Changes to existing definitions follow [Reviewed correction](02_protocol/impacts-method.md#reviewed-correction), while earlier bound work retains its revisions.

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

For the CLI, use Python 3.11+. In your chosen working folder, create and activate a virtual environment (shown for macOS/Linux):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Choose one installation source:

- **Complete checkout:** from its root, run `python -m pip install -e .`.
- **Release wheel:** download the wheel and `SHA256SUMS` from the release above into one folder. From that folder, verify with `shasum -a 256 -c SHA256SUMS` (macOS/Linux), then install with `python -m pip install ./impacts_protocol-0.3.4-py3-none-any.whl` only if the checksum matches.

Follow [Version and entry points](#version-and-entry-points) to identify the installed package and obtain its complete source. Then, outside the intended new customer folder:

```bash
impacts init ../impacts-demo
impacts validate ../impacts-demo
impacts template arbeitsschritt
```

`init` creates an empty Core workspace (`CONTEXT.md`, `applications/`, `vorgaenge/`), refuses an existing target and creates no Git repository or runnable process. Keep the customer workspace separate from the protocol source. Add `--language de` to `init` or `template` for German. Initialize Git at the Core root before committing an Application for Run binding.

Explore the [Application template](02_protocol/templates/application.md), [schemas](02_protocol/schemas/), [Capabilities](02_protocol/capabilities.md) and [Architect skill](02_protocol/impacts-architect/SKILL.md). The programmed [offer walk](06_evaluations/offer-walk/CONTEXT.md) retains checked synthetic preparation at a pending human gate; the [cold walk](06_evaluations/cold-walk/CONTEXT.md) exercises loops, waits, synthetic gates and transport.

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
