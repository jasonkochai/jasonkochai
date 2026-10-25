"""Tests for scripts/stats.py: collecting numbers and drawing them."""

from collections import Counter
from datetime import date

import pytest

import stats

CONFIG = {
    "user": "jasonkochai",
    "exclude_from_languages": ["template"],
    "fold_languages": ["Makefile"],
}


def week(first_day, counts):
    return {"firstDay": first_day,
            "contributionDays": [{"contributionCount": c} for c in counts]}


def repo(name, langs, private=False):
    return {"name": name, "isPrivate": private,
            "languages": {"edges": [{"size": s, "node": {"name": n}}
                                    for n, s in langs]}}


RAW = {
    "viewer": {
        "login": "jasonkochai",
        "contributionsCollection": {
            "totalCommitContributions": 9,
            "contributionCalendar": {
                "totalContributions": 12,
                "weeks": [
                    week("2026-04-12", [0] * 7),
                    week("2026-04-19", [0, 2, 0, 0, 1, 0, 0]),
                    week("2026-04-26", [0] * 7),
                    week("2026-05-03", [4, 0, 0, 5, 0, 0, 0]),
                ],
            },
        },
        "repositories": {
            "totalCount": 3,
            "nodes": [
                repo("solver", [("Python", 600), ("Makefile", 40)]),
                repo("libft", [("C", 360)], private=True),
                repo("template", [("HTML", 10_000)]),
            ],
        },
    }
}


def test_collect_counts_and_trims_leading_empty_weeks():
    data = stats.collect(RAW, CONFIG, date(2026, 5, 5))
    assert data["generated"] == "2026-05-05"
    assert data["contributions"] == 12
    assert data["commits"] == 9
    assert data["active_days"] == 4
    assert data["repositories"] == 3
    assert [w["start"] for w in data["weeks"]] == [
        "2026-04-19", "2026-04-26", "2026-05-03"]
    assert [w["count"] for w in data["weeks"]] == [3, 0, 9]


def test_collect_excludes_and_folds_languages():
    data = stats.collect(RAW, CONFIG, date(2026, 5, 5))
    names = [row["name"] for row in data["languages"]]
    assert names == ["Python", "C", "other"]
    assert "HTML" not in names
    assert sum(row["share"] for row in data["languages"]) == pytest.approx(1)


def test_collect_refuses_a_token_for_someone_else():
    raw = {"viewer": {**RAW["viewer"], "login": "someone"}}
    with pytest.raises(RuntimeError):
        stats.collect(raw, CONFIG, date(2026, 5, 5))


def test_collect_keeps_at_most_52_weeks():
    many = [week(f"2025-{i:03d}", [1] * 7) for i in range(60)]
    raw = {"viewer": {**RAW["viewer"], "contributionsCollection": {
        "totalCommitContributions": 0,
        "contributionCalendar": {"totalContributions": 0, "weeks": many}}}}
    assert len(stats.collect(raw, CONFIG, date(2026, 5, 5))["weeks"]) == 52


def test_shares_handles_empty_and_rest():
    assert stats.shares(Counter()) == []
    rows = stats.shares(Counter({"A": 5, "B": 3, "C": 1, "D": 1}), keep=2)
    assert [r["name"] for r in rows] == ["A", "B", "other"]
    assert rows[-1]["share"] == pytest.approx(0.2)


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_sheets_render_both_themes_with_reduced_motion(theme):
    data = stats.collect(RAW, CONFIG, date(2026, 5, 5))
    for sheet in (stats.stats_sheet(theme, data),
                  stats.activity_sheet(theme, data)):
        svg = sheet.render()
        assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
        assert "prefers-reduced-motion: reduce" in svg
        assert "<title" in svg


def test_ordered_puts_chosen_languages_first_and_other_last():
    rows = [{"name": "C", "share": 0.5}, {"name": "other", "share": 0.02},
            {"name": "Go", "share": 0.08}, {"name": "Python", "share": 0.4}]
    names = [r["name"] for r in stats.ordered(rows, ["Python", "C"])]
    assert names == ["Python", "C", "Go", "other"]
