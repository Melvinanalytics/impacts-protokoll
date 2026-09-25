"""Command-line interface for IMPACTS workspaces."""

import argparse
from pathlib import Path
import sys
import shlex

from .generator import LANGUAGES, TEMPLATE_KINDS, init_workspace, template_text
from .hashing import HashSurfaceError, surface_hash


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="impacts")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a workspace")
    init_parser.add_argument("path")
    init_parser.add_argument("--language", choices=LANGUAGES, default="en", help="Customer working language (default: en)")

    validate_parser = subparsers.add_parser("validate", help="Validate a workspace")
    validate_parser.add_argument("path")

    hash_parser = subparsers.add_parser("hash", help="Hash declared attempt surfaces")
    hash_parser.add_argument("attempt", help="Attempt folder")
    hash_parser.add_argument("surface", nargs="+", help="Declared surface relative to the attempt")

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
        try:
            print(surface_hash(Path(args.attempt), args.surface))
        except HashSurfaceError as error:
            print(error, file=sys.stderr)
            return 1
        return 0
    from .validator import validate

    report = validate(Path(args.path))
    for issue in report.issues:
        print(f"{issue.code}: {issue.path}: {issue.message}")
    return 0 if report.valid else 1


if __name__ == "__main__":
    sys.exit(main())
