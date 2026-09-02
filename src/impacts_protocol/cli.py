"""Command-line interface for IMPACTS workspaces."""

import argparse
from pathlib import Path
import sys

from .generator import TEMPLATE_KINDS, init_workspace, template_text
from .hashing import HashSurfaceError, surface_hash
from .validator import validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="impacts")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Arbeitsbereich erzeugen")
    init_parser.add_argument("path")

    validate_parser = subparsers.add_parser("validate", help="Arbeitsbereich prüfen")
    validate_parser.add_argument("path")

    hash_parser = subparsers.add_parser("hash", help="Flächenhash eines Versuchs berechnen")
    hash_parser.add_argument("attempt", help="Versuchsordner")
    hash_parser.add_argument("surface", nargs="+", help="deklarierte Fläche relativ zum Versuch")

    template_parser = subparsers.add_parser("template", help="CONTEXT.md-Vorlage ausgeben")
    template_parser.add_argument("kind", choices=TEMPLATE_KINDS)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "init":
        try:
            init_workspace(Path(args.path))
        except FileExistsError:
            print(f"Workspace target exists: {args.path}", file=sys.stderr)
            return 1
        return 0
    if args.command == "template":
        print(template_text(args.kind), end="")
        return 0
    if args.command == "hash":
        try:
            print(surface_hash(Path(args.attempt), args.surface))
        except HashSurfaceError as error:
            print(error, file=sys.stderr)
            return 1
        return 0
    report = validate(Path(args.path))
    for issue in report.issues:
        print(f"{issue.code}: {issue.path}: {issue.message}")
    return 0 if report.valid else 1
