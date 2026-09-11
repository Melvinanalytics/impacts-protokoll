"""Stamp a contract-only IMPACTS customer workspace and serve context templates."""

from importlib import resources
from pathlib import Path
import shutil
from tempfile import mkdtemp

from .workspace_contract import WORKSPACE_FOLDERS

TEMPLATE_KINDS = ("application", "hauptprozess", "teilprozess", "arbeitsschritt", "vorgang")


def init_workspace(target: Path, *, language: str = "en") -> Path:
    """Create an empty, valid, file-native workspace template."""
    _check_language(language)
    target = Path(target)
    if target.exists() or target.is_symlink():
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(mkdtemp(prefix=f".{target.name}.", dir=target.parent))
    try:
        _write_workspace(staging, language)
        if target.exists() or target.is_symlink():
            raise FileExistsError(target)
        staging.rename(target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return target


LANGUAGES = ("en", "de")


def _check_language(language: str) -> None:
    if language not in LANGUAGES:
        raise ValueError(f"unsupported working language: {language}")


def _template_file(kind: str, language: str) -> str:
    _check_language(language)
    relative = f"de/{kind}.md" if language == "de" else f"{kind}.md"
    try:
        return resources.files("impacts_protocol.templates").joinpath(relative).read_text(encoding="utf-8")
    except ModuleNotFoundError:
        return (Path(__file__).resolve().parents[2] / "02_protocol/templates" / relative).read_text(encoding="utf-8")


def template_text(kind: str, *, language: str = "en") -> str:
    """Return a localized template; machine contracts are unchanged."""
    if kind not in TEMPLATE_KINDS:
        raise ValueError(f"unknown template kind: {kind}")
    return _template_file(kind, language)


def _write_workspace(target: Path, language: str) -> None:
    for folder in WORKSPACE_FOLDERS:
        (target / folder).mkdir()

    (target / "CONTEXT.md").write_text(
        _template_file("workspace", language),
        encoding="utf-8",
    )
