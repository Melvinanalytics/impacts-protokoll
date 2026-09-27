# CLI conformance corpus

This corpus checks the public JSON CLI contract against another implementation. It is a small, deterministic structural subset of JSON report format version 1. It does not import the reference package, use `tests/support.py`, or create expected reports by calling a validator. The current `cases.json` manifest has 27 cases: the original 19 frozen expectations plus eight additions; old expected hashes and issue-code vectors stay unchanged. The runner and release evidence read the manifest count instead of maintaining a second count.

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

The candidate must emit exactly one JSON object on stdout. Reports have exactly `report_version: 1`, the matching `command`, `tool` with non-empty string fields `name` and `version_source` plus `version` as a string or `null`, and `issues`. A null version means candidate could not resolve package metadata. Validate reports also contain `root` and `valid`; hash reports contain `attempt`, `surfaces`, and `digest`. Report paths and surfaces must match the exact command arguments. Every issue has exactly `code`, `path`, and `message`. `cases.json` freezes the required sorted issue-code list and result for each case; the runner checks that list separately from the process exit code. It also requires well-formed issue records and process exit code 0 for success or 1 for expected failure. Other exit codes, malformed or extra JSON, inconsistent results, and timeouts fail closed. Repeat cases run in fresh processes and must return identical reports.

## Cases and limits

`cases.json` owns the frozen expected outcomes. Application and Run records live as readable fixture files. Only the literal `@APPLICATION_REVISION@` token in Run frontmatter changes: the runner replaces it with the Git tree OID produced by committing the fixture Application. Hash digests are fixed literals calculated independently from the documented raw-byte serialization rule; the runner never computes expected hashes.

Coverage includes valid and invalid Application structure, required-field repair locations, one primary wrong-type diagnostic with unrelated schema errors retained, blocked route-derived graph conclusions with independent local checks, strict duplicate-key parsing, one leading UTF-8 BOM and repeated-BOM rejection, a fixed aggregate hash vector and missing surface, active pending human gate, waiting and resumed Run states, missing gate approval, input/output tampering, orphan and duplicate attempts, historical Application binding, coordinated input plus Run-record rewrite, and invalid UTF-8 filenames through direct hashing and Run validation. The case-sensitive-folder, long-component-folder and Unicode-spelling cases first probe the exact filesystem capability they require. Each invalid-filename case has one descriptor with literal hex basename/content bytes; the runner creates the file only inside its temporary workspace. No invalid-UTF-8 path or binary fixture is stored in the repository.

Invalid UTF-8 filename cases are applicable only when the host filesystem can create the requested POSIX basename. On non-POSIX systems, or when creation returns `EINVAL` or `EILSEQ`, each case is reported as `UNSUPPORTED` and is not counted as passed. Case-sensitive paths require two case-only spellings to coexist; a collision (`EEXIST`) marks that case unsupported. The long-component probe marks a case unsupported only for `ENAMETOOLONG`. Unicode spelling cases require composed and decomposed names to remain distinct; `EEXIST`, `EINVAL` or `EILSEQ` during that probe marks the case unsupported. Other setup errors, including duplicate fixtures, permission and storage failures, remain failures. The runner checks requested folder spellings exactly and compares frozen issue paths as exact strings; it performs no case folding or Unicode normalization. A run that reports unsupported cases exits 0 only when at least one case was applicable and all applicable cases passed.

The invalid-filename Run fixture also has a portable regression check before filename corruption. Its declared `input/daten` surface, Application revision and clean input hash must validate even on a filesystem that cannot create the corrupt filename. Protocol paths use forward slashes independently of the host; actual filename creation remains subject to the filesystem's capabilities.

The synthetic `human:fixture-reviewer` value is test data only. It authenticates no person or approval. The coordinated rewrite case is expected to pass because current files contain no independent trusted history; that result demonstrates a boundary, not tamper resistance. A content digest proves byte identity only. These cases do not test workstep execution, customer evidence, authenticated human decisions, complete protocol semantics, or business effects.

## Independent implementation challenge

Implement the report contract from this written corpus contract and `cases.json`; do not import, copy or consult `src/impacts_protocol/`, project tests or generated reports while writing the candidate. The shared corpus is the specification for this named structural subset, not for the whole protocol. Declare prior source exposure in the result: whether the implementation author previously read, used or received source from this repository, including reference implementation or test code. Prior exposure does not invalidate useful work, but it must be visible and prevents a claim of source-unexposed implementation.

Run the candidate as a command with `--command-json`. Preserve the exact candidate source revision, command, runtime and operating system, runner output, applicable/unsupported counts and every unsupported reason. The submitted record must include extra cases authored independently for this challenge, with their fixtures, expected reports and rationale. Keep those cases separate from the shared corpus unless a reviewed change to the common contract is proposed. Reusing or copying a frozen case does not count as an additional case.

A pass requires every applicable shared case and each submitted extra case to pass. Report unsupported shared cases with their exact capability reason; they are not passes. A pass supports only the exercised structural report contract and named inputs. It does not establish full protocol conformance, production suitability, security, authenticated decisions, business outcomes, other-platform support or absence of untested defects. A pass record is not a human approval or release authorization.

## Declared public inspection scope

This inventory covers tracked source, committed workflow configuration and public synthetic evaluation files in the inspected candidate repository. It excludes private operator/customer systems, external tenants, unpublished workflow artifacts and production environments. `No evidence in scope` means no qualifying evidence is retained in those inspected public files; it does not establish non-use. Production use outside this inspected scope is unknown.

| Feature or adoption claim | Evidence in inspected public scope | Limit or status |
|---|---|---|
| First-use offer preparation | [FIRST-WIN.md](../../FIRST-WIN.md) and synthetic source files describe a no-install exercise. | Expected exercise only; no unaccompanied real-user result is retained. |
| Structural CLI report subset | `cases.json`, this runner and synthetic fixtures define the current 27 cases; workflow files configure Windows/macOS checks. | No independent candidate report is retained for this candidate revision. Passing does not cover all protocol meanings. |
| Wheel provenance-template distribution | CLI/package tests exercise English and German `impacts template herkunft` output and its nine fields. | Source tests do not prove that a 0.3.20 wheel or public release has been built or published. |
| Native and interpreter release evidence | The release workflow and `.github/scripts/test_evidence.py` generate retained test summaries when an exact tagged run publishes. | Candidate release evidence does not exist until that tagged workflow has run; workflow code alone is not a run result, independent verification or build attestation. |
| Filesystem and platform coverage | The corpus probes case-sensitive names, long components, Unicode spelling and invalid UTF-8 filenames; native workflow targets GitHub-hosted Windows and macOS with Python 3.12. | Each unsupported case stays unsupported. NTFS behavior, all Windows versions, other filesystems and platforms are not established. |
| Dependency closure | `.github/runtime-linux-cp311-x86_64.txt` and `install_runtime.py` bind selected dependency wheel hashes for Linux CPython 3.11 x86_64 with glibc 2.17 or newer. | Python, pip, publishers, build provenance and all other targets are outside this bounded recipe. |
| Independent implementation | The challenge above defines submission evidence. | No independent implementation result is retained in inspected public scope. |
| Real first use, delayed continuation, domain/tax review, live Langdock and business baseline | The [follow-up plan](../nontechnical-reconstruction/FOLLOW-UP.md) and [listening screen](../listening-intake/CONTEXT.md) declare procedures and gates. | All external gates remain `open`; synthetic runs, internal model output and CI cannot substitute for them. Production use outside inspected scope is unknown. |

## Sources

- Python's [filesystem encoding guidance](https://docs.python.org/3/library/sys.html#sys.getfilesystemencoding) and [pure paths](https://docs.python.org/3/library/pathlib.html#pure-paths): distinguish portable path representation from the host filesystem's encoding and capabilities.

- [02_protocol/invariants/complete-process-paths.md](../../02_protocol/invariants/complete-process-paths.md): Application graph, gates, and waiting state.
- [02_protocol/templates/application.md](../../02_protocol/templates/application.md) and [02_protocol/templates/vorgang.md](../../02_protocol/templates/vorgang.md): selected Core structure and source binding.
- [src/impacts_protocol/hashing.py](../../src/impacts_protocol/hashing.py): documented raw-byte surface serialization used to calculate frozen vectors.
- [tests/test_owner_c_lifecycle.py](../../tests/test_owner_c_lifecycle.py) and [tests/test_minimal_vorgang.py](../../tests/test_minimal_vorgang.py): existing synthetic lifecycle examples; the corpus runner imports neither tests nor package code.
