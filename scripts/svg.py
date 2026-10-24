"""Shared drawing kit for the profile SVGs: theme tokens, outlined text, keylines."""

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

# Hallmark Blueprint: cyanotype sheet for dark, whiteprint sheet for light.
# Hex values are the theme's OKLCH tokens converted to sRGB.
THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "paper": "#0d3970",
        "paper-2": "#062f61",
        "paper-3": "#012352",
        "ink": "#eef6fd",
        "ink-2": "#d0e1ee",
        "muted": "#a6c2d9",
        "rule": "rgba(220, 234, 244, 0.85)",
        "rule-2": "rgba(220, 234, 244, 0.32)",
        "grid": "rgba(238, 246, 253, 0.09)",
        "grid-2": "rgba(238, 246, 253, 0.2)",
    },
    "light": {
        "paper": "#f3f7fa",
        "paper-2": "#e7eef3",
        "paper-3": "#dce6ee",
        "ink": "#0d3970",
        "ink-2": "#1f4a80",
        "muted": "#4d6b91",
        "rule": "rgba(13, 57, 112, 0.85)",
        "rule-2": "rgba(13, 57, 112, 0.32)",
        "grid": "rgba(13, 57, 112, 0.07)",
        "grid-2": "rgba(13, 57, 112, 0.16)",
    },
}

SHEETS = {"light": "whiteprint", "dark": "cyanotype"}

STAMP = (
    "/* Hallmark \u00b7 shape: profile README, drawing set \u00b7 genre: modern-minimal"
    " \u00b7 theme: Blueprint (deal 1/3) \u00b7 blueprint: {sheet} \u00b7 job: hire\n"
    " * signature: the title block over the 42 Berlin dimension string"
    " \u00b7 imagery: drawings of real data, no photographs\n"
    " * axes: mid/geometric-sans/neutral \u00b7 posture: drenched"
    " \u00b7 contrast: pass \u00b7 v2.0.0 */\n"
    "/* Hallmark \u00b7 pre-emit critique: P4 H4 E4 S5 R4 V5 \u00b7 weakest: P,"
    " the drawing look could turn into costume; every line, end and label"
    " carries a real fact */\n"
)

BASE_CSS = """
.paper { fill: var(--paper); }
.paper-2 { fill: var(--paper-2); }
.ink { fill: var(--ink); }
.muted { fill: var(--muted); }
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
    """Return Chakra Petch SemiBold, the drafted capitals."""
    return Face("ChakraPetch-SemiBold.ttf")


@lru_cache(maxsize=None)
def mono() -> Face:
    """Return IBM Plex Mono Medium, for dates and measurements."""
    return Face("IBMPlexMono-Medium.ttf")


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

    def add(self, *parts: str) -> None:
        """Append raw SVG fragments."""
        self.body.extend(parts)

    def render(self) -> str:
        """Return the finished SVG text."""
        tokens = "; ".join(f"--{k}: {v}" for k, v in THEMES[self.theme].items())
        return "\n".join([
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
            f'height="{self.height}" viewBox="0 0 {WIDTH} {self.height}" '
            f'role="img" aria-labelledby="title">',
            f'<title id="title">{escape(self.title)}</title>',
            "<style>" + STAMP.format(sheet=SHEETS[self.theme])
            + f":root {{ {tokens}; }}{BASE_CSS}{self.css}</style>",
            f'<rect class="paper" width="{WIDTH}" height="{self.height}"/>',
            *self.body,
            "</svg>",
            "",
        ])


def keylines(width: float, height: float, cls: str = "line draw",
             style: str = "") -> str:
    """Return the sheet's double keyline: an outer rule and one 5px inside."""
    def frame(inset: float, klass: str) -> str:
        x0, y0 = inset + 0.5, inset + 0.5
        x1, y1 = width - inset - 0.5, height - inset - 0.5
        d = f"M{x0} {y0}H{x1}V{y1}H{x0}Z"
        st = f' style="{style}"' if style else ""
        return f'<path class="{klass}" pathLength="1"{st} d="{d}"/>'

    return frame(8, cls) + frame(13, cls.replace("line", "line-2"))


def dimension(x0: float, x1: float, y: float, tick: float = 14,
              cls: str = "line", attrs: str = "") -> str:
    """Return a dimension string: a hairline with 45 degree ticks at both ends."""
    h = tick / 2
    extra = f" {attrs}" if attrs else ""
    return (
        f'<g class="{cls}"{extra}>'
        f'<path d="M{x0} {y}H{x1}"/>'
        f'<path d="M{x0 - h} {y + h}L{x0 + h} {y - h}M{x1 - h} {y + h}L{x1 + h} {y - h}"/>'
        f'<path d="M{x0} {y - tick}V{y + tick}M{x1} {y - tick}V{y + tick}"/>'
        "</g>"
    )


def write_pair(name: str, build: Callable[[str], Sheet]) -> list[Path]:
    """Write name-light.svg and name-dark.svg from one builder."""
    ASSETS.mkdir(exist_ok=True)
    written = []
    for theme in ("light", "dark"):
        out = ASSETS / f"{name}-{theme}.svg"
        out.write_text(build(theme).render(), encoding="utf-8")
        written.append(out)
    return written
