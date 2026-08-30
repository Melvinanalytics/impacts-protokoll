"""Stamp a contract-only IMPACTS customer workspace."""

from pathlib import Path
import shutil
from tempfile import mkdtemp

import yaml

from .validator import validate_workspace
from .workspace_contract import WORKSPACE_FOLDERS


def generate_workspace(target: Path, customer_id: str) -> Path:
    """Create an empty, valid, file-native workspace template."""
    target = Path(target)
    if not isinstance(customer_id, str) or not customer_id.strip():
        raise ValueError("customer_id must be non-empty")
    if target.exists() or target.is_symlink():
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(mkdtemp(prefix=f".{target.name}.", dir=target.parent))
    try:
        _write_workspace(staging, customer_id.strip())
        _validate_generated_workspace(staging)
        if target.exists() or target.is_symlink():
            raise FileExistsError(target)
        staging.rename(target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return target


def _write_workspace(target: Path, customer_id: str) -> None:
    for folder in WORKSPACE_FOLDERS:
        (target / folder).mkdir()

    (target / "CONTEXT.md").write_text(
        "---\n"
        "title: IMPACTS Workspace\n"
        "type: workspace\n"
        "evidence_status: reported\n"
        "---\n\n"
        "# IMPACTS Workspace\n\n"
        "Ordner und Referenzen bilden den lesbaren Arbeitskontext. "
        "Aktivierte Pakete stehen in `00_steuerung/paketaktivierungen.yaml`. "
        "Kundeneigene Grundlagen liegen in `02_grundlagen/`, Records in "
        "`03_records/` und konkrete Vorgänge in `06_vorgaenge/`.\n",
        encoding="utf-8",
    )
    _write_yaml(
        target / "00_steuerung/paketaktivierungen.yaml",
        {"customer_id": customer_id, "packages": []},
    )
    _write_yaml(
        target / "02_grundlagen/datenautoritaet.yaml",
        {
            "records": {
                "default": {
                    "writes": "customer",
                    "kind": "file",
                    "path": "03_records",
                }
            }
        },
    )


def _write_yaml(path: Path, content: dict) -> None:
    path.write_text(
        yaml.safe_dump(content, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _validate_generated_workspace(target: Path) -> None:
    report = validate_workspace(target)
    if report.valid:
        return
    details = "; ".join(
        f"{issue.code}: {issue.path}: {issue.message}" for issue in report.issues
    )
    raise ValueError(f"generated workspace failed validation: {details}")
