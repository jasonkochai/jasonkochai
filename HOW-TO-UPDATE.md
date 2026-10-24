# How to update the profile

## Add or change a project

1. Open `projects.yml` and add an entry (copy an existing one):
   - `group: own` for your own work, `group: "42"` for 42 Berlin.
   - `status: shipped`, `building` or `paused`. Your own shipped work shows up under **Shipped** at the top of Projects; building and paused go under **On the bench** with their status.
   - `one_liner`: what it does plus the interesting technical bit. No em dashes, no middle dots, no "passionate" or "seamless". The build fails on those.
   - `links`: `Label: https://...`, in the order they should show. A shipped project needs at least one.
   - `image` (optional): `light`, `dark` and `alt` for a drawing or screenshot in `assets/`.
2. Push to `main`. The **readme** workflow rewrites the project tables in `README.md` and commits the result.
3. When Juniper gets its public repo, add `Code: https://github.com/jasonkochai/<repo>` under its `links`, and switch its `status` when it ships.

To preview locally:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python scripts/build_readme.py
```

`--check` only reports whether the README is out of date or breaks a rule.

## Stats

The **stats** workflow runs every night at 03:17 UTC. It fetches your numbers, redraws `assets/stats-*.svg` and `assets/activity-*.svg`, and moves the "now" marker in the header.

It needs one secret, set once:

1. GitHub → Settings → Developer settings → Fine-grained tokens → Generate new token.
   - Repository access: **All repositories**.
   - Permissions: **Metadata: read** (the default) and **Contents: read**.
2. In this repo: Settings → Secrets and variables → Actions → New repository secret. Name it `STATS_TOKEN` and paste the token.

Without the secret the workflow keeps the last committed stats. If the nightly numbers come out lower than a local run, the token can't see private contributions. Use a classic token with `repo` and `read:user` instead.

Locally, `scripts/stats.py` uses your `gh` login. `stats.yml` lists the repos left out of the language bar (templates, generated pages).

## Text that changes by hand

- **Age, intro, interests, Works with, Path:** edit `README.md` directly, outside the `<!-- projects:... -->` markers.
- **Header dates** (42 Berlin, 05/2026 to 10/2027): `START` and `FINISH` in `scripts/build_svgs.py`. Then run `.venv/bin/python scripts/build_svgs.py`.
- **Juniper drawing:** `TOPICS` and `TOOLS` in `scripts/build_svgs.py`.

## Look

The design is hallmark's Blueprint theme:
- Whiteprint sheet in light mode, cyanotype in dark.
- Chakra Petch for drafted heads, IBM Plex Mono for dates.
- One hue, square keylines, no second colour.

Colours live as tokens in `THEMES` in `scripts/svg.py`. Text inside the SVGs is outlined from the fonts in `scripts/fonts/` (OFL), so it renders the same everywhere. Every animation stops under "reduce motion".
