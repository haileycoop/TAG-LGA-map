# Working on the TAG Councils Map

Quick reference for local development and updating TAG Partner councils (adopters) before publishing.

## What this repo is

- **Static site**: `index.html` loads Leaflet, `data/geo/councils-au.geojson` (LGA boundaries), and `data/tag-adopters.json` (which councils count as TAG Partners).
- **No build step** for the web UI—edit HTML/JSON/data and refresh the browser.
- **Python** is optional day-to-day; use it for boundary rebuilds and adopters validation.

## Run a local dev server

From the **repository root** (the folder that contains `index.html`), serve files over HTTP so `fetch()` can load JSON and GeoJSON (opening `index.html` as a `file://` URL often breaks those requests).

```bash
cd "/path/to/TAG Councils Map"
python3 -m http.server 8000
```

Then open [http://localhost:8000](http://localhost:8000) (or [http://127.0.0.1:8000](http://127.0.0.1:8000)).

Use another port if 8000 is taken, e.g. `python3 -m http.server 8765`.

### If the map shows an error about missing GeoJSON

Boundaries live at `data/geo/councils-au.geojson`. If that file is missing, build it from ABS data:

```bash
python3 scripts/build_councils_au.py --download
```

(Python deps: see `requirements.txt`; a virtualenv under `.venv/` is fine.)

---

## TAG adopters: what gets edited

- **File**: `data/tag-adopters.json`
- **Shape**: JSON with `_meta` and an `adopters` array.
- **Values**: Each adopter must be a **5-digit ABS LGA code** (`LGA_CODE24` for ASGS 2024—the same `lgaCode` values used in the GeoJSON). The app does not use council names in this file anymore.

---

## Workflow: change adopters locally

You can do either (or both):

### 1. Edit the JSON directly

Add or remove strings in the `adopters` array, keeping valid 5-digit codes only.

### 2. Use the map UI (“Manage Partners”)

1. Open the app in **local admin mode** so export is enabled:
   - Serve from **localhost** or a **private LAN IP** (e.g. `192.168.x.x`), **or**
   - Append **`?admin=1`** to the URL if you need admin tools while not on localhost.
2. Switch to **Manage Partners**, toggle councils, then use **Export JSON** (or copy via the copy control). That downloads / copies JSON including `_meta` and the sorted `adopters` list.
3. **Replace** `data/tag-adopters.json` with the exported content (overwrite the file).

### Validate before you commit

```bash
python3 getLGAnames.py --validate
```

This checks every code exists in `data/geo/councils-au.geojson`, is five digits, and has no duplicates.

---

## Workflow: push changes live

There is **no** bundler or deploy script in this repo—the live site is whatever host serves this static tree (for example GitHub Pages, Netlify, or another static host).

Typical flow:

1. Confirm locally: map loads, partners look right, `python3 getLGAnames.py --validate` passes.
2. Commit the files you changed (often `data/tag-adopters.json`; sometimes `index.html` or GeoJSON).
3. **Push** to the branch your hosting uses (often `main`). The published site updates when that host redeploys or refreshes from Git.

If others use the **public** URL in “web shared mode”, they cannot export JSON to disk; they use **Request changes** to draft an email. Only local admin mode can write the adopters file via export—so **you** merge exported JSON (or hand-edits) and push.

---

## Optional: list LGAs or inspect codes

```bash
python3 getLGAnames.py              # tab-separated code / name from GeoJSON
python3 getLGAnames.py --state 2    # example: filter by state code
```

---

## Files worth remembering

| Path | Role |
|------|------|
| `index.html` | Map UI and logic |
| `data/tag-adopters.json` | TAG Partner LGA codes (source of truth for the map) |
| `data/geo/councils-au.geojson` | Council boundaries (built from ABS via `scripts/build_councils_au.py`) |
| `getLGAnames.py` | Validate adopters; print LGA rows |
| `scripts/build_councils_au.py` | Rebuild GeoJSON from ABS LGA 2024 boundaries |
