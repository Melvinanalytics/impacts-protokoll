# CLI conformance corpus

This corpus checks the public JSON CLI contract against another implementation. It is a small, deterministic structural subset of JSON report format version 3. It does not import the reference package, use `tests/support.py`, or create expected reports by calling a validator. The runner and release evidence derive the case count from [cases.json](cases.json).

## Run

From a checkout with Python 3.11+ and Git available; the default candidate must also be installed or otherwise importable by that Python environment:

```bash
python -m pip install -e '.[test]'
python 06_evaluations/conformance/run.py
python 06_evaluations/conformance/run.py --command-json '["/path/to/candidate"]'
python 06_evaluations/conformance/run.py --command-json '["/path/to/python", "-m", "impacts_protocol.cli"]'
```

`--command-json` is a JSON array of executable and fixed arguments. The runner appends `validate <workspace> --json` or `hash <attempt> <surface>... --json` as an argument vector; it never invokes a shell. `--case <id>` selects one frozen case. `--timeout-seconds` sets the per-command limit.

The runner prints applicable, passed, unsupported, failed, and total counts. Exit 0 means at least one case was applicable and all applicable cases passed. Exit 1 means a candidate or fixture failed. Exit 2 means invalid runner arguments or corpus configuration. Exit 3 means every selected case was unsupported, so no conformance claim was exercised.

The candidate must emit exactly one JSON object on stdout. Reports have exactly `report_version: 3`, the matching `command`, `tool` with non-empty string fields `name` and `version_source` plus `version` as a string or `null`, and `issues`. A null version means candidate could not resolve package metadata. Validate reports also contain `root`, `valid`, `external_references_not_verified` (the nonnegative count of declared external-store references in judged Vorgänge, including invalid ones) and `not_judged` (each item has `path`, recorded `protocol`, a string or null, and an optional exclusion `reason`), with `not_judged_counts` splitting `vorgang` and `definition_tree` counts; hash reports contain `attempt`, `surfaces`, and `references`. `references` is null on failure or a list of `{pfad, sha256}` objects, sorted by UTF-8 path bytes. Each digest covers that file's raw bytes. `attempt` names the supplied reference root. Report paths and surfaces must match the exact command arguments. Every issue has exactly `code`, `path`, `message`, and a protocol heading link in `rule`. `cases.json` freezes the external-store count (omitted expectations mean zero), the exact `not_judged` list for validation and the exact sorted issue-code list, including repeated codes, and result for each case. Where a case freezes issue paths, those paths also check issue locations and occurrences. Optional `expected_issue_messages` freezes diagnostic substrings: sorted messages must contain the corresponding sorted substrings with the same count. The runner checks exact issue-code counts separately from process exit status. It also requires well-formed issue records and process exit code 0 for success or 1 for expected failure. Other exit codes, malformed or extra JSON, inconsistent results, and timeouts fail closed. Repeat cases run in fresh processes and must return identical reports.

Every issue code emitted by source maps to frozen cases; `tests/test_conformance.py` rejects an uncovered emission. The symlink descriptor creates only a workspace-local relative link in the disposable fixture; hosts lacking symlink support report unsupported, while other setup failures remain failures.

## Cases and limits

Cases include between steps, owner termination, readable selection decisions, protocol breaks, input-slot coverage and rejection of `stufen`.

`cases.json` owns the frozen expected results. Hauptprozess definitions and Vorgang files live as readable fixture files. The literal `@HAUPTPROZESS_REVISION@` and `@SOURCE_COMMIT@` tokens in Vorgang frontmatter change: the runner replaces them with the committed Hauptprozess tree and source commit OIDs. Hash digests are fixed literals calculated independently from the raw-byte SHA-256 rule; the runner never computes expected hashes.

Coverage includes valid and invalid Hauptprozess structure, required-field repair locations, one primary wrong-type diagnostic with unrelated schema errors retained, blocked route-derived graph conclusions with independent local checks, strict duplicate-key parsing, one leading UTF-8 BOM and repeated-BOM rejection, fixed per-file SHA-256 vectors and missing surface, active pending human gate, waiting and resumed Vorgang states, missing gate approval, input/output reference tampering, orphan and duplicate attempts, historical Hauptprozess binding, coordinated input plus Vorgang-record rewrite, and invalid UTF-8 filenames through direct hashing and Vorgang validation. The case-sensitive-folder, long-component-folder and Unicode-spelling cases first probe the exact filesystem capability they require. Each invalid-filename case has one descriptor with literal hex basename/content bytes; the runner creates the file only inside its temporary workspace. No invalid-UTF-8 path or binary fixture is stored in the repository.

Invalid UTF-8 filename cases are applicable only when the host filesystem can create the requested POSIX basename. On non-POSIX systems, or when creation returns `EINVAL` or `EILSEQ`, each case is reported as `UNSUPPORTED` and is not counted as passed. Case-sensitive paths require two case-only spellings to coexist; a collision (`EEXIST`) marks that case unsupported. The 256-byte path-component probe marks a case unsupported when creation returns `ENAMETOOLONG`, or `EINVAL` on Windows for the path API's over-limit-component response. Unicode spelling cases require composed and decomposed names to remain distinct; `EEXIST`, `EINVAL` or `EILSEQ` during that probe marks the case unsupported. Other setup errors, including duplicate fixtures, permission and storage failures, remain failures. The runner checks requested folder spellings exactly and compares frozen issue paths as exact strings; it performs no case folding or Unicode normalization. A run that reports unsupported cases exits 0 only when at least one case was applicable and all applicable cases passed.

The invalid-filename Vorgang fixture also has a portable regression check before filename corruption. Its declared source record, Hauptprozess revision and clean reference list must validate even on a filesystem that cannot create the corrupt filename. Protocol paths use forward slashes independently of the host; actual filename creation remains subject to the filesystem's capabilities.

The synthetic `human:fixture-reviewer` value is test data only. It authenticates no person or approval. The coordinated rewrite case is expected to pass because current files contain no independent trusted history; that result demonstrates a boundary, not tamper resistance. A content digest proves byte identity only. These cases do not test Arbeitsschritt execution, customer evidence, authenticated human decisions, complete protocol semantics, or business effects.

The wait and input cases require workspace-relative continuation files and input-slot coverage from attempt opening under [binding.md](../../02_protocol/binding.md#waits). `orphan_source_commit: true` makes the runner create a parentless `git commit-tree` object from the committed fixture tree and substitutes `@ORPHAN_COMMIT@` in source references. No branch, tag, remote-tracking ref or HEAD retains that object. `run-input-orphan-commit` must reject those references even though their blobs exist and their digests match. These Git writes occur only in the runner's disposable workspace; they prescribe no Core policy on Git plumbing.

## Independent implementation challenge

**Licensed sentence after closure:** “A second implementation, written from the public contract, produces the same `validate --json` and `hash` results as the reference CLI for `<n>` applicable shared cases and `<N>` independently authored cases on `<environment>`, at revision `<revision>`.”

Implement the report contract from this written corpus contract and `cases.json`. While writing, neither the author nor an assisting model imports, copies or consults `src/impacts_protocol/`, project tests or generated reports. The shared corpus is the specification for this named structural subset, not for the whole protocol.

For this challenge, an **independent implementation** is a separate code base whose author has no maintainer role and no commit to `src/impacts_protocol/`, and which copies no reference implementation code. Declare any prior source exposure: this repository's source, tests, fixtures or generated reports. Reading the public contract is not source exposure. Prior exposure does not invalidate useful work, but it prevents a claim of **source-unexposed implementation**. Declare AI assistance, prompts and supplied files. Maintainers answer questions only by citing or changing public contract text; retain each question and disposition.

Run the candidate as a command with `--command-json`. Preserve the exact candidate source revision, command, runtime and operating system, runner output, applicable/unsupported counts and every unsupported reason. The submitted record must include extra cases authored independently for this challenge, with their fixtures, expected reports and rationale. Keep those cases separate from the shared corpus unless a reviewed change to the common contract is proposed. Reusing or copying a frozen case does not count as an additional case.

Commit a numeric minimum of extra cases before implementation begins; without it the challenge cannot close. The extra cases cover both commands and include cases aimed at contract passages the implementer found unclear.

A pass requires every applicable shared case and every submitted extra case to pass. Commit the extra cases and their expected reports, then run the reference CLI at the same declared protocol revision against all of them. Candidate and reference must return the same `valid` or `references` values and the same sorted issue-code lists, ignoring `tool` and diagnostic `message`. Preserve every disagreement and classify it as a contract, reference or candidate defect before closure. Report unsupported shared cases with their exact capability reason; they are not passes.


A pass supports only the exercised structural report contract and named inputs. It does not establish full protocol conformance, production suitability, security, authenticated decisions, business outcomes, other-platform support or absence of untested defects. A pass record is not a human approval or release authorization.

## Declared public inspection scope

This inventory covers tracked source, committed workflow configuration and public synthetic evaluation files in the inspected candidate repository. It excludes private operator/customer systems, external tenants, unpublished workflow artifacts and production environments. `No evidence in scope` means no qualifying evidence is retained in those inspected public files; it does not establish non-use. Production use outside this inspected scope is unknown.

| Feature or adoption claim | Evidence in inspected public scope | Limit or status |
|---|---|---|
| First-use offer preparation | [FIRST-WIN.md](../../FIRST-WIN.md) and synthetic source files describe a no-install exercise. | Expected exercise only; no unaccompanied real-user result is retained. |
| Structural CLI report subset | `cases.json`, this runner and synthetic fixtures define the current cases; workflow files configure Windows/macOS checks. | No independent candidate report is retained for this candidate revision. Passing does not cover all protocol meanings. |
| Wheel provenance-template distribution | CLI/package tests exercise English and German `impacts template herkunft` output and its nine fields. | Source tests do not prove that a wheel or public release for this source revision has been built or published. |
| Native and interpreter release evidence | The release workflow and `.github/scripts/test_evidence.py` generate retained test summaries when an exact tagged run publishes. | Candidate release evidence does not exist until that tagged workflow has run; workflow code alone is not a run result, independent verification or build attestation. |
| Filesystem and platform coverage | The corpus probes case-sensitive names, long components, Unicode spelling and invalid UTF-8 filenames; native workflow targets GitHub-hosted Windows and macOS with Python 3.12. | Each unsupported case stays unsupported. NTFS behavior, all Windows versions, other filesystems and platforms are not established. |
| Dependency closure | `.github/runtime-linux-cp311-x86_64.txt` and `install_runtime.py` bind selected dependency wheel hashes for Linux CPython 3.11 x86_64 with glibc 2.17 or newer. | Python, pip, publishers, build provenance and all other targets are outside this bounded recipe. |
| Independent implementation | The challenge above defines submission evidence. | No independent implementation result is retained in inspected public scope. |
| Real first use, delayed continuation, domain/tax review, live Langdock and business baseline | The [follow-up plan](../nontechnical-reconstruction/FOLLOW-UP.md) and [listening screen](../nontechnical-reconstruction/listening-intake.md) declare procedures and gates. | All external gates remain `open`; synthetic runs, internal model output and CI cannot substitute for them. Production use outside inspected scope is unknown. |

## Sources

- Python's [filesystem encoding guidance](https://docs.python.org/3/library/sys.html#sys.getfilesystemencoding) and [pure paths](https://docs.python.org/3/library/pathlib.html#pure-paths): distinguish portable path representation from the host filesystem's encoding and capabilities.

- [Layout rules](../../02_protocol/binding.md#hauptprozess-tree-rules): Hauptprozess graph and references to gate and wait rules.
- [02_protocol/templates/hauptprozess.md](../../02_protocol/templates/hauptprozess.md) and [02_protocol/templates/vorgang.md](../../02_protocol/templates/vorgang.md): selected Core structure and source binding.
- [Snapshot and provenance](../../02_protocol/binding.md#snapshot-and-provenance): raw-byte file hashing used to calculate frozen vectors.
- [tests/test_minimal_vorgang.py](../../tests/test_minimal_vorgang.py): existing synthetic lifecycle examples; the corpus runner imports neither tests nor package code.
