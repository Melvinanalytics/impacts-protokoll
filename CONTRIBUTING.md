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
