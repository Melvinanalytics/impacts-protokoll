"""Readers for file-native protocol documents."""

from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode


YAML_MAPPING_TAG = "tag:yaml.org,2002:map"


class DuplicateKeyError(ValueError):
    """A YAML mapping declares the same key more than once."""

    def __init__(self, key: Any):
        self.key = key
        super().__init__(f"duplicate key: {key!r}")


class PathEscapeError(ValueError):
    """A source path resolves outside its declared workspace root."""


def _strict_loader(base_loader: type) -> type:
    """Give either safe parser its own strict mapping constructor."""

    class StrictLoader(base_loader):
        pass

    def construct_unique_mapping(
        loader: StrictLoader, node: MappingNode, deep: bool = False
    ) -> dict[Any, Any]:
        seen: set[str] = set()
        for key_node, _ in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ValueError("frontmatter keys must be strings")
            if key in seen:
                raise DuplicateKeyError(key)
            seen.add(key)
        return base_loader.construct_mapping(loader, node, deep=deep)

    StrictLoader.add_constructor(YAML_MAPPING_TAG, construct_unique_mapping)
    return StrictLoader


_PythonStrictLoader = _strict_loader(yaml.SafeLoader)
_C_SAFE_LOADER = getattr(yaml, "CSafeLoader", None)
_StrictLoader = _strict_loader(_C_SAFE_LOADER) if _C_SAFE_LOADER else _PythonStrictLoader


def load_yaml_strict(source: str) -> Any:
    """Load safe YAML while rejecting duplicate mapping keys."""

    # LibYAML and PyYAML's Python parser disagree on some valid and invalid
    # syntax. Keep the Python parser for those syntax families; use C for the
    # common plain block form, retrying Python if C alone rejects it.
    if _C_SAFE_LOADER is None or not issubclass(_StrictLoader, _C_SAFE_LOADER):
        return yaml.load(source, Loader=_PythonStrictLoader)
    sensitive = "![]{}&*?|>\\'\"%@`#"
    if any(char in source for char in sensitive) or not source.replace("\n", "").isprintable():
        return yaml.load(source, Loader=_PythonStrictLoader)
    try:
        return yaml.load(source, Loader=_StrictLoader)
    except DuplicateKeyError:
        raise
    except (yaml.YAMLError, ValueError):
        return yaml.load(source, Loader=_PythonStrictLoader)


def load_frontmatter(path: Path, root: Path | None = None) -> dict[str, Any]:
    """Load YAML frontmatter, returning an empty object when none is present."""
    metadata, _ = load_frontmatter_and_body(path, root)
    return metadata


def load_frontmatter_and_body(
    path: Path, root: Path | None = None
) -> tuple[dict[str, Any], str]:
    """Load YAML frontmatter and the Markdown body from one context file."""
    try:
        text = _read_text(path, root)
    except (OSError, UnicodeError) as error:
        raise ValueError(f"invalid Markdown: {error}") from error
    if text.startswith("\ufeff"):
        raise ValueError(
            "line 1: repeated UTF-8 BOM; remove extra leading BOMs (at most one is allowed)"
        )
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        closing_index = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration as error:
        raise ValueError("frontmatter has no closing delimiter") from error
    try:
        value = load_yaml_strict("\n".join(lines[1:closing_index]))
    except DuplicateKeyError:
        raise
    except yaml.YAMLError as error:
        raise ValueError(f"invalid frontmatter YAML: {error}") from error
    if value is None:
        return {}, "\n".join(lines[closing_index + 1 :])
    if not isinstance(value, dict):
        raise ValueError("frontmatter must be an object")
    return value, "\n".join(lines[closing_index + 1 :])


def _read_text(path: Path, root: Path | None) -> str:
    path = Path(path)
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError) as error:
        raise ValueError(f"cannot resolve source path: {error}") from error
    if root is not None and not resolved.is_relative_to(Path(root).resolve()):
        raise PathEscapeError("source path resolves outside workspace root")
    return resolved.read_text(encoding="utf-8-sig")
