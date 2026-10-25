"""Build the header, footer and 42 Berlin progress drawings, light and dark."""

from __future__ import annotations

import argparse
from datetime import date

from svg import WIDE, Sheet, Text, display, label, write_pair

EASE = "cubic-bezier(0.22, 1, 0.36, 1)"

# 42 Berlin: curriculum start and expected finish (from the CV).
START = date(2026, 5, 1)
FINISH = date(2027, 10, 31)


def progress(today: date) -> float:
    """Return how far today sits between START and FINISH, clamped to 0..1."""
    span = (FINISH - START).days
    return min(max((today - START).days / span, 0.0), 1.0)


RISE = 20.0  # how much the cut climbs from left to right
CUT_CSS = f"""
.band {{ animation: grow-x 0.8s {EASE} 0.2s both; }}
.thread {{ transform-box: fill-box; transform-origin: right;
  animation: grow-x 0.9s {EASE} 0.45s both; }}
.glint {{ animation: glint 4.5s ease-in-out 1.4s infinite; }}
@keyframes glint {{ 0% {{ transform: translateX(-140px); }}
  55%, 100% {{ transform: translateX(740px); }} }}
"""


def cut(name: str, y: float, side: str) -> str:
    """Return the slanted cut: a taupe band with a glint and a chalk thread.

    y is where the cut meets the left edge; it climbs RISE to the right.
    side "below" puts band and thread under the card (header), "above" puts
    them over it (footer).
    """
    def edge(offset: float) -> tuple[float, float]:
        return y + offset, y - RISE + offset

    sign = 1 if side == "below" else -1
    (a0, a1), (b0, b1) = edge(0), edge(10 * sign)
    t0, t1 = edge(17 * sign)
    band = f"M0 {a0}L600 {a1}L600 {b1}L0 {b0}Z"
    return (
        f'<defs><clipPath id="{name}-band"><path d="{band}"/></clipPath>'
        f'<linearGradient id="{name}-shine" x1="0" x2="1">'
        '<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset="0.5" stop-color="#fff" stop-opacity="0.55"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/>'
        "</linearGradient></defs>"
        f'<path class="accent band from-left" d="{band}"/>'
        f'<g clip-path="url(#{name}-band)"><rect class="glint" x="0" '
        f'y="{min(a1, b1) - 2}" width="110" height="{RISE + 14}" '
        f'fill="url(#{name}-shine)"/></g>'
        f'<path class="ink thread" opacity="0.4" '
        f'd="M0 {t0 - 1}L600 {t1 - 1}L600 {t1 + 1}L0 {t0 + 1}Z"/>'
    )


def struck_line(face_size: float, before: str, after: str, x: float, y: float,
                anchor: str, delay: float) -> tuple[str, list[str]]:
    """Return (css, parts) for "before" struck through in taupe, then "after"."""
    face, gap = display(), face_size * 0.28
    total = face.width(before, face_size) + gap + face.width(after, face_size)
    left = x - {"start": 0.0, "middle": total / 2}[anchor]
    old = Text(face, before, face_size, left, y, cls="muted struck")
    new = Text(face, after, face_size, old.left + old.width + gap, y, cls="ink fixed")
    mid = y - face_size * 0.3
    thick = max(face_size / 10, 3)
    css = f"""
.struck {{ animation: fade 0.7s {EASE} {delay + 0.25:.2f}s both; }}
.strike {{ animation: grow-x 0.45s cubic-bezier(0.65, 0, 0.35, 1) {delay + 1:.2f}s both; }}
.fixed {{ animation: rise 0.6s {EASE} {delay + 1.55:.2f}s both; }}
"""
    parts = [
        old.svg(),
        f'<rect class="accent strike from-left" x="{old.left - 4:.1f}" '
        f'y="{mid - thick / 2:.1f}" width="{old.width + 8:.1f}" '
        f'height="{thick:.1f}" rx="{thick / 2:.1f}" '
        f'transform="rotate(-1.2 {old.left:.1f} {mid:.1f})"/>',
        new.svg(),
    ]
    return css, parts


def header(theme: str) -> Sheet:
    """Return the slogan card, cut off at a slant above a taupe band."""
    sheet = Sheet(204, "Learning AI, the clean way (struck through) the real way.",
                  theme, paper=False)
    x0, y = 40.0, 178.0
    face = display()
    per_px = (face.width("the clean way", 1) + face.width("the real way.", 1)) * 1.03
    size = min(50.0, (600 - 2 * x0) / per_px)
    first = Text(face, "Learning AI,", size, x0, 80)
    css, line = struck_line(size, "the clean way", "the real way.", x0,
                            80 + size * 1.12, "start", 0.0)
    sheet.css = f".first {{ animation: fade 0.7s {EASE} both; }}{css}{CUT_CSS}"
    sheet.add(
        f'<path class="paper" d="M0 {y}V14A14 14 0 0 1 14 0H586A14 14 0 0 1 600 14'
        f'V{y - RISE}Z"/>',
        cut("header", y, "below"),
        f'<g class="first">{first.svg()}</g>',
        *line,
    )
    return sheet


def footer(theme: str) -> Sheet:
    """Return the closing card: the same slanted cut on top, "the end" struck."""
    height, y = 134, 44.0
    sheet = Sheet(height, "The end (struck through) to be continued.", theme,
                  paper=False)
    css, line = struck_line(30.0, "the end", "to be continued.", 300.0, 104.0,
                            "middle", 0.3)
    sheet.css = css + CUT_CSS
    sheet.add(
        f'<path class="paper" d="M0 {y}L600 {y - RISE}V{height - 14}'
        f'A14 14 0 0 1 586 {height}H14A14 14 0 0 1 0 {height - 14}Z"/>',
        cut("footer", y, "above"),
        *line,
    )
    return sheet


def school(theme: str, today: date) -> Sheet:
    """Return the 42 Berlin progress line: share done, filling track, today pulsing."""
    done = progress(today)
    pct = round(done * 100)
    # the heading adds 16px above and the table 5px below; this places the
    # line midway between them, with room for the pulse
    height = 41
    sheet = Sheet(height, f"42 Berlin, {START:%m/%Y} to {FINISH:%m/%Y}: {pct}% done.",
                  theme, width=WIDE, paper=False)
    y = 15.0
    left = Text(display(), f"{pct}% done", 17, 0, y + 6)
    right = Text(label(), f"{FINISH:%m/%Y}", 15, WIDE, y + 5, anchor="end",
                 cls="muted")
    x0, x1 = left.width + 22, WIDE - right.width - 22
    now_x = round(x0 + (x1 - x0) * done, 1)
    sheet.css = f"""
.track {{ animation: fade 0.6s {EASE} both; }}
.done {{ animation: grow-x 1.4s {EASE} 0.3s both; }}
.now {{ animation: rise 0.5s {EASE} 1.4s both; }}
.halo {{ transform-box: fill-box; transform-origin: center; opacity: 0;
  animation: pulse 2.4s ease-out 1.9s infinite; }}
@keyframes pulse {{ from {{ transform: scale(1); opacity: 0.55; }}
  to {{ transform: scale(2.4); opacity: 0; }} }}
"""
    sheet.add(
        f'<g class="track">{left.svg()}{right.svg()}',
        f'<rect class="paper-2" x="{x0:.1f}" y="{y - 1.5}" width="{x1 - x0:.1f}" '
        'height="3" rx="1.5"/></g>',
        f'<rect class="accent done from-left" x="{x0:.1f}" y="{y - 1.5}" '
        f'width="{now_x - x0:.1f}" height="3" rx="1.5"/>',
        f'<circle class="accent halo" cx="{now_x}" cy="{y}" r="6"/>',
        f'<circle class="ink now" cx="{now_x}" cy="{y}" r="6"/>',
    )
    return sheet


def main() -> None:
    """Write the header, footer and 42 Berlin SVG pairs into assets/."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--today", type=date.fromisoformat,
                        default=date.today(),
                        help="date for the 'now' marker (YYYY-MM-DD)")
    args = parser.parse_args()
    write_pair("header", header)
    write_pair("footer", footer)
    write_pair("school", lambda theme: school(theme, args.today))


if __name__ == "__main__":
    main()
