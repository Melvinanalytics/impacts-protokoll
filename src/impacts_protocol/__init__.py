"""File-native IMPACTS workspace protocol."""

from .model import Issue, ValidationReport
from .validator import validate_application, validate_workspace

__all__ = [
    "Issue",
    "ValidationReport",
    "validate_application",
    "validate_workspace",
]
