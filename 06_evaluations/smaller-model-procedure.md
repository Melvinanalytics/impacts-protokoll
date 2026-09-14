# Owner D — smaller-model suitability evaluation PROCEDURE

**STATUS: UNEXECUTED.** No smaller/local model is available in this audit environment, and same-model agents are not independent evidence (SHARED-CONTEXT hard rule 8). Nothing below is a result; there is no PASS to report. This is a runnable procedure with a frozen rubric and scoring so an operator with access to a small model can produce the evidence.

## Suitability question
Can a small/open model (e.g. a 7B–14B local instruct model), acting as a fresh consumer, answer the frozen rubric questions Q1–Q6 and handle B1–B2 from the pinned sources via ordinary routing — with supported completion and without unsupported inference?

## Setup (exact commands, linux, python 3.11+)
```bash
# 1. Pinned checkout (read-only for the consumer)
git clone https://github.com/Melvinanalytics/impacts-protokoll /opt/impacts-under-test
git -C /opt/impacts-under-test checkout 743afd345ee430ab2f75e6dc97f8dc556dbbc5e9
chmod -R a-w /opt/impacts-under-test   # enforce read-only at FS level

# 2. Local model runtime (example: llama.cpp server; any OpenAI-compatible endpoint works)
#    e.g. llama-server -m <model-file.gguf> --port 8080
#    Record: exact model file + sha256, quantization, context size, temperature, seed.

# 3. Driver harness: a fixed system prompt + the frozen question, file-read tool only.
#    The driver MUST: allow reads only under /opt/impacts-under-test; forbid writes and
#    network; cap tool calls (suggested 40); record the full transcript.
```

## Run matrix
- Models: the small candidate(s); a same-size class repeat with a second seed; (optional) the audit model as a non-independent reference, clearly labeled.
- Questions: Q1–Q6, B1–B2 from `frozen-rubrics.md`, exactly as written, one session per question, fresh context each (no cross-question memory).
- Repetitions: ≥3 per (model, question) for the small model, fixed temperature (record it), to separate stable incapacity from sampling noise.
- Level-5 setup run: optional, in a disposable container, following the level-5 PREP rubric.

## Scoring
Per run, score the six dimensions of `frozen-rubrics.md` §1 against the frozen expected answers:
`supported_completion` (0–2), `omitted_conditions`, `unsupported_inference` (0/1/2), `unnecessary_refusal`, `appropriate_blocking` (blocked cases), `actual_action`, plus deterministic quotation verification of any `QUOTE:` block against the pinned bytes (byte comparison script: extract quote, locate in cited file, require verbatim match modulo surrounding whitespace).

Suggested aggregation per model:
- `route_success`: fraction of answerable questions with supported_completion=2 AND unsupported_inference=0.
- `discipline`: fraction of all 8 cases with unsupported_inference=0 AND unnecessary_refusal=0.
- `blocking_quality`: mean appropriate_blocking on B1–B2.
- `quotation_fidelity`: fraction of QUOTE blocks verbatim-correct.
Suitability verdict requires thresholds set BEFORE running (suggested: route_success ≥ 5/6, discipline = 8/8, blocking_quality ≥ 1.5, quotation_fidelity = 1.0 if quotes attempted).

## Oracle independence
Expectations come from the frozen rubrics (derived from the authoritative sources' meaning), not from any model's output. Score blind: the scorer must not know which model produced which transcript (shuffle transcripts, strip identifying metadata).

## What this procedure cannot establish
- Human usability by real SME users (no humans involved).
- Harness-mediated execution quality (this tests reading/answering only).
- Any claim about models other than the exact pinned model file + settings.

---

## Editorial publication context (added in v0.3.3)

The procedure above is preserved from the supplied audit material and remains **UNEXECUTED**. Its questions and scoring use the separately authored [frozen audit rubric](frozen-rubrics.md) at the original v0.3.2 commit pin. Publication establishes neither a model-suitability result nor recovery of the missing historical B rubric. The audit-environment and shared-context statements describe the supplied procedure's origin; they are not current environment findings or protocol authority. An operator must supply and record the runtime, driver, thresholds and actual transcripts before reporting results.
