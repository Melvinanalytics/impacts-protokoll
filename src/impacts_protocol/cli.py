"""Command-line interface for IMPACTS workspaces."""

import argparse
from pathlib import Path
import sys

from .generator import generate_workspace
from .validator import validate_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="impacts")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Arbeitsbereich erzeugen")
    init_parser.add_argument("path")
    init_parser.add_argument("--customer", required=True)

    validate_parser = subparsers.add_parser("validate", help="Arbeitsbereich prüfen")
    validate_parser.add_argument("path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "init":
        try:
            generate_workspace(Path(args.path), args.customer)
        except FileExistsError:
            print(f"Workspace target exists: {args.path}", file=sys.stderr)
            return 1
        return 0
    report = validate_workspace(Path(args.path))
    for issue in report.issues:
        print(f"{issue.code}: {issue.path}: {issue.message}")
    return 0 if report.valid else 1
