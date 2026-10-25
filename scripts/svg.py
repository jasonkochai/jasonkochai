"""Shared drawing kit for the profile SVGs: theme tokens, outlined text, frames."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Callable
from xml.sax.saxutils import escape

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "scripts" / "fonts"
ASSETS = ROOT / "assets"

WIDTH = 600
# Cards shown at full README width but drawn on a wider canvas, so they render smaller.
WIDE = 840

RADIUS = 14

# Brand colours from the profile photo: studio navy backdrop, taupe shirt.
THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "paper": "#17375e",
        "paper-2": "#122d4f",
        "paper-3": "#0d2340",
        "ink": "#efe9e4",
        "ink-2": "#d9d1cb",
        "muted": "#93a6bd",
        "accent": "#a5908b",
        "rule": "rgba(239, 233, 228, 0.55)",
        "rule-2": "rgba(239, 233, 228, 0.18)",
        "grid": "rgba(239, 233, 228, 0.07)",
        "grid-2": "rgba(239, 233, 228, 0.14)",
    },
    "light": {
        "paper": "#f4f6f9",
        "paper-2": "#e8edf3",
        "paper-3": "#dde4ec",
        "ink": "#17375e",
        "ink-2": "#2a4b75",
        "muted": "#5d7391",
        "accent": "#8a746e",
        "rule": "rgba(23, 55, 94, 0.55)",
        "rule-2": "rgba(23, 55, 94, 0.16)",
        "grid": "rgba(23, 55, 94, 0.06)",
        "grid-2": "rgba(23, 55, 94, 0.13)",
    },
}

BASE_CSS = """
.paper { fill: var(--paper); }
.paper-2 { fill: var(--paper-2); }
.paper-3 { fill: var(--paper-3); }
.ink { fill: var(--ink); }
.muted { fill: var(--muted); }
.accent { fill: var(--accent); }
.line { fill: none; stroke: var(--rule); stroke-width: 1; }
.line-2 { fill: none; stroke: var(--rule-2); stroke-width: 1; }
.heavy { fill: none; stroke: var(--ink); stroke-width: 2; }
.grid { fill: none; stroke: var(--grid); stroke-width: 1; }
.grid-2 { fill: none; stroke: var(--grid-2); stroke-width: 1; }
.draw { stroke-dasharray: 1; stroke-dashoffset: 0; }
.from-left { transform-box: fill-box; transform-origin: left; }
.from-bottom { transform-box: fill-box; transform-origin: bottom; }
@keyframes draw { from { stroke-dashoffset: 1; } }
@keyframes fade { from { opacity: 0; } }
@keyframes rise { from { opacity: 0; transform: translateY(8px); } }
@keyframes grow-x { from { transform: scaleX(0); } }
@keyframes grow-y { from { transform: scaleY(0); } }
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; }
}
"""


class Face:
    """An outline font that turns strings into SVG path data."""

    def __init__(self, filename: str) -> None:
        self.font = TTFont(FONTS / filename)
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm
        self.hmtx = self.font["hmtx"]

    def _name(self, ch: str) -> str:
        return self.cmap.get(ord(ch), ".notdef")

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        """Return the advance width of text at size, in user units."""
        scale = size / self.upm
        total = sum(self.hmtx[self._name(ch)][0] * scale for ch in text)
        return total + tracking * size * max(len(text) - 1, 0)

    def path(self, text: str, size: float, x: float, y: float,
             tracking: float = 0.0) -> str:
        """Return SVG path data for text with its baseline at (x, y)."""
        scale = size / self.upm
        pen = SVGPathPen(self.glyphs, ntos=_num)
        cursor = x
        for ch in text:
            name = self._name(ch)
            self.glyphs[name].draw(
                TransformPen(pen, (scale, 0, 0, -scale, cursor, y)))
            cursor += self.hmtx[name][0] * scale + tracking * size
        return pen.getCommands()


def _num(value: float) -> str:
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


@lru_cache(maxsize=None)
def display() -> Face:
    """Return Familjen Grotesk SemiBold, for headlines and names."""
    return Face("FamiljenGrotesk-SemiBold.ttf")


@lru_cache(maxsize=None)
def label() -> Face:
    """Return Familjen Grotesk Medium, for dates, numbers and captions."""
    return Face("FamiljenGrotesk-Medium.ttf")


@dataclass
class Text:
    """A run of outlined text, placed by its anchor."""

    face: Face
    text: str
    size: float
    x: float
    y: float
    anchor: str = "start"
    cls: str = "ink"
    tracking: float = 0.0
    attrs: str = ""

    @property
    def width(self) -> float:
        """Return the rendered width."""
        return self.face.width(self.text, self.size, self.tracking)

    @property
    def left(self) -> float:
        """Return the x of the left edge after anchoring."""
        shift = {"start": 0.0, "middle": self.width / 2, "end": self.width}
        return self.x - shift[self.anchor]

    def svg(self) -> str:
        """Return a path element drawing the text."""
        d = self.face.path(self.text, self.size, self.left, self.y,
                           self.tracking)
        extra = f" {self.attrs}" if self.attrs else ""
        return f'<path class="{self.cls}"{extra} d="{d}"/>'


@dataclass
class Sheet:
    """An SVG document built for one theme."""

    height: int
    title: str
    theme: str
    css: str = ""
    body: list[str] = field(default_factory=list)
    width: int = WIDTH
    paper: bool = True

    def add(self, *parts: str) -> None:
        """Append raw SVG fragments."""
        self.body.extend(parts)

    def render(self) -> str:
        """Return the finished SVG text."""
        tokens = "; ".join(f"--{k}: {v}" for k, v in THEMES[self.theme].items())
        paper = (f'<rect class="paper" width="{self.width}" height="{self.height}" '
                 f'rx="{RADIUS}"/>') if self.paper else ""
        return "\n".join([
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" '
            f'height="{self.height}" viewBox="0 0 {self.width} {self.height}" '
            f'role="img" aria-labelledby="title">',
            f'<title id="title">{escape(self.title)}</title>',
            f"<style>:root {{ {tokens}; }}{BASE_CSS}{self.css}</style>",
            paper,
            *self.body,
            "</svg>",
            "",
        ])


def frame(width: float, height: float) -> str:
    """Return a hairline border that follows the sheet's rounded corners."""
    return (f'<rect class="line-2" x="0.5" y="0.5" width="{width - 1}" '
            f'height="{height - 1}" rx="{RADIUS - 0.5}"/>')


def write_pair(name: str, build: Callable[[str], Sheet]) -> list[Path]:
    """Write name-light.svg and name-dark.svg from one builder."""
    ASSETS.mkdir(exist_ok=True)
    written = []
    for theme in ("light", "dark"):
        out = ASSETS / f"{name}-{theme}.svg"
        out.write_text(build(theme).render(), encoding="utf-8")
        written.append(out)
    return written
