import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unicodedata

import pytest
import yaml
from hypothesis import given, settings, strategies as st

from impacts_protocol import io
from impacts_protocol.hashing import surface_hash
from impacts_protocol.io import (
    DuplicateKeyError,
    load_frontmatter_and_body,
    load_yaml_strict,
)


HYPOTHESIS_SETTINGS = settings(
    max_examples=40,
    database=None,
    derandomize=True,
)
_BOM = b"\xef\xbb\xbf"
_UNICODE_TEXT = st.text(
    alphabet=st.characters(
        whitelist_categories=("Ll", "Lu", "Lo", "Mn", "Mc", "Nd"),
        whitelist_characters=" -_?!",
    ),
    max_size=30,
)
_PLAIN_UNICODE_SCALAR = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Lo")),
    min_size=1,
    max_size=24,
).filter(
    lambda value: value.casefold()
    not in {
        "y",
        "yes",
        "n",
        "no",
        "true",
        "false",
        "on",
        "off",
        "null",
        "nan",
        "inf",
        "infinity",
    }
)
_DUPLICATE_KEY = st.from_regex(r"[a-z][a-z0-9_-]{0,11}", fullmatch=True).filter(
    lambda key: key not in {"yes", "no", "true", "false", "on", "off", "null"}
)


@HYPOTHESIS_SETTINGS
@given(
    value=_UNICODE_TEXT,
    newline=st.sampled_from(("\n", "\r\n")),
    leading_boms=st.integers(min_value=0, max_value=4),
    bom_location=st.sampled_from(("none", "scalar", "body")),
    bom_offset=st.integers(min_value=0, max_value=30),
)
def test_frontmatter_loader_handles_bom_positions_and_newlines_without_rewriting_bytes(
    value, newline, leading_boms, bom_location, bom_offset
):
    scalar = value
    body_value = value
    if bom_location == "scalar":
        offset = bom_offset % (len(scalar) + 1)
        scalar = scalar[:offset] + "\ufeff" + scalar[offset:]
    elif bom_location == "body":
        offset = bom_offset % (len(body_value) + 1)
        body_value = body_value[:offset] + "\ufeff" + body_value[offset:]

    body_line = f"body {body_value}"
    source = (
        f"---{newline}value: {json.dumps(scalar, ensure_ascii=False)}{newline}"
        f"---{newline}{body_line}{newline}"
    ).encode("utf-8")
    raw = _BOM * leading_boms + source
    with TemporaryDirectory() as directory:
        path = Path(directory) / "CONTEXT.md"
        path.write_bytes(raw)

        if leading_boms >= 2:
            with pytest.raises(ValueError):
                load_frontmatter_and_body(path)
        else:
            metadata, body = load_frontmatter_and_body(path)
            assert metadata == {"value": scalar}
            assert body_line in body
        assert path.read_bytes() == raw


@HYPOTHESIS_SETTINGS
@given(value=_UNICODE_TEXT, leading_bom=st.sampled_from((False, True)))
def test_plain_markdown_without_frontmatter_stays_plain_text(value, leading_bom):
    source = f"# {value}\r\nMore text.\r\n"
    raw = (_BOM if leading_bom else b"") + source.encode("utf-8")
    with TemporaryDirectory() as directory:
        path = Path(directory) / "notes.md"
        path.write_bytes(raw)

        metadata, body = load_frontmatter_and_body(path)

        assert metadata == {}
        assert body == source.replace("\r\n", "\n")
        assert path.read_bytes() == raw


@HYPOTHESIS_SETTINGS
@given(key=_DUPLICATE_KEY)
def test_frontmatter_loader_rejects_duplicate_keys_in_both_plain_and_quoted_forms(
    key,
):
    with TemporaryDirectory() as directory:
        path = Path(directory) / "CONTEXT.md"
        for spelling in (key, json.dumps(key)):
            source = f"---\n{spelling}: first\n{spelling}: second\n---\n"
            path.write_text(source, encoding="utf-8")

            with pytest.raises(DuplicateKeyError) as error:
                load_frontmatter_and_body(path)

            assert error.value.key == key


@HYPOTHESIS_SETTINGS
@given(value=_PLAIN_UNICODE_SCALAR)
def test_public_yaml_loader_matches_python_and_c_safe_yaml_semantics(value):
    source = f"value: {value}\n"
    parsed = load_yaml_strict(source)
    python_result = yaml.load(source, Loader=io._PythonStrictLoader)

    assert parsed == python_result == {"value": value}
    if io._C_SAFE_LOADER is not None:
        c_result = yaml.load(source, Loader=io._StrictLoader)
        assert c_result == python_result


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("YES", True),
        ("No", False),
        ("on", True),
        ("OFF", False),
        ("true", True),
        ("False", False),
    ],
)
def test_yaml_boolean_coercion_keeps_existing_safe_loader_dialect(token, expected):
    source = f"enabled: {token}\n"
    parsed = load_yaml_strict(source)

    assert parsed == {"enabled": expected}
    assert yaml.load(source, Loader=io._PythonStrictLoader) == parsed
    if io._C_SAFE_LOADER is not None:
        assert yaml.load(source, Loader=io._StrictLoader) == parsed


def test_frontmatter_read_keeps_bom_bytes_in_the_existing_surface_hash(tmp_path):
    path = tmp_path / "CONTEXT.md"
    original = b"---\r\ntype: workspace\r\n---\r\n\r\n# Body\r\n"
    raw = _BOM + original
    path.write_bytes(raw)
    with_bom_hash = surface_hash(tmp_path, ["CONTEXT.md"])

    load_frontmatter_and_body(path)

    assert path.read_bytes() == raw
    assert surface_hash(tmp_path, ["CONTEXT.md"]) == with_bom_hash
    path.write_bytes(original)
    assert surface_hash(tmp_path, ["CONTEXT.md"]) != with_bom_hash


@pytest.mark.parametrize(
    ("nfc_name", "nfd_name"),
    [
        ("caf\u00e9.md", "cafe\u0301.md"),
        ("\u00c5land.md", "A\u030aland.md"),
    ],
)
def test_surface_hash_keeps_nfc_and_nfd_path_names_byte_distinct(
    tmp_path, nfc_name, nfd_name
):
    stored_names = []
    digests = []
    for root_name, file_name in (("nfc", nfc_name), ("nfd", nfd_name)):
        root = tmp_path / root_name
        input_dir = root / "input"
        input_dir.mkdir(parents=True)
        (input_dir / file_name).write_bytes(b"same file bytes\n")
        stored_name = next(input_dir.iterdir()).name
        stored_names.append(stored_name)
        digests.append(surface_hash(root, [f"input/{stored_name}"]))

    assert unicodedata.normalize("NFC", stored_names[0]) == unicodedata.normalize(
        "NFC", stored_names[1]
    )
    if os.fsencode(stored_names[0]) == os.fsencode(stored_names[1]):
        pytest.skip("filesystem normalized distinct Unicode path spellings")
    assert digests[0] != digests[1]
