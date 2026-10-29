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


def test_own_work_is_one_table_with_shipped_first():
    out = br.render_own([project(name="Other", status="paused"), project()])
    assert "###" not in out
    assert out.index("**Thing**") < out.index("**Other**")


def test_own_table_ends_with_the_more_row():
    out = br.render_own([project(status="building", links={})])
    rows = [line for line in out.splitlines() if line.startswith("|")]
    assert rows[-1] == br.MORE_ROW


def test_no_own_projects_renders_nothing():
    assert br.render_own([project(group="42")]) == ""


def test_rows_link_the_name_to_code_without_status():
    out = br.render_own([project(status="paused")])
    assert "| [**Thing**](https://example.com/thing) |" in out
    assert "paused" not in out
    assert "[Code]" not in out


def test_rows_keep_other_links_and_plain_names_without_code():
    links = {"Demo": "https://example.com/demo", "Code": "https://example.com/thing"}
    out = br.render_own([project(links=links)])
    assert "<br>[Demo](https://example.com/demo) |" in out
    bare = br.render_own([project(status="building", links={})])
    assert "| **Thing** |" in bare


def test_42_section_opens_with_the_progress_card():
    out = br.render_42([project(group="42")])
    assert out.index(br.SCHOOL["light"]) < out.index("| Project |")


def test_pipes_in_copy_are_escaped():
    out = br.render_42([project(group="42", one_liner="a | b")])
    assert "a \\| b" in out


def test_build_rewrites_only_between_markers_and_is_idempotent():
    projects = [project(), project(name="Fly-in", group="42")]
    once = br.build(FRAME, projects)
    assert once.startswith("# Me\n\n")
    assert "old" not in once
    assert "## What I'm building" in once and "## 42 Berlin" in once
    assert br.build(once, projects) == once


def test_missing_marker_raises():
    with pytest.raises(br.ProjectError):
        br.splice("no markers here", "projects:own", "x")
