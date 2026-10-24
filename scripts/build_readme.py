"""Render the generated sections of README.md from projects.yml."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
PROJECTS = ROOT / "projects.yml"

STATUSES = ("shipped", "building", "paused")
GROUPS = ("own", "42")
MAX_ONE_LINER = 240

# Copy the profile never uses (hallmark gate 19 plus the profile's own list).
BANNED_WORDS = [
    "passionate", "tech enthusiast", "always learning", "love to code",
    "seamless", "robust", "empower", "supercharge", "elevate", "effortless",
    "unlock", "unleash", "next-generation", "world-class", "best-in-class",
    "industry-leading", "mission-critical", "future-proof", "cutting-edge",
    "visitor counter",
]
BANNED_MARKS = {"—": "em dash", "–": "en dash", "·": "middle dot"}


class ProjectError(ValueError):
    """projects.yml or README.md breaks a rule."""


def load(path: Path = PROJECTS) -> list[dict[str, Any]]:
    """Return the project list from projects.yml."""
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    projects = data.get("projects") or []
    if not isinstance(projects, list):
        raise ProjectError("projects.yml: 'projects' must be a list")
    return projects


def lint_copy(text: str, where: str) -> list[str]:
    """Return a problem for each banned word or mark in text."""
    problems = []
    lowered = text.lower()
    for word in BANNED_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            problems.append(f"{where}: banned phrase '{word}'")
    for mark, label in BANNED_MARKS.items():
        if mark in text:
            problems.append(f"{where}: {label}")
    return problems


def validate(projects: list[dict[str, Any]], root: Path = ROOT) -> list[str]:
    """Return every rule a project entry breaks."""
    problems: list[str] = []
    seen: set[str] = set()
    for i, p in enumerate(projects):
        where = f"projects[{i}] {p.get('name', '?')}"
        for key in ("name", "group", "status", "one_liner"):
            if not p.get(key):
                problems.append(f"{where}: missing '{key}'")
        if p.get("name") in seen:
            problems.append(f"{where}: duplicate name")
        seen.add(p.get("name", ""))
        if str(p.get("group")) not in GROUPS:
            problems.append(f"{where}: group must be one of {GROUPS}")
        if p.get("status") not in STATUSES:
            problems.append(f"{where}: status must be one of {STATUSES}")
        one_liner = str(p.get("one_liner", ""))
        if len(one_liner) > MAX_ONE_LINER:
            problems.append(f"{where}: one_liner is {len(one_liner)} chars, "
                            f"keep it under {MAX_ONE_LINER}")
        problems += lint_copy(one_liner, where)
        links = p.get("links") or {}
        if not isinstance(links, dict):
            problems.append(f"{where}: links must be a 'label: url' mapping")
            links = {}
        for label, url in links.items():
            if not re.match(r"https?://\S+$", str(url)):
                problems.append(f"{where}: link '{label}' is not a URL")
        if p.get("status") == "shipped" and not links:
            problems.append(f"{where}: a shipped project needs a link")
        image = p.get("image")
        if image:
            for key in ("light", "dark", "alt"):
                if not image.get(key):
                    problems.append(f"{where}: image needs '{key}'")
            for key in ("light", "dark"):
                if image.get(key) and not (root / image[key]).exists():
                    problems.append(f"{where}: {image[key]} does not exist")
    return problems


def _cell(text: str) -> str:
    return " ".join(str(text).split()).replace("|", "\\|")


def _links(p: dict[str, Any]) -> str:
    links = p.get("links") or {}
    return ", ".join(f"[{label}]({url})" for label, url in links.items())


def _row(p: dict[str, Any], status: bool = False) -> str:
    name = f"**{_cell(p['name'])}**"
    if status:
        name += f"<br>{p['status']}"
    what = _cell(p["one_liner"])
    if p.get("links"):
        what += f"<br>{_links(p)}"
    return f"| {name} | {what} |"


def _table(rows: list[dict[str, Any]], status: bool = False) -> list[str]:
    return ["| Project | What it does |", "|:---|:---|",
            *(_row(p, status) for p in rows)]


def _picture(p: dict[str, Any]) -> list[str]:
    image = p["image"]
    alt = _cell(image["alt"]).replace('"', "&quot;")
    return [
        "<picture>",
        f'  <source media="(prefers-color-scheme: dark)" srcset="{image["dark"]}">',
        f'  <img src="{image["light"]}" width="100%" alt="{alt}">',
        "</picture>",
    ]


def render_own(projects: list[dict[str, Any]]) -> str:
    """Return the What I'm building section: Shipped first, then On the bench."""
    own = [p for p in projects if str(p["group"]) == "own"]
    if not own:
        return ""
    shipped = [p for p in own if p["status"] == "shipped"]
    bench = [p for p in own if p["status"] != "shipped"]
    lines = ["## What I'm building", ""]
    if shipped:
        lines += ["### Shipped", "", *_table(shipped), ""]
    if bench:
        lines += ["### On the bench", "", *_table(bench, status=True), ""]
        for p in bench:
            if p.get("image"):
                lines += [*_picture(p), ""]
    return "\n".join(lines).rstrip() + "\n"


def render_42(projects: list[dict[str, Any]]) -> str:
    """Return the 42 Berlin section."""
    rows = [p for p in projects if str(p["group"]) == "42"]
    if not rows:
        return ""
    lines = ["## 42 Berlin", "", *_table(rows)]
    return "\n".join(lines) + "\n"


def splice(readme: str, marker: str, body: str) -> str:
    """Replace the text between <!-- marker:start --> and <!-- marker:end -->."""
    pattern = re.compile(
        rf"(<!-- {re.escape(marker)}:start -->\n).*?(<!-- {re.escape(marker)}:end -->)",
        re.S)
    if not pattern.search(readme):
        raise ProjectError(f"README.md has no {marker}:start/end markers")
    return pattern.sub(lambda m: m.group(1) + body + m.group(2), readme)


def build(readme: str, projects: list[dict[str, Any]]) -> str:
    """Return README text with both generated sections rewritten."""
    for marker, body in (("projects:own", render_own(projects)),
                         ("projects:42", render_42(projects))):
        readme = splice(readme, marker, body + "\n" if body else "")
    return readme


def main() -> int:
    """Rewrite README.md, or with --check fail if it is out of date."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if README.md is stale or breaks a rule")
    args = parser.parse_args()
    projects = load()
    problems = validate(projects)
    current = README.read_text(encoding="utf-8")
    new = build(current, projects) if not problems else current
    problems += lint_copy(new, "README.md")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    if args.check:
        if new != current:
            print("README.md is out of date: run scripts/build_readme.py",
                  file=sys.stderr)
            return 1
        return 0
    README.write_text(new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
