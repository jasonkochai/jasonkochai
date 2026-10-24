"""Build the header and Juniper drawings, light and dark."""

from __future__ import annotations

import argparse
from datetime import date

from svg import Sheet, Text, dimension, display, keylines, mono, write_pair

EASE = "cubic-bezier(0.22, 1, 0.36, 1)"

# 42 Berlin: curriculum start and expected finish (from the CV).
START = date(2026, 5, 1)
FINISH = date(2027, 10, 31)


def progress(today: date) -> float:
    """Return how far today sits between START and FINISH, clamped to 0..1."""
    span = (FINISH - START).days
    return min(max((today - START).days / span, 0.0), 1.0)


def header(theme: str, today: date) -> Sheet:
    """Return the title block: the name over the 42 Berlin dimension string."""
    sheet = Sheet(208, "Jason Koch. 42 Berlin, 05/2026 to 10/2027.", theme)
    name = Text(display(), "JASON KOCH", 72, 36, 100, tracking=-0.012)
    x0, x1, y = 36.0, 564.0, 156.0
    now_x = round(x0 + (x1 - x0) * progress(today), 1)
    sheet.css = f"""
.draw {{ animation: draw 1.4s {EASE} both; }}
.draw + .draw {{ animation-delay: 0.15s; }}
.cover {{ transform: scaleX(0); transform-box: fill-box; transform-origin: right;
  animation: uncover 0.9s linear 0.35s both; }}
.pen {{ opacity: 0; animation: pen 0.9s linear 0.35s both; }}
.dim {{ animation: grow-x 0.9s {EASE} 1.1s both; }}
.done {{ animation: grow-x 0.7s {EASE} 1.6s both; }}
.label {{ animation: fade 0.6s {EASE} 1.5s both; }}
.marker {{ animation: rise 0.5s {EASE} 2.1s both; }}
@keyframes uncover {{ from {{ transform: scaleX(1); }} to {{ transform: scaleX(0); }} }}
@keyframes pen {{
  from {{ opacity: 1; transform: translateX(0); }}
  95% {{ opacity: 1; }}
  to {{ opacity: 0; transform: translateX({name.width:.1f}px); }}
}}
"""
    top = 100 - 72 * 0.74
    sheet.add(
        keylines(600, 208),
        name.svg(),
        f'<rect class="paper cover" x="{name.left - 2}" y="{top - 4:.1f}" '
        f'width="{name.width + 6:.1f}" height="{72 * 0.74 + 10:.1f}"/>',
        f'<path class="heavy pen" d="M{name.left} {top - 8:.1f}V{100 + 6}"/>',
        dimension(x0, x1, y, cls="line dim from-left"),
        f'<path class="heavy done from-left" d="M{x0} {y}H{now_x}"/>',
        '<g class="label">',
        Text(mono(), "05/2026", 20, x0 + 10, y - 12, cls="muted").svg(),
        Text(mono(), "10/2027", 20, x1 - 10, y - 12, anchor="end",
             cls="muted").svg(),
        Text(display(), "42 Berlin", 21, (x0 + x1) / 2, y - 12,
             anchor="middle").svg(),
        "</g>",
        '<g class="marker">',
        f'<path class="ink" d="M{now_x} {y + 4}l6 9h-12z"/>',
        Text(mono(), today.strftime("%m/%Y"), 17, now_x, y + 33,
             anchor="middle", cls="muted").svg(),
        "</g>",
    )
    return sheet


TOPICS = ["digest", "events", "email", "calendar", "notes"]
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
        "Juniper wiring: five Telegram topics (digest, events, email, "
        "calendar, notes) reach one OpenClaw gateway in Docker on my NAS. "
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
        keylines(600, height),
        Text(display(), "Telegram topics", 18, 36, top - 14, cls="muted").svg(),
        Text(display(), "Tools", 18, tool_x, top - 14, cls="muted").svg(),
        f'<path class="line" d="M{box0} {top}H{box1}V{bottom}H{box0}Z"/>',
        f'<path class="line draw" pathLength="1" '
        f'd="M{gx0} {top}H{gx1}V{bottom}H{gx0}Z"/>',
        f'<path class="line-2" d="M{gx0 + 5} {top + 5}H{gx1 - 5}'
        f'V{bottom - 5}H{gx0 + 5}Z"/>',
        Text(display(), "OpenClaw", 24, (gx0 + gx1) / 2, mid - 12,
             anchor="middle").svg(),
        Text(display(), "Docker on my NAS", 18, (gx0 + gx1) / 2, mid + 16,
             anchor="middle", cls="muted").svg(),
        Text(display(), "one Telegram bot", 18, (gx0 + gx1) / 2, mid + 40,
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
    """Write the header and Juniper SVG pairs into assets/."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--today", type=date.fromisoformat,
                        default=date.today(),
                        help="date for the 'now' marker (YYYY-MM-DD)")
    args = parser.parse_args()
    write_pair("header", lambda theme: header(theme, args.today))
    write_pair("juniper", juniper)


if __name__ == "__main__":
    main()
