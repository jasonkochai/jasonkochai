"""Build the header, 42 Berlin progress and Juniper drawings, light and dark."""

from __future__ import annotations

import argparse
import math
from datetime import date

from svg import WIDE, Sheet, Text, display, frame, label, wave, write_pair

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
        '<rect class="paper" width="600" height="154" rx="14"/>',
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
        '<rect class="paper" y="42" width="600" height="108" rx="14"/>',
        waves((14.0, 22.0, 32.0), 60.0),
        *line,
    )
    return sheet


def months(start: date, finish: date) -> list[date]:
    """Return the first day of every month after start, up to finish."""
    out = []
    y, m = start.year, start.month
    while True:
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        if date(y, m, 1) > finish:
            return out
        out.append(date(y, m, 1))


def school(theme: str, today: date) -> Sheet:
    """Return the 42 Berlin progress track: month ticks, the done part, today pulsing."""
    done = progress(today)
    pct = round(done * 100)
    height = 96
    sheet = Sheet(height, f"42 Berlin, {START:%m/%Y} to {FINISH:%m/%Y}: {pct}% done.",
                  theme, width=WIDE)
    x0, x1, y = 40.0, WIDE - 40.0, 48.0
    now_x = round(x0 + (x1 - x0) * done, 1)
    tag_x = min(max(now_x, x0 + 30), x1 - 30)
    sheet.css = f"""
.track {{ animation: fade 0.5s {EASE} both; }}
.tick {{ animation: rise 0.4s {EASE} both; }}
.done {{ animation: grow-x 1.2s {EASE} 0.4s both; }}
.now {{ animation: rise 0.5s {EASE} 1.4s both; }}
.halo {{ transform-box: fill-box; transform-origin: center; opacity: 0;
  animation: pulse 2.4s ease-out 1.9s infinite; }}
.dates {{ animation: fade 0.6s {EASE} 0.6s both; }}
@keyframes pulse {{ from {{ transform: scale(1); opacity: 0.6; }}
  to {{ transform: scale(2.8); opacity: 0; }} }}
"""
    ticks = []
    for i, m in enumerate(months(START, FINISH)):
        tx = x0 + (x1 - x0) * progress(m)
        cls = "accent" if m <= today else "muted"
        alpha = 1.0 if m <= today else 0.4
        ticks.append(f'<rect class="{cls} tick" opacity="{alpha}" '
                     f'style="animation-delay: {0.1 + 0.05 * i:.2f}s" '
                     f'x="{tx - 1:.1f}" y="{y - 9}" width="2" height="18" rx="1"/>')
    sheet.add(
        frame(WIDE, height),
        f'<rect class="paper-2 track" x="{x0}" y="{y - 3}" width="{x1 - x0}" '
        'height="6" rx="3"/>',
        *ticks,
        f'<rect class="accent done from-left" x="{x0}" y="{y - 3}" '
        f'width="{now_x - x0:.1f}" height="6" rx="3"/>',
        f'<circle class="accent halo" cx="{now_x}" cy="{y}" r="8"/>',
        f'<g class="now"><circle class="ink" cx="{now_x}" cy="{y}" r="7"/>',
        Text(display(), f"{pct}% done", 17, tag_x, y - 20, anchor="middle").svg(),
        "</g>",
        '<g class="dates">',
        Text(label(), f"{START:%m/%Y}", 15, x0, y + 32, cls="muted").svg(),
        Text(label(), f"{FINISH:%m/%Y}", 15, x1, y + 32, anchor="end",
             cls="muted").svg(),
        "</g>",
    )
    return sheet


TOPICS = ["news", "events", "email", "calendar", "notes"]
TOOLS = {
    "email": "IMAP, read-only MCP",
    "calendar": "CalDAV, read-only MCP",
    "notes": "Obsidian folder",
}


def juniper(theme: str) -> Sheet:
    """Return Juniper's wiring: Telegram topics, the gateway, each agent's tools."""
    rows = [110 + 40 * i for i in range(len(TOPICS))]
    height = rows[-1] + 50
    sheet = Sheet(
        height,
        "Juniper wiring: five Telegram topics (news, events, email, "
        "calendar, notes) reach one OpenClaw gateway in Docker on my home server. "
        "Email and calendar agents read through read-only MCP servers, "
        "notes through an Obsidian folder.",
        theme,
        width=WIDE,
    )
    box0, box1 = 40.0, 180.0      # topic list
    gx0, gx1 = 300.0, 520.0       # gateway
    wire_end, tool_x = 548.0, 560.0
    top, bottom = rows[0] - 30, rows[-1] + 22
    mid = (top + bottom) / 2
    signal_row = rows[TOPICS.index("email")]
    hop_in = gx0 - 6 - box1
    hop_out = wire_end - 6 - gx1
    sheet.css = f"""
.draw {{ animation: draw 1.2s {EASE} both; }}
.wire {{ animation: grow-x 0.6s {EASE} both; }}
.signal {{ opacity: 0; animation: 8s linear 1.6s infinite; }}
.signal-in {{ animation-name: signal-in; }}
.signal-out {{ animation-name: signal-out; }}
@keyframes signal-in {{
  0% {{ opacity: 0; transform: translateX(0); }}
  2% {{ opacity: 1; }}
  14% {{ opacity: 1; transform: translateX({hop_in}px); }}
  16%, 56% {{ opacity: 0; transform: translateX({hop_in}px); }}
  58% {{ opacity: 1; }}
  70% {{ opacity: 1; transform: translateX(0); }}
  72%, 100% {{ opacity: 0; transform: translateX(0); }}
}}
@keyframes signal-out {{
  0%, 20% {{ opacity: 0; transform: translateX(0); }}
  22% {{ opacity: 1; }}
  32%, 38% {{ opacity: 1; transform: translateX({hop_out}px); }}
  50% {{ opacity: 1; transform: translateX(0); }}
  52%, 100% {{ opacity: 0; transform: translateX(0); }}
}}
"""
    sheet.add(
        frame(WIDE, height),
        Text(display(), "Telegram topics", 18, box0 + 8, top - 14, cls="muted").svg(),
        Text(display(), "Tools", 18, tool_x, top - 14, cls="muted").svg(),
        f'<path class="line" d="M{box0} {top}H{box1}V{bottom}H{box0}Z"/>',
        f'<path class="line draw" pathLength="1" '
        f'd="M{gx0} {top}H{gx1}V{bottom}H{gx0}Z"/>',
        f'<path class="line-2" d="M{gx0 + 5} {top + 5}H{gx1 - 5}'
        f'V{bottom - 5}H{gx0 + 5}Z"/>',
        Text(display(), "OpenClaw", 24, (gx0 + gx1) / 2, mid - 12,
             anchor="middle").svg(),
        Text(display(), "Docker, home server", 18, (gx0 + gx1) / 2, mid + 16,
             anchor="middle", cls="muted").svg(),
        Text(display(), "one Telegram bot", 18, (gx0 + gx1) / 2, mid + 40,
             anchor="middle", cls="muted").svg(),
    )
    for i, (topic, y) in enumerate(zip(TOPICS, rows)):
        delay = f'style="animation-delay: {0.5 + 0.1 * i:.1f}s"'
        sheet.add(
            Text(display(), topic, 22, box0 + 12, y + 7).svg(),
            f'<path class="line wire from-left" {delay} d="M{box1} {y}H{gx0}"/>',
        )
        if topic in TOOLS:
            sheet.add(
                f'<path class="line wire from-left" {delay} '
                f'd="M{gx1} {y}H{wire_end}"/>',
                Text(display(), TOOLS[topic], 19, tool_x, y + 7).svg(),
            )
    sheet.add(
        f'<rect class="ink signal signal-in" x="{box1}" y="{signal_row - 3}" '
        'width="6" height="6"/>',
        f'<rect class="ink signal signal-out" x="{gx1}" y="{signal_row - 3}" '
        'width="6" height="6"/>',
    )
    return sheet


def main() -> None:
    """Write the header, 42 Berlin and Juniper SVG pairs into assets/."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--today", type=date.fromisoformat,
                        default=date.today(),
                        help="date for the 'now' marker (YYYY-MM-DD)")
    args = parser.parse_args()
    write_pair("header", header)
    write_pair("footer", footer)
    write_pair("school", lambda theme: school(theme, args.today))
    write_pair("juniper", juniper)


if __name__ == "__main__":
    main()
