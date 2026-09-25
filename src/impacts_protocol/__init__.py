"""File-native IMPACTS workspace protocol."""

from .generator import init_workspace
from .hashing import HashSurfaceError, surface_hash
from .model import Issue, ValidationReport


def __getattr__(name: str):
    if name != "validate":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .validator import validate

    globals()[name] = validate
    return validate

__all__ = [
    "HashSurfaceError",
    "Issue",
    "ValidationReport",
    "init_workspace",
    "surface_hash",
    "validate",
]
