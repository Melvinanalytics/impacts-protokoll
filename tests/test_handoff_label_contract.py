"""Owner A audit tests: handoff mapping sentence is one parser-consumed label.

Oracle: the handoff mapping sentence declared in 02_protocol/capabilities.md,
"Visible output and handoff", is a parser-consumed label under
02_protocol/language.md, "Preserve meaning" — stable across working
languages. A fresh consumer following the language contract must be able to learn
that at the label's owning home, and the protocol router must reach that home.
These tests derive expectations from those authoritative sources, not from current
implementation output.
"""
import os
import re
from pathlib import Path

# In the repo this file lives at tests/test_handoff_label_contract.py (parents[1]).
# For red/green audit runs against an unmodified tree, point IMPACTS_ROOT at it.
ROOT = Path(os.environ.get("IMPACTS_ROOT") or Path(__file__).resolve().parents[1])

CAPABILITIES = ROOT / "02_protocol/capabilities.md"
ROUTER = ROOT / "02_protocol/CONTEXT.md"
OFFER_RUN = ROOT / "06_evaluations/offer-walk/run.py"
COLD_CHECK = ROOT / "06_evaluations/cold-walk/check.py"


def handoff_section() -> str:
    text = CAPABILITIES.read_text(encoding="utf-8")
    marker = '<a id="sichtbare-ausgabe-und-übergabe"></a>'
    start = text.index(marker)
    nxt = text.find('<a id="', start + len(marker))
    return text[start: nxt if nxt != -1 else len(text)]


def declared_example_sentence() -> str:
    section = handoff_section()
    fence = re.findall(r"(?ms)^```markdown\n(.*?)^```", section)
    assert len(fence) == 1, "the handoff section declares exactly one syntax example"
    lines = [line for line in fence[0].splitlines() if line.strip()]
    assert len(lines) == 1
    return lines[0]


def test_mapping_sentence_is_declared_a_parser_consumed_label():
    """RED on unrepaired trees: the owning declaration must tie the sentence to
    language.md's parser-consumed-label rule, so that a consumer applying
    'translate prose' does not silently break the reference harness check."""
    section = handoff_section()
    assert "language.md#preserve-meaning" in section, (
        "the handoff section never connects the sentence to the "
        "language contract's parser-consumed-label rule")
    assert re.search(r"parser-consumed label", section), (
        "the handoff section never names the sentence a parser-consumed label")
    assert re.search(r"every working language", section), (
        "the handoff section never states the label is stable across languages")


def test_router_reaches_the_handoff_contract_from_the_workstep_route():
    """RED on unrepaired trees: the workstep task route must conditionally load
    the section that owns the handoff mapping syntax."""
    text = ROUTER.read_text(encoding="utf-8")
    row = next(line for line in text.splitlines()
               if line.startswith("| Workstep prompt"))
    assert "capabilities.md#sichtbare-ausgabe-und-übergabe" in row, (
        "no documented route from workstep composition to the handoff contract")


def test_declared_syntax_is_what_the_reference_harnesses_read():
    """Guard (green before and after): the documented example sentence stays
    inside the grammar the two reference harnesses actually accept."""
    sentence = declared_example_sentence()
    # offer-walk run.py bound_inputs grammar (anchored, exact sentence).
    offer = re.compile(
        r"(?m)^Bei Route `bestanden`: `(output/[^` ]+) -> (arbeitsschritt:[^` ]+)`\.$")
    assert offer.fullmatch(sentence), (
        "offer-walk harness would reject the documented syntax example")
    # cold-walk check.py grammar.
    cold = re.compile(r"(?m)^Bei Route `([^`]+)`: `([^`]+) -> ")
    assert cold.search(sentence), (
        "cold-walk harness would reject the documented syntax example")


def test_generated_offer_uses_the_declared_stable_sentence_form():
    """Guard: the offer-walk generator emits the declared label byte-consistently
    in both working languages (only the harness-declared syntax appears)."""
    source = OFFER_RUN.read_text(encoding="utf-8")
    emitted = sorted(set(re.findall(r'"(Bei Route `bestanden`: [^"]+)"', source)))
    assert len(emitted) == 2  # one mapping sentence per handoff file
    for line in emitted:
        line = line.removesuffix("\\n")  # trailing newline escape inside the source literal
        assert re.fullmatch(
            r"Bei Route `bestanden`: `output/[^` ]+ -> arbeitsschritt:freigeben/input/[^` ]+`\.",
            line), f"generator emits a non-declared mapping sentence: {line}"
    assert "On route" not in source and "Bei Route" in source
