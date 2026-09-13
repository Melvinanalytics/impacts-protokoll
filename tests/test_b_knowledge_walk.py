"""Owner B audit — §5.F non-process knowledge: fresh-reader resolution.

Exercises the knowledge/record form in
02_protocol/impacts-architect/references/datenbezug.md (DomainModel + x_tables
+ CSV records) WITHOUT turning it into a Pipeline. The excerpt calculator is
the repo's own executed example reader (tests/test_linked_data.py: read) — no
second calculator is maintained. All expectations below are hand-derived from
the CSV bytes and the model's documented reading convention BEFORE running:

  customers: C-1/C-2 share display_name "Beispielkunde"
  agreements: A-1 v1 [2026-01-01,2026-07-01), A-1 v2 [2026-07-01,open), A-2 v1 C-2
  items: I-1(A-1/1,P-10,1 Stück) I-2(A-1/2,P-10,2 Stück) I-3(A-1/2,S-20,12 Std)
         I-4(A-2/1,S-20,8 Std)

Run from a checkout root:  python -m pytest tests/test_b_knowledge_walk.py
"""
import copy
import os
from pathlib import Path
import re
import sys

import pytest

ROOT = Path(os.environ.get("IMPACTS_AUDIT_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import tests.test_linked_data as example
from impacts_protocol.validator import SCHEMA_NAMES


@pytest.fixture
def source():
    return example.source.__wrapped__()  # the documented fixture, unwrapped


def test_form_is_local_vocabulary_not_a_core_pipeline():
    """The knowledge form must not masquerade as a Core object: its frontmatter
    type is local vocabulary, and no laufpfad/route machinery is involved."""
    text = example.DOCUMENT.read_text(encoding="utf-8")
    model_type = re.search(r"```markdown\n---\ntype: (\w+)", text)[1]
    assert model_type == "DomainModel"
    assert model_type not in SCHEMA_NAMES
    assert "laufpfad" not in text.split("## Domain model and source tables")[1].split("## Bind a working excerpt")[0]


def test_fresh_reader_resolves_fact_through_declared_links(source):
    """Fact: agreed scope of C-1 at 2026-09-10, resolved only via the
    x_tables resource/foreign-key links (hand-computed oracle)."""
    result = example.read(source, customer_id="C-1", as_of="2026-09-10")
    assert result["customer"]["customer_id"] == "C-1"
    assert [(r["agreement_id"], r["version"]) for r in result["agreements"]] == [("A-1", "2")]
    assert [(r["item_id"], r["quantity"], r["unit"]) for r in result["items"]] == [
        ("I-2", "2", "Stück"), ("I-3", "12", "Stunde")]


def test_validity_interval_boundaries_are_half_open(source):
    """valid_from inclusive, valid_to exclusive — hand-derived from the dates."""
    assert [r["version"] for r in example.read(source, "C-1", "2026-06-30")["agreements"]] == ["1"]
    assert [r["version"] for r in example.read(source, "C-1", "2026-07-01")["agreements"]] == ["2"]


def test_empty_valid_to_is_confirmed_open_end_not_unknown(source):
    """A-2 v1 has empty valid_to: documented as 'bestätigtes offenes Ende'.
    It must stay selectable at any later date — missing != false/zero."""
    result = example.read(source, "C-2", "2031-01-01")
    assert [r["agreement_id"] for r in result["agreements"]] == ["A-2"]
    assert [r["item_id"] for r in result["items"]] == ["I-4"]


def test_identity_is_key_not_name(source):
    """Two customers share display_name 'Beispielkunde': a name must not resolve."""
    with pytest.raises(LookupError, match="^customer identity unresolved$"):
        example.read(source, customer_id="Beispielkunde")
    assert len({r["customer_id"] for r in source[1]["customers"]}) == 2
    assert len({r["display_name"] for r in source[1]["customers"]}) == 1


def test_multi_entity_relationship_keeps_direction_and_multiplicity(source):
    """agreement_items -> agreements (composite key, agreed_under_version);
    items -> products|services (exactly one, catalog KIND). Multiple valid
    agreements of one customer stay multiple results (no silent collapse)."""
    model, tables = source
    links = {l["meaning"]: l for l in model["agreement_items"]["foreign_keys"]}
    assert links["agreed_under_version"]["fields"] == ["agreement_id", "agreement_version"]
    assert links["agreed_under_version"]["references"] == ["agreement_id", "version"]
    assert model["agreement_items"]["exactly_one"] == ["product_id", "service_id"]
    tables["agreements"].append(dict(tables["agreements"][2], agreement_id="A-3", customer_id="C-1"))
    tables["agreement_items"].append(
        dict(tables["agreement_items"][3], item_id="I-5", agreement_id="A-3"))
    result = example.read(source)
    assert [r["agreement_id"] for r in result["agreements"]] == ["A-1", "A-3"]


def test_kind_vs_instance_and_requested_offered_agreed_delivered(source):
    """The excerpt carries catalog KINDS under an AGREED state only. No
    requested/offered/delivered/consumed/price claim may appear or be derived."""
    result = example.read(source)
    for row in result["products"] + result["services"]:
        assert set(row) <= {("product_id"), ("service_id"), "label"}
    blob = repr(result).lower()
    for forbidden in ("delivered", "geliefert", "consumed", "verbrauch", "price", "preis"):
        assert forbidden not in blob
    # zero agreed quantity is structurally permitted but still asserts no delivery
    src = copy.deepcopy(source)
    src[1]["agreement_items"][1]["quantity"] = "0"
    result0 = example.read(src)
    assert result0["items"][0]["quantity"] == "0"  # present, agreed, nothing more


def test_forbidden_transitive_inference_stays_open(source):
    """C-1 -> A-1/2 -> I-3 -> S-20 establishes NO 'S-20 covers C-1's delivered
    device' claim. The document's own checkable-questions table fixes the
    expected answer as `open`; the reader must produce no such link."""
    text = example.DOCUMENT.read_text(encoding="utf-8")
    row = next(l for l in text.splitlines() if "cover the delivered device" in l)
    assert "`open`" in row
    result = example.read(source)
    assert not any("cover" in key or "device" in key
                   for service in result["services"] for key in service)


def test_units_do_not_sum_across_kinds(source):
    """2 Stück + 12 Stunde is not 14 of anything; separate positions retained."""
    result = example.read(source)
    units = {r["unit"] for r in result["items"]}
    assert units == {"Stück", "Stunde"}
    assert len(result["items"]) == 2  # not collapsed into one summed position


def test_unknown_is_a_scoped_gap_not_an_empty_answer(source):
    with pytest.raises(LookupError, match="^customer identity unresolved$"):
        example.read(source, customer_id="C-404")
    with pytest.raises(LookupError, match="^no matching agreement in this source scope$"):
        example.read(source, customer_id="C-1", as_of="2025-12-31")


def test_unlinked_neighbor_table_is_rejected_not_silently_read(tmp_path, monkeypatch):
    """Domain meaning must come through intended links, not folder proximity:
    a decoy CSV block sitting next to the linked ones is not part of the model
    and must trip the fixture's link-coverage guard."""
    text = example.DOCUMENT.read_text(encoding="utf-8")
    decoy = text + "\n### `records/decoy.csv`\n\n```csv\ncustomer_id,display_name\nC-1,Lockvogel\n```\n"
    probe = tmp_path / "datenbezug.md"
    probe.write_text(decoy, encoding="utf-8")
    monkeypatch.setattr(example, "DOCUMENT", probe)
    with pytest.raises(AssertionError):
        example.source.__wrapped__()
