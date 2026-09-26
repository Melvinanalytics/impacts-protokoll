# CLI conformance corpus

This corpus checks the public JSON CLI contract against another implementation. It is a small, deterministic structural subset of JSON report format version 1. It does not import the reference package, use `tests/support.py`, or create expected reports by calling a validator.

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

Coverage includes valid and invalid Application structure, strict duplicate-key parsing, one leading UTF-8 BOM and repeated-BOM rejection, a fixed aggregate hash vector and missing surface, active pending human gate, waiting and resumed Run states, missing gate approval, input/output tampering, orphan and duplicate attempts, historical Application binding, coordinated input plus Run-record rewrite, and invalid UTF-8 filenames through direct hashing and Run validation. Each invalid-filename case has one descriptor with literal hex basename/content bytes; the runner creates the file only inside its temporary workspace. No invalid-UTF-8 path or binary fixture is stored in the repository.

Invalid UTF-8 filename cases are applicable only when the host filesystem can create the requested POSIX basename. On non-POSIX systems, or when creation returns `EINVAL` or `EILSEQ`, each case is reported as `UNSUPPORTED` and is not counted as passed. Other setup errors, including permission and storage failures, are failures. A run that reports unsupported cases exits 0 only when at least one case was applicable and all applicable cases passed.

The synthetic `human:fixture-reviewer` value is test data only. It authenticates no person or approval. The coordinated rewrite case is expected to pass because current files contain no independent trusted history; that result demonstrates a boundary, not tamper resistance. A content digest proves byte identity only. These cases do not test workstep execution, customer evidence, authenticated human decisions, complete protocol semantics, or business effects.

## Sources

- [02_protocol/invariants/complete-process-paths.md](../../02_protocol/invariants/complete-process-paths.md): Application graph, gates, and waiting state.
- [02_protocol/templates/application.md](../../02_protocol/templates/application.md) and [02_protocol/templates/vorgang.md](../../02_protocol/templates/vorgang.md): selected Core structure and source binding.
- [src/impacts_protocol/hashing.py](../../src/impacts_protocol/hashing.py): documented raw-byte surface serialization used to calculate frozen vectors.
- [tests/test_owner_c_lifecycle.py](../../tests/test_owner_c_lifecycle.py) and [tests/test_minimal_vorgang.py](../../tests/test_minimal_vorgang.py): existing synthetic lifecycle examples; the corpus runner imports neither tests nor package code.
