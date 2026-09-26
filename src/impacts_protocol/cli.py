"""Command-line interface for IMPACTS workspaces."""

import argparse
import json
from pathlib import Path
import sys
import shlex

from .generator import LANGUAGES, TEMPLATE_KINDS, init_workspace, template_text
from .hashing import HashSurfaceError, surface_hash


def _package_metadata() -> dict[str, str | None]:
    from importlib import metadata as importlib_metadata

    try:
        distribution = importlib_metadata.distribution("impacts-protocol")
    except importlib_metadata.PackageNotFoundError:
        source_pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
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


def _package_metadata_identity(metadata: dict[str, str | None] | None = None) -> str:
    metadata = metadata or _package_metadata()
    name = metadata["name"] or "impacts-protocol"
    version = metadata["version"]
    version_source = metadata["version_source"] or "metadata unavailable"
    if version is None:
        return f"{name} version unknown ({version_source})"
    return f"{name} {version} ({version_source})"


def _print_json_report(report: dict) -> None:
    print(json.dumps(report, ensure_ascii=True, allow_nan=False))


def _issue_json(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


class _PrintPackageMetadataAction(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        kwargs.setdefault("help", "show package metadata identity and exit")
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        print(_package_metadata_identity())
        parser.exit()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="impacts")
    parser.add_argument("--version", action=_PrintPackageMetadataAction)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a workspace")
    init_parser.add_argument("path")
    init_parser.add_argument("--language", choices=LANGUAGES, default="en", help="Customer working language (default: en)")

    validate_parser = subparsers.add_parser("validate", help="Validate a workspace")
    validate_parser.add_argument("path")
    validate_parser.add_argument("--verbose", action="store_true", help="Report package identity")
    validate_parser.add_argument("--json", action="store_true", help="Print a JSON report")

    hash_parser = subparsers.add_parser("hash", help="Hash declared attempt surfaces")
    hash_parser.add_argument("attempt", help="Attempt folder")
    hash_parser.add_argument("surface", nargs="+", help="Declared surface relative to the attempt")
    hash_parser.add_argument("--json", action="store_true", help="Print a JSON report")

    template_parser = subparsers.add_parser("template", help="Print a working template")
    template_parser.add_argument("kind", choices=TEMPLATE_KINDS)
    template_parser.add_argument("--language", choices=LANGUAGES, default="en", help="Customer working language (default: en)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "init":
        try:
            init_workspace(Path(args.path), language=args.language)
        except FileExistsError:
            print(f"Workspace target exists: {args.path}", file=sys.stderr)
            return 1
        target = Path(args.path)
        if args.language == "de":
            print(f"Arbeitsbereich angelegt. Nächster Schritt: {target / 'CONTEXT.md'} lesen und prüfen:")
        else:
            print(f"Workspace created. Next: read {target / 'CONTEXT.md'} and validate:")
        print(f"impacts validate {shlex.quote(str(target))}")
        return 0
    if args.command == "template":
        print(template_text(args.kind, language=args.language), end="")
        return 0
    if args.command == "hash":
        if args.json:
            tool = _package_metadata()
            try:
                digest = surface_hash(Path(args.attempt), args.surface)
            except HashSurfaceError as error:
                _print_json_report(
                    {
                        "report_version": 1,
                        "command": "hash",
                        "tool": tool,
                        "issues": [_issue_json(error.code, str(error.path), error.message)],
                        "digest": None,
                        "attempt": args.attempt,
                        "surfaces": args.surface,
                    }
                )
                return 1
            _print_json_report(
                {
                    "report_version": 1,
                    "command": "hash",
                    "tool": tool,
                    "issues": [],
                    "digest": digest,
                    "attempt": args.attempt,
                    "surfaces": args.surface,
                }
            )
            return 0
        try:
            print(surface_hash(Path(args.attempt), args.surface))
        except HashSurfaceError as error:
            print(error, file=sys.stderr)
            return 1
        return 0
    tool = _package_metadata() if args.verbose or args.json else None
    if args.verbose:
        print(
            f"Package metadata identity: {_package_metadata_identity(tool)}",
            file=sys.stderr,
        )
    from .validator import validate

    report = validate(Path(args.path))
    if args.json:
        _print_json_report(
            {
                "report_version": 1,
                "command": "validate",
                "tool": tool,
                "issues": [
                    _issue_json(issue.code, issue.path, issue.message)
                    for issue in report.issues
                ],
                "valid": report.valid,
                "root": args.path,
            }
        )
        return 0 if report.valid else 1
    for issue in report.issues:
        print(f"{issue.code}: {issue.path}: {issue.message}")
    return 0 if report.valid else 1


if __name__ == "__main__":
    sys.exit(main())
