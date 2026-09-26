"""Check the existing release allowlist; this neither exports nor approves a release."""
from pathlib import Path, PurePosixPath
import importlib.util
import os
import posixpath
import re
import shutil
import subprocess
import textwrap
import tomllib
from urllib.parse import unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]

# One allowlist for the release surface.
PUBLIC_PATHS = (
    '.gitignore', '.github/', 'AGENTS.md', 'CONTEXT.md', 'CONTRIBUTING.md', 'LICENSE', 'README.md', 'FIRST-WIN.md', 'pyproject.toml',
    '02_protocol/', '06_evaluations/', 'src/', 'tests/',
)


def export_files(root):
    files = {}
    for entry in PUBLIC_PATHS:
        path = root / entry
        assert path.exists(), f'Missing allowlisted path: {entry}'
        candidates = path.rglob('*') if path.is_dir() else [path]
        for candidate in candidates:
            assert not candidate.is_symlink(), f'Symlink in export: {candidate.relative_to(root)}'
            if not candidate.is_file() or '__pycache__' in candidate.parts or candidate.suffix == '.pyc':
                continue
            relative = candidate.relative_to(root).as_posix()
            files[relative] = candidate.read_text(encoding='utf-8')
    # Remove the source-only design-record navigation row on export.
    files['CONTEXT.md'] = '\n'.join(line for line in files['CONTEXT.md'].splitlines() if '| Design record:' not in line)
    return files


def prose(text):
    return re.sub(r'^(`{3,}|~{3,})[^\n]*\n.*?^\1\s*$', '', text, flags=re.M | re.S)


def anchors(text):
    found = set(re.findall(r'<a\s+(?:id|name)=["\x27]([^"\x27]+)', text))
    counts = {}
    for title in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', prose(text), re.M):
        title = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', title).replace('`', '').lower()
        slug = re.sub(r'[^\w\- ]', '', title).replace(' ', '-')
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        found.add(slug + (f'-{count}' if count else ''))
    return found


def link_issues(files):
    """Check inline Markdown references using only the selected artifact's paths."""
    directories = {str(parent) for name in files for parent in PurePosixPath(name).parents}
    issues = []
    for name, text in files.items():
        if not name.endswith('.md'):
            continue
        for target in re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)', prose(text)):
            target = target.split(' "', 1)[0].strip('<> ')
            url = urlsplit(target)
            if url.scheme in {'http', 'https', 'mailto'}:
                continue
            if url.scheme or url.netloc or unquote(url.path).startswith('/'):
                issues.append((name, target, 'nonportable reference'))
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(url.path))) if url.path else name
            if resolved not in files and resolved not in directories:
                issues.append((name, target, 'target outside export'))
            elif url.fragment and resolved.endswith('.md') and unquote(url.fragment) not in anchors(files[resolved]):
                issues.append((name, target, 'missing anchor'))
    return issues


def test_public_markdown_references_resolve_inside_the_allowlisted_export():
    assert link_issues(export_files(ROOT)) == []


def test_public_docs_contain_no_workstation_paths():
    for name, text in export_files(ROOT).items():
        if name.endswith('.md'):
            assert not re.search(r'/Users/|/home/|/var/folders/|file://', text), name


@pytest.mark.parametrize('target', [
    '../research/private.md', '/Users/example/private.md', 'file:///tmp/private.md',
    '../../outside.md', 'included.md#missing',
])
def test_an_omitted_or_nonportable_target_or_missing_anchor_blocks_reference_closure(target):
    files = {'docs/README.md': f'[reference]({target})', 'docs/included.md': '# Present\n'}
    assert len(link_issues(files)) == 1


def test_export_links_support_relative_paths_unicode_aliases_and_duplicate_headings():
    files = {'README.md': '[one](docs/guide.md#überblick-1) [two](docs/guide.md#legacy) [dir](docs/)',
             'docs/guide.md': '# Überblick\n# Überblick\n<a id="legacy"></a>\n'}
    assert link_issues(files) == []


def test_export_excludes_all_private_documentation_and_handovers():
    paths = export_files(ROOT)
    assert all(not p.startswith('docs/') for p in paths)
    assert all(not p.startswith('v03_') for p in paths)
    assert set(PUBLIC_PATHS) == {'.gitignore', '.github/', 'AGENTS.md', 'CONTEXT.md', 'CONTRIBUTING.md', 'LICENSE', 'README.md', 'FIRST-WIN.md', 'pyproject.toml', '02_protocol/', '06_evaluations/', 'src/', 'tests/'}


@pytest.mark.parametrize("path", ["README.md", "02_protocol/translations/de.md"])
def test_current_entry_instructions_match_distribution_version(path):
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    text = (ROOT / path).read_text()
    release_tags = re.findall(r"releases/tag/v([^/)\s]+)", text)
    clone_tags = re.findall(r"git clone --branch v(\S+)", text)
    wheel_versions = re.findall(r"impacts_protocol-([^-\s]+)-py3-none-any\.whl", text)
    edition_versions = re.findall(r"(?:Edition|Ausgabe)\s+v(\d+\.\d+\.\d+)", text)
    link_label_versions = re.findall(
        r"\[(?:Releases?\s+)?v(\d+\.\d+\.\d+)(?:\s+release)?\]", text, re.I
    )
    assert release_tags and wheel_versions
    assert edition_versions and link_label_versions
    assert set(
        release_tags
        + clone_tags
        + wheel_versions
        + edition_versions
        + link_label_versions
    ) == {version}


@pytest.mark.parametrize(
    ("path", "required_terms"),
    [
        ("README.md", ("wheel", "complete source archive", "`SHA256SUMS`")),
        ("02_protocol/translations/de.md", ("Wheel", "vollständige Quellarchiv", "`SHA256SUMS`")),
    ],
)
def test_checksum_recipe_downloads_every_listed_release_asset(path, required_terms):
    text = (ROOT / path).read_text()
    paragraph = next(section for section in text.split("\n\n") if "shasum -a 256 -c SHA256SUMS" in section)

    assert all(term in paragraph for term in required_terms)
    assert "every listed asset" in paragraph or "jedes aufgeführte Artefakt" in paragraph


def test_tag_workflow_separates_read_only_build_from_publication():
    workflow = (ROOT / ".github/workflows/release.yml").read_text()
    assert 'tags:\n      - "v*"' in workflow
    assert "workflow_dispatch:" in workflow
    build = workflow[workflow.index("  build:\n") : workflow.index("  publish:\n")]
    publish = workflow[workflow.index("  publish:\n") :]
    assert "contents: read" in build
    assert "contents: write" not in build
    assert "pip install" in build
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in build
    assert "contents: write" in publish
    assert "pip install" not in publish
    assert "python -m build" not in publish
    assert "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c" in publish
    assert "git cat-file -t" in workflow
    assert "git merge-base --is-ancestor HEAD refs/remotes/origin/main" in workflow
    assert "Expected zero or one Release" in publish
    assert "https://uploads.github.com/repos/${GITHUB_REPOSITORY}/releases/${RELEASE_ID}/assets" in publish
    assert "--hostname" not in publish
    assert "python3 -c 'import sys; assert sys.version_info >= (3, 11)'" in publish
    assert "\n          python " not in publish
    assert "--release-id" in workflow
    assert "--expect-draft" in workflow
    body_patch = publish.index("gh api --method PATCH")
    body_response_check = publish.index(".tag_name == $tag and .draft == true", body_patch)
    draft_recheck = publish.index("release_guard.py live", body_response_check)
    publish_by_id = publish.index("gh api --method PATCH", draft_recheck)
    final_verify = publish.rindex("release_guard.py live")
    assert body_patch < body_response_check < draft_recheck < publish_by_id < final_verify
    assert '--release-id "${RELEASE_ID}" --expect-draft' in publish[draft_recheck:publish_by_id]
    assert '-f tag_name="${RELEASE_TAG}" -F draft=false' in publish[publish_by_id:final_verify]
    assert "--token" not in publish
    assert "pypi" not in workflow.lower()


@pytest.mark.parametrize(
    ("response_tag", "published"),
    [("v0.3.18", True), ("untagged-48312c7106a2a0522ebc", False)],
)
def test_draft_tag_response_gates_publication(tmp_path, response_tag, published):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("release workflow shell check requires bash")
    if shutil.which("jq") is None:
        pytest.skip("release workflow shell check requires jq")

    workflow = (ROOT / ".github/workflows/release.yml").read_text()
    step = workflow[workflow.index("      - name: Verify draft, publish by ID, then verify public Release") :]
    script = textwrap.dedent(step.split("        run: |\n", 1)[1])
    body_patch = script.index("gh api --method PATCH")
    final_verify = script.rindex("python3 .github/scripts/release_guard.py live")
    transaction = "set -euo pipefail\n" + script[body_patch:final_verify]

    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    gh = stub_bin / "gh"
    gh.write_text("""#!/bin/sh
input=""
while [ "$#" -gt 0 ]; do
  if [ "$1" = "--input" ]; then
    input="$2"
    shift 2
  else
    shift
  fi
done
if [ -n "$input" ]; then
  cp "$input" "$PATCH_CAPTURE"
  printf '{"tag_name":"%s","draft":true,"body":"workflow evidence"}\\n' "$PATCH_RESPONSE_TAG"
else
  touch "$PUBLISH_MARKER"
  printf '{"tag_name":"%s","draft":false}\\n' "$RELEASE_TAG"
fi
""")
    python3 = stub_bin / "python3"
    python3.write_text("#!/bin/sh\nexit 0\n")
    for executable in (gh, python3):
        executable.chmod(0o755)

    runner_temp = tmp_path / "runner-temp"
    runner_temp.mkdir()
    patch_capture = tmp_path / "observed-patch.json"
    (runner_temp / "release-notes-patch.json").write_text(
        '{"tag_name":"v0.3.18","body":"workflow evidence"}\n'
    )
    publish_marker = tmp_path / "published"
    env = os.environ.copy()
    env.update({
        "PATH": os.pathsep.join((str(stub_bin), env.get("PATH", ""))),
        "RELEASE_TAG": "v0.3.18",
        "RELEASE_ID": "397359181",
        "RUNNER_TEMP": str(runner_temp),
        "GITHUB_REPOSITORY": "example/protocol",
        "DIST_DIR": "release-dist",
        "PATCH_RESPONSE_TAG": response_tag,
        "PATCH_CAPTURE": str(patch_capture),
        "PUBLISH_MARKER": str(publish_marker),
    })
    result = subprocess.run(
        [bash, "-e", "-c", transaction],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert (result.returncode == 0) is published, result.stdout + result.stderr
    assert publish_marker.exists() is published
    assert '"tag_name":"v0.3.18"' in patch_capture.read_text()


def test_push_and_manual_runs_share_one_concurrency_key_per_tag():
    workflow = (ROOT / ".github/workflows/release.yml").read_text()
    group = next(line.strip() for line in workflow.splitlines() if line.strip().startswith("group:"))
    assert "github.ref_name" in group
    assert "inputs.version" in group
    assert "github.ref ||" not in group


def test_live_current_release_contains_required_assets():
    if os.environ.get("IMPACTS_LIVE_RELEASE_CHECK") != "1":
        pytest.skip("set IMPACTS_LIVE_RELEASE_CHECK=1 for the GitHub integration check")
    path = ROOT / ".github/scripts/release_guard.py"
    spec = importlib.util.spec_from_file_location("release_guard_live", path)
    assert spec and spec.loader
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    payload = guard.fetch_release(
        guard.REPOSITORY, f"v{version}", os.environ.get("GITHUB_TOKEN")
    )
    guard.verify_release_payload(payload, version)


# Frozen debt statement. Changing public history needs a separate human decision.
HISTORICAL_RELEASE_DEBT = {
    "tags_without_release": ("v0.3.1", "v0.2.0", "v0.1.0"),
    "source_archive_may_be_absent_before": "v0.3.5",
}
