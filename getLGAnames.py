#!/usr/bin/env python3
"""
Helpers for Victoria LGA GeoJSON used by the TAG Councils map.

GeoJSON path: data/geo/councils-vic.geojson
TAG adopters: data/tag-adopters.json (field "adopters")

Australia-wide: plan to join on ABS ASGS LGA codes instead of LGA_NAME once
national boundary data is in place; update this script and tag-adopters.json then.
"""
import argparse
import json
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
GEOJSON_PATH = os.path.join(script_dir, "data", "geo", "councils-vic.geojson")
ADOPTERS_PATH = os.path.join(script_dir, "data", "tag-adopters.json")


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


def print_lga_names():
    geojson_data = load_geojson()
    for feature in geojson_data["features"]:
        print(feature["properties"]["LGA_NAME"])


def validate_adopters():
    geojson_data = load_geojson()
    lga_names = [f["properties"]["LGA_NAME"] for f in geojson_data["features"]]
    valid_set = set(lga_names)

    adopters = load_adopters()
    seen = set()
    errors = []

    for name in adopters:
        if name in seen:
            errors.append(f'Duplicate adopter entry: "{name}"')
        seen.add(name)
        if name not in valid_set:
            errors.append(f'Unknown adopter (not in GeoJSON LGA_NAME): "{name}"')

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        print(f"Validation failed ({len(errors)} issue(s)).", file=sys.stderr)
        sys.exit(1)

    print(f"OK: {len(adopters)} adopters each match a feature in {GEOJSON_PATH}")


def main():
    parser = argparse.ArgumentParser(description="LGA names from GeoJSON; optional adopters validation.")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Check data/tag-adopters.json against GeoJSON LGA_NAME values; exit 1 on unknown or duplicate names",
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

    print_lga_names()


if __name__ == "__main__":
    main()
