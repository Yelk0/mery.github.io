"""Move a downloaded table into data/<place>/<dataset>.csv.

A national publication is fetched once. This module splits it afterwards.
The cell text is copied as published, so reading it back yields the same numbers.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Callable
from pathlib import Path

from mery.paths import DATA
from mery.places import (
    DEBT_CODES,
    DEBT_INSTRUMENTS,
    EPA_LABELS,
    INE_LABELS,
    REGION_SLUGS,
    volume_name,
)

_COUNTRY_ROWS = frozenset({"spain", "espana"})
_INSTRUMENT_COLUMNS = tuple(DEBT_INSTRUMENTS.values())

FLAT_FILES = (
    "80109.csv",
    "80110.csv",
    "65321.csv",
    "cre-volume.csv",
    "be1306.csv",
    "health.csv",
    "schools.csv",
    "care.csv",
    "balance.csv",
    "budget.csv",
    "spain-budget.csv",
    "budget-parts.csv",
    "transfers.csv",
    "spain.csv",
    "spain-eu.csv",
    "spain-debt.csv",
    "eu-volume.csv",
)


def place_directory(row_slug: str) -> str:
    """Folder name for a slug stored in a downloaded table."""
    if row_slug in _COUNTRY_ROWS:
        return "spain"
    if row_slug not in REGION_SLUGS:
        raise ValueError(f"Unknown place slug {row_slug}")
    return row_slug


def write_table(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def remove_flat(name: str) -> None:
    (DATA / name).unlink(missing_ok=True)


def scatter_slug(flat: Path, filename: str) -> None:
    """Split a semicolon table on its slug column. spain and espana both land in data/spain/."""
    header, groups = _groups(flat, "slug", place_directory)
    for directory, rows in groups.items():
        write_table(DATA / directory / filename, header, rows)


def scatter_labels(
    flat: Path,
    filename: str,
    *,
    column: str,
    labels: dict[str, str],
    required: frozenset[str],
) -> None:
    """Split a table on a territory label. Rows for provinces are left out."""
    directories = {label: slug for slug, label in labels.items()}
    header, groups, seen = _label_groups(flat, column, directories)
    missing = required - seen
    if missing:
        raise ValueError(f"{flat.name} is missing {', '.join(sorted(missing))}")
    for directory, rows in groups.items():
        write_table(DATA / directory / filename, header, rows)


def scatter_debt(flat: Path) -> None:
    """Turn the wide Bank of Spain table into one debt.csv per community."""
    text = flat.read_bytes().decode("latin-1")
    sheet = list(csv.reader(text.splitlines()))
    if len(sheet) < 7:
        raise ValueError(f"{flat} has no debt rows")
    columns: dict[tuple[str, str], int] = {}
    for index, code in enumerate(sheet[0]):
        for instrument, key in DEBT_INSTRUMENTS.items():
            marker = f"_{instrument}_PS_ACS_"
            if marker in code:
                columns[(code.rsplit("_", 1)[-1], key)] = index
    pending: dict[str, dict[int, dict[str, str]]] = {}
    order: dict[str, list[int]] = {}
    for row in sheet[6:]:
        if not row:
            continue
        label = row[0].strip().strip('"')
        if not label.startswith("DIC "):
            continue
        year = int(label.split()[-1])
        for (region_code, key), index in columns.items():
            raw = row[index].strip().strip('"') if index < len(row) else ""
            years = pending.setdefault(region_code, {})
            years.setdefault(year, {})[key] = raw
            if year not in order.setdefault(region_code, []):
                order[region_code].append(year)
    header = ["year", *_INSTRUMENT_COLUMNS]
    missing: list[str] = []
    for slug, code in DEBT_CODES.items():
        cells = pending.get(code)
        if cells is None:
            missing.append(slug)
            continue
        table = [
            [str(year), *[cells[year].get(key, "") for key in _INSTRUMENT_COLUMNS]]
            for year in order[code]
        ]
        write_table(DATA / slug / "debt.csv", header, table)
    if missing:
        raise ValueError(f"Debt file has no series for {', '.join(missing)}")


def scatter_spain_accounts(flat: Path) -> None:
    """The public-accounts file holds three series. Each one gets its own file."""
    balance: list[list[str]] = []
    spending: list[list[str]] = []
    central: list[list[str]] = []
    with flat.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            year = row["year"]
            balance.append(["espana", year, row["million"], row["percent"]])
            if row.get("spent"):
                spending.append([year, row["spent"]])
            if row.get("central"):
                central.append([year, row["central"]])
    write_table(DATA / "spain" / "balance.csv", ["slug", "year", "million", "percent"], balance)
    write_table(DATA / "spain" / "spending.csv", ["year", "million"], spending)
    write_table(DATA / "spain" / "central-spending.csv", ["year", "million"], central)


def copy_file(source: Path, directory: str, filename: str) -> None:
    destination = DATA / directory / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())


def scatter_office(flat: Path) -> None:
    """Write each community's presidents and cabinet. data/people.json stays for the site."""
    payload: object = json.loads(flat.read_text(encoding="utf-8"))
    regions = _region_list(payload)
    for region in regions:
        slug = region.get("slug")
        if not isinstance(slug, str) or slug not in REGION_SLUGS:
            raise ValueError(f"Unknown region in {flat.name}: {slug!r}")
        destination = DATA / slug / "office.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(region, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def restore_slug(filename: str, flat: Path) -> None:
    """Rebuild a flat table from place files so a downloader can merge into it."""
    paths = sorted(path for path in DATA.glob(f"*/{filename}") if path.is_file())
    if not paths:
        return
    header: list[str] | None = None
    rows: list[list[str]] = []
    for path in paths:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter=";")
            file_header = next(reader, None)
            if file_header is None:
                continue
            if header is None:
                header = file_header
            elif file_header != header:
                raise ValueError(f"{path} header does not match {filename}")
            rows.extend(row for row in reader if row)
    if header is None:
        return
    write_table(flat, header, rows)


def arrange() -> None:
    """Split the flat downloads that are still in data/ into one file per place."""
    found = False
    if (DATA / "80109.csv").exists():
        scatter_labels(
            DATA / "80109.csv",
            "gdp.csv",
            column="Comunidades y Ciudades Autónomas y Provincias",
            labels=INE_LABELS | {"spain": "Total Nacional"},
            required=frozenset(INE_LABELS.values()) | {"Total Nacional"},
        )
        found = True
    if (DATA / "80110.csv").exists():
        scatter_labels(
            DATA / "80110.csv",
            "per-capita.csv",
            column="Comunidades y Ciudades Autónomas y Provincias",
            labels=INE_LABELS | {"spain": "Total Nacional"},
            required=frozenset(INE_LABELS.values()) | {"Total Nacional"},
        )
        found = True
    if (DATA / "65321.csv").exists():
        scatter_labels(
            DATA / "65321.csv",
            "jobs.csv",
            column="Comunidades y Ciudades Autónomas",
            labels=EPA_LABELS | {"spain": "Total Nacional"},
            required=frozenset(EPA_LABELS.values()) | {"Total Nacional"},
        )
        found = True
    if (DATA / "cre-volume.csv").exists():
        volume_labels = {slug: volume_name(label) for slug, label in INE_LABELS.items()}
        volume_labels["spain"] = "TOTAL NACIONAL"
        scatter_labels(
            DATA / "cre-volume.csv",
            "real-growth.csv",
            column="Comunidad Autónoma",
            labels=volume_labels,
            required=frozenset(volume_labels.values()),
        )
        found = True
    if (DATA / "be1306.csv").exists():
        scatter_debt(DATA / "be1306.csv")
        found = True
    for name in ("health.csv", "schools.csv", "care.csv", "balance.csv", "budget.csv", "transfers.csv", "budget-parts.csv"):
        path = DATA / name
        if path.exists():
            scatter_slug(path, name)
            found = True
    if (DATA / "spain-budget.csv").exists():
        scatter_slug(DATA / "spain-budget.csv", "budget.csv")
        found = True
    if (DATA / "spain.csv").exists():
        scatter_spain_accounts(DATA / "spain.csv")
        found = True
    if (DATA / "spain-eu.csv").exists():
        copy_file(DATA / "spain-eu.csv", "spain", "eu-transfers.csv")
        found = True
    if (DATA / "spain-debt.csv").exists():
        copy_file(DATA / "spain-debt.csv", "spain", "pde-debt.csv")
        found = True
    if (DATA / "eu-volume.csv").exists():
        copy_file(DATA / "eu-volume.csv", "spain", "eu-volume.csv")
        found = True
    people = DATA / "people.json"
    if people.exists():
        scatter_office(people)
        found = True
    if not found:
        raise SystemExit("No flat downloads in data/. The place files are already arranged.")


def retire_flat_files() -> None:
    for name in FLAT_FILES:
        remove_flat(name)


def _read_sheet(flat: Path) -> tuple[list[str], list[list[str]]]:
    with flat.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=";")
        header = next(reader, None)
        if not header:
            raise ValueError(f"{flat} has no header")
        return header, [row for row in reader if row]


def _column(header: list[str], name: str, flat: Path) -> int:
    try:
        return header.index(name)
    except ValueError as error:
        raise ValueError(f"{flat.name} has no {name} column") from error


def _groups(
    flat: Path,
    column: str,
    directory_for: Callable[[str], str],
) -> tuple[list[str], dict[str, list[list[str]]]]:
    header, rows = _read_sheet(flat)
    index = _column(header, column, flat)
    groups: dict[str, list[list[str]]] = {}
    for row in rows:
        if index >= len(row) or not row[index]:
            continue
        groups.setdefault(directory_for(row[index]), []).append(row)
    if not groups:
        raise ValueError(f"{flat.name} has no place rows")
    return header, groups


def _label_groups(
    flat: Path,
    column: str,
    directories: dict[str, str],
) -> tuple[list[str], dict[str, list[list[str]]], set[str]]:
    header, rows = _read_sheet(flat)
    index = _column(header, column, flat)
    groups: dict[str, list[list[str]]] = {}
    seen: set[str] = set()
    for row in rows:
        if index >= len(row) or not row[index]:
            continue
        label = row[index]
        directory = directories.get(label)
        if directory is None:
            continue
        seen.add(label)
        groups.setdefault(directory, []).append(row)
    if not groups:
        raise ValueError(f"{flat.name} has no known places")
    return header, groups, seen


def _region_list(payload: object) -> list[dict[str, object]]:
    if not isinstance(payload, dict):
        raise ValueError("people.json must be an object")
    regions = payload.get("regions")
    if not isinstance(regions, list):
        raise ValueError("people.json has no regions")
    typed: list[dict[str, object]] = []
    for region in regions:
        if not isinstance(region, dict):
            raise ValueError("A region entry must be an object")
        item: dict[str, object] = {}
        for key, value in region.items():
            if not isinstance(key, str):
                raise ValueError("Region keys must be strings")
            item[key] = value
        typed.append(item)
    return typed
