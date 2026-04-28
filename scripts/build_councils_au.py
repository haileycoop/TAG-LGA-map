#!/usr/bin/env python3
"""
Build data/geo/councils-au.geojson from ABS ASGS Edition 3 LGA boundaries.

Source: ABS Digital boundary files — Local Government Areas 2024 GDA2020
https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files
Direct zip: .../digital-boundary-files/LGA_2024_AUST_GDA2020.zip (shapefile inside).

Output properties: lgaCode, lgaName, stateCode, stateName, areaSqkm (stable for the web app).
Geometry: EPSG:4326. Default simplification tolerance 0.002 degrees (~200 m) to keep repo size reasonable.

Run from repo root:
  python3 scripts/build_councils_au.py --download
  python3 scripts/build_councils_au.py
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.request
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ZIP_URL = (
    "https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/"
    "jul2021-jun2026/access-and-downloads/digital-boundary-files/LGA_2024_AUST_GDA2020.zip"
)
DEFAULT_SHP_NAME = "LGA_2024_AUST_GDA2020.shp"


def download_zip(zip_path: str, url: str) -> None:
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    print(f"Downloading {url} …")
    urllib.request.urlretrieve(url, zip_path)
    print(f"Wrote {zip_path}")


def unzip_shapefile(zip_path: str, dest_dir: str) -> str:
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)
    shp = os.path.join(dest_dir, DEFAULT_SHP_NAME)
    if not os.path.isfile(shp):
        raise FileNotFoundError(f"Expected shapefile not found after unzip: {shp}")
    return shp


def main() -> None:
    import geopandas as gpd

    parser = argparse.ArgumentParser(description="Build councils-au.geojson from ABS LGA 2024 shapefile.")
    parser.add_argument(
        "--input-shp",
        default=os.path.join(REPO_ROOT, "build", "abs", DEFAULT_SHP_NAME),
        help="Path to LGA_2024_AUST_GDA2020.shp",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(REPO_ROOT, "data", "geo", "councils-au.geojson"),
        help="Output GeoJSON path",
    )
    parser.add_argument(
        "--simplify",
        type=float,
        default=0.002,
        help="Tolerance in degrees for geometry.simplify (0 to disable)",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help=f"Download ABS zip to build/abs/ and unzip if shapefile is missing",
    )
    parser.add_argument("--zip-url", default=DEFAULT_ZIP_URL, help="Override ABS zip URL")
    args = parser.parse_args()

    shp = args.input_shp
    if not os.path.isfile(shp):
        if not args.download:
            print(f"Shapefile not found: {shp}\nUse --download to fetch from ABS.", file=sys.stderr)
            sys.exit(1)
        zip_path = os.path.join(REPO_ROOT, "build", "abs", "LGA_2024_AUST_GDA2020.zip")
        download_zip(zip_path, args.zip_url)
        shp = unzip_shapefile(zip_path, os.path.join(REPO_ROOT, "build", "abs"))

    gdf = gpd.read_file(shp)
    if gdf.crs is None:
        raise SystemExit("Source CRS missing")
    gdf = gdf.to_crs(4326)

    if args.simplify and args.simplify > 0:
        gdf = gdf.copy()
        gdf["geometry"] = gdf.geometry.simplify(args.simplify, preserve_topology=True)

    out = gdf.rename(
        columns={
            "LGA_CODE24": "lgaCode",
            "LGA_NAME24": "lgaName",
            "STE_CODE21": "stateCode",
            "STE_NAME21": "stateName",
            "AREASQKM": "areaSqkm",
        }
    )[["lgaCode", "lgaName", "stateCode", "stateName", "areaSqkm", "geometry"]]
    out = out.sort_values("lgaCode")

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    out.to_file(args.output, driver="GeoJSON")
    size_mb = os.path.getsize(args.output) / (1024 * 1024)
    print(f"Wrote {args.output} ({size_mb:.1f} MB), {len(out)} features")


if __name__ == "__main__":
    main()
