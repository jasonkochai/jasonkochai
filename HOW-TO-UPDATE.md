# How to update the profile

## Add or change a project

1. Open `projects.yml` and add an entry (copy an existing one):
   - `group: own` for your own work, `group: "42"` for 42 Berlin.
   - `status: shipped`, `building` or `paused`. Your own work goes into the What I'm building table, shipped first. The last row, **More soon**, is fixed (`MORE_ROW` in `scripts/build_readme.py`).
   - `one_liner`: what it does plus the interesting technical bit. No em dashes, no middle dots, no "passionate" or "seamless". The build fails on those.
   - `links`: `Label: https://...`, in the order they should show. A shipped project needs at least one.
   - `image` (optional): `light`, `dark` and `alt` for a drawing or screenshot in `assets/`.
2. Push to `main`. The **readme** workflow rewrites the project tables in `README.md` and commits the result.
3. Juniper's diagram lives in the private repo `jasonkochai/juniper`. When you make that repo public, add `Code: https://github.com/jasonkochai/juniper` under its `links`.

To preview locally:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python scripts/build_readme.py
```

`--check` only reports whether the README is out of date or breaks a rule.

## Stats

The **stats** workflow runs every night at 03:17 UTC. It fetches your numbers, redraws `assets/stats-*.svg` and `assets/activity-*.svg`, and moves the "now" dot on the 42 Berlin progress line.

It needs one secret, set once:

1. GitHub → Settings → Developer settings → Fine-grained tokens → Generate new token.
   - Repository access: **All repositories**.
   - Permissions: **Metadata: read** (the default) and **Contents: read**.
2. In this repo: Settings → Secrets and variables → Actions → New repository secret. Name it `STATS_TOKEN` and paste the token.

Without the secret the workflow keeps the last committed stats. If the nightly numbers come out lower than a local run, the token can't see private contributions. Use a classic token with `repo` and `read:user` instead.

Locally, `scripts/stats.py` uses your `gh` login. `stats.yml` lists the repos left out of the language bar (templates, generated pages).

## Text that changes by hand

- **Intro, What I learned, links, stack:** edit `README.md` directly, outside the `<!-- projects:... -->` markers.
- **42 Berlin dates** (42 Berlin, 05/2026 to 10/2027): `START` and `FINISH` in `scripts/build_svgs.py`. Then run `.venv/bin/python scripts/build_svgs.py`.

## Look

Brand colours from the profile photo: studio navy and the taupe of the shirt, the same as the X and YouTube banners.
- Navy cards in dark mode, a light blue-grey card in light mode, taupe as the only accent.
- Familjen Grotesk for everything (OFL, in `scripts/fonts/`). Text inside the SVGs is outlined from the font, so it renders the same everywhere.
- The header strikes through "the clean way" and brings in "the real way.". Your 42 Berlin progress is a thin line at the top of the 42 Berlin section.
- The header card is cut off at a slant over a taupe band and a thin chalk line; the band draws in like the strike-through and a glint keeps sliding along it. The footer mirrors the cut on its top edge and strikes "the end" for "to be continued.". Slant: `RISE` in `scripts/build_svgs.py`.
- Stats, activity and the 42 Berlin line are drawn on a wider canvas (`WIDE` in `scripts/svg.py`), so they fill the README width but render smaller. Raise `WIDE` to shrink them further.

Colours live as tokens in `THEMES` in `scripts/svg.py`. Every animation stops under "reduce motion".

## Widgets

- **Typing line** under the header: edit the `lines=` part of its URL in `README.md`. Sentences are separated by `;`, spaces are `+`, a comma is `%2C`.
- **Badges and stack:** plain `<img>` tags in `README.md` (shields.io and skillicons.dev).
- **Snake:** the **snake** workflow redraws it every night onto the `output` branch. Run it once by hand (Actions, snake, Run workflow) after the first push.

The language bar shows the languages in `language_order` (in `stats.yml`) first, then the rest by size, with other last.
