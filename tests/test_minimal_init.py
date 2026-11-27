from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

ROOT = Path(__file__).resolve().parents[1]

import impacts_protocol
from impacts_protocol.cli import main
from impacts_protocol.io import load_frontmatter


def _init_workspace(target: Path) -> Path:
    initializer = getattr(impacts_protocol, "init_workspace", None)
    if initializer is None:
        pytest.fail("public init_workspace is missing")
    return initializer(target)


def test_init_creates_only_minimal_workspace():
    with TemporaryDirectory() as directory:
        target = Path(directory) / "workspace"

        root = _init_workspace(target)

        assert sorted(path.name for path in root.iterdir()) == [
            ".gitattributes",
            ".gitignore",
            "AGENTS.md",
            "CONTEXT.md",
            "hauptprozesse",
            "vorgaenge",
        ]
        assert (root / ".gitattributes").read_bytes() == b"* -text\n"
        assert (root / ".gitignore").read_text().split() == ["Thumbs.db", "desktop.ini", "~$*"]
        assert load_frontmatter(root / "CONTEXT.md") == {"type": "workspace", "protocol": "v0.8.2"}


def test_cli_init_needs_no_customer_argument():
    with TemporaryDirectory() as directory:
        target = Path(directory) / "workspace"

        assert main(["init", str(target)]) == 0
        assert target.is_dir()


def test_init_is_atomic_when_target_exists():
    with TemporaryDirectory() as directory:
        target = Path(directory) / "workspace"
        target.mkdir()
        marker = target / "keep"
        marker.write_text("keep", encoding="utf-8")

        with pytest.raises(FileExistsError):
            _init_workspace(target)

        assert marker.read_text(encoding="utf-8") == "keep"
        assert list(target.iterdir()) == [marker]


def test_init_router_body_states_the_operating_contract():
    with TemporaryDirectory() as directory:
        root = _init_workspace(Path(directory) / "workspace")

        body = (root / "CONTEXT.md").read_text(encoding="utf-8").split("---", 2)[2]

        for phrase in (
            "impacts template",
            "impacts validate",
            "Git root",
            "02_protocol/binding.md#execution",
            "02_protocol/ontology.md",
        ):
            assert phrase in body, f"router body lacks {phrase!r}"


def test_execution_procedure_names_the_hash_command_where_outputs_are_recorded():
    binding = (ROOT / "02_protocol" / "binding.md").read_text(encoding="utf-8")
    procedure = binding.split("## Execution", 1)[1].split("\n\n", 2)[1]
    assert "impacts hash" in procedure


def test_vorgang_template_names_the_revision_command_where_it_is_filled():
    template = ROOT / "02_protocol" / "templates" / "vorgang.md"
    assert "git rev-parse HEAD:hauptprozesse/" in template.read_text(encoding="utf-8")


def test_init_never_touches_an_existing_gitignore(tmp_path):
    target = tmp_path / "workspace"
    target.mkdir()
    (target / ".gitignore").write_text("mine\n")
    with pytest.raises(FileExistsError):
        _init_workspace(target)
    assert (target / ".gitignore").read_text() == "mine\n"


@pytest.mark.parametrize("language", ["en", "de"])
def test_generated_agent_entry_routes_to_workspace_authorities(tmp_path, language):
    root = impacts_protocol.init_workspace(tmp_path / "workspace", language=language)
    entry = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert "[CONTEXT.md](CONTEXT.md)" in entry
    router = (root / "CONTEXT.md").read_text(encoding="utf-8")
    for target in (
        "02_protocol/impacts-architect/references/formwahl.md#folder-structure-by-form",
        "02_protocol/impacts-architect/references/zuschnitt.md#naming",
        "02_protocol/binding.md#hauptprozess-tree-rules",
        "02_protocol/impacts-method.md#maintain-agent-instructions",
        "02_protocol/impacts-method.md#reviewed-correction",
    ):
        assert target in router
        path, heading = target.split("#")
        source = (ROOT / path).read_text(encoding="utf-8")
        headings = [line.lstrip("# ").lower().replace(" ", "-") for line in source.splitlines() if line.startswith("#")]
        assert heading in headings


def test_first_win_exercise_validates_cleanly_when_pinned(tmp_path):
    import re
    import tomllib
    from impacts_protocol import validate

    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    text = (ROOT / "FIRST-WIN.md").read_text(encoding="utf-8")
    blocks = re.findall(r"`([^`\n]+\.md)`[^\n]*:\n\n```markdown\n(.*?)\n```", text, flags=re.S)
    assert len(blocks) == 6, [name for name, _ in blocks]
    for rel, content in blocks:
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if rel == "CONTEXT.md":
            content = f"---\ntype: workspace\nprotocol: v{version}\n---\n\n" + content
        dest.write_text(content + "\n", encoding="utf-8")
    report = validate(tmp_path)
    assert report.valid, [(i.code, i.path, i.message) for i in report.issues]


@pytest.mark.parametrize("pin", ["v0.8.0", "v0.8.1", "v0.8.2", "v0.8.99"])
def test_patch_pins_still_reject_undeclared_domain_folder(tmp_path, pin):
    from impacts_protocol import validate
    root = impacts_protocol.init_workspace(tmp_path / "workspace")
    router = root / "CONTEXT.md"
    router.write_text(router.read_text().replace("protocol: v0.8.2", f"protocol: {pin}"))
    assert load_frontmatter(router)["protocol"] == pin
    (root / "plans").mkdir()
    (root / "plans" / "item.md").write_text("Synthetic unclassified content\n")
    report = validate(root)
    assert not report.valid
    assert "topology.form_missing" in {issue.code for issue in report.issues}
