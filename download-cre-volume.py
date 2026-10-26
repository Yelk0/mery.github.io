#!/usr/bin/env python3
"""Download regional-accounts volume growth and write data/cre-volume.csv.

INE table 80111 publishes these rates rounded to one decimal. The regional
accounts workbook keeps the unrounded rates, which is what a chained index
needs. The workbook is the CRE file "PIB y PIB per cápita. Serie 2000-2025",
sheet Tabla_3.
"""

from __future__ import annotations

import csv
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "cre-volume.csv"
URL = "https://www.ine.es/daco/daco42/cre00/b2024/pr_cre_26.xls"
USER_AGENT = "plan-mery/cre-downloader"


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
    # A venv python is a symlink, so resolving both paths hides the venv.
    if Path(sys.prefix).resolve() != venv.resolve():
        os.execv(str(python), [str(python), __file__, *sys.argv[1:]])
    import xlrd
    return xlrd


def main() -> None:
    xlrd = ensure_xlrd()
    OUT.parent.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".xls", delete=False) as handle:
        destination = Path(handle.name)
    try:
        request = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as handle:
            handle.write(response.read())
        book = xlrd.open_workbook(str(destination))
        sheet = book.sheet_by_name("Tabla_3")
        years = {}
        for column in range(sheet.ncols):
            header = str(sheet.cell_value(4, column)).strip()
            if len(header) >= 4 and header[:4].isdigit():
                years[column] = int(header[:4])
        if 2001 not in years.values() or 2025 not in years.values():
            raise SystemExit(f"Volume sheet is missing 2001 or 2025: {sorted(set(years.values()))}")
        rows = []
        for row_index in range(6, sheet.nrows):
            name = str(sheet.cell_value(row_index, 1)).strip()
            if not name or name.startswith("("):
                continue
            for column, year in years.items():
                rate = sheet.cell_value(row_index, column)
                if rate == "":
                    continue
                rows.append((name, year, float(rate)))
        with OUT.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter=";")
            writer.writerow(["Comunidad Autónoma", "Año", "Tasa"])
            writer.writerows(rows)
    finally:
        destination.unlink(missing_ok=True)
    print(f"Wrote {OUT} ({len(rows)} rates) from {URL}")


if __name__ == "__main__":
    main()
