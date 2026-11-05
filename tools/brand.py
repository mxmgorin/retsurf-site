#!/usr/bin/env python3
"""Draws the site's brand art from the app's banner: the seam, the shorelines of the sand
band, and the hero's horizon as layers (sun, three sea tiles, surfer, and the 404 page's
wipeout), with brand.css that places and animates them. brand.css also carries the app's
themes, read from its palettes, so the site and the app share one set of colors.

    tools/brand.py [APP_DIR]    # default: ../retsurf

Each theme is a block of custom properties on `[data-theme]`: its colors, the sand band's,
the sun's height and its own copy of the art, recolored the way the app recolors its
banner (Night's colors swapped for the theme's) under images/brand/<theme>/. Dusk, the
app's default, is also the bare `:root`, and Sand stands in for it when the system asks
for light.

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

# The app's palettes, by their constants in its theme; the lowercase name is the
# theme's id, as the app spells it in its config.
THEMES = ["NIGHT", "OLED", "DUSK", "SAND", "DMG"]
# The art is drawn in SOURCE's colors and lives at images/brand/ itself, as the app's
# brand SVGs are drawn in Night's; DEFAULT is the page without a picked theme.
SOURCE, DEFAULT, AUTO_LIGHT = "NIGHT", "DUSK", "SAND"

# The app's colors the site shares: CSS property to the field of a palette.
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
# The sand band's colors: CSS property to the field of the Sand palette under a dark
# theme; a light theme draws the band in its own colors, from LIGHT_BAND.
SAND_PALETTE = {
    "bg": "surface",
    "surface": "key",
    "line": "border",
    "ink": "ink",
    "dim": "muted",
    "teal": "accent",
}
LIGHT_BAND = {
    "bg": "field",
    "surface": "key",
    "line": "border",
    "ink": "ink",
    "dim": "muted",
    "teal": "accent",
}
# Swapped for the theme's own in every SVG, as the app does in its banner.
RECOLORED = ["bg", "ink", "accent", "surf_warm", "deep_teal", "sun_top", "wave_mid", "border"]
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


def palettes(theme):
    """Reads the theme's palettes; returns each one's opaque colors as (r, g, b), its
    `sun_drop` and `light`, by field, under the palette's constant."""
    out = {}
    for name in THEMES:
        body = re.search(rf"const {name}: Palette = Palette \{{(.*?)\n\}};", theme, re.S).group(1)
        base = re.search(r"\.\.(\w+)\s*$", body)
        fields = dict(out[base.group(1)]) if base else {}
        for field, args in re.findall(r"(\w+): (?:egui::Color32::from_)?(?:rgb|gray)\(([^)]*)\),", body):
            channels = [int(x, 16) for x in re.findall(r"0x([0-9a-fA-F]{2})", args)]
            fields[field] = tuple(channels * 3 if len(channels) == 1 else channels)
        for field, named in re.findall(r"(\w+): egui::Color32::(BLACK|WHITE),", body):
            fields[field] = (0, 0, 0) if named == "BLACK" else (255, 255, 255)
        for field, value in re.findall(r"(sun_drop): (-?[\d.]+),", body):
            fields[field] = float(value)
        for field, value in re.findall(r"(light): (true|false),", body):
            fields[field] = value == "true"
        out[name] = fields
    return out


def recolor(svg, swaps):
    """`svg` with each `#rrggbb` in `swaps` replaced, in one pass."""
    return re.sub(r"#[0-9a-f]{6}", lambda m: swaps.get(m.group(0), m.group(0)), svg)


def sun_svg(drop, colors):
    """The icon's striped sun in its halo, `drop` diameters below its Night height and
    cut flat at the horizon; returns the SVG, its top and its height in the strip."""
    c = HALO_R
    center = SUN_Y + drop * 2 * R
    cut = min(2 * c, c + HORIZON - center)
    stripes = "".join(
        f'<rect y="{c + (y - ICON_SUN_Y) / ICON_SUN_R * R:.2f}" width="{2 * c}" height="{h / ICON_SUN_R * R:.2f}"/>'
        for y, h in ICON_STRIPES)
    teal, coral, top = colors
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{2 * c:g}" height="{cut:.1f}">
  <defs>
    <linearGradient id="sun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset="0.3" stop-color="{coral}"/><stop offset="1" stop-color="{teal}"/></linearGradient>
    <radialGradient id="halo"><stop offset="0.62" stop-color="{coral}" stop-opacity="0.22"/><stop offset="1" stop-color="{coral}" stop-opacity="0"/></radialGradient>
    <mask id="stripes"><rect width="{2 * c}" height="{2 * c}" fill="#fff"/><g fill="#000">{stripes}</g></mask>
  </defs>
  <circle cx="{c}" cy="{c}" r="{c}" fill="url(#halo)"/>
  <circle cx="{c}" cy="{c}" r="{R}" fill="url(#sun)" mask="url(#stripes)"/>
</svg>
'''
    return svg, center - c, cut


def hex_color(rgb):
    return "#" + "".join(f"{c:02x}" for c in rgb)


def write(name, text):
    with open(name, "w") as out:
        out.write(text)


def main():
    app = sys.argv[1] if len(sys.argv) > 1 else APP
    banner = open(os.path.join(app, BANNER)).read()
    pals = palettes(open(os.path.join(app, THEME)).read())
    night, sand = pals[SOURCE], pals["SAND"]
    TEAL, CORAL, LINE, SAND = (hex_color(c) for c in (night["accent"], night["surf_warm"], night["border"], sand["bg"]))

    # Night's art, in Night's colors; every other theme recolors it.
    art = {}
    seam = polyline(lambda x: SEAM_HEIGHT / 2 + SEAM_AMP * math.sin(2 * math.pi * x / SEAM_PERIOD), -4, SEAM_PERIOD + 4, 2)
    art["seam"] = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{SEAM_PERIOD}" height="{SEAM_HEIGHT}">'
                   f'<path d="{seam}" fill="none" stroke="{LINE}" stroke-width="1.5"/></svg>\n')

    # Shorelines: sand below the edge on the top one, above it on the bottom one.
    edge = lambda x: SHORE_HEIGHT / 2 + wave(x, SHORE_TILE, SHORE_PARTS)
    line = polyline(edge, -6, SHORE_TILE + 6, 2)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{SHORE_TILE}" height="{SHORE_HEIGHT}">'
    art["shore-top"] = (f'{svg}<path d="{line} V{SHORE_HEIGHT} H-6Z" fill="{SAND}"/>'
                        f'<path d="{line}" fill="none" stroke="{TEAL}" stroke-width="{FOAM}"/></svg>\n')
    art["shore-bottom"] = f'{svg}<path d="{line} V0 H-6Z" fill="{SAND}"/></svg>\n'

    css = [f'''/* Generated by tools/brand.py; edit that, not this. */

/* The sand band, in its theme's band colors. */
.band.sand {{
  --bg: var(--sand-bg);
  --surface: var(--sand-surface);
  --line: var(--sand-line);
  --ink: var(--sand-ink);
  --dim: var(--sand-dim);
  --teal: var(--sand-teal);
  --shore-h: {SHORE_HEIGHT}px;
}}
.sand::before {{ background: var(--art-shore-top) 0 100% repeat-x; }}
.sand::after {{ background: var(--art-shore-bottom) 0 0 repeat-x; }}

.hero {{
  --horizon-h: {HEIGHT}px;
  --sun-wide: {SUN_WIDE}px;
  --sun-narrow: {SUN_NARROW}px;
  --surfer-wide: {SURFER_WIDE}px;
  --surfer-narrow: {SURFER_NARROW}px;
}}

.sun {{
  top: var(--sun-top);
  width: {2 * HALO_R:g}px;
  height: var(--sun-h);
  margin-left: -{HALO_R:g}px;
  background: var(--art-sun) 0 0 / 100% 100% no-repeat;
}}
''']

    for name, y, stroke, opacity, tile, seconds, parts in WAVES:
        d = polyline(lambda x: y + wave(x, tile, parts), -6, tile + 6, 2)
        art[f"sea-{name}"] = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{tile}" height="{HEIGHT}">'
                              f'<path d="{d}" fill="none" stroke="{TEAL}" stroke-width="{stroke:.1f}" opacity="{opacity}"/></svg>\n')
        css.append(f'''
.sea-{name} {{
  left: -{tile}px;
  background: var(--art-sea-{name}) 50% 0 repeat-x;
  animation: sea-{name} {seconds}s linear infinite;
}}
@keyframes sea-{name} {{ to {{ transform: translateX({tile}px); }} }}
''')

    mascot = re.search(r'<g transform="translate\([\d. ]+\) rotate\([\d.]+\) scale\([\d.]+\)">(.*)</g>\s*</svg>', banner, re.S).group(1)
    bx, by, bw, bh = MASCOT_BOX
    box = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{bw * SURFER_SCALE:.1f}" height="{bh * SURFER_SCALE:.1f}" '
           f'viewBox="{bx} {by} {bw} {bh}">')
    art["surfer"] = f"{box}{mascot}</svg>\n"
    board, body = re.match(r"\s*(<ellipse[^>]*/>)(.*)", mascot, re.S).groups()
    art["board"] = f'{box}<g transform="rotate({WIPEOUT_TILT} 0 -3.2)">{board}</g></svg>\n'
    art["legs"] = f'{box}<g transform="{LEGS_UP}">{body}</g></svg>\n'

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
  background: var(--art-surfer) 0 0 / 100% 100% no-repeat;
  animation: surf {fseconds}s linear infinite;
}}
@keyframes surf {{
{frames}
}}

.board {{ background-image: var(--art-board); }}
/* The front wave meets a point behind the surfer this much sooner. */
.legs {{
  margin-left: {bx * SURFER_SCALE - WIPEOUT_GAP:.1f}px;
  background-image: var(--art-legs);
  animation-delay: -{fseconds * WIPEOUT_GAP / ftile:.3f}s;
}}
''')

    # The default first: its `:root` would outweigh a picked theme's block coming before it.
    for name in [DEFAULT, *(t for t in THEMES if t != DEFAULT)]:
        p = pals[name]
        theme_id = name.lower()
        folder = "" if name == SOURCE else f"{theme_id}/"
        os.makedirs(os.path.join(ART, folder), exist_ok=True)
        band_from, band_map = (p, LIGHT_BAND) if p["light"] else (sand, SAND_PALETTE)
        band_color = p["surface"] if p["light"] else sand["bg"]
        swaps = {hex_color(night[f]): hex_color(p[f]) for f in RECOLORED}
        swaps[SAND] = hex_color(band_color)
        sun, sun_top, sun_h = sun_svg(p["sun_drop"], (TEAL, CORAL, hex_color(night["sun_top"])))
        for key, svg in {**art, "sun": sun}.items():
            write(os.path.join(ART, folder, f"{key}.svg"), recolor(svg, swaps))

        shared = {prop: p[field] for prop, field in PALETTE.items()}
        hover = tuple(round(c + (255 - c) * HOVER_LIGHTEN) for c in shared["teal"])
        # The alternating band: halfway from the page to its surfaces.
        band = tuple((a + b) // 2 for a, b in zip(p["bg"], p["surface"]))
        props = [f"color-scheme: {'light' if p['light'] else 'dark'}"]
        props += [f"--{prop}: {hex_color(rgb)}" for prop, rgb in shared.items()]
        props += [f"--{prop}-rgb: {', '.join(map(str, shared[prop]))}" for prop in TRANSLUCENT]
        props += [f"--teal-hover: {hex_color(hover)}", f"--band: {hex_color(band)}", f"--sand: {hex_color(band_color)}"]
        props += [f"--sand-{prop}: {hex_color(band_from[field])}" for prop, field in band_map.items()]
        props += [f"--sun-y: {SUN_Y + p['sun_drop'] * 2 * R:g}px", f"--sun-top: {sun_top:.2f}px", f"--sun-h: {sun_h:.1f}px"]
        props += [f'--art-{key}: url("images/brand/{folder}{key}.svg")' for key in ["sun", *art]]
        body = "".join(f"  {line};\n" for line in props)
        selector = f':root,\n[data-theme="{theme_id}"]' if name == DEFAULT else f'[data-theme="{theme_id}"]'
        css.append(f"\n/* The app's `{theme_id}` theme. */\n{selector} {{\n{body}}}\n")
        if name == AUTO_LIGHT:
            nested = "".join(f"    {line};\n" for line in props)
            css.append(f"@media (prefers-color-scheme: light) {{\n  :root:not([data-theme]) {{\n{nested}  }}\n}}\n")
    write(CSS, "".join(css))


if __name__ == "__main__":
    main()
