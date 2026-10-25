"""Build the header, footer and 42 Berlin progress drawings, light and dark."""

from __future__ import annotations

import argparse
import math
from datetime import date

from svg import WIDE, Sheet, Text, display, label, wave, write_pair

EASE = "cubic-bezier(0.22, 1, 0.36, 1)"

# 42 Berlin: curriculum start and expected finish (from the CV).
START = date(2026, 5, 1)
FINISH = date(2027, 10, 31)


def progress(today: date) -> float:
    """Return how far today sits between START and FINISH, clamped to 0..1."""
    span = (FINISH - START).days
    return min(max((today - START).days / span, 0.0), 1.0)


PERIOD = 300.0  # wave length; the drift moves one period per loop
WAVE_CSS = f"""
.drift {{ animation: drift linear infinite; }}
.drift-back {{ animation: drift-back linear infinite; }}
@keyframes drift {{ from {{ transform: translateX(0); }}
  to {{ transform: translateX(-{PERIOD}px); }} }}
@keyframes drift-back {{ from {{ transform: translateX(-{PERIOD}px); }}
  to {{ transform: translateX(0); }} }}
"""


def waves(bases: tuple[float, float, float], edge: float) -> str:
    """Return three drifting wave layers: taupe at the back, navy in front.

    bases go back to front; edge is where the layers close off, so the
    front layer melts into the card.
    """
    layers = [("accent", 0.55, "drift", 13), ("paper-3", 1.0, "drift-back", 17),
              ("paper", 1.0, "drift", 9)]
    out = []
    for (cls, alpha, move, secs), base in zip(layers, bases):
        # back layers close off inside the front one, so their edges never show
        close = edge if cls == "paper" else edge + math.copysign(12, base - edge)
        d = wave(base, 7, PERIOD, 600 + PERIOD, close)
        out.append(f'<g class="{move}" style="animation-duration: {secs}s">'
                   f'<path class="{cls}" opacity="{alpha}" d="{d}"/></g>')
    return "".join(out)


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
    """Return the slogan card, opening onto drifting waves at its bottom edge."""
    sheet = Sheet(192, "Learning AI, the clean way (struck through) the real way.",
                  theme, paper=False)
    x0 = 40.0
    face = display()
    per_px = (face.width("the clean way", 1) + face.width("the real way.", 1)) * 1.03
    size = min(50.0, (600 - 2 * x0) / per_px)
    first = Text(face, "Learning AI,", size, x0, 80)
    css, line = struck_line(size, "the clean way", "the real way.", x0,
                            80 + size * 1.12, "start", 0.0)
    sheet.css = f".first {{ animation: fade 0.7s {EASE} both; }}{css}{WAVE_CSS}"
    sheet.add(
        # rounded on top, square at the bottom where the waves take over
        '<path class="paper" d="M0 154V14A14 14 0 0 1 14 0H586A14 14 0 0 1 600 14V154Z"/>',
        waves((182.0, 175.0, 166.0), 138.0),
        f'<g class="first">{first.svg()}</g>',
        *line,
    )
    return sheet


def footer(theme: str) -> Sheet:
    """Return the closing card: waves on top, "the end" struck for "to be continued."."""
    sheet = Sheet(150, "The end (struck through) to be continued.", theme,
                  paper=False)
    css, line = struck_line(30.0, "the end", "to be continued.", 300.0, 112.0,
                            "middle", 0.3)
    sheet.css = css + WAVE_CSS
    sheet.add(
        '<path class="paper" d="M0 42H600V136A14 14 0 0 1 586 150H14A14 14 0 0 1 0 136Z"/>',
        waves((14.0, 22.0, 32.0), 60.0),
        *line,
    )
    return sheet


def school(theme: str, today: date) -> Sheet:
    """Return the 42 Berlin progress line: share done, filling track, today pulsing."""
    done = progress(today)
    pct = round(done * 100)
    height = 40
    sheet = Sheet(height, f"42 Berlin, {START:%m/%Y} to {FINISH:%m/%Y}: {pct}% done.",
                  theme, width=WIDE, paper=False)
    y = height / 2
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
