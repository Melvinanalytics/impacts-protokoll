# Contributing

Changes enter `main` through a reviewed pull request. Keep customer material in its customer repository. Report the revision, expected and observed behavior, synthetic evidence, and checks not run.

## Hardening roadmap after v0.3.13

The table records scoped milestones, not evidence of publication. Apply the publication checks below to identify what is live. The v0.4 row is a design gate, not an implemented sealing feature.

| Target | Work and acceptance |
|---|---|
| v0.3.14 | Package metadata diagnostics, shared strict YAML ingestion, one primary error for repeated leading BOMs, documented existing exit codes, and bounded generated parser tests in both CI interpreters. Preserve raw-byte hashes, default output and Core schemas. |
| v0.3.16 | Opt-in JSON for `validate` and `hash`; a public, implementation-independent structural conformance corpus with frozen expected outcomes, runnable from complete source against a candidate command; measured scale and explicit concurrent-writer limits. Preserve existing commands and text output. The [corpus](06_evaluations/conformance/CONTEXT.md) runs through pytest in both CI interpreters. |
| v0.4 design gate | Define an independently retained trust anchor and verifier before proposing sealing. Exercise coordinated content/hash rewriting, rollback, forked histories, missing anchors, identity/key rotation and unavailable verification. A valid signature must bind the retained state to an authorized identity and independently checked revision; it does not prove business truth. Choose transport and trust custody in the consuming harness. A new Core command or schema requires a demonstrated gap in existing structures. |

The v0.3.15 tag was retained after publication stopped: the source-archive guard misread Git-quoted Unicode filenames. No v0.3.15 Release was published. The correction is included in v0.3.16; its guard reads NUL-delimited Git paths without altering the tagged source or weakening archive checks.

The five [JSON Schemas](02_protocol/schemas/) already define Core frontmatter; editor support should reuse those contracts. `validate` already checks declared attempt directories, routes and hashes, so recovery first uses that existing command. A separate `doctor` command is justified only by a concrete recovery check that cannot fit the existing read-only path. A conformance corpus can establish a tested contract subset without independently versioning another copy of the specification. It does not establish complete protocol conformance or model behavior.

Single-snapshot validation detects changed bytes against retained digests. It cannot detect a writer replacing both the bytes and their recorded digests without a trusted earlier state. This applies to active, waiting and completed attempts. Concurrent execution must therefore use the consuming harness's writer coordination, current-state checks and retained revision; a green validator result is not a lock, transaction, authentication or history-rewrite detector.

### v0.3.17 audit follow-through

The patch keeps Core schemas, hash semantics and the four CLI commands unchanged. Each residual has one disposition:

| Residual | Disposition |
|---|---|
| Cold-walk duplicate-key traceback | Malformed decision fixtures produce a concise path, source location and remedy; unexpected proof failures remain visible. |
| YAML key diagnostics | Duplicate and non-string keys retain their original token and line/column, including the Markdown frontmatter offset. |
| Graph diagnostics after parse failure | Preserve conservative dependent-check suppression; [CLI guidance](README.md#cli-output-and-text-input) explains repair and revalidation. No false claim of exhaustive diagnostics. |
| Parser edge coverage | Add bounded location, Unicode-normalization, alias and nesting checks. These are regression examples, not a resource-exhaustion guarantee or a new YAML dialect. |
| Corpus input boundaries | Add leading/repeated BOM and invalid-UTF-8 filename cases. A filesystem that cannot create the byte filename reports the case as unsupported, never passed. |
| JSON for `init`/`template` and issue categories | Document the existing issue categories. Defer new output modes until a consumer needs structured results from these creation commands. |
| Git revision in `--version` | Keep installed package identity separate from source binding. Record a tag/commit or verified archive separately; the enclosing checkout cannot identify an installed wheel. |
| Fully hash-pinned consumer dependencies | The wheel checksum does not pin transitive dependencies. The enterprise custodian supplies an approved dependency set for its Python/platform; this patch does not publish a universal lock or attestation. |
| Anonymous CI visibility | Test the exact tag on Python 3.11 and 3.14 and publish compact workflow results in the Release body. Counts include JUnit subtests and explicitly identify source, run and build attempt; raw logs may still require authentication. |
| Scale portability | Retain the measured workload, machine and limitations. No new speed or concurrency claim. |

Successful historical corpus cases cover the named contracts; they do not prove zero semantic drift for all inputs. Parser acceptance intentionally changed for malformed inputs. Review and integration records identify their actual actors; an agent's review is not a human approval.

### v0.3.18 publication identity correction

`verified` (publication state and workflow result): the v0.3.17 [workflow run](https://github.com/Melvinanalytics/impacts-protokoll/actions/runs/36264479825) passed its build and test job, then failed publication verification. The [published record](https://github.com/Melvinanalytics/impacts-protokoll/releases/tag/untagged-48312c7106a2a0522ebc) uses the unexpected tag `untagged-48312c7106a2a0522ebc`, pointing to the same commit as the intended annotated [v0.3.17 tag](https://github.com/Melvinanalytics/impacts-protokoll/tree/v0.3.17). The final public lookup for the intended release returned 404. `verified` (source inspection): the [tagged workflow](https://github.com/Melvinanalytics/impacts-protokoll/blob/6f343277b3b0d26961ee158bdef0fcae3d21b55c/.github/workflows/release.yml#L243-L256) omitted `tag_name` from both update requests and did not check tag identity after the notes update. `open`: the retained responses do not establish which request changed the association. The published immutable record and both tags are retained.

v0.3.18 sends the intended tag explicitly in both updates and rechecks draft identity and artifact digests after changing the notes, before publication. The correction changes the publication path, not Core contracts or hash rules. See GitHub's [release update API](https://docs.github.com/en/rest/releases/releases#update-a-release) and [immutable release restrictions](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases).

### v0.3.19 first-use and portability scope

`reported` (S4–S7 scenario findings): the monthly-close example uses existing `validate --json` and `hash.mismatch` for its GO/NO-GO; no new decision format is needed. First-use diagnostics explain the accepted folder-name form and locate malformed YAML at its source. Incomplete process-tree enumeration reports its structural cause before dependent graph claims while preserving independent local gate checks. A hash-surface symlink remains rejected with a lifecycle-aware remedy. The existing [stable-source provenance guidance](02_protocol/capabilities.md#provenance-file-example) gives ordinary files one copyable evidence home without a new schema. The CLI does not prove that an attempt contains every relevant file: undeclared extras remain a human completeness check. Hashing remains fail-fast; successful validation remains silent unless `--verbose` or `--json` is requested. Existing `SHA256SUMS`, `impacts --version` and the Run-bound revision answer artifact-byte, package-edition and historical-binding questions respectively, within their stated limits. No second version command or `hash --all-declared` is added.

`required gate` (not evidence of a passing run): PR and exact-tag workflows run the 19-case corpus on GitHub-hosted Windows and macOS with Python 3.12. At least 17 cases must pass; only `hash-invalid-utf8-filename` and `run-invalid-utf8-filename` may be unsupported, and any failure blocks the release build. This characterizes those runners and cases only. An I/O or storage error, including FUSE `EIO`, is a failure. The existing Linux Python 3.11/3.14 full suite and three-asset release contract remain in force. No customer scenario workspace, JUnit report or private review is published.

### v0.3.20 public integration and evidence scope

This section defines the v0.3.20 source and evidence scope. Publication status and published bytes are established only by the published [v0.3.20 Release](https://github.com/Melvinanalytics/impacts-protokoll/releases/tag/v0.3.20), its immutable tag and assets, and their verified checksums; release notes remain editable and source text alone cannot establish publication. IMPACTS keeps sources, required checks, executed checks and responsible decisions inspectable. It does not authenticate people, grant permissions, execute work, prove business effect or detect a coordinated content-and-digest rewrite. A name, reviewer label or `human:<id>` string is attribution, not authentication or approval evidence.

#### Three useful contributions

1. **Independent implementation.** Implement the [declared JSON structural subset](06_evaluations/conformance/CONTEXT.md#independent-implementation-challenge) from its written contract and frozen cases. Disclose previous exposure to this repository's source and tests, record the candidate revision and exact run scope, and add independently authored cases. A shared-corpus pass alone is incomplete and no pass claims full protocol conformance or production suitability.
2. **Unaccompanied first-use record.** Use the no-install [first-win exercise](FIRST-WIN.md) without coaching. Retain the instruction/source revision, what the operator could find and complete, observed blockers, open items, next action and checks actually performed. An internal walkthrough or coached repair is not an unaccompanied user result.
3. **Bounded listening-adapter result.** Apply a named, revision-bound capture adapter through the [listening-intake screen](06_evaluations/listening-intake/CONTEXT.md), including its counterbalanced blocks, fresh operators, retained inputs/outputs, blinded scoring, effort accounting and stop rule. Report hard failures and missing data. Do not present one adapter output, a synthetic simulation or model evaluation as a completed screen, Langdock result or customer validation.

Use the repository's [issue forms](.github/ISSUE_TEMPLATE/) to propose or report scoped work and its [pull request template](.github/PULL_REQUEST_TEMPLATE.md) for changes. The public community routes are GitHub [issues](https://github.com/Melvinanalytics/impacts-protokoll/issues), [pull requests](https://github.com/Melvinanalytics/impacts-protokoll/pulls) and [Discussions](https://github.com/Melvinanalytics/impacts-protokoll/discussions). Discussions are for exploratory questions; issues hold scoped findings and evidence, and pull requests hold reviewed changes. To object to a claim or contract, cite its exact source and scope, give a counterexample or evidence, and propose the smallest correction. An open objection is not an approval or maintainer decision. Public adoption issues accept only synthetic or already-public evidence, a non-sensitive reference and bounded scope, and a sanitized summary. Keep customer records and raw sources, captured outputs, and review records in the customer repository; never attach or link them in a public issue. Do not submit credentials, personal data or live access state.

#### Finding classes and current disposition

An issue should name the source revision, inspected scope, evidence path, exact command and result, and checks not performed. A `reported` observation must remain attributed; a frozen expected result is not an observation from a candidate run.

| Finding class | Current disposition | Evidence needed for a useful report |
|---|---|---|
| Diagnostics | Frozen cases require their listed codes/results; message wording remains diagnostic. Documented parse or routing prerequisites suppress dependent conclusions, while independent defects remain reportable. | Minimal synthetic files, exact candidate command, JSON report, expected and observed codes/paths, source revision, and checks performed. |
| Provenance-template distribution | **Closed for the published v0.3.20 wheel:** `impacts template herkunft` is included in the wheel CLI and English/German templates, with nine fields. | For a distribution defect, give the installed package version, wheel SHA-256, command, language and captured output; do not use a universal line-count expectation. |
| Durable native release evidence | **Closed for the published v0.3.20 Release:** its publicly readable release notes retain Python test totals and exact Windows/macOS corpus reports from the successful tagged workflow. The notes remain editable and label these results as workflow-reported evidence. | For a reporting defect, give tag, source commit, workflow URL/attempt, runner platform/runtime, corpus digest/count and retained release-note result. A workflow configuration alone is not execution evidence. |
| NTFS and platform boundary | **Open outside named runner results.** The hosted Windows job does not identify every filesystem or establish universal NTFS behavior; unsupported cases are not passes. | Name OS version, filesystem, runtime, relevant case capability, command, raw output and exact unsupported/failure reason. Do not generalize beyond that environment. |
| Dependency closure | **Bounded only:** hash-enforced selected wheels for Linux CPython 3.11 x86_64 with glibc 2.17 or newer. Other targets remain open. No publisher-authenticity claim. | Name Python implementation/version, pip, OS, architecture, libc, dependency source, lock revision, command and install result. State whether the target is inside the recipe's bound. |
| Public-review reproducibility | **Open for independent third-party reruns.** Release notes retain workflow-reported test evidence after publication; this is not independent verification or a build attestation. | Give the published source commit, exact inputs/command/environment, candidate output and independently retained result. Report access limits and checks not performed. |

#### Compatibility and change process

English owns the active contract. Reuse the current file/template/schema home and state the concrete gap before adding a field, role, file kind, command or version. Preserve machine tokens and Core schemas unless a separately evidenced gap and reviewed change authorize their update. Keep German readable surfaces aligned and refresh their source-byte hashes.

For JSON CLI changes, `report_version` versions the report shape. Message text is diagnostic. `cases.json` defines the exact required results for its listed cases; a changed frozen expectation needs an explicit fixture or expected-result diff, rationale and fresh runner evidence. Do not create a parallel protocol or conformance-specification version. A new structural claim needs named cases and stated limits. Keep reference implementation tests separate from the implementation-independent corpus.

Pull requests should link the issue or bounded gap, name changed authority files, provide synthetic evidence and exact checks/results, disclose checks not run, and update affected translations. Maintainers review the actual diff and evidence through repository permissions and GitHub records; an author cannot create approval by entering a name or identifier. Preserve the issue, reviewed source revision and decision rationale in the repository so a successor can continue. If no authorized maintainer is available, leave the change unmerged and its status explicit rather than inventing a review or transferring authority by text.

#### External adoption and deployment gates

These gates remain **open**. CI, Luna-generated output, synthetic replays, internal model reviews or repository instructions do not substitute for the named external evidence.

Each linked contract owns its pass rule and licensed sentence. Its execution issue links the contract and records each run in comments: the freeze commit, the evidence and a named maintainer's closure decision after review of the frozen evidence. A closed gate supports only its licensed sentence, at the revision that sentence names.

| Gate | Authoritative contract | Execution issue |
|---|---|---|
| Independent implementation | [Independent implementation challenge](06_evaluations/conformance/CONTEXT.md#independent-implementation-challenge) | [#27](https://github.com/Melvinanalytics/impacts-protokoll/issues/27) |
| Unaccompanied first use and correction | [Follow-up Gate A](06_evaluations/nontechnical-reconstruction/FOLLOW-UP.md#gate-a) | [#28](https://github.com/Melvinanalytics/impacts-protokoll/issues/28) |
| Second operator after 168 elapsed hours | [Follow-up Gate B](06_evaluations/nontechnical-reconstruction/FOLLOW-UP.md#gate-b) | [#29](https://github.com/Melvinanalytics/impacts-protokoll/issues/29) |
| Listening intake in authorized Langdock | [Listening-intake screen](06_evaluations/listening-intake/CONTEXT.md) | [#30](https://github.com/Melvinanalytics/impacts-protokoll/issues/30) |
| Bounded domain review | [Follow-up Gate C](06_evaluations/nontechnical-reconstruction/FOLLOW-UP.md#gate-c) | [#31](https://github.com/Melvinanalytics/impacts-protokoll/issues/31) |
| Matched business comparison | [Follow-up Gate D](06_evaluations/nontechnical-reconstruction/FOLLOW-UP.md#gate-d) | [#32](https://github.com/Melvinanalytics/impacts-protokoll/issues/32) |
Production use outside the declared inspected public repository scope is unknown.

## Publish an edition

An edition claim spans source text and public delivery. `pyproject.toml`, the annotated Git tag, GitHub Release, release assets, README URLs and filenames, the German guide, and installed package metadata must name the same version. A green documentation test establishes only the source-tree part.

Use this order:

1. Create `release/vX.Y.Z` from current public `main`.
2. Change `[project].version` plus all release URLs, clone commands, wheel filenames and edition wording in `README.md` and `02_protocol/translations/de.md`. Regenerate affected translation hashes.
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

Historical debt remains historical: tags `v0.3.1`, `v0.2.0` and `v0.1.0` have no GitHub Release, and Releases before `v0.3.5` may omit the complete source archive. Do not delete or rewrite those tags or Releases without an explicit human decision.
