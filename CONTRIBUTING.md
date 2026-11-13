# Contributing

Changes enter `main` through a reviewed pull request. Keep customer material in its customer repository. Report the revision, expected and observed behavior, synthetic evidence, and checks not run.

### v0.5.0

This edition checks folder structure, and it breaks every workspace that moves its pin: `impacts validate` fails a workspace pinned to v0.5.0 until each top-level folder declares its form in one root-router line, `Form: <folder>/ <form> per <unit>`. A workspace still pinned to v0.4.x is not judged by this check; rehearse the lift on a copy, since the findings appear only on the new pin. The forms are Pipeline, Record Library, Knowledge Bundle and Context Map; code folders take `Capability`, `Tool` or `Check`. `records/` is a Record Library, `grundlagen/` a Knowledge Bundle, `capabilities/` a Capability, and only `analyse/` is a Context Map. Three issue codes are new: `topology.form_missing`, `topology.form_invalid` and `topology.shape`. The check flags undeclared top-level folders, mixed Record Library levels, Hauptprozess definitions outside `hauptprozesse/` and Context Map levels, router links that break, or leave the workspace from a level, and Knowledge Bundle entries that are unlinked, undeclared, date-named or named after a record instance. A folder that cannot move yet is held by a row a person writes in the root router, never an agent; the check lists it on every run and never enters it. Dot-entries and entries Git ignores are skipped. The check proves declared shape, links and names, not an entry's kind; only review finds a unit spelled differently in two homes, or a case folder declared as a sub-level under another name. JSON reports list held folders under `held`.

Each record kind starts as one table; once a subject earns its own folder, the table moves into the kind's `CONTEXT.md`. A Knowledge Bundle refuses copies of received sources: they stay at their record home and are cited by path, revision and digest. A hand correction of a result counts as a demonstrated defect, unless it sets a case value or an exceptional preference, and goes to its home under Reviewed correction. `impacts init` writes a `.gitignore` for system and office leftovers (`Thumbs.db`, `desktop.ini`, `~$*`).

See [Folder structure by form](02_protocol/impacts-architect/references/formwahl.md#folder-structure-by-form) for the forms and what the check fails on.

### v0.4.1

This edition changes protocol text only; schemas, required fields, issue codes, CLI commands and conformance cases are unchanged, and v0.4.0 pins stay judged. One Vorgang now carries one obligation: a bid, the award that ends it and the order it creates are separate Vorgänge, and the commitment that creates an obligation is its Auslöser, never a prerequisite. Before a tree is drawn, its repeating unit is stated in one line: subject, who owes whom, the outside event it is owed from and every end. Three cut questions are asked when cutting and before a repository moves its protocol pin. A workspace with more than one Hauptprozess keeps a value-chain table in its root router. Loop passes made in a predecessor count toward its successor's bound, and open predecessor work binds as a record source.

See [Process decomposition](02_protocol/impacts-architect/references/zuschnitt.md#hauptprozess) for the repeating unit, the cut rules and the synthetic supply chain.

### v0.4.0

This edition uses `hauptprozesse/` and `hauptprozess_revision` and requires workspace and Vorgang `protocol` pins for new work; work recording another major.minor and marked legacy work is reported as not judged rather than failed. Validator text starts with a status line and links failed checks to their rules; JSON reports use `report_version: 3`. An `ablage` reference must name a store declared in the workspace root router.

See [Breaking changes from v0.3](README.md#breaking-changes-from-v03) for the full list.

### v0.3.32 selected Vorgang pages in process

This edition adds an optional argument to `impacts_protocol.view.site_model`. Schemas, required fields, issue codes, CLI commands and conformance cases are unchanged; existing Hauptprozesse and Vorgang files stay valid with the same meaning.

See [Optional technical use](README.md#optional-technical-use) for the current `site_model(workspace, vorgaenge=...)` API contract.

Outside this edition: parallel branches inside one Vorgang, which needs a schema change, and preparing later steps ahead of their turn. Core required fields are unchanged. The wheel includes the static Viewer HTML resource and 14 templates: seven English and seven German.

The protected tag workflow includes this version's section from `CONTRIBUTING.md` in its generated Release body and appends the actual workflow test evidence. Local preparation notes are review inputs, not an uploaded Release body. The workflow rebuilds the wheel and source archive; only the resulting published `SHA256SUMS` identifies the published asset bytes.

## Bounded Linux dependency install

For a fresh virtual environment running CPython 3.11 on Linux x86_64 with glibc 2.17 or newer, the checkout includes a hash-enforced install recipe:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python .github/scripts/install_runtime.py
```

Run it from the complete checkout. It checks the interpreter, architecture, libc and virtual environment; installs binary dependencies from the PyPI index with `--require-hashes`; then installs this checkout editable without resolving dependencies again. Record the checkout's Git commit. The lock binds selected wheel bytes for this target. It does not bind Python, pip, the checkout's authenticity, build provenance or package publishers. It makes no dependency-closure claim for other Python versions, operating systems, architectures or libc versions.

## Three useful contributions

1. **Independent implementation.** Implement the [declared JSON structural subset](06_evaluations/conformance/CONTEXT.md#independent-implementation-challenge) from its written contract and frozen cases. Disclose previous exposure to this repository's source and tests, record the candidate revision and exact run scope, and add independently authored cases. A shared-corpus pass alone is incomplete and no pass claims full protocol conformance or production suitability.
2. **Unaccompanied first-use record.** Use the no-install [first-win exercise](FIRST-WIN.md) without coaching. Retain the instruction/source revision, what the operator could find and complete, observed blockers, open items, next action and checks actually performed. An internal walkthrough or coached repair is not an unaccompanied user result.
3. **Bounded listening-adapter result.** Apply a named, revision-bound capture adapter through the [listening-intake screen](06_evaluations/nontechnical-reconstruction/listening-intake.md), including its counterbalanced blocks, fresh operators, retained inputs/outputs, blinded scoring, effort accounting and stop rule. Report hard failures and missing data. Do not present one adapter output, a synthetic simulation or model evaluation as a completed screen, Langdock result or customer validation.

Use the repository's [issue forms](.github/ISSUE_TEMPLATE/) to propose or report scoped work and its [pull request template](.github/PULL_REQUEST_TEMPLATE.md) for changes. The public community routes are GitHub [issues](https://github.com/Melvinanalytics/impacts-protokoll/issues), [pull requests](https://github.com/Melvinanalytics/impacts-protokoll/pulls) and [Discussions](https://github.com/Melvinanalytics/impacts-protokoll/discussions). Discussions are for exploratory questions; issues hold scoped findings and evidence, and pull requests hold reviewed changes. To object to a claim or contract, cite its exact source and scope, give a counterexample or evidence, and propose the smallest correction. An open objection is not an approval or maintainer decision. Public adoption issues accept only synthetic or already-public evidence, a non-sensitive reference and bounded scope, and a sanitized summary. Keep customer records and raw sources, captured outputs, and review records in the customer repository; never attach or link them in a public issue. Do not submit credentials, personal data or live access state.

## Finding classes and current disposition

An issue should name the source revision, inspected scope, evidence path, exact command and result, and checks not performed. A `reported` observation must remain attributed; a frozen expected result is not an observation from a candidate run.

| Finding class | Current disposition | Evidence needed for a useful report |
|---|---|---|
| Diagnostics | Frozen cases require their listed codes/results; message wording remains diagnostic. Documented parse or routing prerequisites suppress dependent conclusions, while independent defects remain reportable. | Minimal synthetic files, exact candidate command, JSON report, expected and observed codes/paths, source revision, and checks performed. |
| Provenance-template distribution | **Closed for the published v0.3.20 wheel:** `impacts template herkunft` is included in the wheel CLI and English/German templates, with nine fields. | For a distribution defect, give the installed package version, wheel SHA-256, command, language and captured output; do not use a universal line-count expectation. |
| Durable native release evidence | **Closed for the published v0.3.20 Release:** its publicly readable release notes retain Python test totals and exact Windows/macOS corpus reports from the successful tagged workflow. The notes remain editable and label these results as workflow-reported evidence. | For a reporting defect, give tag, source commit, workflow URL/attempt, runner platform/runtime, corpus digest/count and retained release-note result. A workflow configuration alone is not execution evidence. |
| NTFS and platform boundary | **Open outside named runner results.** The hosted Windows job does not identify every filesystem or establish universal NTFS behavior; unsupported cases are not passes. | Name OS version, filesystem, runtime, relevant case capability, command, raw output and exact unsupported/failure reason. Do not generalize beyond that environment. |
| Dependency closure | **Bounded only:** hash-enforced selected wheels for Linux CPython 3.11 x86_64 with glibc 2.17 or newer. Other targets remain open. No publisher-authenticity claim. | Name Python implementation/version, pip, OS, architecture, libc, dependency source, lock revision, command and install result. State whether the target is inside the recipe's bound. |
| Public-review reproducibility | **Open for independent third-party reruns.** Release notes retain workflow-reported test evidence after publication; this is not independent verification or a build attestation. | Give the published source commit, exact inputs/command/environment, candidate output and independently retained result. Report access limits and checks not performed. |

## Compatibility and change process

English owns the active contract. Reuse the current file/template/schema home and state the concrete gap before adding a field, role, file kind, command or version. Preserve machine tokens and Core schemas unless a separately evidenced gap and reviewed change authorize their update. Keep German readable surfaces aligned and refresh their source-byte hashes.

For JSON CLI changes, `report_version` versions the report shape. Message text is diagnostic. `cases.json` defines the exact required results for its listed cases; a changed frozen expectation needs an explicit fixture or expected-result diff, rationale and fresh runner evidence. Do not create a parallel protocol or conformance-specification version. A new structural claim needs named cases and stated limits. Keep reference implementation tests separate from the implementation-independent corpus.

Pull requests should link the issue or bounded gap, name changed authority files, provide synthetic evidence and exact checks/results, disclose checks not run, and update affected translations. Maintainers review the actual diff and evidence through repository permissions and GitHub records; an author cannot create approval by entering a name or identifier. Preserve the issue, reviewed source revision and decision rationale in the repository so a successor can continue. If no authorized maintainer is available, leave the change unmerged and its status explicit rather than inventing a review or transferring authority by text.

## External adoption and deployment gates

These gates remain **open**. CI, Luna-generated output, synthetic replays, internal model reviews or repository instructions do not substitute for the named external evidence.

Each linked contract owns its pass rule and licensed sentence. Its execution issue links the contract and records each run in comments: the freeze commit, the evidence and a named maintainer's closure decision after review of the frozen evidence. A closed gate supports only its licensed sentence, at the revision that sentence names.

| Gate | Authoritative contract | Execution issue |
|---|---|---|
| Independent implementation | [Independent implementation challenge](06_evaluations/conformance/CONTEXT.md#independent-implementation-challenge) | [#27](https://github.com/Melvinanalytics/impacts-protokoll/issues/27) |
| Unaccompanied first use and correction | [Follow-up Gate A](06_evaluations/nontechnical-reconstruction/FOLLOW-UP.md#gate-a) | [#28](https://github.com/Melvinanalytics/impacts-protokoll/issues/28) |
| Second operator after 168 elapsed hours | [Follow-up Gate B](06_evaluations/nontechnical-reconstruction/FOLLOW-UP.md#gate-b) | [#29](https://github.com/Melvinanalytics/impacts-protokoll/issues/29) |
| Listening intake in authorized Langdock | [Listening-intake screen](06_evaluations/nontechnical-reconstruction/listening-intake.md) | [#30](https://github.com/Melvinanalytics/impacts-protokoll/issues/30) |
| Bounded domain review | [Follow-up Gate C](06_evaluations/nontechnical-reconstruction/FOLLOW-UP.md#gate-c) | [#31](https://github.com/Melvinanalytics/impacts-protokoll/issues/31) |
| Matched business comparison | [Follow-up Gate D](06_evaluations/nontechnical-reconstruction/FOLLOW-UP.md#gate-d) | [#32](https://github.com/Melvinanalytics/impacts-protokoll/issues/32) |

Production use outside the declared inspected public repository scope is unknown.

## Publish an edition

An edition claim spans source text and public delivery. `pyproject.toml`, the annotated Git tag, GitHub Release, release assets, README URLs and filenames, the German guide, and installed package metadata must name the same version. A green documentation test establishes only the source-tree part.

Run the complete repository checks in the clean public candidate tree. A source checkout with additional private directories is not that release surface; prepare the complete allowlisted export first rather than raising the budget or suppressing failures. Retain the candidate tree identity and check the actual predecessor selected by the complexity gate against the intended prior release. An uncommitted tree check does not establish the later release commit or its ancestry.

Use this order:

1. Create `release/vX.Y.Z` from current public `main`.
2. Change `[project].version` plus all release URLs, clone commands, wheel filenames and edition wording in `README.md` and `02_protocol/translations/readme.de.md`. Regenerate affected translation hashes.
3. Run the complete repository checks. Open and review the release pull request. Do not create a public Release from an unmerged branch.
4. Merge the reviewed release commit. Create an **annotated** `vX.Y.Z` tag on that exact public `main` commit and push the tag once.
5. The tag workflow uses a read-only build job to check the tag, source claims and full test suite on Python 3.11 and 3.14; build the wheel and complete source archive on Python 3.11; and write `SHA256SUMS`. A separate publish job downloads those checked bytes without installing or running package code, uploads exactly the three artifacts to a hidden draft Release, verifies their remote names and SHA-256 digests, and attaches compact test evidence to the draft body before publication by numeric ID. Evidence must match the source and workflow run, with both interpreters from the same build attempt. Retrying only publication may reuse that successful earlier build attempt. The publicly readable body labels JUnit counts including subtests as workflow evidence, not independent verification or attestation.
6. Verify that `main`, `vX.Y.Z`, the Release and its assets resolve to the intended commit and bytes. Run the optional live check below.

For an initially unpublished version, a failure before the final publish command leaves the Release absent or draft. A rerun rejects an already published Release without modifying it. Repair a published edition through a new reviewed commit and version; do not move a published version tag or replace assets on a published Release. A manual rerun accepts only an existing annotated tag and may repair an unpublished draft.

Recovery depends on which source is wrong:

- If the workflow itself fails while the tagged source remains correct, repair the workflow through a normal pull request to `main`, then run `workflow_dispatch` from `main` for the same existing annotated tag. The publish job may reuse exactly one unpublished draft for that tag.
- If the tagged source is wrong, do not move or replace the tag and do not create a Release manually. Leave or discard the unpublished draft and correct the source in a new edition such as `vX.Y.(Z+1)`.

The workflow makes the draft-to-public Release boundary fail closed: it publishes only after the uploaded artifact names and digests pass. The preceding merge and tag push are separate public writes and cannot form one transaction with GitHub Release publication. Do not call the edition released until `main`, tag, Release, assets and public verification agree. Verify that public state separately after the workflow succeeds.

```bash
IMPACTS_LIVE_RELEASE_CHECK=1 python -m pytest -q \
  tests/test_public_release.py::test_live_current_release_contains_required_assets
```

That optional test checks the presence of the named assets. To verify their exact names and bytes, download them and run `release_guard.py live --tag vX.Y.Z --dist <download-directory>`.

An edition does not identify a consumer's bound revision. Customer repositories continue to record the exact commit or verified archive they use.

Do not delete or rewrite existing version tags or Releases without an explicit human decision.
