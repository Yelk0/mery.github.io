#!/usr/bin/env python3
"""Download EU and Spain real GDP volume and write data/eu-volume.csv.

Eurostat table nama_10_gdp, chain-linked volumes, index 2015=100, gross
domestic product. EU27_2020 is the European Union of the present 27
countries. Spain's row compares this Spain index with this EU index.
"""

from __future__ import annotations

import csv
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "eu-volume.csv"
GEOS = ("ES", "EU27_2020")
URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/nama_10_gdp/"
    "A.CLV_I15.B1GQ."
    + "+".join(GEOS)
    + "?format=TSV"
)
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
FIRST = 2000


def parse_cell(cell: str) -> float | None:
    text = cell.strip()
    if not text or text.startswith(":"):
        return None
    match = NUMBER.match(text)
    if not match:
        return None
    return float(match.group(0))


def main() -> None:
    request = urllib.request.Request(URL, headers={"User-Agent": "plan-mery/eu-volume"})
    with urllib.request.urlopen(request, timeout=120) as response:
        lines = [line for line in response.read().decode("utf-8").splitlines() if line.strip()]
    years = []
    for cell in lines[0].split("\t")[1:]:
        match = re.search(r"(20\d{2}|19\d{2})", cell)
        years.append(int(match.group(1)) if match else None)
    rows = []
    seen = set()
    for line in lines[1:]:
        parts = line.split("\t")
        geo = parts[0].rsplit(",", 1)[-1].strip()
        if geo not in GEOS:
            continue
        seen.add(geo)
        for year, cell in zip(years, parts[1:]):
            if year is None or year < FIRST:
                continue
            index = parse_cell(cell)
            if index is None:
                continue
            rows.append((geo, year, index))
    missing = [geo for geo in GEOS if geo not in seen]
    if missing:
        raise SystemExit(f"EU volume is missing {', '.join(missing)}")
    for geo in GEOS:
        got = {year for row_geo, year, _index in rows if row_geo == geo}
        if FIRST not in got or 2025 not in got:
            raise SystemExit(f"{geo} volume is missing 2000 or 2025")
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["geo", "year", "index"])
        writer.writerows(rows)
    print(f"Wrote {OUT} ({len(rows)} indexes) from Eurostat nama_10_gdp")


if __name__ == "__main__":
    main()
