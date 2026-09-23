import hashlib
import importlib.util
import io
import json
from pathlib import Path
from urllib.error import HTTPError
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
