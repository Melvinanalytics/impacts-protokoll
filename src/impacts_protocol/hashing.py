"""The one surface hash of the protocol (design section 7)."""

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
    files: dict[str, str] = {}
    for relative in declared:
        for path in _candidates(attempt_root / relative, attempt_root):
            try:
                normalized = path.resolve().relative_to(attempt_root.resolve()).as_posix()
            except (OSError, ValueError) as error:
                raise HashSurfaceError("hash.mismatch", path, "Hash surface escapes attempt directory") from error
            files[normalized] = hashlib.sha256(path.read_bytes()).hexdigest()
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
