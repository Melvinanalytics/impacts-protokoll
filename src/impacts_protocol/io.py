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


class _StrictLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _StrictLoader, node: MappingNode, deep: bool = False
) -> dict[Any, Any]:
    seen = []
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise DuplicateKeyError(key)
        seen.append(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_StrictLoader.add_constructor(
    YAML_MAPPING_TAG,
    _construct_unique_mapping,
)


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
        value = yaml.load(
            "\n".join(lines[1:closing_index]),
            Loader=_StrictLoader,
        )
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
    return resolved.read_text(encoding="utf-8")
