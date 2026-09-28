"""Keep the synthetic listening screen and future gates explicit and bounded."""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "06_evaluations" / "listening-intake"


def load_messages():
    return [
        json.loads(line)
        for line in (SCREEN / "messages.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def test_screen_has_twenty_synthetic_messages_in_ten_matched_pairs():
    messages = load_messages()
    assert len(messages) == 20
    assert {item["id"] for item in messages} == {f"M{index:02d}" for index in range(1, 21)}
    assert all(item["source"].startswith("synthetic-chat:") for item in messages)

    pairs = defaultdict(list)
    for item in messages:
        pairs[item["pair"]].append(item)
    assert set(pairs) == {f"P{index:02d}" for index in range(1, 11)}
    assert {item["challenge"] for item in messages} == {
        "negation",
        "conditional-scope",
        "supersession",
        "claimed-approval",
        "personal-data",
        "duplicate",
        "contradiction",
        "identity-ambiguity",
        "instruction-injection",
        "unknown-owner",
    }
    for pair in pairs.values():
        assert len(pair) == 2
        assert {item["set"] for item in pair} == {"A", "B"}
        assert len({item["challenge"] for item in pair}) == 1

    assert {name: sum(item["set"] == name for item in messages) for name in ("A", "B")} == {
        "A": 10,
        "B": 10,
    }
    by_id = {item["id"]: item for item in messages}
    assert by_id["M11"]["message"] == by_id["M01"]["message"]
    assert by_id["M12"]["message"] == by_id["M02"]["message"]


def test_screen_cannot_complete_without_independent_reuse_records():
    context = (SCREEN / "CONTEXT.md").read_text(encoding="utf-8")
    expected = (SCREEN / "EXPECTED.md").read_text(encoding="utf-8")
    questions = (SCREEN / "QUESTIONS.md").read_text(encoding="utf-8")
    response_form = (SCREEN / "reuse-record-template.md").read_text(encoding="utf-8")

    for phrase in (
        "manual baseline",
        "candidate capture",
        "fresh independent capture operator",
        "independent scorer",
        "all human effort",
        "hard failure",
        "stop candidate evaluation",
        "one-sided 95% upper bound of about 14%",
        "independent Bernoulli assumption",
        "Langdock result",
        "runtime capability",
        "fresh reuse operator and session",
        "The analytical handoff contains only the neutrally named retained record package and `QUESTIONS.md`",
        "The capture operator does not answer the reuse questions",
        "all four capture records and capture-effort logs are frozen",
        "each has a corresponding answer-and-effort record",
        "missing independent session",
        "missing answer or effort",
        "Each response must contain all answers, citations and actual effort values",
        "distinct fresh reuse operator/session",
        "using only the retained record and `QUESTIONS.md`",
    ):
        assert phrase in context
    for phrase in (
        "Question mapping",
        "invents an owner, approval or rule authority",
        "do not repair the candidate answer",
        "identity ambiguity",
        "instruction injection",
    ):
        assert phrase in expected
    assert context.count("| Block") == 1
    assert "All results and gates remain `open`." in context
    assert expected.endswith("\n")
    assert "M01" not in questions and "hard failure" not in questions
    assert "EXPECTED.md" not in questions and "arm" not in questions.lower()
    assert "Do not invent" not in questions
    assert len([line for line in questions.splitlines() if line[:1].isdigit() and line[1:3] == ". "]) == 7
    question_rows = [line for line in questions.splitlines() if line[:1].isdigit() and line[1:3] == ". "]
    assert [line[:1] for line in question_rows] == list("1234567")
    nonempty_questions = [line for line in questions.splitlines() if line]
    assert nonempty_questions == ["# Reuse questions", *question_rows]
    assert "Status: `open`." in response_form
    assert "Block / arm / set" not in response_form
    assert "Opaque handoff ID" in response_form
    assert response_form.count("`<actual answer and citations>`") == 7
    assert "Active minutes" in response_form and "Waiting minutes" in response_form
    assert "EXPECTED.md" not in questions


def test_future_gates_are_unperformed_and_cover_all_requested_scoring():
    followup = (
        ROOT / "06_evaluations" / "nontechnical-reconstruction" / "FOLLOW-UP.md"
    ).read_text(encoding="utf-8")
    for phrase in (
        "Status: protocol prepared; every gate and result is `open`",
        "A gate cannot run while any of these is `open`",
        "168 hours",
        "bounded domain review",
        "matched business comparison",
        "Licensed sentence after closure",
        "stays in the denominator",
        "never rewrite a failed answer after the scorer sees it",
        "do not merge populations or time periods that do not match",
        "adverse actions",
        "useful result",
        "status navigation",
        "total human effort/time",
        "review time",
        "Stop further candidate exposure if candidate adverse actions exceed the matched baseline",
    ):
        assert phrase in followup
    assert "no participant result" in followup
    assert "No unperformed score, pass, benefit or reduction" in followup


def test_retention_guidance_keeps_harness_boundary_and_deletion_design_open():
    capabilities = (ROOT / "02_protocol" / "capabilities.md").read_text(encoding="utf-8")
    german = (ROOT / "02_protocol" / "translations" / "de.md").read_text(encoding="utf-8")
    for phrase in (
        "## Retention and deletion at the harness boundary",
        "legal basis",
        "retention period and exceptions",
        "known copies, projections, caches, search indexes, exports and backups",
        "deletion preview",
        "human approval",
        "Prevent a concurrent writer",
        "partial failure",
        "backup and restore paths",
        "neither deleted content nor a content hash",
        "Unknown consumers remain unknown",
        "`hash.mismatch`, indistinguishable from tampering",
        "no Core deletion state or schema",
    ):
        assert phrase in capabilities
    assert "Aufbewahrung und Löschung an der Harness-Grenze" in german
    assert "`hash.mismatch`" in german
    assert "Offene Designfrage" in german
