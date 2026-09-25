"""Canonical attempt-surface hashing.

Hash each regular file's raw bytes with SHA-256. Sort by the UTF-8 bytes of its
attempt-relative POSIX path. Encode the list of {"path", "sha256"} records as
UTF-8 JSON with ensure_ascii=False, sorted keys and separators=(",", ":"), then
append one LF. SHA-256 that payload and prefix its lowercase hex with "sha256:".
Overlapping declarations include each path once. A symlinked surface fails as
``structure.symlink``. Every other unbindable surface (missing, empty, escaping,
unreadable, non-UTF-8 or non-regular) fails as ``hash.mismatch``, as does a
differing digest. This content identity does not establish permission.
"""

import hashlib
import json
from pathlib import Path
from typing import Sequence


class HashSurfaceError(ValueError):
    """A declared hash surface cannot be bound."""

    def __init__(self, code: str, path: Path, message: str):
        self.code = code
        self.path = Path(path)
        self.message = message
        super().__init__(f"{code}: {path}: {message}")


def surface_hash(attempt_root: Path, declared: Sequence[str]) -> str:
    """Bind every regular file under the declared surfaces of one attempt."""
    attempt_root = Path(attempt_root)
    if not isinstance(declared, Sequence) or isinstance(declared, (str, bytes)) or not declared:
        raise HashSurfaceError("hash.mismatch", attempt_root, "Declare at least one hash surface")
    files: dict[str, str] = {}
    for relative in declared:
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise HashSurfaceError("hash.mismatch", attempt_root, "Hash surface must be a nonempty relative path")
        source = attempt_root / relative
        try:
            for path in _candidates(source, attempt_root):
                normalized = path.resolve().relative_to(attempt_root.resolve()).as_posix()
                try:
                    normalized.encode("utf-8")
                except UnicodeEncodeError as error:
                    raise HashSurfaceError(
                        "hash.mismatch",
                        attempt_root,
                        f"Hash surface path is not valid UTF-8: {normalized!r}",
                    ) from error
                with path.open("rb") as content:
                    files[normalized] = hashlib.file_digest(content, "sha256").hexdigest()
        except HashSurfaceError:
            raise
        except (OSError, ValueError, RuntimeError) as error:
            raise HashSurfaceError("hash.mismatch", source, f"Hash surface cannot be read: {error}") from error
    entries = [
        {"path": path, "sha256": digest}
        for path, digest in sorted(files.items(), key=lambda item: item[0].encode("utf-8"))
    ]
    payload = (
        json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _candidates(source: Path, attempt_root: Path) -> list[Path]:
    if _has_symlink_component(source, attempt_root):
        raise HashSurfaceError("structure.symlink", source, "Hash surface contains a symlink")
    try:
        source.resolve().relative_to(attempt_root.resolve())
    except (OSError, ValueError) as error:
        raise HashSurfaceError("hash.mismatch", source, "Hash surface escapes attempt directory") from error
    if source.is_file():
        return [source]
    if not source.is_dir():
        raise HashSurfaceError("hash.mismatch", source, "Declared hash surface has no regular file")

    files: list[Path] = []
    pending = [source]
    while pending:
        directory = pending.pop()
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if path.is_symlink():
                raise HashSurfaceError("structure.symlink", path, "Hash surface contains a symlink")
            if path.is_dir():
                pending.append(path)
            elif path.is_file():
                files.append(path)
            else:
                raise HashSurfaceError("hash.mismatch", path, "Hash surface contains a non-regular entry")
    if not files:
        raise HashSurfaceError("hash.mismatch", source, "Declared hash surface has no regular file")
    return sorted(files)


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
