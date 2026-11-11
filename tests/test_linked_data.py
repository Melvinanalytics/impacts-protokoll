"""Executable counterexamples for datenbezug.md, not a Core reader or connector.

The fixture owns this small x_tables dialect. All loaded rows are checked before
selection; it neither verifies source truth nor interprets arbitrary prose rules.
"""

import copy
import csv
from datetime import date
from decimal import Decimal
from io import StringIO
import json
from pathlib import Path
import re
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]

from impacts_protocol.validator import SCHEMA_NAMES, SCHEMA_REGISTRY


DOCUMENT = ROOT / "02_protocol/impacts-architect/references/datenbezug.md"
FIXTURES = ROOT / "06_evaluations/offer-walk/fixtures"


@pytest.fixture
def source():
    model = yaml.safe_load((FIXTURES / "grundlagen/geschaeftsdaten.md").read_text().split("---")[1])["x_tables"]
    tables = {path.stem: list(csv.DictReader(StringIO(path.read_text())))
              for path in (FIXTURES / "records").glob("*.csv")}
    assert set(tables) == set(model)
    return model, tables


def read(source, customer_id="C-1", as_of="2026-09-10"):
    """Exercise this example's declared keys, intervals, units and selection."""
    model, tables = source
    indexes = {}
    for name, spec in model.items():
        index = {}
        for row in tables[name]:
            key = tuple(row.get(field) for field in spec["primary_key"])
            if not all(key):
                raise ValueError("empty primary key")
            if key in index:
                raise ValueError("duplicate primary key")
            index[key] = row
        indexes[name] = index
    for name, spec in model.items():
        for row in tables[name]:
            for link in spec.get("foreign_keys", []):
                assert link["references"] == model[link["target"]]["primary_key"]
                key = tuple(row.get(field) for field in link["fields"])
                if link.get("nullable") and all(value == "" for value in key):
                    continue
                if key not in indexes[link["target"]]:
                    raise ValueError("unresolved foreign key")
            fields = spec.get("exactly_one")
            if fields and sum(bool(row.get(field)) for field in fields) != 1:
                raise ValueError("exactly one target required")
    intervals = {}
    for row in tables["agreements"]:
        if not re.fullmatch(r"[1-9][0-9]*", row["version"]):
            raise ValueError("non-canonical version")
        start = date.fromisoformat(row["valid_from"])
        end = date.fromisoformat(row["valid_to"]) if row["valid_to"] else None
        if end is not None and start >= end:
            raise ValueError("empty applicability interval")
        previous = intervals.setdefault(row["agreement_id"], [])
        for prior_start, prior_end in previous:
            if (prior_end is None or start < prior_end) and (end is None or prior_start < end):
                raise ValueError("overlapping agreement versions")
        previous.append((start, end))
    for row in tables["agreement_items"]:
        value = Decimal(row["quantity"])
        if not value.is_finite() or value < 0:
            raise ValueError("invalid quantity")
        expected_unit = "Stück" if row["product_id"] else "Stunde"
        if row["unit"] != expected_unit:
            raise ValueError("incompatible unit")
    if (customer_id,) not in indexes["customers"]:
        raise LookupError("customer identity unresolved")
    day = date.fromisoformat(as_of)
    agreements = [row for row in tables["agreements"]
                  if row["customer_id"] == customer_id
                  and date.fromisoformat(row["valid_from"]) <= day
                  and (not row["valid_to"] or day < date.fromisoformat(row["valid_to"]))]
    if not agreements:
        raise LookupError("no matching agreement in this source scope")
    keys = {(row["agreement_id"], row["version"]) for row in agreements}
    items = [row for row in tables["agreement_items"]
             if (row["agreement_id"], row["agreement_version"]) in keys]
    return {"customer": indexes["customers"][(customer_id,)], "as_of": as_of,
            "agreements": agreements, "items": items,
            "products": [indexes["products"][(row["product_id"],)] for row in items if row["product_id"]],
            "services": [indexes["services"][(row["service_id"],)] for row in items if row["service_id"]]}


@pytest.mark.parametrize("customer,day,items", [
    ("C-1", "2026-09-10", ["I-2", "I-3"]),
    ("C-2", "2026-09-10", ["I-4"]),
    ("C-1", "2026-06-30", ["I-1"]),
    ("C-1", "2026-07-01", ["I-2", "I-3"]),
])
def test_selection_preserves_identity_and_version(source, customer, day, items):
    before = copy.deepcopy(source)
    result = read(source, customer, day)
    assert [row["item_id"] for row in result["items"]] == items
    assert source == before


@pytest.mark.parametrize("table,index,change,error", [
    ("customers", 1, {"customer_id": "C-1"}, "duplicate primary key"),
    ("customers", 0, {"customer_id": ""}, "empty primary key"),
    ("agreement_items", 2, {"service_id": "S-404"}, "unresolved foreign key"),
    ("agreement_items", 2, {"agreement_version": "99"}, "unresolved foreign key"),
    ("agreement_items", 2, {"agreement_version": "02"}, "unresolved foreign key"),
    ("agreement_items", 2, {"product_id": "P-10"}, "exactly one target required"),
    ("agreement_items", 2, {"service_id": ""}, "exactly one target required"),
    ("agreement_items", 2, {"quantity": "-1"}, "invalid quantity"),
    ("agreement_items", 2, {"quantity": "NaN"}, "invalid quantity"),
    ("agreement_items", 2, {"unit": "Stück"}, "incompatible unit"),
    ("agreements", 0, {"valid_to": ""}, "overlapping agreement versions"),
    ("agreements", 0, {"valid_to": "2026-01-01"}, "empty applicability interval"),
    # This reader deliberately checks even rows outside the selected customer.
    ("agreement_items", 3, {"service_id": "S-404"}, "unresolved foreign key"),
])
def test_bad_source_cannot_yield_a_successful_excerpt(source, table, index, change, error):
    source[1][table][index].update(change)
    with pytest.raises(ValueError, match=f"^{error}$"):
        read(source)


@pytest.mark.parametrize("customer,day,error", [
    ("C-404", "2026-09-10", "customer identity unresolved"),
    ("Beispielkunde", "2026-09-10", "customer identity unresolved"),
    ("C-1", "2025-12-31", "no matching agreement in this source scope"),
])
def test_missing_evidence_is_a_scoped_gap(source, customer, day, error):
    with pytest.raises(LookupError, match=f"^{error}$"):
        read(source, customer, day)


def test_multiple_valid_agreements_are_not_reduced_to_first(source):
    tables = source[1]
    tables["agreements"].append(dict(tables["agreements"][2], agreement_id="A-3", customer_id="C-1"))
    tables["agreement_items"].append(dict(tables["agreement_items"][3], item_id="I-5", agreement_id="A-3"))
    result = read(source)
    assert [row["agreement_id"] for row in result["agreements"]] == ["A-1", "A-3"]
    assert [row["item_id"] for row in result["items"]] == ["I-2", "I-3", "I-5"]


def test_valid_foreign_key_does_not_verify_source_truth(source):
    # Reassign to a real, different version. Integrity checks cannot know that
    # the original source assertion was true or that this reassignment is false.
    source[1]["agreement_items"][2]["agreement_version"] = "1"
    assert [row["item_id"] for row in read(source)["items"]] == ["I-2"]


def test_compact_document_view_matches_computed_excerpt(source):
    shown = json.loads((FIXTURES / "excerpt.json").read_text())
    result = read(source)
    assert shown["customer_id"] == result["customer"]["customer_id"]
    assert shown["as_of"] == result["as_of"]
    assert shown["agreement"] == {"agreement_id": result["agreements"][0]["agreement_id"],
                                  "version": int(result["agreements"][0]["version"])}
    for compact, full in zip(shown["items"], result["items"], strict=True):
        for key, value in compact.items():
            assert value == (Decimal(full[key]) if key == "quantity" else full[key])


# Knowledge form: resolution through declared links only.


def test_form_is_local_vocabulary_not_a_core_pipeline():
    """The knowledge form must not masquerade as a Core object: its frontmatter
    type is local vocabulary, and no laufpfad/route machinery is involved."""
    text = DOCUMENT.read_text(encoding="utf-8")
    model_type = yaml.safe_load((FIXTURES / "grundlagen/geschaeftsdaten.md").read_text().split("---")[1])["type"]
    assert model_type == "DomainModel"
    assert model_type not in SCHEMA_NAMES
    assert "laufpfad" not in text.split("## Domain model and source tables")[1].split("## Bind a working excerpt")[0]


def test_fresh_reader_resolves_fact_through_declared_links(source):
    """Fact: agreed scope of C-1 at 2026-09-10, resolved only via the
    x_tables resource/foreign-key links (hand-computed oracle)."""
    result = read(source, customer_id="C-1", as_of="2026-09-10")
    assert result["customer"]["customer_id"] == "C-1"
    assert [(r["agreement_id"], r["version"]) for r in result["agreements"]] == [("A-1", "2")]
    assert [(r["item_id"], r["quantity"], r["unit"]) for r in result["items"]] == [
        ("I-2", "2", "Stück"), ("I-3", "12", "Stunde")]


def test_empty_valid_to_is_confirmed_open_end_not_unknown(source):
    """A-2 v1 has empty valid_to: documented as 'bestätigtes offenes Ende'.
    It must stay selectable at any later date — missing != false/zero."""
    result = read(source, "C-2", "2031-01-01")
    assert [r["agreement_id"] for r in result["agreements"]] == ["A-2"]
    assert [r["item_id"] for r in result["items"]] == ["I-4"]


def test_multi_entity_relationship_keeps_direction_and_multiplicity(source):
    """agreement_items -> agreements (composite key, agreed_under_version);
    items -> products|services (exactly one, catalog KIND)."""
    model, _ = source
    links = {l["meaning"]: l for l in model["agreement_items"]["foreign_keys"]}
    assert links["agreed_under_version"]["fields"] == ["agreement_id", "agreement_version"]
    assert links["agreed_under_version"]["references"] == ["agreement_id", "version"]
    assert model["agreement_items"]["exactly_one"] == ["product_id", "service_id"]


def test_kind_vs_instance_and_requested_offered_agreed_delivered(source):
    """The excerpt carries catalog KINDS under an AGREED state only. No
    requested/offered/delivered/consumed/price claim may appear or be derived."""
    result = read(source)
    for row in result["products"] + result["services"]:
        assert set(row) <= {("product_id"), ("service_id"), "label"}
    blob = repr(result).lower()
    for forbidden in ("delivered", "geliefert", "consumed", "verbrauch", "price", "preis"):
        assert forbidden not in blob
    # zero agreed quantity is structurally permitted but still asserts no delivery
    src = copy.deepcopy(source)
    src[1]["agreement_items"][1]["quantity"] = "0"
    result0 = read(src)
    assert result0["items"][0]["quantity"] == "0"  # present, agreed, nothing more


def test_forbidden_transitive_inference_stays_open(source):
    """C-1 -> A-1/2 -> I-3 -> S-20 establishes NO 'S-20 covers C-1's delivered
    device' claim. The document's own checkable-questions table fixes the
    expected answer as `open`; the reader must produce no such link."""
    text = DOCUMENT.read_text(encoding="utf-8")
    row = next(l for l in text.splitlines() if "cover the delivered device" in l)
    assert "`open`" in row
    result = read(source)
    assert not any("cover" in key or "device" in key
                   for service in result["services"] for key in service)


def test_units_do_not_sum_across_kinds(source):
    """2 Stück + 12 Stunde is not 14 of anything; separate positions retained."""
    result = read(source)
    units = {r["unit"] for r in result["items"]}
    assert units == {"Stück", "Stunde"}
    assert len(result["items"]) == 2  # not collapsed into one summed position


def test_unlinked_neighbor_table_is_rejected_not_silently_read(tmp_path, monkeypatch):
    """Domain meaning must come through intended links, not folder proximity:
    a decoy CSV block sitting next to the linked ones is not part of the model
    and must trip the fixture's link-coverage guard."""
    import shutil
    fixture_copy = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, fixture_copy)
    (fixture_copy / "records/decoy.csv").write_text("customer_id,display_name\nC-1,Lockvogel\n")
    monkeypatch.setattr(sys.modules[__name__], "FIXTURES", fixture_copy)
    with pytest.raises(AssertionError):
        source.__wrapped__()


@pytest.fixture
def offer():
    return ((FIXTURES / "template.de.md").read_text().removesuffix("\n"),
            json.loads((FIXTURES / "data.json").read_text()),
            (FIXTURES / "filled.md").read_text().removesuffix("\n"))


# Use the executed example implementation; do not maintain a second calculator.
import importlib.util
_spec = importlib.util.spec_from_file_location("offer_walk", ROOT / "06_evaluations/offer-walk/run.py")
_offer_walk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_offer_walk)
fill_offer = _offer_walk.fill_offer


def test_offer_blank_becomes_the_documented_instance_without_changing_inputs(offer):
    template, values, expected = offer
    before = copy.deepcopy(offer)
    assert fill_offer(template, values) == expected
    assert offer == before


def test_same_blank_fills_an_independent_second_vorgang(offer):
    template, first, _ = offer
    first_result = fill_offer(template, first)
    second = copy.deepcopy(first)
    second.update(offer_id="O-2", customer_id="C-2", request_ref="AN-2")
    second["items"][0]["quantity"] = "1"
    second["items"][1]["quantity"] = "3"
    result = fill_offer(template, second)
    assert "Angebot O-2" in result and "Kunde: C-2" in result and "340.00 EUR" in result
    assert fill_offer(template, first) == first_result
    assert "{{offer_id}}" in template


@pytest.mark.parametrize("change,error", [
    ({"currency": "USD"}, "incompatible unit or currency"),
    ({"unit_price": ""}, "missing quantity or price"),
    ({"price_source": ""}, "missing or duplicate position identity/source"),
    ({"quantity": "NaN"}, "invalid quantity or price"),
    ({"unit_price": "100.001"}, "rounding rule required"),
])
def test_undefined_offer_inputs_do_not_produce_a_filled_result(offer, change, error):
    template, values, _ = offer
    values["items"][0].update(change)
    with pytest.raises(ValueError, match=f"^{error}$"):
        fill_offer(template, values)


def test_offer_cannot_hide_an_unfilled_required_placeholder(offer):
    template, values, _ = offer
    with pytest.raises(ValueError, match="^unfilled placeholder$"):
        fill_offer(template + "\nLieferung: {{delivery}}", values)


@pytest.fixture
def offer_workstep():
    return yaml.safe_load((FIXTURES / "arbeitsschritt.md").read_text().split("---")[1])


def test_worked_offer_step_uses_the_existing_core_schema(offer_workstep):
    assert list(SCHEMA_REGISTRY.errors("arbeitsschritt", offer_workstep)) == []


@pytest.mark.parametrize("changes", [
    {"role": "dokumentrohling-agent"},
    {"input_spec": [{"name": "angebotsdaten.json"}]},
    {"id": "entwerfen"},
    {"pruefung": [{"name": "betraege_korrekt"}]},
])
def test_weak_model_schema_inventions_are_rejected(offer_workstep, changes):
    offer_workstep.update(changes)
    assert list(SCHEMA_REGISTRY.errors("arbeitsschritt", offer_workstep))
