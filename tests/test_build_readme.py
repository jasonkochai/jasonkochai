"""Tests for scripts/build_readme.py."""

from pathlib import Path

import pytest

import build_readme as br

FRAME = (
    "# Me\n\n"
    "<!-- projects:own:start -->\nold\n<!-- projects:own:end -->\n\n"
    "<!-- projects:42:start -->\nold\n<!-- projects:42:end -->\n"
)


def project(**over):
    base = {
        "name": "Thing",
        "group": "own",
        "status": "shipped",
        "one_liner": "Does one thing with a real link.",
        "links": {"Code": "https://example.com/thing"},
    }
    base.update(over)
    return base


def test_real_projects_file_is_valid():
    assert br.validate(br.load()) == []


def test_real_readme_is_up_to_date():
    current = br.README.read_text(encoding="utf-8")
    assert br.build(current, br.load()) == current
    assert br.lint_copy(current, "README.md") == []


@pytest.mark.parametrize("over, fragment", [
    ({"status": "done"}, "status must be one of"),
    ({"group": "work"}, "group must be one of"),
    ({"links": {}}, "a shipped project needs a link"),
    ({"links": {"Code": "not a url"}}, "is not a URL"),
    ({"one_liner": "x" * 300}, "keep it under"),
    ({"one_liner": "Fast — and seamless."}, "em dash"),
    ({"one_liner": "A seamless tool."}, "banned phrase 'seamless'"),
    ({"one_liner": "Python · C"}, "middle dot"),
    ({"name": ""}, "missing 'name'"),
])
def test_validate_flags_each_rule(over, fragment):
    problems = br.validate([project(**over)])
    assert any(fragment in p for p in problems), problems


def test_building_project_may_have_no_link():
    assert br.validate([project(status="building", links={})]) == []


def test_duplicate_names_are_flagged():
    problems = br.validate([project(), project()])
    assert any("duplicate name" in p for p in problems)


def test_missing_image_file_is_flagged(tmp_path: Path):
    image = {"light": "a.svg", "dark": "b.svg", "alt": "x"}
    problems = br.validate([project(image=image)], root=tmp_path)
    assert any("a.svg does not exist" in p for p in problems)


def test_shipped_section_only_appears_with_shipped_own_work():
    bench_only = br.render_own([project(status="building", links={})])
    assert "### Shipped" not in bench_only
    assert "### On the bench" in bench_only
    both = br.render_own([project(), project(name="Other", status="paused")])
    assert both.index("### Shipped") < both.index("### On the bench")


def test_no_own_projects_renders_nothing():
    assert br.render_own([project(group="42")]) == ""


def test_bench_rows_carry_status_and_links():
    out = br.render_own([project(status="paused")])
    assert "| **Thing**<br>paused |" in out
    assert "[Code](https://example.com/thing)" in out


def test_pipes_in_copy_are_escaped():
    out = br.render_42([project(group="42", one_liner="a | b")])
    assert "a \\| b" in out


def test_build_rewrites_only_between_markers_and_is_idempotent():
    projects = [project(), project(name="Fly-in", group="42")]
    once = br.build(FRAME, projects)
    assert once.startswith("# Me\n\n")
    assert "old" not in once
    assert "## Projects" in once and "## 42 Berlin" in once
    assert br.build(once, projects) == once


def test_missing_marker_raises():
    with pytest.raises(br.ProjectError):
        br.splice("no markers here", "projects:own", "x")
