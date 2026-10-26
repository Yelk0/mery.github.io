#!/usr/bin/env python3
"""Download early school leaving by region and write data/schools.csv.

The rate is the share of people aged 18 to 24 who left education without an
upper-secondary qualification. Eurostat table edat_lfse_16, annual, both
sexes, percent. Spain and each community are NUTS 2 regions.
"""

from __future__ import annotations

import csv
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "schools.csv"
GEOS = {
    "ES": "spain",
    "ES11": "galicia",
    "ES12": "asturias",
    "ES13": "cantabria",
    "ES21": "pais-vasco",
    "ES22": "navarra",
    "ES23": "la-rioja",
    "ES24": "aragon",
    "ES30": "madrid",
    "ES41": "castilla-y-leon",
    "ES42": "castilla-la-mancha",
    "ES43": "extremadura",
    "ES51": "cataluna",
    "ES52": "valencia",
    "ES53": "baleares",
    "ES61": "andalucia",
    "ES62": "murcia",
    "ES63": "ceuta",
    "ES64": "melilla",
    "ES70": "canarias",
}
URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/edat_lfse_16/"
    + "A.PC.T.Y18-24."
    + "+".join(GEOS)
    + "?format=TSV"
)
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def parse_cell(cell: str) -> float | None:
    text = cell.strip()
    if not text or text.startswith(":"):
        return None
    match = NUMBER.match(text)
    if not match:
        return None
    return float(match.group(0))


def main() -> None:
    request = urllib.request.Request(URL, headers={"User-Agent": "plan-mery/schools"})
    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read().decode("utf-8")
    lines = [line for line in raw.splitlines() if line.strip()]
    header = lines[0].split("\t")
    years = []
    for cell in header[1:]:
        match = re.search(r"(20\d{2}|19\d{2})", cell)
        years.append(int(match.group(1)) if match else None)
    rows = []
    seen = set()
    for line in lines[1:]:
        parts = line.split("\t")
        geo = parts[0].rsplit(",", 1)[-1].strip()
        slug = GEOS.get(geo)
        if slug is None:
            continue
        seen.add(slug)
        for year, cell in zip(years, parts[1:]):
            if year is None:
                continue
            rate = parse_cell(cell)
            if rate is None:
                continue
            rows.append((slug, year, rate))
    missing = sorted(set(GEOS.values()) - seen)
    if missing:
        raise SystemExit(f"Early school leaving is missing {', '.join(missing)}")
    if not any(slug == "spain" and year == 2024 for slug, year, _rate in rows):
        raise SystemExit("Early school leaving has no Spain figure for 2024")
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["slug", "year", "rate"])
        writer.writerows(rows)
    print(f"Wrote {OUT} ({len(rows)} rates) from Eurostat edat_lfse_16")


if __name__ == "__main__":
    main()
