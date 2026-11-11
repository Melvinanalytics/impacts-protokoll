"""Per-file SHA-256 references.

The byte-digest and failure rules live at
02_protocol/binding.md#snapshot-and-provenance.
This content identity does not establish permission.
"""

import hashlib
from pathlib import Path
from typing import Sequence


class HashSurfaceError(ValueError):
    """A declared hash surface cannot be bound."""

    def __init__(self, code: str, path: Path, message: str):
        self.code = code
        self.path = Path(path)
        self.message = message
        super().__init__(f"{code}: {path}: {message}")


def file_references(attempt_root: Path, declared: Sequence[str]) -> list[dict[str, str]]:
    """List file references inside a caller-stabilized root.

    The caller must keep file bytes and directory entries stable through enumeration
    and reading. Static symlink checks do not synchronize concurrent replacement.
    """
    attempt_root = Path(attempt_root)
    if not isinstance(declared, Sequence) or isinstance(declared, (str, bytes)) or not declared:
        raise HashSurfaceError("binding.reference_missing", attempt_root, "Declare at least one reference")
    files: dict[str, str] = {}
    for relative in declared:
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise HashSurfaceError("binding.reference_missing", attempt_root, "Hash surface must be a nonempty relative path")
        source = attempt_root / relative
        try:
            for path in _candidates(source, attempt_root):
                normalized = path.resolve().relative_to(attempt_root.resolve()).as_posix()
                try:
                    normalized.encode("utf-8")
                except UnicodeEncodeError as error:
                    raise HashSurfaceError(
                        "binding.reference_missing",
                        attempt_root,
                        f"Hash surface path is not valid UTF-8: {normalized!r}",
                    ) from error
                with path.open("rb") as content:
                    files[normalized] = hashlib.file_digest(content, "sha256").hexdigest()
        except HashSurfaceError:
            raise
        except (OSError, ValueError, RuntimeError) as error:
            raise HashSurfaceError("binding.reference_missing", source, f"Hash surface cannot be read: {error}") from error
    return [
        {"pfad": path, "sha256": "sha256:" + digest}
        for path, digest in sorted(files.items(), key=lambda item: item[0].encode("utf-8"))
    ]


def _candidates(source: Path, attempt_root: Path) -> list[Path]:
    if _has_symlink_component(source, attempt_root):
        raise HashSurfaceError("structure.symlink", source, _symlink_message())
    try:
        source.resolve().relative_to(attempt_root.resolve())
    except (OSError, ValueError) as error:
        raise HashSurfaceError("binding.reference_missing", source, "Hash surface escapes attempt directory") from error
    if source.is_file():
        return [source]
    if not source.is_dir():
        raise HashSurfaceError("binding.reference_missing", source, "Declared reference has no regular file")

    files: list[Path] = []
    pending = [source]
    while pending:
        directory = pending.pop()
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if path.is_symlink():
                raise HashSurfaceError("structure.symlink", path, _symlink_message())
            if path.is_dir():
                pending.append(path)
            elif path.is_file():
                files.append(path)
            else:
                raise HashSurfaceError("binding.reference_missing", path, "Hash surface contains a non-regular entry")
    if not files:
        raise HashSurfaceError("binding.reference_missing", source, "Declared reference has no regular file")
    return sorted(files)


def _symlink_message() -> str:
    return (
        "Hash surface contains a symlink. To proceed, materialize approved regular-file bytes before binding "
        "and record provenance separately. If the input is already bound or completed, preserve it "
        "and use the permitted new attempt/revision path rather than rewriting evidence."
    )


def _has_symlink_component(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    current = root
    if current.is_symlink():
        return True
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def file_sha256(path: Path) -> str:
    """Digest raw bytes of one file. Caller enforces its read boundary."""
    with path.open("rb") as content:
        return "sha256:" + hashlib.file_digest(content, "sha256").hexdigest()
