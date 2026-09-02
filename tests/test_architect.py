from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol.io import load_frontmatter_and_body

SKILL = ROOT / "02_protocol" / "impacts-architect"
SKILL_FILE = SKILL / "SKILL.md"
LINK = re.compile(r"\]\(([^)]+)\)")


def _body() -> str:
    _, body = load_frontmatter_and_body(SKILL_FILE)
    return body


def test_skill_frontmatter_names_the_skill():
    metadata, _ = load_frontmatter_and_body(SKILL_FILE)

    assert metadata["name"] == "impacts-architect"
    assert len(metadata["description"]) > 80


def test_skill_covers_three_modes_and_the_walk_test():
    body = _body()

    for heading in ("## Build mode", "## Restructure mode", "## Import mode", "## Walk test"):
        assert heading in body, heading


def test_build_mode_runs_the_seven_phases_in_order():
    body = _body()
    build = body[body.index("## Build mode") : body.index("## Restructure mode")]
    positions = [build.index(phase) for phase in ("Identify", "Minimize", "Perfect", "Augment", "Construct", "Test", "Scale")]

    assert positions == sorted(positions)


def test_skill_names_the_core_commands():
    body = _body()

    for command in ("impacts template", "impacts validate", "impacts hash", "git rev-parse HEAD:applications/"):
        assert command in body, command


def test_skill_never_lets_an_agent_write_human_attribution():
    assert "human:<id>" in _body()


def test_every_relative_link_in_the_skill_resolves():
    unresolved = []
    for document in SKILL.rglob("*.md"):
        for target in LINK.findall(document.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "#")):
                continue
            path = (document.parent / target.split("#", 1)[0]).resolve()
            if not path.exists():
                unresolved.append(f"{document.relative_to(ROOT)} -> {target}")

    assert unresolved == []


def test_as_is_capture_template_parses_with_its_capture_fields():
    metadata, body = load_frontmatter_and_body(SKILL / "templates" / "ist-prozess.md")

    assert metadata["type"] == "ist-prozess"
    assert {"owner", "frequency", "value", "pain", "touchpoint", "evidence_status"} <= set(metadata)
    assert "Ablauf heute" in body
