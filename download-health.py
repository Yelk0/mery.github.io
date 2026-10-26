#!/usr/bin/env python3
"""Download December surgical waiting times and write data/health.csv.

Each file is the Ministry of Health SISLE summary for 31 December. The figure
is the average days a structural waiting-list patient had already been waiting.
Regions send the counts themselves, and a later file can correct an earlier one.
"""

from __future__ import annotations

import csv
import re
import shutil
import subprocess
import tempfile
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "health.csv"
BASE = "https://www.sanidad.gob.es"
PAGES = [
    BASE + "/estadEstudios/estadisticas/inforRecopilaciones/listaEspera.htm",
    BASE + "/estadEstudios/estadisticas/inforRecopilaciones/listaEsperaInfAnt.htm",
]
USER_AGENT = "plan-mery/health"
# Longer aliases first so Castilla-La Mancha is not read as Castilla y León.
ALIASES = [
    ("castilla-la mancha", "castilla-la-mancha"),
    ("castilla la mancha", "castilla-la-mancha"),
    ("castilla y leon", "castilla-y-leon"),
    ("comunidad valenciana", "valencia"),
    ("valenciana", "valencia"),
    ("pais vasco", "pais-vasco"),
    ("principado de asturias", "asturias"),
    ("pdo de asturias", "asturias"),
    ("asturias", "asturias"),
    ("foral de navarra", "navarra"),
    ("navarra", "navarra"),
    ("andalucia", "andalucia"),
    ("extremadura", "extremadura"),
    ("baleares", "baleares"),
    ("balears", "baleares"),
    ("cantabria", "cantabria"),
    ("catalunya", "cataluna"),
    ("cataluna", "cataluna"),
    ("canarias", "canarias"),
    ("galicia", "galicia"),
    ("murcia", "murcia"),
    ("madrid", "madrid"),
    ("aragon", "aragon"),
    ("rioja", "la-rioja"),
    ("ceuta", "ceuta"),
    ("melilla", "melilla"),
]
NUMBER = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?")


def fold(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", stripped).lower().strip()


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def december_links() -> dict[int, str]:
    chosen: dict[int, tuple[int, str]] = {}
    for page in PAGES:
        html = fetch(page).decode("latin-1", "replace")
        for href in re.findall(r'href="([^"]+\.pdf)"', html, flags=re.I):
            name = href.split("/")[-1]
            folded = name.lower()
            if "jun" in folded or not ("dic" in folded or "diciembre" in folded):
                continue
            if "nota" in folded or "aclarat" in folded or "datos_" in folded:
                continue
            if "lista" not in folded and "indicador" not in folded:
                continue
            year = year_of(folded)
            if year is None:
                continue
            absolute = href if href.startswith("http") else urllib.request.urljoin(page, href)
            # A rectified file, then a name ending in 2, beats the first publication.
            rank = (2 if "rectific" in folded else 0) + (1 if re.search(r"2\.pdf$", folded) else 0)
            previous = chosen.get(year)
            if previous is None or rank >= previous[0]:
                chosen[year] = (rank, absolute)
    if 2024 not in chosen or 2016 not in chosen:
        raise SystemExit(f"Waiting-list archive is missing a December file: {sorted(chosen)}")
    return {year: url for year, (_rank, url) in chosen.items()}


def year_of(name: str) -> int | None:
    match = re.search(r"(20\d{2})", name)
    if match:
        return int(match.group(1))
    match = re.search(r"(?:dic|diciembre)[^\d]*(\d{2})", name)
    if match:
        return 2000 + int(match.group(1))
    return None


def slug_of(label: str) -> str | None:
    if label == "total":
        return "spain"
    for alias, slug in ALIASES:
        if label == alias or label.endswith(" " + alias) or label.startswith(alias + " "):
            return slug
    return None


def days_on(folded: str) -> int | None:
    cleaned = re.sub(r"sns:.*", "", folded)
    tokens = NUMBER.findall(cleaned)
    if not 3 <= len(tokens) <= 5:
        return None
    last = tokens[-1]
    if "," in last or "." in last:
        return None
    days = int(last)
    if not 15 <= days <= 400:
        return None
    return days


def candidates(text: str) -> list[tuple[int, str, int]]:
    folded_lines = [fold(line) for line in text.splitlines()]
    found = []
    for index, folded in enumerate(folded_lines):
        if not folded:
            continue
        match = NUMBER.search(folded)
        label = folded if match is None else folded[: match.start()]
        slug = slug_of(label.strip(" .:-"))
        if slug is None:
            continue
        days = days_on(folded) if match else None
        if days is None:
            # A chart note sometimes pushes the figures onto the next line.
            for look in range(index + 1, min(index + 4, len(folded_lines))):
                nxt = folded_lines[look]
                if not nxt or nxt.startswith("sns"):
                    continue
                later = NUMBER.search(nxt)
                later_label = nxt if later is None else nxt[: later.start()]
                if slug_of(later_label.strip(" .:-")):
                    break
                days = days_on(nxt)
                if days is not None:
                    break
        if days is None:
            continue
        found.append((index, slug, days))
    return found


def surgical_window(text: str) -> tuple[int, int] | None:
    folded_lines = [fold(line) for line in text.splitlines()]
    starts = [
        index
        for index, line in enumerate(folded_lines)
        if "quirurgic" in line and ("comunidad" in line or "distribucion" in line or "situacion" in line)
    ]
    if not starts:
        starts = [index for index, line in enumerate(folded_lines) if "lista de espera quirurgic" in line]
    if not starts:
        return None
    start = starts[0]
    end = len(folded_lines)
    for index in range(start + 1, len(folded_lines)):
        line = folded_lines[index]
        if "consulta" in line and "espera" in line:
            end = index
            break
    return start, end


def parse_pdf(path: Path) -> dict[str, int]:
    text = subprocess.check_output(["pdftotext", "-layout", str(path), "-"], text=True, errors="replace")
    window = surgical_window(text)
    rows = candidates(text)
    if window is not None:
        start, end = window
        scoped = [row for row in rows if start <= row[0] < end]
        if len({slug for _index, slug, _days in scoped if slug != "spain"}) >= 12:
            rows = scoped
    clusters: list[list[tuple[int, str, int]]] = []
    for row in rows:
        if not clusters or row[0] - clusters[-1][-1][0] > 25:
            clusters.append([row])
        else:
            clusters[-1].append(row)
    if not clusters:
        return {}
    best = max(clusters, key=lambda cluster: len({slug for _index, slug, _days in cluster if slug != "spain"}))
    parsed: dict[str, int] = {}
    for _index, slug, days in best:
        parsed.setdefault(slug, days)
    regions = [slug for slug in parsed if slug != "spain"]
    if len(regions) < 15 or "spain" not in parsed:
        return {}
    return parsed


def main() -> None:
    if shutil.which("pdftotext") is None:
        raise SystemExit("pdftotext is required to read the waiting-list PDFs")
    links = december_links()
    folder = Path(tempfile.mkdtemp(prefix="plan-mery-health-"))
    rows = []
    kept = []
    for year in sorted(links):
        destination = folder / f"{year}.pdf"
        destination.write_bytes(fetch(links[year]))
        parsed = parse_pdf(destination)
        if not parsed:
            print(f"skip {year}: no regional waiting-time table")
            continue
        for slug, days in sorted(parsed.items()):
            rows.append((slug, year, days))
        kept.append(f"{year}:{parsed['spain']}")
    expected = {
        ("andalucia", 2024, 176),
        ("spain", 2024, 126),
        ("spain", 2023, 128),
        ("baleares", 2019, 79),
        ("spain", 2025, 122),
    }
    found = {(slug, year, days) for slug, year, days in rows}
    missing = expected - found
    if missing:
        raise SystemExit(f"Waiting-list parser missed known figures: {sorted(missing)}")
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["slug", "year", "days"])
        writer.writerows(rows)
    print(f"Wrote {OUT} ({len(rows)} figures). Spain days by year: {', '.join(kept)}")


if __name__ == "__main__":
    main()
