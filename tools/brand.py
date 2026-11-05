#!/usr/bin/env python3
"""Draws the site's brand art from the app's banner: the seam, the shorelines of the sand
band, and the hero's horizon as layers (sun, three sea tiles, surfer, and the 404 page's
wipeout), with brand.css that places and animates them. brand.css also carries the app's
palettes, read from its theme: Night for the page, Sand for the sand band, so the site
and the app share one set of colors.

    tools/brand.py [APP_DIR]    # default: ../retsurf

Each sea layer is one tile wide and scrolls right by exactly one tile per cycle, so it
loops without a seam. The surfer stays put and rides the front wave: its keyframes sample
that wave's height and slope under it over one cycle. Tiles are anchored to the page
center, so the surfer's offset from the center fixes its phase; the narrow layout's
offset is the wide one less a whole tile, so one set of keyframes serves both.
"""

import math
import os
import re
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(SITE, "..", "retsurf")
BANNER = os.path.join("resources", "retsurf-banner-bare.svg")
THEME = os.path.join("src", "ui", "theme.rs")
ART = os.path.join(SITE, "images", "brand")
CSS = os.path.join(SITE, "brand.css")

# The app's colors the site shares: CSS property to the field of the theme's Night palette.
PALETTE = {
    "bg": "bg",
    "surface": "surface",
    "line": "border",
    "keycap": "hairline",
    "ink": "ink",
    "dim": "muted",
    "teal": "accent",
    "coral": "surf_warm",
}
# The sand band's colors: CSS property to the field of the theme's Sand palette.
SAND_PALETTE = {
    "bg": "surface",
    "surface": "key",
    "line": "border",
    "ink": "ink",
    "dim": "muted",
    "teal": "accent",
}
# Those the site also draws translucent: they get an `-rgb` property of bare channels.
TRANSLUCENT = ["bg", "teal", "coral"]
# The primary button's hover: the accent mixed this far toward white.
HOVER_LIGHTEN = 0.12

# The icon's sun, at the icon's own scale: center, radius, halo radius and the stripes
# (top, height) its mask cuts.
ICON_SUN_Y, ICON_SUN_R, ICON_HALO_R = 218, 128, 200
ICON_STRIPES = [(240, 7), (264, 10), (293, 14), (327, 19)]

# The horizon scales from the sun's radius; the ratios follow the banner.
R = 60
SUN_Y = 96
HALO_R = R * ICON_HALO_R / ICON_SUN_R
HORIZON = SUN_Y + 0.67 * R

# Sea layers, back to front: center line, stroke, opacity, tile width, seconds per tile,
# and the sines summed into the wave as (amplitude, harmonics per tile, phase).
WAVES = [
    ("back", HORIZON, 0.10 * R, 0.4, 216, 30, [(3, 2, 0.0), (1.2, 3, 1.3)]),
    ("mid", HORIZON + 0.39 * R, 0.125 * R, 0.7, 336, 20, [(8, 2, 0.7), (2, 4, 2.1)]),
    ("front", HORIZON + 0.8 * R, 0.156 * R, 1.0, 215, 9, [(11, 1, 0.3), (2, 2, 1.0)]),
]
HEIGHT = math.ceil(WAVES[-1][1] + sum(a for a, _, _ in WAVES[-1][6]) + WAVES[-1][2] / 2 + 6)

# Offsets from the page center: the sun under the text column, the surfer under the
# photo; narrow, both on a phone.
SUN_WIDE, SUN_NARROW = -420, -110
SURFER_WIDE = 330
SURFER_NARROW = SURFER_WIDE - WAVES[-1][4]

# Surfer: its scale over the banner's, the board's sink into the wave, the share of the
# wave's slope it leans with, and the keyframes per cycle.
SURFER_SCALE = 1.5 * R / 22 * 0.65
SURFER_SINK = 2
SURFER_LEAN = 0.7
SURFER_FRAMES = 36
# The mascot's box in its own units: its origin sits under the board's center.
MASCOT_BOX = (-15, -29, 32, 29)
BOARD_BOTTOM = -1.4

# Wipeout: the board drifts on alone, tossed by this tilt, and the mascot's legs stick out
# of the water this far behind it. Below the box's bottom is under water: the box cuts it.
WIPEOUT_TILT = -18
WIPEOUT_GAP = 60
# Flips the mascot head down: its hips and the edge of its body clear the waterline.
LEGS_UP = "translate(0 -17.5) rotate(180) rotate(-12 0 -12.7)"

SEAM_PERIOD, SEAM_HEIGHT, SEAM_AMP = 96, 10, 2.5

# Shoreline tile: its width, height, and the sines of its edge; the sea's foam on the top one.
SHORE_TILE, SHORE_HEIGHT = 240, 20
SHORE_PARTS = [(3.5, 1, 0.0), (1.5, 3, 0.8)]
FOAM = 2


def wave(x, tile, parts):
    return sum(a * math.sin(2 * math.pi * k * x / tile + ph) for a, k, ph in parts)


def slope(x, tile, parts):
    return sum(a * 2 * math.pi * k / tile * math.cos(2 * math.pi * k * x / tile + ph) for a, k, ph in parts)


def polyline(f, x0, x1, step):
    return "M" + " L".join(f"{x} {f(x):.2f}" for x in range(x0, x1 + 1, step))


def palette(theme, name):
    """Reads the theme's palette `name`; returns each opaque field's (r, g, b) by name."""
    body = re.search(rf"const {name}: Palette = Palette \{{(.*?)\n\}};", theme, re.S).group(1)
    colors = {}
    for name, args in re.findall(r"(\w+): (?:egui::Color32::from_)?(?:rgb|gray)\(([^)]*)\),", body):
        channels = [int(x, 16) for x in re.findall(r"0x([0-9a-fA-F]{2})", args)]
        colors[name] = tuple(channels * 3 if len(channels) == 1 else channels)
    return colors


def hex_color(rgb):
    return "#" + "".join(f"{c:02x}" for c in rgb)


def write(name, text):
    with open(name, "w") as out:
        out.write(text)


def main():
    app = sys.argv[1] if len(sys.argv) > 1 else APP
    banner = open(os.path.join(app, BANNER)).read()
    theme = open(os.path.join(app, THEME)).read()
    night, sand = palette(theme, "NIGHT"), palette(theme, "SAND")
    shared = {prop: night[field] for prop, field in PALETTE.items()}
    SAND = hex_color(sand["bg"])
    TEAL, CORAL, LINE = (hex_color(shared[p]) for p in ("teal", "coral", "line"))
    hover = tuple(round(c + (255 - c) * HOVER_LIGHTEN) for c in shared["teal"])
    os.makedirs(ART, exist_ok=True)

    seam = polyline(lambda x: SEAM_HEIGHT / 2 + SEAM_AMP * math.sin(2 * math.pi * x / SEAM_PERIOD), -4, SEAM_PERIOD + 4, 2)
    write(os.path.join(ART, "seam.svg"),
          f'<svg xmlns="http://www.w3.org/2000/svg" width="{SEAM_PERIOD}" height="{SEAM_HEIGHT}">'
          f'<path d="{seam}" fill="none" stroke="{LINE}" stroke-width="1.5"/></svg>\n')

    # Shorelines: sand below the edge on the top one, above it on the bottom one.
    edge = lambda x: SHORE_HEIGHT / 2 + wave(x, SHORE_TILE, SHORE_PARTS)
    line = polyline(edge, -6, SHORE_TILE + 6, 2)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{SHORE_TILE}" height="{SHORE_HEIGHT}">'
    write(os.path.join(ART, "shore-top.svg"),
          f'{svg}<path d="{line} V{SHORE_HEIGHT} H-6Z" fill="{SAND}"/>'
          f'<path d="{line}" fill="none" stroke="{TEAL}" stroke-width="{FOAM}"/></svg>\n')
    write(os.path.join(ART, "shore-bottom.svg"), f'{svg}<path d="{line} V0 H-6Z" fill="{SAND}"/></svg>\n')

    # Sun: the icon's striped disc in its halo, cut flat at the horizon.
    c = HALO_R
    cut = c + HORIZON - SUN_Y
    stripes = "".join(
        f'<rect y="{c + (y - ICON_SUN_Y) / ICON_SUN_R * R:.2f}" width="{2 * c}" height="{h / ICON_SUN_R * R:.2f}"/>'
        for y, h in ICON_STRIPES)
    write(os.path.join(ART, "sun.svg"), f'''<svg xmlns="http://www.w3.org/2000/svg" width="{2 * c:g}" height="{cut:.1f}">
  <defs>
    <linearGradient id="sun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffb870"/><stop offset="0.3" stop-color="{CORAL}"/><stop offset="1" stop-color="{TEAL}"/></linearGradient>
    <radialGradient id="halo"><stop offset="0.62" stop-color="{CORAL}" stop-opacity="0.22"/><stop offset="1" stop-color="{CORAL}" stop-opacity="0"/></radialGradient>
    <mask id="stripes"><rect width="{2 * c}" height="{2 * c}" fill="#fff"/><g fill="#000">{stripes}</g></mask>
  </defs>
  <circle cx="{c}" cy="{c}" r="{c}" fill="url(#halo)"/>
  <circle cx="{c}" cy="{c}" r="{R}" fill="url(#sun)" mask="url(#stripes)"/>
</svg>
''')

    props = "".join(f"  --{p}: {hex_color(rgb)};\n" for p, rgb in shared.items())
    sand_props = "".join(f"  --{p}: {hex_color(sand[field])};\n" for p, field in SAND_PALETTE.items())
    props += "".join(f"  --{p}-rgb: {', '.join(map(str, shared[p]))};\n" for p in TRANSLUCENT)
    css = [f'''/* Generated by tools/brand.py; edit that, not this. */

/* The app's palette, from its theme. */
:root {{
{props}  --teal-hover: {hex_color(hover)};
}}

:root {{
  --sand: {SAND};
  --shore-h: {SHORE_HEIGHT}px;
}}

/* The app's Sand palette, for the components inside the sand band. */
.band.sand {{
{sand_props}}}
.sand::before {{ background: url("images/brand/shore-top.svg") 0 100% repeat-x; }}
.sand::after {{ background: url("images/brand/shore-bottom.svg") 0 0 repeat-x; }}

.hero {{
  --horizon-h: {HEIGHT}px;
  --sun-y: {SUN_Y}px;
  --sun-wide: {SUN_WIDE}px;
  --sun-narrow: {SUN_NARROW}px;
  --surfer-wide: {SURFER_WIDE}px;
  --surfer-narrow: {SURFER_NARROW}px;
}}

.sun {{
  top: {SUN_Y - c:.2f}px;
  width: {2 * c:g}px;
  height: {cut:.1f}px;
  margin-left: -{c:g}px;
  background: url("images/brand/sun.svg") 0 0 / 100% 100% no-repeat;
}}
''']

    for name, y, stroke, opacity, tile, seconds, parts in WAVES:
        d = polyline(lambda x: y + wave(x, tile, parts), -6, tile + 6, 2)
        write(os.path.join(ART, f"sea-{name}.svg"),
              f'<svg xmlns="http://www.w3.org/2000/svg" width="{tile}" height="{HEIGHT}">'
              f'<path d="{d}" fill="none" stroke="{TEAL}" stroke-width="{stroke:.1f}" opacity="{opacity}"/></svg>\n')
        css.append(f'''
.sea-{name} {{
  left: -{tile}px;
  background: url("images/brand/sea-{name}.svg") 50% 0 repeat-x;
  animation: sea-{name} {seconds}s linear infinite;
}}
@keyframes sea-{name} {{ to {{ transform: translateX({tile}px); }} }}
''')

    mascot = re.search(r'<g transform="translate\([\d. ]+\) rotate\([\d.]+\) scale\([\d.]+\)">(.*)</g>\s*</svg>', banner, re.S).group(1)
    bx, by, bw, bh = MASCOT_BOX
    box = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{bw * SURFER_SCALE:.1f}" height="{bh * SURFER_SCALE:.1f}" '
           f'viewBox="{bx} {by} {bw} {bh}">')
    write(os.path.join(ART, "surfer.svg"), f"{box}{mascot}</svg>\n")
    board, body = re.match(r"\s*(<ellipse[^>]*/>)(.*)", mascot, re.S).groups()
    write(os.path.join(ART, "board.svg"), f'{box}<g transform="rotate({WIPEOUT_TILT} 0 -3.2)">{board}</g></svg>\n')
    write(os.path.join(ART, "legs.svg"), f'{box}<g transform="{LEGS_UP}">{body}</g></svg>\n')

    _, fy, fstroke, _, ftile, fseconds, fparts = WAVES[-1]
    rest = fy - fstroke / 2 + SURFER_SINK - BOARD_BOTTOM * SURFER_SCALE

    def pose(u):
        x = (SURFER_WIDE - ftile * u) % ftile
        lean = math.degrees(math.atan(slope(x, ftile, fparts))) * SURFER_LEAN
        return f"translateY({wave(x, ftile, fparts):.2f}px) rotate({lean:.2f}deg)"

    frames = "\n".join(f"  {100 * i / SURFER_FRAMES:.2f}% {{ transform: {pose(i / SURFER_FRAMES)}; }}"
                       for i in range(SURFER_FRAMES + 1))
    css.append(f'''
.surfer {{
  top: {rest - bh * SURFER_SCALE:.2f}px;
  width: {bw * SURFER_SCALE:.1f}px;
  height: {bh * SURFER_SCALE:.1f}px;
  margin-left: {bx * SURFER_SCALE:.1f}px;
  transform-origin: {-bx * SURFER_SCALE:.1f}px 100%;
  transform: {pose(0)};
  background: url("images/brand/surfer.svg") 0 0 / 100% 100% no-repeat;
  animation: surf {fseconds}s linear infinite;
}}
@keyframes surf {{
{frames}
}}

.board {{ background-image: url("images/brand/board.svg"); }}
/* The front wave meets a point behind the surfer this much sooner. */
.legs {{
  margin-left: {bx * SURFER_SCALE - WIPEOUT_GAP:.1f}px;
  background-image: url("images/brand/legs.svg");
  animation-delay: -{fseconds * WIPEOUT_GAP / ftile:.3f}s;
}}
''')
    write(CSS, "".join(css))


if __name__ == "__main__":
    main()
