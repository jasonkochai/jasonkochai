"""Fetch GitHub activity and draw the stats and activity SVGs, light and dark."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import urllib.request
from collections import Counter
from datetime import date
from typing import Any

import yaml

from svg import ROOT, Sheet, Text, display, keylines, mono, write_pair

DATA = ROOT / "data" / "stats.json"
CONFIG = ROOT / "stats.yml"
EASE = "cubic-bezier(0.22, 1, 0.36, 1)"
MAX_WEEKS = 52

QUERY = """
query {
  viewer {
    login
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { firstDay contributionDays { contributionCount } }
      }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      totalCount
      nodes {
        name
        isPrivate
        languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


def load_config() -> dict[str, Any]:
    """Return stats.yml as a dict."""
    with CONFIG.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def token() -> str:
    """Return a GitHub token from STATS_TOKEN, GITHUB_TOKEN or the gh CLI."""
    for name in ("STATS_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(name):
            return os.environ[name]
    return subprocess.run(["gh", "auth", "token"], capture_output=True,
                          text=True, check=True).stdout.strip()


def graphql(query: str, auth: str) -> dict[str, Any]:
    """Run one GraphQL query against the GitHub API."""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {auth}",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def collect(raw: dict[str, Any], config: dict[str, Any],
            today: date) -> dict[str, Any]:
    """Turn the API payload into the numbers the SVGs draw."""
    viewer = raw["viewer"]
    if viewer["login"].lower() != str(config["user"]).lower():
        raise RuntimeError(f"token belongs to {viewer['login']}, "
                           f"not {config['user']}")
    cc = viewer["contributionsCollection"]
    cal = cc["contributionCalendar"]
    days = [d["contributionCount"] for w in cal["weeks"]
            for d in w["contributionDays"]]
    weeks = [{"start": w["firstDay"],
              "count": sum(d["contributionCount"]
                           for d in w["contributionDays"])}
             for w in cal["weeks"]]
    first = next((i for i, w in enumerate(weeks) if w["count"]), len(weeks))
    weeks = weeks[first:][-MAX_WEEKS:]

    repos = viewer["repositories"]["nodes"]
    skip = set(config.get("exclude_from_languages") or [])
    fold = set(config.get("fold_languages") or [])
    sizes: Counter[str] = Counter()
    for repo in repos:
        if repo["name"] in skip:
            continue
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            sizes["other" if name in fold else name] += edge["size"]
    return {
        "generated": today.isoformat(),
        "contributions": cal["totalContributions"],
        "commits": cc["totalCommitContributions"],
        "active_days": sum(1 for n in days if n),
        "repositories": viewer["repositories"]["totalCount"],
        "languages": shares(sizes),
        "weeks": weeks,
    }


def shares(sizes: Counter[str], keep: int = 3) -> list[dict[str, Any]]:
    """Return the top languages by bytes with whole-percent shares, rest as other."""
    total = sum(sizes.values())
    if not total:
        return []
    named = [(n, s) for n, s in sizes.most_common() if n != "other"]
    top = named[:keep]
    rest = total - sum(s for _, s in top)
    rows = [{"name": n, "share": s / total} for n, s in top]
    if rest:
        rows.append({"name": "other", "share": rest / total})
    return rows


# Drawing ---------------------------------------------------------------

FIGURES = [
    ("contributions", "contributions", "in 12 months"),
    ("commits", "commits", "in 12 months"),
    ("active_days", "active days", "in 12 months"),
    ("repositories", "repositories", "incl. private"),
]


def odometer(value: int, x: float, baseline: float, size: float,
             delay: float) -> tuple[str, str]:
    """Return (defs, body) for a number whose digits roll up from zero."""
    face = display()
    col = max(face.width(str(d), size) for d in range(10))
    step = size * 1.1
    top = baseline - size * 0.78
    defs, body = [], []
    for i, ch in enumerate(str(value)):
        digit = int(ch)
        cx = x + i * col
        clip = f"d{int(x)}-{i}"
        defs.append(f'<clipPath id="{clip}"><rect x="{cx - 2:.1f}" '
                    f'y="{top - 4:.1f}" width="{col + 4:.1f}" '
                    f'height="{size * 0.78 + 10:.1f}"/></clipPath>')
        strip = "".join(
            Text(face, str(d), size, cx + (col - face.width(str(d), size)) / 2,
                 baseline + d * step).svg()
            for d in range(10))
        body.append(
            f'<g clip-path="url(#{clip})"><g class="roll" style="'
            f"transform: translateY(-{digit * step:.1f}px); "
            f'animation-delay: {delay + 0.08 * i:.2f}s">{strip}</g></g>')
    return "".join(defs), "".join(body)


def stats_sheet(theme: str, data: dict[str, Any]) -> Sheet:
    """Return the register of four figures over the language bar."""
    langs = ", ".join(f"{row['name']} {round(row['share'] * 100)}%"
                      for row in data["languages"])
    sheet = Sheet(
        232,
        f"{data['contributions']} contributions, {data['commits']} commits "
        f"and {data['active_days']} active days in the last 12 months, "
        f"{data['repositories']} repositories. Languages: {langs}.",
        theme,
    )
    sheet.css = f"""
.roll {{ animation: roll 1.3s {EASE} both; }}
.label {{ animation: fade 0.6s {EASE} 0.9s both; }}
.seg {{ animation: grow-x 0.7s {EASE} both; }}
@keyframes roll {{ from {{ transform: translateY(0); }} }}
"""
    x0, x1, cell = 28.0, 572.0, (572.0 - 28.0) / 4
    defs = [
        '<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" '
        'patternTransform="rotate(45)"><path class="heavy" d="M0 0V6"/></pattern>',
        '<pattern id="dots" width="4" height="4" patternUnits="userSpaceOnUse">'
        '<rect class="ink" width="1.5" height="1.5"/></pattern>',
    ]
    body = [keylines(600, 232),
            f'<path class="line" d="M{x0} 34H{x1}M{x0} 150H{x1}"/>']
    for i, (key, line1, line2) in enumerate(FIGURES):
        cx = x0 + i * cell
        if i:
            body.append(f'<path class="line-2" d="M{cx} 34V150"/>')
        d, b = odometer(int(data[key]), cx + 12, 94, 46, 0.2 + 0.15 * i)
        defs.append(d)
        body.append(b)
        body.append('<g class="label">'
                    + Text(display(), line1, 18, cx + 12, 122, cls="muted").svg()
                    + Text(display(), line2, 18, cx + 12, 143, cls="muted").svg()
                    + "</g>")

    fills = ["ink", "url(#hatch)", "url(#dots)", "none"]
    bx, by, bh = x0, 192.0, 12.0
    start = bx
    for i, row in enumerate(data["languages"]):
        w = (x1 - bx) * row["share"]
        fill = fills[min(i, len(fills) - 1)]
        style = f"animation-delay: {0.6 + 0.25 * i:.2f}s"
        if fill == "ink":
            body.append(f'<rect class="ink seg from-left" style="{style}" x="{start:.1f}" '
                        f'y="{by}" width="{w:.1f}" height="{bh}"/>')
        else:
            body.append(f'<rect class="seg from-left" style="{style}; fill: {fill}" '
                        f'x="{start:.1f}" y="{by}" width="{w:.1f}" height="{bh}"/>')
        label_x = start if i < len(data["languages"]) - 1 or w > 90 else x1
        anchor = "start" if label_x == start else "end"
        name = Text(display(), row["name"], 18, label_x, by - 10, anchor=anchor)
        pct = f"{round(row['share'] * 100)}%"
        if anchor == "start":
            pct_text = Text(mono(), pct, 16, name.left + name.width + 6, by - 10,
                            cls="muted")
        else:
            pct_text = Text(mono(), pct, 16, x1, by - 10, anchor="end",
                            cls="muted")
            name = Text(display(), row["name"], 18,
                        x1 - pct_text.width - 6, by - 10, anchor="end")
        body.append(f'<g class="label">{name.svg()}{pct_text.svg()}</g>')
        if i:
            body.append(f'<path class="line" d="M{start:.1f} {by - 4}V{by + bh + 4}"/>')
        start += w
    body.append(f'<path class="line" d="M{x0} {by - 0.5}H{x1}V{by + bh + 0.5}H{x0}Z"/>')
    sheet.add(f"<defs>{''.join(defs)}</defs>", *body)
    return sheet


def activity_sheet(theme: str, data: dict[str, Any]) -> Sheet:
    """Return weekly contributions as plotted bars, swept by a plotter head."""
    weeks = data["weeks"]
    first = date.fromisoformat(weeks[0]["start"])
    last = date.fromisoformat(weeks[-1]["start"])
    peak = max(w["count"] for w in weeks) or 1
    sheet = Sheet(
        204,
        f"Contributions per week since {first:%m/%Y}: peak {peak} in one week.",
        theme,
    )
    x0, x1, top, base = 36.0, 564.0, 72.0, 156.0
    slot = (x1 - x0) / max(len(weeks), 26)
    bar = max(slot * 0.55, 3.0)
    sweep = 2.4
    last_x = x0 + slot * (len(weeks) - 1) + slot / 2
    sheet.css = f"""
.bar {{ animation: grow-y 0.5s {EASE} both; }}
.head {{ transform: translateX({last_x - x0:.1f}px); animation: sweep {sweep}s linear 0.3s both; }}
.label {{ animation: fade 0.6s {EASE} {sweep:.1f}s both; }}
@keyframes sweep {{ from {{ transform: translateX(0); }} }}
"""
    grid = []
    for gx in range(int(x0), int(x1) + 1, 24):
        cls = "grid-2" if (gx - int(x0)) % 120 == 0 else "grid"
        grid.append(f'<path class="{cls}" d="M{gx} {top - 8}V{base}"/>')
    for gy in range(int(base), int(top) - 9, -24):
        grid.append(f'<path class="grid" d="M{x0} {gy}H{x0 + 24 * ((x1 - x0) // 24)}"/>')
    bars = []
    for i, w in enumerate(weeks):
        cx = x0 + slot * i + slot / 2
        h = (base - top) * w["count"] / peak
        delay = 0.3 + sweep * i / max(len(weeks) - 1, 1)
        if w["count"]:
            bars.append(f'<rect class="ink bar from-bottom" style="animation-delay: {delay:.2f}s" '
                        f'x="{cx - bar / 2:.1f}" y="{base - h:.1f}" '
                        f'width="{bar:.1f}" height="{h:.1f}"/>')
        else:
            bars.append(f'<path class="line-2" d="M{cx - bar / 2:.1f} {base - 1.5}'
                        f'H{cx + bar / 2:.1f}"/>')
    peak_i = max(range(len(weeks)), key=lambda i: weeks[i]["count"])
    peak_x = x0 + slot * peak_i + slot / 2
    sheet.add(
        keylines(600, 204),
        Text(display(), f"Contributions per week since {first:%m/%Y}", 18, 36, 44,
             cls="muted").svg(),
        *grid,
        *bars,
        f'<path class="line" d="M{x0} {base + 0.5}H{x1}"/>',
        '<g class="label">',
        Text(mono(), str(peak), 16, peak_x, base - (base - top) - 6,
             anchor="middle", cls="muted").svg(),
        Text(mono(), f"{first:%m/%Y}", 16, x0, base + 24, cls="muted").svg(),
        Text(mono(), f"{last:%m/%Y}", 16, x1, base + 24, anchor="end",
             cls="muted").svg(),
        "</g>",
        f'<g class="head"><path class="heavy" d="M{x0} {top - 10}V{base + 6}"/>'
        f'<path class="ink" d="M{x0 - 4} {top - 14}h8v8h-8z"/></g>',
    )
    return sheet


def main() -> None:
    """Fetch (unless --data is given) and write the stats and activity SVGs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", help="draw from this JSON instead of the API")
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    if args.data:
        with open(args.data, encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        data = collect(graphql(QUERY, token()), load_config(), args.today)
        DATA.parent.mkdir(exist_ok=True)
        DATA.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    write_pair("stats", lambda theme: stats_sheet(theme, data))
    write_pair("activity", lambda theme: activity_sheet(theme, data))


if __name__ == "__main__":
    main()
