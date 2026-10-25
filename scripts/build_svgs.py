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


# Card edge shapes the ribbons bend between: (left y, control 1, control 2, right y).
Curve = tuple[float, tuple[float, float], tuple[float, float], float]
FRONT: list[Curve] = [(196, (150, 150), (420, 232), 170),
                      (160, (200, 226), (380, 150), 204),
                      (184, (120, 160), (470, 214), 158)]
RIBBON: list[Curve] = [(204, (180, 166), (400, 236), 182),
                       (172, (220, 232), (360, 166), 212),
                       (194, (150, 176), (450, 222), 168)]
EASE_SPLINE = "0.45 0 0.55 1"


def _between(a: list[Curve], b: list[Curve], t: float, shift: int) -> list[Curve]:
    """Return curves a fraction t of the way from a to b, b rotated by shift."""
    out: list[Curve] = []
    for i, (yl, (c1x, c1y), (c2x, c2y), yr) in enumerate(a):
        bl, (d1x, d1y), (d2x, d2y), br = b[(i + shift) % len(b)]

        def mix(u: float, v: float) -> float:
            return round(u + (v - u) * t, 1)
        out.append((mix(yl, bl), (mix(c1x, d1x), mix(c1y, d1y)),
                    (mix(c2x, d2x), mix(c2y, d2y)), mix(yr, br)))
    return out


def _morph(shapes: list[str], secs: float) -> str:
    """Return a SMIL animation looping the path through shapes and back."""
    values = ";".join([*shapes, shapes[0]])
    splines = ";".join([EASE_SPLINE] * len(shapes))
    return (f'<animate attributeName="d" dur="{secs}s" repeatCount="indefinite" '
            f'calcMode="spline" keySplines="{splines}" values="{values}"/>')


def _card(c: Curve, top: float) -> str:
    yl, (c1x, c1y), (c2x, c2y), yr = c
    return (f"M0 {yl}V{top + 14}A14 14 0 0 1 14 {top}H586A14 14 0 0 1 600 {top + 14}"
            f"V{yr}C{c2x} {c2y} {c1x} {c1y} 0 {yl}Z")


def _band(c: Curve, top: float) -> str:
    yl, (c1x, c1y), (c2x, c2y), yr = c
    return f"M0 {top + 40}H600V{yr}C{c2x} {c2y} {c1x} {c1y} 0 {yl}Z"


def _thread(c: Curve) -> str:
    yl, (c1x, c1y), (c2x, c2y), yr = c
    return f"M0 {yl}C{c1x} {c1y} {c2x} {c2y} 600 {yr}"


def silk(top: float = 0.0) -> str:
    """Return the card with a flowing edge: taupe ribbon, two chalk threads, card.

    Every layer bends between its own shapes on its own timing, so the edge
    keeps moving without ever repeating in step.
    """
    # threads run just past the ribbon; where they rise above the card it hides them
    threads = [_between(FRONT, RIBBON, 1.1, 1), _between(FRONT, RIBBON, 1.2, 2)]
    parts = [f'<path class="accent">{_morph([_band(c, top) for c in RIBBON], 14)}</path>']
    for curves, secs, alpha in zip(threads, (9, 17), (0.6, 0.35)):
        parts.append(f'<path class="thread" opacity="{alpha}">'
                     f'{_morph([_thread(c) for c in curves], secs)}</path>')
    parts.append(f'<path class="paper">{_morph([_card(c, top) for c in FRONT], 11)}</path>')
    first = [f'd="{_band(RIBBON[0], top)}"', f'd="{_thread(threads[0][0])}"',
             f'd="{_thread(threads[1][0])}"', f'd="{_card(FRONT[0], top)}"']
    for i, d in enumerate(first):
        parts[i] = parts[i].replace("<path ", f"<path {d} ", 1)
    return "".join(parts)


SILK_CSS = """
.thread { fill: none; stroke: var(--ink); stroke-width: 1.5; }
"""


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
    """Return the slogan card, its bottom edge flowing like silk."""
    sheet = Sheet(226, "Learning AI, the clean way (struck through) the real way.",
                  theme, paper=False)
    x0 = 40.0
    face = display()
    per_px = (face.width("the clean way", 1) + face.width("the real way.", 1)) * 1.03
    size = min(50.0, (600 - 2 * x0) / per_px)
    first = Text(face, "Learning AI,", size, x0, 80)
    css, line = struck_line(size, "the clean way", "the real way.", x0,
                            80 + size * 1.12, "start", 0.0)
    sheet.css = f".first {{ animation: fade 0.7s {EASE} both; }}{css}{SILK_CSS}"
    sheet.add(silk(), f'<g class="first">{first.svg()}</g>', *line)
    return sheet


def footer(theme: str) -> Sheet:
    """Return the closing card: the same silk edge mirrored on top, "the end" struck."""
    top, low = 110.0, 226.0  # card starts at top; low is just past the deepest thread
    height = low - top
    sheet = Sheet(int(height), "The end (struck through) to be continued.", theme,
                  paper=False)
    css, line = struck_line(28.0, "the end", "to be continued.", 300.0, height - 22,
                            "middle", 0.3)
    sheet.css = css + SILK_CSS
    sheet.add(f'<g transform="translate(0 {low}) scale(1 -1)">{silk(top)}</g>', *line)
    return sheet


SENTENCES = [
    "Obsessed with AI",
    "Claude Code is my daily driver",
    "Building Juniper, my own multi-agent assistant",
    "Self-hosting on my home server and a VPS",
    "Many more projects in the works",
    "Learning software engineering at 42 Berlin",
]
SLOT = 4.0  # seconds each sentence is on screen


def typing(theme: str) -> Sheet:
    """Return the sentences typed out one after another, each erased before the next."""
    width, height, size = 600, 40, 21.0
    total = SLOT * len(SENTENCES)

    def pct(secs: float) -> str:
        return f"{100 * secs / total:.2f}%"

    type_end, erase_start = pct(SLOT * 0.4), pct(SLOT * 0.85)
    sheet = Sheet(height, "; ".join(SENTENCES) + ".", theme, width=width,
                  paper=False)
    css = [f"""
.reveal {{ transform-box: fill-box; transform-origin: left; transform: scaleX(0);
  animation: {total}s linear infinite both; }}
"""]
    parts = []
    face = label()
    for i, sentence in enumerate(SENTENCES):
        text = Text(face, sentence, size, width / 2, 27, anchor="middle", cls="accent")
        n = len(sentence)
        delay = f"animation-delay: {SLOT * i:.1f}s"
        css.append(f"""
@keyframes type-{i} {{
  0% {{ transform: scaleX(0); animation-timing-function: steps({n}, end); }}
  {type_end}, {erase_start} {{ transform: scaleX(1); animation-timing-function: steps({n}, end); }}
  {pct(SLOT)}, 100% {{ transform: scaleX(0); }}
}}""")
        parts.append(
            f'<clipPath id="t{i}"><rect class="reveal" style="animation-name: type-{i}; '
            f'{delay}" x="{text.left - 1:.1f}" y="0" width="{text.width + 2:.1f}" '
            f'height="{height}"/></clipPath>'
            f'<g clip-path="url(#t{i})">{text.svg()}</g>')
    sheet.css = "".join(css)
    sheet.add(*parts)
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
    write_pair("typing", typing)
    write_pair("school", lambda theme: school(theme, args.today))


if __name__ == "__main__":
    main()
