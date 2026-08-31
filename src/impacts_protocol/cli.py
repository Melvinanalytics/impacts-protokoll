"""Command-line interface for IMPACTS workspaces."""

import argparse
from pathlib import Path
import sys

from .generator import init_workspace
from .validator import validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="impacts")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Arbeitsbereich erzeugen")
    init_parser.add_argument("path")

    validate_parser = subparsers.add_parser("validate", help="Arbeitsbereich prüfen")
    validate_parser.add_argument("path")
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
    report = validate(Path(args.path))
    for issue in report.issues:
        print(f"{issue.code}: {issue.path}: {issue.message}")
    return 0 if report.valid else 1
