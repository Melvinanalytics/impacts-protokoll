# Contributing

Changes enter `main` through a reviewed pull request. Keep customer material in its customer repository. Report the revision, expected and observed behavior, synthetic evidence, and checks not run.

## Publish an edition

An edition claim spans source text and public delivery. `pyproject.toml`, the annotated Git tag, GitHub Release, release assets, README URLs and filenames, the German guide, and installed package metadata must name the same version. A green documentation test establishes only the source-tree part.

Use this order:

1. Create `release/vX.Y.Z` from current public `main`.
2. Change `[project].version` plus all release URLs, clone commands, wheel filenames and edition wording in `README.md` and `02_protocol/translations/de.md`. Regenerate affected translation hashes.
3. Run the complete repository checks. Open and review the release pull request. Do not create a public Release from an unmerged branch.
4. Merge the reviewed release commit. Create an **annotated** `vX.Y.Z` tag on that exact public `main` commit and push the tag once.
5. The tag workflow uses a read-only build job to check the tag, source claims and full test suite; build the wheel and complete source archive; and write `SHA256SUMS`. A separate publish job downloads those checked bytes without installing or running package code, uploads exactly the three artifacts to a hidden draft Release, verifies their remote names and SHA-256 digests, and only then publishes that Release by numeric ID.
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
