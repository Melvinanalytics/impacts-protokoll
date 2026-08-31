#!/usr/bin/env python3
"""Check the contract-only workspace template without executing work."""

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from impacts_protocol import init_workspace, validate
from impacts_protocol.workspace_contract import (
    WORKSPACE_FOLDERS,
    WORKSPACE_TEMPLATE_FILES,
)


@dataclass(frozen=True)
class WalkResult:
    folders: tuple[str, ...]
    files: tuple[str, ...]
    issues: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.issues


def inspect_workspace(root: Path) -> WalkResult:
    """Inspect only the generated folder and contract surfaces."""
    root = Path(root)
    issues = [
        f"{issue.code}: {issue.path}: {issue.message}"
        for issue in validate(root).issues
    ]
    folders = tuple(sorted(path.name for path in root.iterdir() if path.is_dir()))
    expected_folders = tuple(sorted(WORKSPACE_FOLDERS))
    if folders != expected_folders:
        issues.append(
            f"template.folders: expected {expected_folders!r}, found {folders!r}"
        )
    files = tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        )
    )
    expected_files = WORKSPACE_TEMPLATE_FILES
    if files != expected_files:
        issues.append(
            f"template.files: expected {expected_files!r}, found {files!r}"
        )
    return WalkResult(folders, files, tuple(dict.fromkeys(issues)))


def main() -> int:
    """Generate, inspect, and report one disposable template."""
    with TemporaryDirectory(prefix="impacts-cold-walk-") as directory:
        root = init_workspace(Path(directory) / "workspace")
        result = inspect_workspace(root)
        for folder in result.folders:
            print(f"FOLDER {folder}")
        for path in result.files:
            print(f"FILE {path}")
        if result.valid:
            print("PASS contract-only workspace")
            return 0
        for issue in result.issues:
            print(f"FAIL {issue}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
