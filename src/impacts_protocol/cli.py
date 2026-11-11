"""Command-line interface for IMPACTS workspaces."""

import argparse
import json
from pathlib import Path
import sys
import shlex

from .generator import CLI_TEMPLATE_KINDS, LANGUAGES, init_workspace, template_text
from .hashing import HashSurfaceError, file_references
from .model import issue_rule
from .version import package_metadata


def _package_metadata() -> dict[str, str | None]:
    return package_metadata(__file__)

def _package_metadata_identity() -> str:
    metadata = _package_metadata()
    name = metadata["name"] or "impacts-protocol"
    version = metadata["version"]
    version_source = metadata["version_source"] or "metadata unavailable"
    if version is None:
        return f"{name} version unknown ({version_source})"
    return f"{name} {version} ({version_source})"


def _print_json_report(report: dict) -> None:
    print(json.dumps(report, ensure_ascii=True, allow_nan=False))


def _issue_json(code: str, path: str, message: str, rule: str = "") -> dict[str, str]:
    return {"code": code, "path": path, "message": message, "rule": rule or issue_rule(code)}


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
    validate_parser.add_argument("--json", action="store_true", help="Print a JSON report")

    hash_parser = subparsers.add_parser("hash", help="List per-file SHA-256 references")
    hash_parser.add_argument("attempt", help="Reference root")
    hash_parser.add_argument("surface", nargs="+", help="File or directory relative to the root")
    hash_parser.add_argument("--json", action="store_true", help="Print a JSON report")

    template_parser = subparsers.add_parser("template", help="Print a working template")
    template_parser.add_argument("kind", choices=CLI_TEMPLATE_KINDS)
    template_parser.add_argument("--language", choices=LANGUAGES, default="en", help="Customer working language (default: en)")

    view_parser = subparsers.add_parser("view", help="Write a read-only HTML view of a workspace, Hauptprozess or Vorgang")
    view_parser.add_argument("source", help="Workspace folder, Hauptprozess folder or vorgaenge/<slug>/CONTEXT.md")
    view_parser.add_argument("--out", required=True, help="New folder for the pages; must not exist")
    view_parser.add_argument("--json", action="store_true", help="Also write model.json, an export, never a source")
    view_parser.add_argument("--language", choices=LANGUAGES, help="Page language when the workspace records none")
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
    if args.command == "view":
        from .view import run

        return run(Path(args.source), Path(args.out), write_json=args.json, language=args.language)
    if args.command == "template":
        print(template_text(args.kind, language=args.language), end="")
        return 0
    if args.command == "hash":
        if args.json:
            tool = _package_metadata()
            try:
                references = file_references(Path(args.attempt), args.surface)
            except HashSurfaceError as error:
                _print_json_report(
                    {
                        "report_version": 3,
                        "command": "hash",
                        "tool": tool,
                        "issues": [_issue_json(error.code, str(error.path), error.message)],
                        "references": None,
                        "attempt": args.attempt,
                        "surfaces": args.surface,
                    }
                )
                return 1
            _print_json_report(
                {
                    "report_version": 3,
                    "command": "hash",
                    "tool": tool,
                    "issues": [],
                    "references": references,
                    "attempt": args.attempt,
                    "surfaces": args.surface,
                }
            )
            return 0
        try:
            print(json.dumps(file_references(Path(args.attempt), args.surface), ensure_ascii=True))
        except HashSurfaceError as error:
            print(error, file=sys.stderr)
            return 1
        return 0
    tool = _package_metadata() if args.json else None
    from .validator import validate

    report = validate(Path(args.path))
    if args.json:
        _print_json_report(
            {
                "report_version": 3,
                "command": "validate",
                "tool": tool,
                "issues": [
                    _issue_json(issue.code, issue.path, issue.message, issue.rule)
                    for issue in report.issues
                ],
                "not_judged": [{"path": item.path, "protocol": item.protocol,
                                **({"reason": item.reason} if item.reason else {})} for item in report.not_judged],
                "not_judged_counts": report.not_judged_counts,
                "release": report.release,
                "pin": report.pin,
                "judged": report.judged,
                "superseded": list(report.superseded),
                "external_references": list(report.external_references),
                "external_references_not_verified": report.external_references_not_verified,
                "valid": report.valid,
                "root": args.path,
            }
        )
        return 0 if report.valid else 1
    counts = report.judged
    print(f"impacts validate {report.release} against pin {report.pin or 'none'}: "
          f"{counts['hauptprozess']} Hauptprozesse, {counts['teilprozess']} Teilprozesse, "
          f"{counts['arbeitsschritt']} Arbeitsschritte, {counts['vorgang']} Vorgänge, "
          f"{counts['versuch']} Versuche judged; {report.not_judged_counts['vorgang']} Vorgänge not judged; "
          f"{report.not_judged_counts['definition_tree']} definition trees outside hauptprozesse/"
          + ("; workspace not judged" if any(item.path == "CONTEXT.md" for item in report.not_judged) else ""))
    for item in report.not_judged:
        print(item.message)
    if report.external_references_not_verified:
        print(f"{report.external_references_not_verified} references in external stores not verified by Core")
    for issue in report.issues:
        print(f"{issue.code}: {issue.path}: {issue.message} ({issue.rule})")
    return 0 if report.valid else 1


if __name__ == "__main__":
    sys.exit(main())
