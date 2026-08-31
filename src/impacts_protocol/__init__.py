"""File-native IMPACTS workspace protocol."""

from .generator import init_workspace
from .model import Issue, ValidationReport
from .validator import validate

__all__ = [
    "Issue",
    "ValidationReport",
    "init_workspace",
    "validate",
]
