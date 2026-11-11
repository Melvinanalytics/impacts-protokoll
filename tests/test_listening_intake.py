"""Check the synthetic listening message structure."""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "06_evaluations" / "nontechnical-reconstruction"


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


def test_blinded_handoff_questions_and_response_slots():
    questions = (SCREEN / "QUESTIONS.md").read_text(encoding="utf-8")
    response_form = (SCREEN / "reuse-record-template.md").read_text(encoding="utf-8")

    rows = re.findall(r"^(\d+)\. (.+)$", questions, re.M)
    assert [number for number, _ in rows] == [str(number) for number in range(1, 8)]
    assert all(question.endswith("?") for _, question in rows)
    nonempty = [line for line in questions.splitlines() if line.strip()]
    assert re.fullmatch(r"# [^#]+", nonempty[0])
    assert nonempty[1:] == [f"{number}. {question}" for number, question in rows]
    for document in (questions, response_form):
        assert not re.search(r"\bM\d+\b", document)
        assert not re.search(r"\b(?:EXPECTED|listening-expected)\.md\b", document, re.I)
        assert not re.search(r"\b(?:manual baseline|candidate capture|arm [AB])\b", document, re.I)
    assert not re.search(r"\b(?:arm|scoring[- ]key)\b", questions, re.I)
    assert "Block / arm / set" not in response_form
    assert "- Opaque handoff ID: `<coordinator-assigned neutral ID>`" in response_form
    assert re.findall(r"^### Q(\d+)$", response_form, re.M) == list("1234567")
    assert response_form.count("`<actual answer and citations>`") == 7
