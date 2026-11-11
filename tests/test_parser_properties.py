from datetime import date
import json
import os
from pathlib import Path
import random
import subprocess
import sys
from tempfile import TemporaryDirectory
import unicodedata

import pytest
import yaml
from hypothesis import given, settings, strategies as st

from impacts_protocol import init_workspace, io, validate
from impacts_protocol.hashing import file_references
from impacts_protocol.io import (
    DuplicateKeyError,
    load_frontmatter_and_body,
    load_yaml_strict,
)


ROOT = Path(__file__).resolve().parents[1]

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


@pytest.mark.parametrize("force_python", [False, True])
def test_duplicate_key_errors_report_plain_and_absolute_frontmatter_locations(
    tmp_path, monkeypatch, force_python
):
    if force_python:
        monkeypatch.setattr(io, "_StrictLoader", io._PythonStrictLoader)
    plain_yaml = "type: workspace\nnested:\n  route: approve\n  route: deny\n"
    with pytest.raises(DuplicateKeyError) as plain_error:
        load_yaml_strict(plain_yaml)
    assert plain_error.value.key == "route"
    assert plain_error.value.line == 4
    assert plain_error.value.column == 3

    markdown = tmp_path / "CONTEXT.md"
    markdown.write_text(f"---\n{plain_yaml}---\n", encoding="utf-8")
    with pytest.raises(DuplicateKeyError) as markdown_error:
        load_frontmatter_and_body(markdown)
    assert markdown_error.value.key == "route"
    assert markdown_error.value.line == 5
    assert markdown_error.value.column == 3


@pytest.mark.parametrize("force_python", [False, True])
def test_boolean_mapping_key_diagnostic_identifies_coerced_token_and_line(
    tmp_path, monkeypatch, force_python
):
    if force_python:
        monkeypatch.setattr(io, "_StrictLoader", io._PythonStrictLoader)
    path = tmp_path / "CONTEXT.md"
    path.write_text("---\ntype: workspace\ntrue: value\n---\n", encoding="utf-8")

    with pytest.raises(ValueError) as error:
        load_frontmatter_and_body(path)

    assert "line 3" in str(error.value)
    assert "token 'true'" in str(error.value)
    assert "resolves to True" in str(error.value)


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


def test_yaml_loader_accepts_bounded_alias_reuse_and_nesting():
    alias_source = "shared: &shared\n  value: retained\n" + "".join(
        f"reference{index}: *shared\n" for index in range(32)
    )
    aliases = load_yaml_strict(alias_source)
    assert len(aliases) == 33
    assert all(
        aliases[f"reference{index}"] is aliases["shared"] for index in range(32)
    )

    depth = 48
    nested_source = "root:\n" + "".join(
        "  " * (level + 1) + f"level{level}:\n" for level in range(depth)
    )
    nested_source += "  " * (depth + 1) + "leaf: retained\n"
    nested = load_yaml_strict(nested_source)["root"]
    for level in range(depth):
        nested = nested[f"level{level}"]
    assert nested == {"leaf": "retained"}


def test_frontmatter_read_keeps_bom_bytes_in_the_existing_file_references(tmp_path):
    path = tmp_path / "CONTEXT.md"
    original = b"---\r\ntype: workspace\r\n---\r\n\r\n# Body\r\n"
    raw = _BOM + original
    path.write_bytes(raw)
    with_bom_hash = file_references(tmp_path, ["CONTEXT.md"])

    load_frontmatter_and_body(path)

    assert path.read_bytes() == raw
    assert file_references(tmp_path, ["CONTEXT.md"]) == with_bom_hash
    path.write_bytes(original)
    assert file_references(tmp_path, ["CONTEXT.md"]) != with_bom_hash


@pytest.mark.parametrize(
    ("nfc_name", "nfd_name"),
    [
        ("caf\u00e9.md", "cafe\u0301.md"),
        ("\u00c5land.md", "A\u030aland.md"),
    ],
)
def test_file_references_keeps_nfc_and_nfd_path_names_byte_distinct(
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
        digests.append(file_references(root, [f"input/{stored_name}"]))

    assert unicodedata.normalize("NFC", stored_names[0]) == unicodedata.normalize(
        "NFC", stored_names[1]
    )
    if os.fsencode(stored_names[0]) == os.fsencode(stored_names[1]):
        pytest.skip("filesystem normalized distinct Unicode path spellings")
    assert digests[0] != digests[1]


def test_frontmatter_preserves_canonically_equivalent_scalar_bytes_and_hashes(
    tmp_path,
):
    values = ("Caf\u00e9", "Cafe\u0301")
    parsed_values = []
    digests = []
    for root_name, value in zip(("nfc", "nfd"), values):
        root = tmp_path / root_name
        root.mkdir()
        path = root / "CONTEXT.md"
        raw = f'---\nlabel: "{value}"\n---\n'.encode("utf-8")
        path.write_bytes(raw)

        metadata, _ = load_frontmatter_and_body(path)
        parsed_values.append(metadata["label"])
        digests.append(file_references(root, ["CONTEXT.md"]))
        assert path.read_bytes() == raw

    assert parsed_values == list(values)
    assert unicodedata.normalize("NFC", parsed_values[0]) == unicodedata.normalize(
        "NFC", parsed_values[1]
    )
    assert parsed_values[0] != parsed_values[1]
    assert digests[0] != digests[1]


def test_cli_validator_reports_duplicate_key_source_location(tmp_path):
    root = init_workspace(tmp_path / "workspace")
    context = root / "CONTEXT.md"
    context.write_text(
        "---\ntype: workspace\nnested:\n  route: approve\n  route: deny\n---\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    result = subprocess.run(
        [sys.executable, "-m", "impacts_protocol.cli", "validate", str(root)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 1
    assert (
        "format.invalid: CONTEXT.md: line 5, column 3: duplicate key: 'route'"
        in result.stdout
    )
    assert result.stderr == ""


# Loader backends: the C and Python safe loaders must agree on every input.
def test_default_loader_selects_fast_safe_parser_when_available():
    expected = yaml.CSafeLoader if hasattr(yaml, "CSafeLoader") else yaml.SafeLoader
    assert io._StrictLoader.__bases__ == (expected,)


@pytest.fixture(params=["python", "c"])
def strict_yaml_path(request, monkeypatch):
    if request.param == "c" and not hasattr(yaml, "CSafeLoader"):
        pytest.skip("PyYAML C extension unavailable")
    base = yaml.CSafeLoader if request.param == "c" else yaml.SafeLoader
    forced = io._strict_loader(base)
    monkeypatch.setattr(io, "_StrictLoader", forced)
    if request.param == "python":
        monkeypatch.setattr(io, "_PythonStrictLoader", forced)
    assert io._StrictLoader.__bases__ == (base,)
    return request.param


def _typed(value):
    if isinstance(value, dict):
        return (dict, tuple((key, _typed(child)) for key, child in value.items()))
    if isinstance(value, list):
        return (list, tuple(_typed(child) for child in value))
    return (type(value), value)


def test_safe_yaml_paths_preserve_scalar_types_aliases_and_body(tmp_path, strict_yaml_path):
    path = tmp_path / "CONTEXT.md"
    path.write_text(
        "---\n"
        "type: vorgang\n"
        "implicit:\n"
        "  truth: yes\n"
        "  falsehood: false\n"
        "  integer: 42\n"
        "  decimal: 3.5\n"
        "  date: 2026-09-25\n"
        "  empty: null\n"
        "nested: &nested\n"
        "  child: {name: text, count: 2}\n"
        "alias: *nested\n"
        "---\n# Body\n",
        encoding="utf-8",
    )
    metadata, body = load_frontmatter_and_body(path, tmp_path)
    reference = yaml.load(
        path.read_text().split("---")[1], Loader=io._strict_loader(yaml.SafeLoader)
    )
    assert _typed(metadata) == _typed(reference)
    assert metadata["implicit"] == {
        "truth": True,
        "falsehood": False,
        "integer": 42,
        "decimal": 3.5,
        "date": date(2026, 9, 25),
        "empty": None,
    }
    assert metadata["nested"] is metadata["alias"]
    assert body == "# Body"


@pytest.mark.parametrize("source,error", [
    ("type: a\ntype: b", DuplicateKeyError),
    ("type: a\nnested: {x: 1, x: 2}", DuplicateKeyError),
    ("type: a\nnested: {1: x}", ValueError),
    ("type: a\n<<: {x: 1}", ValueError),
    ("type: a\nnested: {<<: {x: 1}}", ValueError),
    ("type: !!python/object/apply:os.system ['true']", ValueError),
    ("type: [", ValueError),
])
def test_safe_yaml_paths_reject_bad_mappings_and_tags(
    tmp_path, strict_yaml_path, source, error
):
    path = tmp_path / "CONTEXT.md"
    path.write_text(f"---\n{source}\n---\n", encoding="utf-8")
    with pytest.raises(error) as caught:
        load_frontmatter_and_body(path, tmp_path)
    if error is DuplicateKeyError:
        assert caught.value.key in {"type", "x"}
    elif "<<:" in source or "!!python" in source or source.endswith("["):
        assert "invalid frontmatter YAML:" in str(caught.value)
    else:
        assert "frontmatter keys must be strings" in str(caught.value)


def test_frontmatter_yaml_syntax_error_uses_original_markdown_location_and_safe_fix(
    tmp_path, strict_yaml_path
):
    path = tmp_path / "CONTEXT.md"
    path.write_text(
        "---\n"
        "type: workspace\n"
        "name: Bakery: East\n"
        "---\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as caught:
        load_frontmatter_and_body(path, tmp_path)

    message = str(caught.value)
    assert message.startswith("invalid frontmatter YAML: line 3, column 13:")
    assert "mapping values are not allowed" in message
    assert "inspect indentation and YAML punctuation at this location" in message
    assert "quote ambiguous scalar text such as values containing ': '" in message
    assert "line 2, column 13" not in message


def test_standalone_yaml_syntax_error_keeps_unshifted_source_location(strict_yaml_path):
    source = "type: workspace\nname: Bakery: East\n"

    with pytest.raises(yaml.YAMLError) as caught:
        io.load_yaml_strict(source)

    message = str(caught.value)
    assert message.startswith("line 2, column 13:")
    assert "mapping values are not allowed" in message
    assert "line 3, column 13" not in message


@pytest.mark.parametrize("source,error", [
    ("outer: {x: 1, x: 2}", DuplicateKeyError),
    ("outer: {1: x}", ValueError),
    ("outer: {<<: {x: 1}}", yaml.YAMLError),
])
def test_strict_mapping_constructor_runs_on_each_backend(
    strict_yaml_path, source, error
):
    with pytest.raises(error):
        yaml.load(source, Loader=io._StrictLoader)


@pytest.mark.parametrize("tag", ["bool", "timestamp"])
def test_native_scalar_constructor_failures_are_yaml_errors_at_source_node(strict_yaml_path, tag):
    source = f"probe: !!{tag} CANARY_SCALAR\n"
    with pytest.raises(yaml.YAMLError) as caught:
        yaml.load(source, Loader=io._StrictLoader)
    assert caught.value.problem_mark.line == 0
    assert caught.value.problem_mark.column == 7
    with pytest.raises(yaml.YAMLError, match=f"line 1, column 8: invalid YAML {tag} scalar"):
        io.load_yaml_strict(source)


def test_normalized_native_scalar_neighbors_keep_safe_yaml_types(strict_yaml_path):
    from datetime import date, datetime
    source = "flag: !!bool YES\nday: !!timestamp 2040-04-07\ntime: !!timestamp 2040-04-07T09:17:32+00:00\ncount: !!int 42\namount: !!float 2.5\n"
    metadata = yaml.load(source, Loader=io._StrictLoader)
    assert metadata["flag"] is True
    assert type(metadata["day"]) is date
    assert type(metadata["time"]) is datetime
    assert metadata["count"] == 42 and type(metadata["count"]) is int
    assert metadata["amount"] == 2.5 and type(metadata["amount"]) is float
    assert io.load_yaml_strict(source) == metadata


def test_safe_yaml_paths_keep_validator_findings(tmp_path, strict_yaml_path):
    root = init_workspace(tmp_path / "kunde")
    path = root / "CONTEXT.md"
    path.write_text("---\ntype: workspace\ntype: other\n---\n", encoding="utf-8")
    report = validate(root)
    assert [(issue.code, issue.path) for issue in report.issues] == [
        ("format.invalid", "CONTEXT.md")
    ]


@pytest.mark.parametrize("source", [
    "extra: a\tb",                    # C accepts; Python rejects
    'extra: "\\uD800"',             # Python accepts; C rejects
    "extra: [a:]",                    # Python accepts; C rejects
    "extra: !",                       # both accept with different scalar values
    "extra: {a: 1?}",                 # C accepts; Python rejects
    "extra: {a: 1, b: true}",         # supported flow mapping
    "extra: &anchor [one, two]\ncopy: *anchor",
    "extra: 'quoted # text'",
    "extra: null",
    "extra: yes",
    "extra: 0x2a",
    "extra: 2026-09-25",
    "extra:\n  nested:\n    count: 3",
    "extra:\n  - one\n  - two",
    "extra: |\n  line one\n  line two",
    "extra: {a: 1, a: 2}",           # nested duplicate
    "extra: {1: value}",             # non-string key
    "extra: {<<: {a: 1}}",           # merge key rejected
    "extra: !!python/object/apply:os.system ['true']",
    "extra: [",
])
def test_loader_matches_python_contract_in_full_validate(tmp_path, source, monkeypatch):
    root = init_workspace(tmp_path / "kunde")
    (root / "CONTEXT.md").write_text(
        f"---\ntype: workspace\n{source}\n---\n", encoding="utf-8"
    )
    monkeypatch.setattr(io, "_StrictLoader", io._PythonStrictLoader)
    try:
        expected_metadata, expected_body = load_frontmatter_and_body(root / "CONTEXT.md", root)
    except ValueError as error:
        expected_error = (type(error), str(error))
    else:
        expected_error = None
    expected = validate(root)
    if not hasattr(yaml, "CSafeLoader"):
        pytest.skip("PyYAML C extension unavailable")
    monkeypatch.setattr(io, "_StrictLoader", io._strict_loader(yaml.CSafeLoader))
    if expected_error is None:
        metadata, body = load_frontmatter_and_body(root / "CONTEXT.md", root)
        assert _typed(metadata) == _typed(expected_metadata)
        assert body == expected_body
    else:
        with pytest.raises(expected_error[0]) as caught:
            load_frontmatter_and_body(root / "CONTEXT.md", root)
        assert str(caught.value) == expected_error[1]
    assert validate(root) == expected


def test_plain_block_fast_path_matches_python_on_seeded_corpus():
    if not hasattr(yaml, "CSafeLoader"):
        pytest.skip("PyYAML C extension unavailable")
    rng = random.Random(52)
    alphabet = "ab01: ,\n-./()_é"
    seeds = (
        "type: workspace",
        "root: a",
        "root:\n  a: 1",
        "root:\n  - a",
        "- a\n- b",
    )
    c_loader = io._strict_loader(yaml.CSafeLoader)

    def outcome(source, loader):
        try:
            return ("value", _typed(yaml.load(source, Loader=loader)))
        except DuplicateKeyError as error:
            return ("duplicate", error.key)
        except ValueError as error:
            return ("value_error", str(error))
        except yaml.YAMLError:
            return ("yaml_error",)

    for seed in seeds:
        for _ in range(120):
            source = seed
            for _ in range(rng.randint(1, 4)):
                position = rng.randrange(len(source) + 1)
                replacement = rng.choice(alphabet)
                delete = int(rng.random() < 0.4)
                source = source[:position] + replacement + source[position + delete:]
            assert outcome(source, c_loader) == outcome(source, io._PythonStrictLoader), source


def test_python_fallback_imports_without_c_extension(tmp_path):
    path = tmp_path / "CONTEXT.md"
    path.write_text("---\ntype: workspace\n---\n", encoding="utf-8")
    program = (
        "import sys, yaml; "
        "yaml.__dict__.pop('CSafeLoader', None); "
        "sys.path.insert(0, sys.argv[1]); "
        "from impacts_protocol import io; "
        "assert io._StrictLoader.__bases__ == (yaml.SafeLoader,); "
        "assert io.load_frontmatter(sys.argv[2]) == {'type': 'workspace'}"
    )
    check = subprocess.run(
        [sys.executable, "-c", program, str(ROOT / "src"), str(path)],
        capture_output=True, text=True,
    )
    assert check.returncode == 0, check.stderr


def test_c_rejection_retries_python_for_plain_frontmatter(tmp_path, monkeypatch):
    if not hasattr(yaml, "CSafeLoader"):
        pytest.skip("PyYAML C extension unavailable")
    path = tmp_path / "CONTEXT.md"
    path.write_text("---\ntype: workspace\n---\n", encoding="utf-8")
    original_load = yaml.load
    calls = []

    def reject_c(source, Loader):
        calls.append(Loader)
        if Loader is io._StrictLoader:
            raise yaml.YAMLError("C parser rejected fixture")
        return original_load(source, Loader=Loader)

    monkeypatch.setattr(io.yaml, "load", reject_c)
    assert load_frontmatter_and_body(path, tmp_path) == ({"type": "workspace"}, "")
    assert calls == [io._StrictLoader, io._PythonStrictLoader]


@pytest.mark.parametrize("text", [
    "---\ntype: [\n---\n",                      # malformed YAML
    "---\ntype: vorgang\n",                     # no closing delimiter
    "---\n- a\n- b\n---\n",                     # frontmatter not a mapping
    "---\n1: x\n---\n",                         # non-string key
    "---\ntype: vorgang\n<<:\n  id: vorgang:x\n---\n",  # YAML merge key
])
def test_frontmatter_malformed_partitions_fail_closed(tmp_path, text):
    path = tmp_path / "CONTEXT.md"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        load_frontmatter_and_body(path, tmp_path)


def test_non_utf8_context_fails_closed(tmp_path):
    path = tmp_path / "CONTEXT.md"
    path.write_bytes(b"---\ntype: vorgang\n---\n\nK\xf6rper\n")
    with pytest.raises(ValueError):
        load_frontmatter_and_body(path, tmp_path)


def test_block_scalar_with_bare_dashes_line_is_silently_truncated(tmp_path):
    """B-4 characterization: the line-based splitter closes frontmatter early.

    The truncation can only drop schema fields (fail closed) or shorten a
    free-text value without machine notice. This test pins the current
    behavior so any repair must update it deliberately.
    """
    path = tmp_path / "CONTEXT.md"
    path.write_text(
        "---\ntype: vorgang\nnote: >\n  line one\n---\n  line two\n---\n",
        encoding="utf-8",
    )
    metadata, body = load_frontmatter_and_body(path, tmp_path)
    assert metadata == {"type": "vorgang", "note": "line one"}
    assert "line two" in body
