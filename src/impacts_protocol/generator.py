"""Stamp a contract-only IMPACTS customer workspace."""

from pathlib import Path
import shutil
from tempfile import mkdtemp

from .workspace_contract import WORKSPACE_FOLDERS


def init_workspace(target: Path) -> Path:
    """Create an empty, valid, file-native workspace template."""
    target = Path(target)
    if target.exists() or target.is_symlink():
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(mkdtemp(prefix=f".{target.name}.", dir=target.parent))
    try:
        _write_workspace(staging)
        if target.exists() or target.is_symlink():
            raise FileExistsError(target)
        staging.rename(target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return target


def _write_workspace(target: Path) -> None:
    for folder in WORKSPACE_FOLDERS:
        (target / folder).mkdir()

    (target / "CONTEXT.md").write_text(
        "---\n"
        "type: workspace\n"
        "---\n\n"
        "# IMPACTS Workspace\n\n"
        "Applications definieren wiederverwendbare Prozesse. "
        "Vorgänge halten konkrete Durchläufe.\n",
        encoding="utf-8",
    )
