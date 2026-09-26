import hashlib
import http.client
import importlib.util
import io
import json
from pathlib import Path
import ssl
import subprocess
import tarfile
from urllib.error import HTTPError, URLError
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[1]
GUARD_PATH = ROOT / ".github/scripts/release_guard.py"
SPEC = importlib.util.spec_from_file_location("release_guard", GUARD_PATH)
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


def test_current_source_claims_match_current_tag():
    version = guard.project_version(ROOT)
    assert guard.verify_source_claims(ROOT, f"v{version}") == version


@pytest.mark.parametrize(
    "text",
    [
        "Edition v0.3.8 [v0.3.8 release](https://example.invalid/releases/tag/v0.3.8) impacts_protocol-0.3.8-py3-none-any.whl",
        "Ausgabe v0.3.8 [Releases v0.3.8](https://example.invalid/releases/tag/v0.3.8) impacts_protocol-0.3.8-py3-none-any.whl",
    ],
)
def test_visible_edition_and_release_link_versions_are_checked(text):
    assert guard.doc_versions(text) == {"0.3.8"}
    assert guard.doc_versions(text.replace("Edition v0.3.8", "Edition v9.9.9").replace("Ausgabe v0.3.8", "Ausgabe v9.9.9")) == {
        "0.3.8",
        "9.9.9",
    }


@pytest.mark.parametrize("tag", ["0.3.8", "v0.3", "vnext", "v0.3.8-rc1"])
def test_release_tag_is_a_stable_semantic_version(tag):
    with pytest.raises(guard.ReleaseGuardError):
        guard.version_from_tag(tag)


def test_checksum_file_accepts_only_flat_sha256_entries(tmp_path):
    checksum = tmp_path / "SHA256SUMS"
    checksum.write_text(f"{'0' * 64}  source.tar.gz\n{'1' * 64}  wheel.whl\n")
    assert guard.checksum_entries(checksum) == [
        ("0" * 64, "source.tar.gz"),
        ("1" * 64, "wheel.whl"),
    ]
    checksum.write_text(f"{'0' * 64}  nested/source.tar.gz\n")
    with pytest.raises(guard.ReleaseGuardError):
        guard.checksum_entries(checksum)


def test_wheel_metadata_must_carry_release_version(tmp_path):
    wheel = tmp_path / "example.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "impacts_protocol-0.3.8.dist-info/METADATA",
            "Name: impacts-protocol\nVersion: 0.3.8\n",
        )
    guard.verify_wheel_version(wheel, "0.3.8")
    with pytest.raises(guard.ReleaseGuardError):
        guard.verify_wheel_version(wheel, "0.3.9")


def test_git_source_archive_preserves_non_ascii_and_control_character_paths(tmp_path):
    root = tmp_path / "checkout"
    root.mkdir()
    files = {
        "plain.txt": b"plain content\n",
        "input/ä.txt": "naïve content\n".encode("utf-8"),
        "input/tab\tname.txt": b"tab path\n",
        "input/line\nbreak.txt": b"newline path\n",
    }
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def git(*args):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

    git("init", "--quiet")
    git("config", "user.name", "Release Guard Test")
    git("config", "user.email", "release-guard@example.invalid")
    git("add", "--all")
    git("commit", "--quiet", "-m", "source fixture")

    expected_files = set(files)
    assert guard.tracked_files(root) == expected_files

    prefix = "impacts-protokoll-9.8.7/"
    source_archive = tmp_path / "source.tar.gz"
    subprocess.run(
        [
            "git", "archive", "--format=tar.gz", f"--prefix={prefix}", "HEAD",
            f"--output={source_archive}",
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )
    guard.verify_source_archive(root, source_archive, "9.8.7")

    def rewrite_archive(destination, transform, extra_member=None):
        with tarfile.open(source_archive, "r:gz") as source:
            members = []
            for member in source.getmembers():
                body = source.extractfile(member)
                content = body.read() if body is not None else None
                replacement = transform(member, content)
                if replacement is not None:
                    members.append(replacement)
        if extra_member is not None:
            members.append(extra_member)
        with tarfile.open(destination, "w:gz", encoding="utf-8") as output:
            for member, content in members:
                if content is not None:
                    member.size = len(content)
                output.addfile(member, io.BytesIO(content) if content is not None else None)

    missing_archive = tmp_path / "missing.tar.gz"
    rewrite_archive(
        missing_archive,
        lambda member, content: None
        if member.name == f"{prefix}input/ä.txt"
        else (member, content),
    )
    with pytest.raises(guard.ReleaseGuardError, match="omits tracked files"):
        guard.verify_source_archive(root, missing_archive, "9.8.7")

    extra_archive = tmp_path / "extra.tar.gz"
    extra_content = b"unexpected\n"
    extra_member = tarfile.TarInfo(f"{prefix}unexpected.txt")
    extra_member.size = len(extra_content)
    rewrite_archive(
        extra_archive,
        lambda member, content: (member, content),
        extra_member=(extra_member, extra_content),
    )
    with pytest.raises(guard.ReleaseGuardError, match="Unexpected source member"):
        guard.verify_source_archive(root, extra_archive, "9.8.7")

    tampered_archive = tmp_path / "tampered.tar.gz"
    rewrite_archive(
        tampered_archive,
        lambda member, content: (
            member,
            b"tampered\n" if member.name == f"{prefix}plain.txt" else content,
        ),
    )
    with pytest.raises(guard.ReleaseGuardError, match="differs from tagged checkout"):
        guard.verify_source_archive(root, tampered_archive, "9.8.7")


def test_remote_release_requires_named_assets_and_matching_digests(tmp_path):
    version = "0.3.8"
    names = guard.expected_assets(version)
    for name in names:
        (tmp_path / name).write_bytes(name.encode())
    payload = {
        "tag_name": "v0.3.8",
        "draft": True,
        "assets": [
            {"name": name, "digest": f"sha256:{hashlib.sha256(name.encode()).hexdigest()}"}
            for name in names
        ]
    }
    guard.verify_release_payload(
        payload,
        version,
        tmp_path,
        require_exact=True,
        require_digests=True,
        expected_tag="v0.3.8",
        expected_draft=True,
    )
    payload["assets"][0]["digest"] = f"sha256:{'0' * 64}"
    with pytest.raises(guard.ReleaseGuardError):
        guard.verify_release_payload(
            payload, version, tmp_path, require_exact=True, require_digests=True
        )


class _JsonResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_draft_release_is_resolved_by_id_when_published_tag_endpoint_is_404(monkeypatch):
    payload = {
        "tag_name": "v0.3.8",
        "draft": True,
        "assets": [{"name": name} for name in guard.expected_assets("0.3.8")],
    }

    def fake_urlopen(request, timeout):
        assert timeout == 20
        if request.full_url.endswith("/releases/tags/v0.3.8"):
            raise HTTPError(request.full_url, 404, "Not Found", {}, None)
        assert request.full_url.endswith("/releases/12345")
        return _JsonResponse(json.dumps(payload).encode())

    monkeypatch.setattr(guard, "urlopen", fake_urlopen)
    with pytest.raises(guard.ReleaseGuardError, match="HTTP 404"):
        guard.fetch_release("owner/repo", "v0.3.8", "token")
    draft = guard.fetch_release_by_id("owner/repo", 12345, "token")
    guard.verify_release_payload(
        draft,
        "0.3.8",
        expected_tag="v0.3.8",
        expected_draft=True,
    )
    guard.verify_live_release(
        "owner/repo",
        "v0.3.8",
        "token",
        None,
        retries=1,
        release_id=12345,
        expected_draft=True,
    )


@pytest.mark.parametrize("network_error", [URLError("dns"), TimeoutError("timeout")])
def test_live_release_retries_transient_network_errors(monkeypatch, network_error):
    payload = {
        "tag_name": "v0.3.8",
        "draft": False,
        "assets": [{"name": name} for name in guard.expected_assets("0.3.8")],
    }
    attempts = 0

    def fake_urlopen(request, timeout):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise network_error
        return _JsonResponse(json.dumps(payload).encode())

    monkeypatch.setattr(guard, "urlopen", fake_urlopen)
    monkeypatch.setattr(guard.time, "sleep", lambda _seconds: None)
    guard.verify_live_release(
        "owner/repo", "v0.3.8", None, None, retries=2
    )
    assert attempts == 2


@pytest.mark.parametrize(
    "network_error",
    [
        http.client.RemoteDisconnected("closed"),
        ConnectionResetError("reset"),
        ssl.SSLError("tls"),
        ssl.SSLEOFError("tls-eof"),
        http.client.IncompleteRead(b'{"tag_name":', 1),
    ],
)
def test_live_release_retries_remaining_transport_errors(monkeypatch, network_error):
    payload = {
        "tag_name": "v0.3.8",
        "draft": False,
        "assets": [{"name": name} for name in guard.expected_assets("0.3.8")],
    }
    attempts = 0

    def fake_urlopen(request, timeout):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise network_error
        return _JsonResponse(json.dumps(payload).encode())

    monkeypatch.setattr(guard, "urlopen", fake_urlopen)
    monkeypatch.setattr(guard.time, "sleep", lambda _seconds: None)
    guard.verify_live_release(
        "owner/repo", "v0.3.8", None, None, retries=2
    )
    assert attempts == 2


@pytest.mark.parametrize("bad_payload", [b'{"tag_name":', b"not-json", b"\xff"])
def test_live_release_retries_response_decoding_errors(monkeypatch, bad_payload):
    payload = {
        "tag_name": "v0.3.8",
        "draft": False,
        "assets": [{"name": name} for name in guard.expected_assets("0.3.8")],
    }
    attempts = 0

    def fake_urlopen(request, timeout):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return _JsonResponse(bad_payload)
        return _JsonResponse(json.dumps(payload).encode())

    monkeypatch.setattr(guard, "urlopen", fake_urlopen)
    monkeypatch.setattr(guard.time, "sleep", lambda _seconds: None)
    guard.verify_live_release(
        "owner/repo", "v0.3.8", None, None, retries=2
    )
    assert attempts == 2


@pytest.mark.parametrize("bad_payload", [b"[]", b"null", b'"ok"'])
def test_live_release_rejects_non_object_json_without_retry(monkeypatch, bad_payload):
    attempts = 0
    sleeps = []

    def fake_urlopen(request, timeout):
        nonlocal attempts
        attempts += 1
        return _JsonResponse(bad_payload)

    monkeypatch.setattr(guard, "urlopen", fake_urlopen)
    monkeypatch.setattr(guard.time, "sleep", sleeps.append)
    with pytest.raises(guard.ReleaseGuardError, match="not an object"):
        guard.verify_live_release(
            "owner/repo", "v0.3.8", None, None, retries=3
        )
    assert attempts == 1
    assert sleeps == []


@pytest.mark.parametrize("status", [408, 500, 502, 503, 504])
def test_live_release_retries_selected_http_statuses(monkeypatch, status):
    payload = {
        "tag_name": "v0.3.8",
        "draft": False,
        "assets": [{"name": name} for name in guard.expected_assets("0.3.8")],
    }
    attempts = 0
    sleeps = []

    def fake_urlopen(request, timeout):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise HTTPError(request.full_url, status, "transient", {}, None)
        return _JsonResponse(json.dumps(payload).encode())

    monkeypatch.setattr(guard, "urlopen", fake_urlopen)
    monkeypatch.setattr(guard.time, "sleep", sleeps.append)
    guard.verify_live_release(
        "owner/repo", "v0.3.8", None, None, retries=2
    )
    assert attempts == 2
    assert sleeps == [5]


@pytest.mark.parametrize("status", [401, 403, 404, 422, 429])
def test_live_release_rejects_terminal_http_statuses_without_retry(monkeypatch, status):
    attempts = 0
    sleeps = []

    def fake_urlopen(request, timeout):
        nonlocal attempts
        attempts += 1
        raise HTTPError(request.full_url, status, "terminal", {}, None)

    monkeypatch.setattr(guard, "urlopen", fake_urlopen)
    monkeypatch.setattr(guard.time, "sleep", sleeps.append)
    with pytest.raises(guard.ReleaseGuardError, match=f"HTTP {status}"):
        guard.verify_live_release(
            "owner/repo", "v0.3.8", None, None, retries=3
        )
    assert attempts == 1
    assert sleeps == []


def test_live_release_rejects_retry_after_without_scheduling(monkeypatch):
    attempts = 0
    sleeps = []

    def fake_urlopen(request, timeout):
        nonlocal attempts
        attempts += 1
        raise HTTPError(
            request.full_url,
            503,
            "retry later",
            {"Retry-After": "60"},
            None,
        )

    monkeypatch.setattr(guard, "urlopen", fake_urlopen)
    monkeypatch.setattr(guard.time, "sleep", sleeps.append)
    with pytest.raises(guard.ReleaseGuardError, match="Retry-After"):
        guard.verify_live_release(
            "owner/repo", "v0.3.8", None, None, retries=3
        )
    assert attempts == 1
    assert sleeps == []


@pytest.mark.parametrize(
    "certificate_error",
    [
        ssl.SSLCertVerificationError(1, "certificate verify failed"),
        URLError(ssl.SSLCertVerificationError(1, "certificate verify failed")),
    ],
)
def test_live_release_rejects_certificate_failures_without_retry(
    monkeypatch, certificate_error
):
    attempts = 0
    sleeps = []

    def fake_urlopen(request, timeout):
        nonlocal attempts
        attempts += 1
        raise certificate_error

    monkeypatch.setattr(guard, "urlopen", fake_urlopen)
    monkeypatch.setattr(guard.time, "sleep", sleeps.append)
    with pytest.raises(guard.ReleaseGuardError, match="certificate"):
        guard.verify_live_release(
            "owner/repo", "v0.3.8", None, None, retries=3
        )
    assert attempts == 1
    assert sleeps == []


def test_live_release_rejects_semantic_mismatch_without_retry(monkeypatch):
    attempts = 0
    sleeps = []
    payload = {
        "tag_name": "v0.3.9",
        "draft": False,
        "assets": [{"name": name} for name in guard.expected_assets("0.3.8")],
    }

    def fake_urlopen(request, timeout):
        nonlocal attempts
        attempts += 1
        return _JsonResponse(json.dumps(payload).encode())

    monkeypatch.setattr(guard, "urlopen", fake_urlopen)
    monkeypatch.setattr(guard.time, "sleep", sleeps.append)
    with pytest.raises(guard.ReleaseGuardError, match="Release tag"):
        guard.verify_live_release(
            "owner/repo", "v0.3.8", None, None, retries=3
        )
    assert attempts == 1
    assert sleeps == []


def test_live_release_fails_closed_after_transport_retries(monkeypatch):
    attempts = 0
    sleeps = []

    def fake_urlopen(request, timeout):
        nonlocal attempts
        attempts += 1
        raise http.client.RemoteDisconnected("closed")

    monkeypatch.setattr(guard, "urlopen", fake_urlopen)
    monkeypatch.setattr(guard.time, "sleep", sleeps.append)
    with pytest.raises(guard.ReleaseGuardError, match="RemoteDisconnected"):
        guard.verify_live_release(
            "owner/repo", "v0.3.8", None, None, retries=2
        )
    assert attempts == 2
    assert sleeps == [5]


def test_live_release_requires_at_least_one_attempt():
    with pytest.raises(guard.ReleaseGuardError, match="at least 1"):
        guard.verify_live_release(
            "owner/repo", "v0.3.8", None, None, retries=0
        )


def test_release_identity_and_draft_state_must_match():
    payload = {
        "tag_name": "v0.3.8",
        "draft": False,
        "assets": [{"name": name} for name in guard.expected_assets("0.3.8")],
    }
    with pytest.raises(guard.ReleaseGuardError, match="draft state"):
        guard.verify_release_payload(
            payload,
            "0.3.8",
            expected_tag="v0.3.8",
            expected_draft=True,
        )
    with pytest.raises(guard.ReleaseGuardError, match="Release tag"):
        guard.verify_release_payload(
            payload,
            "0.3.8",
            expected_tag="v0.3.9",
        )


def test_live_command_reads_token_from_environment(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "environment-token")
    args = guard.parser().parse_args(["live", "--tag", "v0.3.8"])
    assert args.token == "environment-token"
