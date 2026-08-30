"""Immutable validator result types."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[Issue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues
