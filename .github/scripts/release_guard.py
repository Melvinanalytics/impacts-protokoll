#!/usr/bin/env python3
"""Fail-closed checks for one IMPACTS Protocol GitHub Release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import time
import tomllib
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import zipfile


REPOSITORY = "Melvinanalytics/impacts-protokoll"
DOC_PATHS = ("README.md", "02_protocol/translations/de.md")


class ReleaseGuardError(RuntimeError):
    """A release identity or artifact invariant failed."""


def project_version(root: Path) -> str:
    with (root / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def version_from_tag(tag: str) -> str:
    match = re.fullmatch(r"v(\d+\.\d+\.\d+)", tag)
    if not match:
        raise ReleaseGuardError(f"Release tag must be vMAJOR.MINOR.PATCH, got {tag!r}")
    return match.group(1)


def expected_assets(version: str) -> tuple[str, str, str]:
    return (
        f"impacts_protocol-{version}-py3-none-any.whl",
        f"impacts-protokoll-{version}-source.tar.gz",
        "SHA256SUMS",
    )


def doc_versions(text: str) -> set[str]:
    release_tags = re.findall(r"releases/tag/v([^/)\s]+)", text)
    clone_tags = re.findall(r"git clone --branch v(\S+)", text)
    wheel_versions = re.findall(r"impacts_protocol-([^-\s]+)-py3-none-any\.whl", text)
    edition_versions = re.findall(r"(?:Edition|Ausgabe)\s+v(\d+\.\d+\.\d+)", text)
    link_label_versions = re.findall(
        r"\[(?:Releases?\s+)?v(\d+\.\d+\.\d+)(?:\s+release)?\]", text, re.I
    )
    if not release_tags or not wheel_versions:
        raise ReleaseGuardError("Release URL and wheel filename must both be present")
    return set(
        release_tags
        + clone_tags
        + wheel_versions
        + edition_versions
        + link_label_versions
    )


def verify_source_claims(root: Path, tag: str) -> str:
    version = version_from_tag(tag)
    declared = project_version(root)
    if declared != version:
        raise ReleaseGuardError(
            f"pyproject.toml declares {declared}, but tag {tag} declares {version}"
        )
    for relative in DOC_PATHS:
        found = doc_versions((root / relative).read_text(encoding="utf-8"))
        if found != {version}:
            raise ReleaseGuardError(
                f"{relative} contains release versions {sorted(found)}, expected only {version}"
            )
    return version


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checksum_entries(path: Path) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  ([^/]+)", line)
        if not match:
            raise ReleaseGuardError(f"Invalid SHA256SUMS line {number}: {line!r}")
        entries.append((match.group(1), match.group(2)))
    return entries


def tracked_files(root: Path) -> set[str]:
    output = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=root, text=True
    )
    return {line for line in output.splitlines() if line}


def verify_wheel_version(wheel: Path, version: str) -> None:
    with zipfile.ZipFile(wheel) as archive:
        metadata = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(metadata) != 1:
            raise ReleaseGuardError("Wheel must contain exactly one .dist-info/METADATA")
        text = archive.read(metadata[0]).decode("utf-8")
    if f"\nVersion: {version}\n" not in f"\n{text}":
        raise ReleaseGuardError(f"Wheel metadata does not declare version {version}")


def verify_source_archive(root: Path, archive_path: Path, version: str) -> None:
    prefix = f"impacts-protokoll-{version}/"
    expected = tracked_files(root)
    found: set[str] = set()
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            if member.name == prefix.rstrip("/") and member.isdir():
                continue
            if not member.name.startswith(prefix):
                raise ReleaseGuardError(f"Source member outside {prefix}: {member.name}")
            relative = member.name.removeprefix(prefix)
            if not relative or member.isdir():
                continue
            if not member.isfile():
                raise ReleaseGuardError(f"Source archive contains non-file member: {member.name}")
            if relative not in expected:
                raise ReleaseGuardError(f"Unexpected source member: {relative}")
            extracted = archive.extractfile(member)
            if extracted is None or extracted.read() != (root / relative).read_bytes():
                raise ReleaseGuardError(f"Source member differs from tagged checkout: {relative}")
            found.add(relative)
    missing = sorted(expected - found)
    if missing:
        raise ReleaseGuardError(f"Source archive omits tracked files: {missing}")


def verify_artifacts(root: Path, dist: Path, tag: str) -> str:
    version = verify_source_claims(root, tag)
    wheel_name, source_name, checksum_name = expected_assets(version)
    actual = {path.name for path in dist.iterdir() if path.is_file()}
    expected = {wheel_name, source_name, checksum_name}
    if actual != expected:
        raise ReleaseGuardError(
            f"Release directory contains {sorted(actual)}, expected exactly {sorted(expected)}"
        )
    entries = checksum_entries(dist / checksum_name)
    listed = [name for _, name in entries]
    if listed != [wheel_name, source_name]:
        raise ReleaseGuardError(
            f"SHA256SUMS must list wheel then source archive exactly once, got {listed}"
        )
    for claimed, name in entries:
        observed = file_sha256(dist / name)
        if observed != claimed:
            raise ReleaseGuardError(f"Checksum mismatch for {name}: {claimed} != {observed}")
    verify_wheel_version(dist / wheel_name, version)
    verify_source_archive(root, dist / source_name, version)
    return version


def _fetch_release_url(url: str, token: str | None = None) -> dict:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "impacts-protocol-release-guard",
            "X-GitHub-Api-Version": "2022-11-28",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response)
    except HTTPError as error:
        raise ReleaseGuardError(
            f"GitHub Release lookup failed for {url}: HTTP {error.code}"
        ) from error


def fetch_release(repository: str, tag: str, token: str | None = None) -> dict:
    """Fetch a published release by tag; GitHub's tag endpoint excludes drafts."""
    return _fetch_release_url(
        f"https://api.github.com/repos/{repository}/releases/tags/{tag}", token
    )


def fetch_release_by_id(
    repository: str, release_id: int, token: str | None = None
) -> dict:
    """Fetch a release, including a draft, by its numeric GitHub ID."""
    return _fetch_release_url(
        f"https://api.github.com/repos/{repository}/releases/{release_id}", token
    )


def verify_release_payload(
    payload: dict,
    version: str,
    dist: Path | None = None,
    *,
    require_exact: bool = False,
    require_digests: bool = False,
    expected_tag: str | None = None,
    expected_draft: bool | None = None,
) -> None:
    tag = payload.get("tag_name", payload.get("tagName"))
    draft = payload.get("draft", payload.get("isDraft"))
    if expected_tag is not None and tag != expected_tag:
        raise ReleaseGuardError(f"GitHub Release tag is {tag!r}, expected {expected_tag!r}")
    if expected_draft is not None and draft is not expected_draft:
        raise ReleaseGuardError(
            f"GitHub Release draft state is {draft!r}, expected {expected_draft!r}"
        )
    expected = set(expected_assets(version))
    assets = {asset.get("name"): asset for asset in payload.get("assets", [])}
    actual = set(assets)
    if not expected.issubset(actual):
        raise ReleaseGuardError(f"GitHub Release omits assets: {sorted(expected - actual)}")
    if require_exact and actual != expected:
        raise ReleaseGuardError(f"GitHub Release has unexpected assets: {sorted(actual - expected)}")
    if dist is None:
        return
    for name in expected:
        remote = assets[name].get("digest")
        local = f"sha256:{file_sha256(dist / name)}"
        if require_digests and remote != local:
            raise ReleaseGuardError(f"Remote digest for {name} is {remote!r}, expected {local}")


def verify_live_release(
    repository: str,
    tag: str,
    token: str | None,
    dist: Path | None,
    retries: int,
    release_id: int | None = None,
    expected_draft: bool | None = None,
) -> None:
    version = version_from_tag(tag)
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            payload = (
                fetch_release_by_id(repository, release_id, token)
                if release_id is not None
                else fetch_release(repository, tag, token)
            )
            verify_release_payload(
                payload,
                version,
                dist,
                require_exact=dist is not None,
                require_digests=dist is not None,
                expected_tag=tag,
                expected_draft=expected_draft,
            )
            return
        except ReleaseGuardError as error:
            last_error = error
            if attempt + 1 < retries:
                time.sleep(5)
    assert last_error is not None
    raise last_error


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    sub = result.add_subparsers(dest="command", required=True)
    source = sub.add_parser("source")
    source.add_argument("--root", type=Path, default=Path("."))
    source.add_argument("--tag", required=True)
    artifacts = sub.add_parser("artifacts")
    artifacts.add_argument("--root", type=Path, default=Path("."))
    artifacts.add_argument("--dist", type=Path, required=True)
    artifacts.add_argument("--tag", required=True)
    live = sub.add_parser("live")
    live.add_argument("--repository", default=REPOSITORY)
    live.add_argument("--tag", required=True)
    live.add_argument("--token", default=os.environ.get("GH_TOKEN"))
    live.add_argument("--dist", type=Path)
    live.add_argument("--retries", type=int, default=1)
    live.add_argument("--release-id", type=int)
    live.add_argument("--expect-draft", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    if args.command == "source":
        verify_source_claims(args.root.resolve(), args.tag)
    elif args.command == "artifacts":
        verify_artifacts(args.root.resolve(), args.dist.resolve(), args.tag)
    else:
        verify_live_release(
            args.repository,
            args.tag,
            args.token,
            args.dist,
            args.retries,
            args.release_id,
            True if args.expect_draft else None,
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReleaseGuardError as error:
        raise SystemExit(f"release guard: {error}") from error
