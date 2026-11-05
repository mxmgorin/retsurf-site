# retsurf-site

Source of [retsurf.app](https://retsurf.app/), the landing page for [retsurf](https://github.com/mxmgorin/retsurf).

The site is self-contained: images, videos, fonts and the logo live here, and a push to `main`
deploys it. `tools/brand.py` redraws the hero's horizon, the shorelines and the section seam, with
`brand.css`, from the app's banner in `../retsurf`; `brand.css` also carries the app's
themes (Dusk by default, Night, OLED, Sand, DMG), which the header's theme menu switches. `images/retsurf-og.png`, the link preview,
is a 1200x630 screenshot of `tools/og.html`.

Copyright (C) 2025-2026 Maxim Gorin. All rights reserved. The retsurf app is licensed
separately under GPL-3.0-or-later.
