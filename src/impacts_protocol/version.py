"""Package edition and protocol release identity, from package metadata or source."""

from pathlib import Path
import re

PROTOCOL_PATTERN = r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"


def package_metadata(source_file: str = __file__) -> dict[str, str | None]:
    from importlib import metadata as importlib_metadata

    try:
        distribution = importlib_metadata.distribution("impacts-protocol")
    except importlib_metadata.PackageNotFoundError:
        source_pyproject = Path(source_file).resolve().parents[2] / "pyproject.toml"
        try:
            import tomllib

            project = tomllib.loads(source_pyproject.read_text(encoding="utf-8"))["project"]
            name = project["name"]
            version = project["version"]
        except (OSError, KeyError, TypeError, ValueError):
            return {
                "name": "impacts-protocol",
                "version": None,
                "version_source": "metadata unavailable",
            }
        return {
            "name": name,
            "version": version if isinstance(version, str) and version else None,
            "version_source": "source pyproject.toml; source revision unknown",
        }

    name = distribution.metadata.get("Name") or "impacts-protocol"
    version = distribution.version
    return {
        "name": name,
        "version": version if isinstance(version, str) and version else None,
        "version_source": "installed distribution metadata",
    }


def protocol_release() -> str:
    version = package_metadata()["version"]
    release = f"v{version}"
    if re.fullmatch(PROTOCOL_PATTERN, release) is None:
        raise ValueError(f"Package version must be MAJOR.MINOR.PATCH: {version!r}")
    return release


def protocol_line(value: object) -> tuple[str, str] | None:
    match = re.fullmatch(PROTOCOL_PATTERN, value) if isinstance(value, str) else None
    return (match[1], match[2]) if match else None
