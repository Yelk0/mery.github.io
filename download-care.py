#!/usr/bin/env python3
"""Download dependency waiting rates and write data/care.csv.

The rate is people with a recognised right who were still waiting for a care
plan, divided by everyone with a recognised right, at 31 December. IMSERSO
publishes both counts. A later workbook can revise an earlier December.
"""

from __future__ import annotations

import csv
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "care.csv"
HISTORIC = (
    "https://imserso.es/el-imserso/documentacion/estadisticas/"
    "sistema-autonomia-atencion-dependencia-saad/estadisticas-mensual/historico-informes-publicados"
)
MONTHLY = (
    "https://imserso.es/el-imserso/documentacion/estadisticas/"
    "sistema-autonomia-atencion-dependencia-saad/estadisticas-mensual"
)
USER_AGENT = "Mozilla/5.0 plan-mery/care"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
DECEMBER = re.compile(r"31[/-]12[/-](\d{4})")


def ensure_xlrd():
    try:
        import xlrd
        return xlrd
    except ImportError:
        pass
    venv = Path(tempfile.gettempdir()) / "plan-mery-xlsvenv"
    python = venv / "bin" / "python"
    if not python.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(venv)])
    if subprocess.run([str(python), "-c", "import xlrd"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
        subprocess.check_call([str(python), "-m", "pip", "install", "xlrd"])
    if Path(sys.prefix).resolve() != venv.resolve():
        os.execv(str(python), [str(python), __file__, *sys.argv[1:]])
    import xlrd
    return xlrd


def fold(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", stripped).lower().strip()


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Referer": "https://imserso.es/"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def absolute(page: str, href: str) -> str:
    if href.startswith("http"):
        return href
    return urllib.request.urljoin(page, href)


def workbook_links() -> list[str]:
    pages = [MONTHLY]
    historic = fetch(HISTORIC).decode("utf-8", "replace")
    for href in re.findall(r'href="([^"]*informes-publicados[^"]*)"', historic):
        if href.startswith(("mailto:", "whatsapp:", "javascript:")):
            continue
        pages.append(absolute(HISTORIC, href))
    found = []
    seen = set()
    for page in pages:
        try:
            html = fetch(page).decode("utf-8", "replace")
        except Exception as error:
            print(f"skip page {page}: {error}")
            continue
        for href in re.findall(r'href="([^"]+)"', html):
            name = href.lower()
            if "estsisaad" not in name:
                continue
            if not (name.endswith(".xls") or ".xls/" in name or name.endswith(".xlsx") or ".xlsx/" in name):
                continue
            if "1231" not in name and "20123/11151734" not in name:
                continue
            url = absolute(page, href)
            if url in seen:
                continue
            seen.add(url)
            found.append(url)
    if len(found) < 8:
        raise SystemExit(f"Only {len(found)} SAAD workbooks found")
    return found


def care_slug(label: str) -> str | None:
    folded = fold(label)
    if not folded:
        return None
    if "total" in folded:
        return "spain"
    checks = [
        ("mancha", "castilla-la-mancha"),
        ("leon", "castilla-y-leon"),
        ("andaluc", "andalucia"),
        ("valenc", "valencia"),
        ("balear", "baleares"),
        ("extremad", "extremadura"),
        ("catal", "cataluna"),
        ("canaria", "canarias"),
        ("cantabr", "cantabria"),
        ("asturi", "asturias"),
        ("aragon", "aragon"),
        ("galicia", "galicia"),
        ("madrid", "madrid"),
        ("murcia", "murcia"),
        ("navarr", "navarra"),
        ("vasco", "pais-vasco"),
        ("euskadi", "pais-vasco"),
        ("rioja", "la-rioja"),
        ("ceuta", "ceuta"),
        ("melilla", "melilla"),
    ]
    for needle, slug in checks:
        if needle in folded:
            return slug
    return None


def column_index(ref: str) -> int:
    match = re.match(r"([A-Z]+)", ref)
    index = 0
    for character in match.group(1):
        index = index * 26 + ord(character) - 64
    return index - 1


def xlsx_sheets(path: Path) -> list[tuple[str, list[list[str]]]]:
    archive = zipfile.ZipFile(path)
    strings = []
    if "xl/sharedStrings.xml" in archive.namelist():
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        for item in root.findall("m:si", NS):
            strings.append("".join(node.text or "" for node in item.iter(f"{{{NS['m']}}}t")))
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relations = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {relation.attrib["Id"]: relation.attrib["Target"] for relation in relations}
    sheets = []
    for sheet in workbook.findall("m:sheets/m:sheet", NS):
        target = targets[sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]]
        if not target.startswith("xl/"):
            target = "xl/" + target.lstrip("/")
        root = ET.fromstring(archive.read(target))
        grid: dict[int, dict[int, str]] = {}
        for cell in root.findall(".//m:c", NS):
            ref = cell.attrib.get("r")
            if not ref:
                continue
            row_match = re.search(r"(\d+)", ref)
            row = int(row_match.group(1)) - 1
            column = column_index(ref)
            value = cell.find("m:v", NS)
            if cell.attrib.get("t") == "s" and value is not None and value.text:
                text = strings[int(value.text)]
            elif value is not None and value.text:
                text = value.text
            else:
                text = ""
            grid.setdefault(row, {})[column] = text
        if not grid:
            continue
        height = max(grid) + 1
        width = max(column for row in grid.values() for column in row) + 1
        rows = [[grid.get(row, {}).get(column, "") for column in range(width)] for row in range(height)]
        sheets.append((sheet.attrib["name"], rows))
    return sheets


def xls_sheets(path: Path, xlrd) -> list[tuple[str, list[list[str]]]]:
    book = xlrd.open_workbook(str(path))
    sheets = []
    for sheet in book.sheets():
        rows = []
        for row_index in range(sheet.nrows):
            values = []
            for column in range(sheet.ncols):
                cell = sheet.cell(row_index, column)
                if cell.ctype == xlrd.XL_CELL_DATE:
                    year, month, day, *_rest = xlrd.xldate_as_tuple(cell.value, book.datemode)
                    values.append(f"{day:02d}/{month:02d}/{year}")
                elif cell.ctype == xlrd.XL_CELL_NUMBER:
                    values.append(str(cell.value))
                else:
                    values.append(str(cell.value).strip())
            rows.append(values)
        sheets.append((sheet.name, rows))
    return sheets


def as_count(value: str) -> float | None:
    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text.replace(",", "."))
    except ValueError:
        return None
    if number < 0:
        return None
    return number


def december_columns(rows: list[list[str]]) -> dict[int, int]:
    found: dict[int, int] = {}
    for row in rows[:12]:
        for column, value in enumerate(row):
            match = DECEMBER.search(str(value))
            if match:
                found[column] = int(match.group(1))
    return found


def region_rows(rows: list[list[str]]) -> list[tuple[str, list[str]]]:
    parsed = []
    for row in rows:
        for value in row[:4]:
            slug = care_slug(str(value))
            if slug:
                parsed.append((slug, row))
                break
    return parsed


def sheet_kind(rows: list[list[str]]) -> str | None:
    title = fold(" ".join(str(cell) for row in rows[:8] for cell in row[:6]))
    if "evoluc" not in title:
        return None
    # People with a right who still have no care plan. Older files say
    # "pendientes de PIA"; the current file says "sin resoluciones de PIA".
    if "sin resoluciones de pia" in title or "pendientes de pia" in title:
        return "pending"
    if "con derecho" in title:
        return "entitled"
    return None


def counts_from_sheet(rows: list[list[str]]) -> dict[str, dict[int, float]]:
    columns = december_columns(rows)
    regions = region_rows(rows)
    if len(columns) < 2 or len(regions) < 15:
        return {}
    spain = next((row for slug, row in regions if slug == "spain"), None)
    levels = {}
    for column, year in columns.items():
        if spain is None or column >= len(spain):
            continue
        total = as_count(spain[column])
        if total is not None and total > 100:
            levels[column] = year
    series: dict[str, dict[int, float]] = {}
    for slug, row in regions:
        for column, year in levels.items():
            if column >= len(row):
                continue
            count = as_count(row[column])
            if count is None:
                continue
            series.setdefault(slug, {})[year] = count
    return series


def rates_from_workbook(path: Path, xlrd) -> dict[str, dict[int, float]]:
    sheets = xlsx_sheets(path) if path.suffix == ".xlsx" else xls_sheets(path, xlrd)
    pending = {}
    entitled = {}
    for _name, rows in sheets:
        kind = sheet_kind(rows)
        if kind == "pending" and not pending:
            pending = counts_from_sheet(rows)
        elif kind == "entitled" and not entitled:
            entitled = counts_from_sheet(rows)
    rates: dict[str, dict[int, float]] = {}
    for slug, years in pending.items():
        for year, waiting in years.items():
            base = entitled.get(slug, {}).get(year)
            if base in (None, 0):
                continue
            rates.setdefault(slug, {})[year] = 100 * waiting / base
    return rates


def main() -> None:
    xlrd = ensure_xlrd()
    folder = Path(tempfile.mkdtemp(prefix="plan-mery-saad-"))
    combined: dict[tuple[str, int], float] = {}
    used = 0
    for url in workbook_links():
        name = url.split("/")[-2] if "/documents/" in url else url.rsplit("/", 1)[-1]
        suffix = ".xlsx" if ".xlsx" in url.lower() else ".xls"
        path = folder / f"{name}{suffix}"
        try:
            path.write_bytes(fetch(url))
            rates = rates_from_workbook(path, xlrd)
        except Exception as error:
            print(f"skip {name}: {error}")
            continue
        if not rates.get("spain"):
            print(f"skip {name}: no December waiting rate")
            continue
        used += 1
        for slug, years in rates.items():
            for year, rate in years.items():
                combined[(slug, year)] = rate
        print(f"read {name}: {min(rates['spain'])}–{max(rates['spain'])}")
    covered = [slug for (slug, year) in combined if year == 2024]
    if "spain" not in covered or len(covered) < 18:
        raise SystemExit("Dependency waiting rates did not cover December 2024")
    rows = [(slug, year, rate) for (slug, year), rate in sorted(combined.items())]
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["slug", "year", "rate"])
        writer.writerows(rows)
    years = sorted({year for slug, year in combined if slug == "spain"})
    print(f"Wrote {OUT} ({len(rows)} rates) for {years[0]}–{years[-1]}")


if __name__ == "__main__":
    main()
