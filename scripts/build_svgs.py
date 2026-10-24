"""Build the header, 42 Berlin progress and Juniper drawings, light and dark."""

from __future__ import annotations

import argparse
from datetime import date

from svg import Sheet, Text, display, frame, label, write_pair

EASE = "cubic-bezier(0.22, 1, 0.36, 1)"

# 42 Berlin: curriculum start and expected finish (from the CV).
START = date(2026, 5, 1)
FINISH = date(2027, 10, 31)


def progress(today: date) -> float:
    """Return how far today sits between START and FINISH, clamped to 0..1."""
    span = (FINISH - START).days
    return min(max((today - START).days / span, 0.0), 1.0)


def header(theme: str) -> Sheet:
    """Return the slogan: "the clean way" struck through, "the real way." after it."""
    sheet = Sheet(
        182,
        "Learning AI, the clean way (struck through) the real way.",
        theme,
    )
    x0, gap = 40.0, 14.0
    face = display()
    per_px = face.width("the clean way", 1) + face.width("the real way.", 1)
    size = min(50.0, (600 - 2 * x0 - gap) / per_px)
    first = Text(face, "Learning AI,", size, x0, 80)
    clean = Text(face, "the clean way", size, x0, 80 + size * 1.12,
                 cls="muted struck")
    real = Text(face, "the real way.", size, clean.left + clean.width + gap,
                clean.y, cls="ink fixed")
    strike_y = clean.y - size * 0.3
    sheet.css = f"""
.first {{ animation: fade 0.7s {EASE} both; }}
.struck {{ animation: fade 0.7s {EASE} 0.25s both; }}
.strike {{ animation: grow-x 0.45s cubic-bezier(0.65, 0, 0.35, 1) 1s both; }}
.fixed {{ animation: rise 0.6s {EASE} 1.55s both; }}
"""
    sheet.add(
        f'<g class="first">{first.svg()}</g>',
        clean.svg(),
        f'<rect class="accent strike from-left" x="{clean.left - 4:.1f}" '
        f'y="{strike_y - 2.5:.1f}" width="{clean.width + 8:.1f}" height="5" '
        f'rx="2.5" transform="rotate(-1.2 {clean.left:.1f} {strike_y:.1f})"/>',
        real.svg(),
    )
    return sheet


def school(theme: str, today: date) -> Sheet:
    """Return the 42 Berlin progress bar from START to FINISH with today marked."""
    sheet = Sheet(
        72,
        f"42 Berlin, {START:%m/%Y} to {FINISH:%m/%Y}. "
        f"{round(progress(today) * 100)}% done.",
        theme,
    )
    bx0, bx1, y = 200.0, 470.0, 36.0
    now_x = round(bx0 + (bx1 - bx0) * progress(today), 1)
    sheet.css = f"""
.bar {{ animation: fade 0.6s {EASE} both; }}
.done {{ animation: grow-x 0.9s {EASE} 0.3s both; }}
.now {{ animation: rise 0.5s {EASE} 1.1s both; }}
"""
    sheet.add(
        frame(600, 72),
        '<g class="bar">',
        Text(display(), "42 Berlin", 18, 28, y + 6).svg(),
        Text(label(), f"{START:%m/%Y}", 14, bx0 - 12, y + 5, anchor="end",
             cls="muted").svg(),
        f'<rect class="paper-2" x="{bx0}" y="{y - 2}" width="{bx1 - bx0}" '
        'height="4" rx="2"/>',
        Text(label(), f"{FINISH:%m/%Y}", 14, bx1 + 12, y + 5,
             cls="muted").svg(),
        "</g>",
        f'<rect class="accent done from-left" x="{bx0}" y="{y - 2}" '
        f'width="{now_x - bx0:.1f}" height="4" rx="2"/>',
        f'<circle class="ink now" cx="{now_x}" cy="{y}" r="5"/>',
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
    )
    box0, box1 = 28.0, 142.0      # topic list
    gx0, gx1 = 170.0, 348.0       # gateway
    wire_end, tool_x = 366.0, 374.0
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
        frame(600, height),
        Text(display(), "Telegram topics", 18, 36, top - 14, cls="muted").svg(),
        Text(display(), "Tools", 18, tool_x, top - 14, cls="muted").svg(),
        f'<path class="line" d="M{box0} {top}H{box1}V{bottom}H{box0}Z"/>',
        f'<path class="line draw" pathLength="1" '
        f'd="M{gx0} {top}H{gx1}V{bottom}H{gx0}Z"/>',
        f'<path class="line-2" d="M{gx0 + 5} {top + 5}H{gx1 - 5}'
        f'V{bottom - 5}H{gx0 + 5}Z"/>',
        Text(display(), "OpenClaw", 24, (gx0 + gx1) / 2, mid - 12,
             anchor="middle").svg(),
        Text(display(), "Docker, home server", 16.5, (gx0 + gx1) / 2, mid + 16,
             anchor="middle", cls="muted").svg(),
        Text(display(), "one Telegram bot", 16.5, (gx0 + gx1) / 2, mid + 40,
             anchor="middle", cls="muted").svg(),
    )
    for i, (topic, y) in enumerate(zip(TOPICS, rows)):
        delay = f'style="animation-delay: {0.5 + 0.1 * i:.1f}s"'
        sheet.add(
            Text(display(), topic, 22, 40, y + 7).svg(),
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
    write_pair("school", lambda theme: school(theme, args.today))
    write_pair("juniper", juniper)


if __name__ == "__main__":
    main()
