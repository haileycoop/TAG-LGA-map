#!/usr/bin/env python3
"""
Helpers for ABS ASGS LGA GeoJSON used by the TAG Councils map.

GeoJSON path: data/geo/councils-au.geojson (properties: lgaCode, lgaName, stateCode, …)
TAG adopters: data/tag-adopters.json — "adopters" must be a list of 5-digit ABS LGA codes
(LGA_CODE24 for ASGS 2024 / build script output).

Build boundaries: python3 scripts/build_councils_au.py --download
Validate: python3 getLGAnames.py --validate
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
GEOJSON_PATH = os.path.join(script_dir, "data", "geo", "councils-au.geojson")
ADOPTERS_PATH = os.path.join(script_dir, "data", "tag-adopters.json")

CODE_RE = re.compile(r"^\d{5}$")


def load_geojson():
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_adopters():
    with open(ADOPTERS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    adopters = data.get("adopters")
    if not isinstance(adopters, list):
        raise ValueError('tag-adopters.json must contain a list in "adopters"')
    return adopters


def print_lga_rows(state_filter: str | None):
    geojson_data = load_geojson()
    for feature in geojson_data["features"]:
        props = feature.get("properties") or {}
        code = props.get("lgaCode")
        name = props.get("lgaName")
        st = props.get("stateCode")
        if state_filter is not None and str(st) != state_filter:
            continue
        if code is None or name is None:
            print(feature, file=sys.stderr)
            continue
        print(f"{code}\t{name}")


def validate_adopters():
    geojson_data = load_geojson()
    codes = []
    for f in geojson_data["features"]:
        props = f.get("properties") or {}
        c = props.get("lgaCode")
        if c is not None:
            codes.append(str(c))
    valid_set = set(codes)

    adopters = load_adopters()
    seen = set()
    errors = []

    for entry in adopters:
        s = str(entry).strip()
        if not CODE_RE.match(s):
            errors.append(f'Invalid adopter (expected 5-digit LGA code): "{entry}"')
            continue
        if s in seen:
            errors.append(f"Duplicate adopter entry: {s}")
        seen.add(s)
        if s not in valid_set:
            errors.append(f"Unknown adopter (not in GeoJSON lgaCode): {s}")

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        print(f"Validation failed ({len(errors)} issue(s)).", file=sys.stderr)
        sys.exit(1)

    print(f"OK: {len(adopters)} adopters each match a feature in {GEOJSON_PATH}")


def main():
    parser = argparse.ArgumentParser(description="LGA rows from GeoJSON; validate TAG adopters (LGA codes).")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Check data/tag-adopters.json codes exist in councils-au.geojson",
    )
    parser.add_argument(
        "--state",
        metavar="CODE",
        help="With default print mode: only LGAs where stateCode equals this (e.g. 2 for Victoria)",
    )
    args = parser.parse_args()

    if not os.path.isfile(GEOJSON_PATH):
        print(f"Missing GeoJSON: {GEOJSON_PATH}", file=sys.stderr)
        sys.exit(1)

    if args.validate:
        if not os.path.isfile(ADOPTERS_PATH):
            print(f"Missing adopters file: {ADOPTERS_PATH}", file=sys.stderr)
            sys.exit(1)
        validate_adopters()
        return

    print_lga_rows(args.state)


if __name__ == "__main__":
    main()
