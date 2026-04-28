#!/usr/bin/env python3
"""
One-off migration: replace human-readable LGA names in data/tag-adopters.json
with ABS LGA 5-digit codes (ASGS 2024 / shapefile LGA_CODE24), using Victoria
features only for name resolution.

Matching rule: strip common council suffixes from the adopter string, then
case-insensitive match to LGA_NAME24 for rows where stateCode == '2'.

After migration, edit data/tag-adopters.json by LGA code only.

Requires the same ABS shapefile as scripts/build_councils_au.py (run --download there first).

  python3 scripts/migrate_adopters_to_lga_codes.py --write
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SHP = os.path.join(REPO_ROOT, "build", "abs", "LGA_2024_AUST_GDA2020.shp")
ADOPTERS_PATH = os.path.join(REPO_ROOT, "data", "tag-adopters.json")

SUFFIXES = (
    " City",
    " Shire",
    " Rural City",
    " Municipal Council",
    " Regional Council",
    " Borough",
    " Council",
)

CODE_RE = re.compile(r"^\d{5}$")


def strip_suffixes(name: str) -> str:
    s = name.strip()
    changed = True
    while changed:
        changed = False
        for suf in SUFFIXES:
            if s.endswith(suf):
                s = s[: -len(suf)].strip()
                changed = True
    return s


def load_vic_lga_index(shp_path: str) -> dict[str, tuple[str, str]]:
    import geopandas as gpd

    gdf = gpd.read_file(shp_path)
    vic = gdf[gdf["STE_CODE21"] == "2"].copy()
    # casefold(LGA_NAME24) -> (lgaCode, lgaName as in ABS)
    by_name_cf: dict[str, tuple[str, str]] = {}
    for _, row in vic.iterrows():
        code = str(row["LGA_CODE24"])
        nm = str(row["LGA_NAME24"])
        key = nm.casefold()
        if key in by_name_cf:
            raise SystemExit(f"Duplicate LGA_NAME24 in VIC data: {nm}")
        by_name_cf[key] = (code, nm)
    return by_name_cf


def name_to_code(name: str, by_name_cf: dict[str, tuple[str, str]]) -> tuple[str, str]:
    """Return (lgaCode, matchedAbsName)."""
    n = name.strip()
    k = n.casefold()
    if k in by_name_cf:
        return by_name_cf[k]
    stripped = strip_suffixes(n)
    k2 = stripped.casefold()
    if k2 in by_name_cf:
        return by_name_cf[k2]
    raise ValueError(f'No VIC LGA match for "{name}" (tried exact and stripped="{stripped}")')


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate tag-adopters.json from names to LGA codes.")
    parser.add_argument("--input-shp", default=DEFAULT_SHP, help="ABS LGA 2024 shapefile path")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write data/tag-adopters.json (otherwise dry-run print only)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input_shp):
        print(f"Missing shapefile: {args.input_shp}\nRun: python3 scripts/build_councils_au.py --download", file=sys.stderr)
        sys.exit(1)

    with open(ADOPTERS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    adopters = data.get("adopters")
    if not isinstance(adopters, list):
        print('Expected "adopters" array in tag-adopters.json', file=sys.stderr)
        sys.exit(1)

    if adopters and all(CODE_RE.match(str(a)) for a in adopters):
        print("Adopters already look like LGA codes; nothing to do.")
        return

    by_name_cf = load_vic_lga_index(args.input_shp)
    codes: list[str] = []
    for a in adopters:
        a = str(a).strip()
        if CODE_RE.match(a):
            codes.append(a)
            continue
        code, abs_nm = name_to_code(a, by_name_cf)
        print(f"  {a!r} -> {code} ({abs_nm})")
        codes.append(code)

    out = {
        "_meta": {
            "schema": "lgaCode",
            "asgsYear": 2024,
            "datum": "GDA2020",
            "note": "Each entry is an ABS LGA_CODE24 (5 digits). Add councils from any state using the same codes.",
        },
        "adopters": codes,
    }

    if args.write:
        with open(ADOPTERS_PATH, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
            f.write("\n")
        print(f"Wrote {ADOPTERS_PATH} with {len(codes)} codes")
    else:
        print("Dry run only. Pass --write to update tag-adopters.json")


if __name__ == "__main__":
    main()
