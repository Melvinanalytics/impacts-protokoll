# Context-efficiency measurement

Status: candidate evidence for v0.3.7, measured 2026-09-23. This evaluation tests one synthetic routing question. It establishes no universal token saving, customer improvement or model-independent result.

## Question and comparison

[prompt.txt](prompt.txt) is the frozen input. Three fresh read-only sessions answered it on each source:

- baseline: public v0.3.6, `5ad90cd42b792ef2919ebcfaf558bb11cb80ec3a`;
- candidate: v0.3.7 routing candidate, `441d066`;
- same Codex CLI 0.155.1, `gpt-5.6-sol`, low reasoning effort, ephemeral session and read-only sandbox.

Each session began at root `CONTEXT.md`. It could read repository files but not edit them. The prompt excluded answer keys, coverage records, sibling evaluations and Git history. The raw harness logs remain local because they contain workstation paths and repeated tool output; [measurement.json](measurement.json) records their SHA-256 digests, usage values and answer digests. Those hashes identify the inspected logs but do not make the omitted logs independently reviewable. [measure.py](measure.py) recomputes the record from supplied JSONL and answer files.

## Measured bottleneck

The first candidate diagnostic regressed: one run used 241,924 input tokens and loaded 81,698 tool-output bytes, versus 129,479 tokens and 39,143 bytes in its matched v0.3.6 run. The reader reached the new method only after detouring through Architect and form-selection material. The missing task-specific route in `02_protocol/CONTEXT.md` was the observed bottleneck.

The correction adds one direct route for context delivery and names mutually conditional delivery paths: projection for a knowledge bundle, snapshot for a bound input and handoff for a successor step. It also tells readers to load the selected bounded set together where access permits. It changes no Core contract or source authority.

## Exact candidate result

Medians across three runs:

| Metric | v0.3.6 | Candidate `441d066` | Reduction |
|---|---:|---:|---:|
| Total input tokens reported by harness | 129,479 | 92,362 | 28.67% |
| Cached input tokens | 105,216 | 84,608 | 19.59% |
| Tool calls | 4 | 3 | 25.00% |
| Tool-output bytes | 39,143 | 17,509 | 55.27% |
| Output tokens | 1,011 | 924 | 8.61% |

Tradeoffs remain visible: median reasoning tokens rose from 268 to 295, and answer bytes rose from 849 to 1,019. The candidate answers explicitly selected the projection path and excluded the snapshot/handoff branches. A blind independent scorer marked all six answers safe and complete; all three candidate answers received full route-discipline scores, versus two of three baseline answers.

Total input tokens include fixed system, prompt, harness and accumulated tool context. Tool-output bytes are a deterministic transport measure, not a tokenizer count of customer payload. Cached tokens are reported by the harness and remain part of its total input figure. The result applies only to this question, revisions, model and settings.

## Rerun

Create clean checkouts of the two recorded revisions. For each checkout, execute at least three fresh runs with the exact prompt and identical model, reasoning, sandbox, tools and session settings. Retain JSONL plus the final answer for each run. Then run:

```sh
python3 06_evaluations/context-efficiency/measure.py \
  --baseline-run baseline-1 <baseline-1.jsonl> <baseline-1.md> \
  --baseline-run baseline-2 <baseline-2.jsonl> <baseline-2.md> \
  --baseline-run baseline-3 <baseline-3.jsonl> <baseline-3.md> \
  --candidate-run candidate-1 <candidate-1.jsonl> <candidate-1.md> \
  --candidate-run candidate-2 <candidate-2.jsonl> <candidate-2.md> \
  --candidate-run candidate-3 <candidate-3.jsonl> <candidate-3.md>
```

Score answers blind before revealing their revision. A lower payload fails as an improvement if required conditions disappear, unsupported conclusions appear or dependent use is no longer blocked. Extend the claim only with additional frozen questions and matched repetitions.

## Historical binding correction, 2026-09-23

The numeric comparison above is supported by the six rows in `measurement.json`; the omitted raw logs prevent independent reconstruction of their tool paths. The earlier diagnostic pair of 241,924 input tokens and 81,698 tool-output bytes is described in prose only. Neither value has a retained row, raw log or log digest in this package, so the pair remains a reported diagnostic rather than a reproducible measurement. The values 129,479 and 39,143 are both the retained baseline medians and the values in the first retained baseline row; that coincidence supplies no evidence for the omitted diagnostic.

The historical measurement used the pre-change positional pairing shown below. It is retained as evidence of that invocation shape, not as a supported v0.3.8 command:

```sh
python3 06_evaluations/context-efficiency/measure.py \
  --baseline-jsonl <baseline-1.jsonl> --baseline-answer <baseline-1.md> \
  --baseline-jsonl <baseline-2.jsonl> --baseline-answer <baseline-2.md> \
  --baseline-jsonl <baseline-3.jsonl> --baseline-answer <baseline-3.md> \
  --candidate-jsonl <candidate-1.jsonl> --candidate-answer <candidate-1.md> \
  --candidate-jsonl <candidate-2.jsonl> --candidate-answer <candidate-2.md> \
  --candidate-jsonl <candidate-3.jsonl> --candidate-answer <candidate-3.md>
```

`measurement.json` names baseline revision `5ad90cd42b792ef2919ebcfaf558bb11cb80ec3a` and candidate revision `441d066`. The first string exactly matches the public v0.3.6 tag commit. The second is deliberately retained as the abbreviated string recorded by the historical measurement; local Git currently resolves it to `441d06637b3f91420f2e528d52f531ca5d2e38b7`, but that resolution does not replace the recorded identity. `measure.py` is absent at both measured source revisions. The pre-change parser first appears locally at `a97da4ea5b57b7b6a5df9e601a946d6c405fd1b7`; its bytes match public v0.3.7 commit `a4bac26d93881a2d08369d744c53f4ab4023daad`. The measured source revisions and parser revision are separate bindings.

The command under [Rerun](#rerun) uses the v0.3.8 hardened interface. Each repeated triple binds one non-empty unique run ID to exactly one JSONL file and one answer. The parser rejects duplicate run IDs, duplicate JSONL content and missing or non-string command output before computing the unchanged metrics. This hardening produces no new performance evidence and does not alter `measurement.json`.
