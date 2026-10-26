#!/usr/bin/env python3
"""Score each regional president against the rest of Spain.

Reads the INE GDP files and data/people.json. Writes data/store.json, which
the website reads. A year counts for the president who held office for most
of it, and only if that was more than half the year. A person is ranked on
how many percent the region's total GDP pulled ahead of Spain across every
spell, once they have four counted years. Years held by someone else are
left out. The rank is real growth against Spain, minus half the rise in
the debt ratio, then school leaving, surgical waits, and the care queue.
Ten waiting days count as one point. A missing service figure is scored as
the worst measured change on record. Prices, population, and jobs stay
beside that rank.
"""

from __future__ import annotations

import csv
import json
import math
import unicodedata
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PER_CAPITA_PATH = ROOT / "data" / "80110.csv"
GDP_PATH = ROOT / "data" / "80109.csv"
VOLUME_PATH = ROOT / "data" / "cre-volume.csv"
JOBS_PATH = ROOT / "data" / "65321.csv"
DEBT_PATH = ROOT / "data" / "be1306.csv"
BALANCE_PATH = ROOT / "data" / "balance.csv"
BUDGET_PATH = ROOT / "data" / "budget.csv"
SPAIN_BUDGET_PATH = ROOT / "data" / "spain-budget.csv"
PARTS_PATH = ROOT / "data" / "budget-parts.csv"
TRANSFERS_PATH = ROOT / "data" / "transfers.csv"
SPAIN_PATH = ROOT / "data" / "spain.csv"
SPAIN_EU_PATH = ROOT / "data" / "spain-eu.csv"
SPAIN_DEBT_PATH = ROOT / "data" / "spain-debt.csv"
EU_VOLUME_PATH = ROOT / "data" / "eu-volume.csv"
HEALTH_PATH = ROOT / "data" / "health.csv"
SCHOOLS_PATH = ROOT / "data" / "schools.csv"
CARE_PATH = ROOT / "data" / "care.csv"
PEOPLE_PATH = ROOT / "data" / "people.json"
OUT = ROOT / "data" / "store.json"

INE_LABELS = {
    "andalucia": "01 ANDALUCÍA",
    "aragon": "02 ARAGÓN",
    "asturias": "03 ASTURIAS, PRINCIPADO DE",
    "baleares": "04 BALEARS, ILLES",
    "canarias": "05 CANARIAS",
    "cantabria": "06 CANTABRIA",
    "castilla-y-leon": "07 CASTILLA Y LEÓN",
    "castilla-la-mancha": "08 CASTILLA - LA MANCHA",
    "cataluna": "09 CATALUÑA",
    "valencia": "10 COMUNITAT VALENCIANA",
    "extremadura": "11 EXTREMADURA",
    "galicia": "12 GALICIA",
    "madrid": "13 MADRID, COMUNIDAD DE",
    "murcia": "14 MURCIA, REGIÓN DE",
    "navarra": "15 NAVARRA, COMUNIDAD FORAL DE",
    "pais-vasco": "16 PAÍS VASCO",
    "la-rioja": "17 RIOJA, LA",
    "ceuta": "18 CEUTA",
    "melilla": "19 MELILLA",
}
PER_CAPITA_MAGNITUDES = {
    "Valor": "valor",
    "Índice España = 100": "index",
    "Tasa de Variación Interanual": "growth",
}
GDP_MAGNITUDES = {
    "Valor": "valor",
    "Tasas de variación interanuales": "growth",
}
FIRST_YEAR = 2000
MIN_CAREER_YEARS = 4
LAST_YEAR = 2025
# A point of debt is a stock. A percent of growth is the whole spell. Half
# keeps a paydown from outranking a long growth record on its own.
DEBT_WEIGHT = 0.5
# A waiting day is a smaller step than a percentage point of school leaving
# or of the care queue. Ten days count as one point.
HEALTH_DAYS_PER_POINT = 10
# Andalucía revised its waiting-list count for the December 2018 notification.
# A window that starts before that December and ends on it or later mixes
# the old count with the new one, so the health figure is left blank.
HEALTH_BREAKS = {"andalucia": 2018}
# EPA public/private employment starts in 2002. Earlier spell endpoints stay blank.
JOBS_FIRST_YEAR = 2002
# Hospitals, schools, and dependency support in the two cities are run by the
# state (INGESA, the Ministry of Education, and IMSERSO), not by the city.
STATE_SERVICES = frozenset({"ceuta", "melilla"})
# A community row is a fixed four-year block. The next block is the later
# comparison. 2024–2025 is still open, so it does not grow to four years.
WINDOW_SPAN = 4
FORAL = frozenset({"pais-vasco", "navarra"})
BUDGET_POLICIES = ("health", "education", "care", "housing", "transport", "interest", "rest")
SHARE_ORDER = (
    "health", "education", "care", "housing", "transport", "interest", "pensions",
    "justice", "defence", "security", "foreign", "employment", "unemployment", "benefits", "labour",
    "social_security", "culture", "agriculture", "farm_works", "industry", "energy",
    "commerce", "tourism", "research", "economic", "leadership", "general",
    "statistics", "tax", "transfers", "eu_transfers", "communications",
    "community", "other_social", "resilient", "rest",
)
DEBT_INSTRUMENTS = {
    "P00000": "total",
    "F30000": "bonds",
    "F31000": "bonds_short",
    "F32000": "bonds_long",
    "F40000": "loans",
    "F42116": "fund",
}
DEBT_CODES = {
    "andalucia": "AAN",
    "aragon": "AAR",
    "asturias": "AAS",
    "baleares": "ABA",
    "canarias": "ACA",
    "cantabria": "ACB",
    "castilla-la-mancha": "ACL",
    "castilla-y-leon": "ACO",
    "cataluna": "ACT",
    "extremadura": "AEX",
    "galicia": "AGA",
    "la-rioja": "ALR",
    "madrid": "AMA",
    "murcia": "AMU",
    "navarra": "ANA",
    "pais-vasco": "APV",
    "valencia": "AVA",
}
EPA_LABELS = {
    "andalucia": "01 Andalucía",
    "aragon": "02 Aragón",
    "asturias": "03 Asturias, Principado de",
    "baleares": "04 Balears, Illes",
    "canarias": "05 Canarias",
    "cantabria": "06 Cantabria",
    "castilla-y-leon": "07 Castilla y León",
    "castilla-la-mancha": "08 Castilla - La Mancha",
    "cataluna": "09 Cataluña",
    "valencia": "10 Comunitat Valenciana",
    "extremadura": "11 Extremadura",
    "galicia": "12 Galicia",
    "madrid": "13 Madrid, Comunidad de",
    "murcia": "14 Murcia, Región de",
    "navarra": "15 Navarra, Comunidad Foral de",
    "pais-vasco": "16 País Vasco",
    "la-rioja": "17 Rioja, La",
    "ceuta": "18 Ceuta",
    "melilla": "19 Melilla",
}
# Investiture gaps shorter than this are normal. Longer ones are reported.
GAP_NOTE_DAYS = 45


def parse_number(raw: str) -> float | None:
    text = raw.strip().strip('"')
    if not text:
        return None
    return float(text.replace(".", "").replace(",", "."))


def load_table(path: Path, magnitudes: dict[str, str]) -> dict[str, dict[int, dict[str, float | None]]]:
    series: dict[str, dict[int, dict[str, float | None]]] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            magnitude = magnitudes.get(row["Magnitud"])
            if magnitude is None:
                continue
            label = row["Comunidades y Ciudades Autónomas y Provincias"]
            year = int(row["Periodo"])
            series.setdefault(label, {}).setdefault(year, {})[magnitude] = parse_number(row["Total"])
    return series


def load_volume(path: Path) -> dict[str, dict[int, float]]:
    series: dict[str, dict[int, float]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            series.setdefault(row["Comunidad Autónoma"], {})[int(row["Año"])] = float(row["Tasa"])
    return series


def chain_index(rates: dict[int, float], year: int) -> float | None:
    """Volume index with 2000 = 100. The published rates begin at 2001."""
    if year < FIRST_YEAR or year > LAST_YEAR:
        return None
    index = 100.0
    for current in range(FIRST_YEAR + 1, year + 1):
        rate = rates.get(current)
        if rate is None:
            return None
        index *= 1 + rate
    return index


def load_jobs(path: Path) -> dict[str, dict[int, dict[str, float]]]:
    buckets: dict[tuple[str, str, int], list[float]] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            if row["Sexo"] != "Ambos sexos":
                continue
            sector = {"Empleo público": "public", "Empleo privado": "private"}.get(row["Tipo de sector"])
            if sector is None:
                continue
            period = row["Periodo"]
            if len(period) < 6 or not period[:4].isdigit():
                continue
            value = parse_number(row["Total"])
            if value is None:
                continue
            buckets.setdefault((row["Comunidades y Ciudades Autónomas"], sector, int(period[:4])), []).append(value)
    annual: dict[str, dict[int, dict[str, float]]] = {}
    for (label, sector, year), values in buckets.items():
        annual.setdefault(label, {}).setdefault(year, {})[sector] = sum(values) / len(values)
    return annual


def load_debt(path: Path) -> dict[str, dict[int, float]]:
    text = path.read_bytes().decode("latin-1")
    rows = list(csv.reader(text.splitlines()))
    columns = {}
    for index, code in enumerate(rows[0]):
        if "_P00000_PS_ACS_" in code:
            columns[code.rsplit("_", 1)[-1]] = index
    series: dict[str, dict[int, float]] = {code: {} for code in columns}
    for row in rows[6:]:
        label = row[0].strip().strip('"')
        if not label.startswith("DIC "):
            continue
        year = int(label.split()[-1])
        for code, index in columns.items():
            series[code][year] = parse_number(row[index])
    return series


def load_debt_stock(path: Path) -> dict[str, dict[int, dict[str, float | None]]]:
    """December debt by instrument. Bonds are securities; loans include the state fund."""
    text = path.read_bytes().decode("latin-1")
    rows = list(csv.reader(text.splitlines()))
    columns: dict[tuple[str, str], int] = {}
    for index, code in enumerate(rows[0]):
        for instrument, key in DEBT_INSTRUMENTS.items():
            marker = f"_{instrument}_PS_ACS_"
            if marker in code:
                columns[(code.rsplit("_", 1)[-1], key)] = index
    series: dict[str, dict[int, dict[str, float | None]]] = {}
    for row in rows[6:]:
        label = row[0].strip().strip('"')
        if not label.startswith("DIC "):
            continue
        year = int(label.split()[-1])
        for (region_code, key), index in columns.items():
            raw = row[index].strip().strip('"')
            value = None if raw in ("", "_") else parse_number(raw)
            series.setdefault(region_code, {}).setdefault(year, {})[key] = value
    return series


def load_balance(path: Path) -> dict[str, dict[int, dict]]:
    series: dict[str, dict[int, dict]] = {}
    if not path.exists():
        return series
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            series.setdefault(row["slug"], {})[int(row["year"])] = {
                "percent": float(row["percent"]),
                "million": float(row["million"]),
            }
    return series


def load_budget(path: Path) -> dict[str, dict[int, dict[str, float]]]:
    series: dict[str, dict[int, dict[str, float]]] = {}
    if not path.exists():
        return series
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            values = {name: float(row[name]) for name in SHARE_ORDER if row.get(name) not in (None, "")}
            values["spent"] = float(row["spent"])
            series.setdefault(row["slug"], {})[int(row["year"])] = values
    return series


def community_windows() -> list[dict]:
    windows = []
    start = FIRST_YEAR
    while start <= LAST_YEAR:
        full_end = start + WINDOW_SPAN - 1
        end = min(full_end, LAST_YEAR)
        later_start = full_end + 1
        later_end = later_start + WINDOW_SPAN - 1
        windows.append(
            {
                "id": f"{start}-{end}",
                "start": start,
                "end": end,
                "open": end < full_end,
                "later_start": later_start,
                "later_end": later_end,
                "later_ready": later_end <= LAST_YEAR,
            }
        )
        start += WINDOW_SPAN
    return windows


def policy_shares(totals: dict[str, float], policies: tuple[str, ...]) -> dict[str, float] | None:
    spent = sum(totals[name] for name in policies)
    if spent <= 0:
        return None
    rounded = {name: round(100 * totals[name] / spent, 1) for name in policies}
    gap = round(100 - sum(rounded.values()), 1)
    core = {"health", "education", "care", "housing", "transport", "interest", "pensions"}
    others = [name for name in rounded if name not in core]
    host = "rest" if "rest" in rounded else max(others or list(rounded), key=rounded.get)
    rounded[host] = round(rounded[host] + gap, 1)
    return rounded


def policy_gdp(
    totals: dict[str, float],
    policies: tuple[str, ...],
    gdp_years: dict[int, dict] | None,
    years: list[int],
) -> dict[str, float] | None:
    """Each policy as a percentage of GDP, summed over the same years as the budget."""
    if not gdp_years or not years:
        return None
    economy = 0.0
    for year in years:
        valor = (gdp_years.get(year) or {}).get("valor")
        if valor in (None, 0):
            return None
        economy += float(valor)
    if economy <= 0:
        return None
    return {name: round(100 * totals[name] / economy, 2) for name in policies}


def load_parts(path: Path) -> dict[str, dict[int, dict[str, dict[str, float]]]]:
    series: dict[str, dict[int, dict[str, dict[str, float]]]] = {}
    if not path.exists():
        return series
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            year = series.setdefault(row["slug"], {}).setdefault(int(row["year"]), {})
            year.setdefault(row["parent"], {})[row["part"]] = float(row["amount"])
    return series


def attach_parts(
    shares: dict,
    part_years: dict[int, dict[str, dict[str, float]]] | None,
    years: list[int],
    gdp_years: dict[int, dict] | None,
) -> None:
    """Sub-bars use the same budget scale as the policy they belong to."""
    if not part_years or any(year not in part_years for year in years):
        return
    summed: dict[str, dict[str, float]] = {}
    for year in years:
        for parent, pieces in part_years[year].items():
            bucket = summed.setdefault(parent, {})
            for part, amount in pieces.items():
                bucket[part] = bucket.get(part, 0.0) + amount
    economy = 0.0
    if gdp_years:
        for year in years:
            valor = (gdp_years.get(year) or {}).get("valor")
            if valor in (None, 0):
                economy = 0.0
                break
            economy += float(valor)
    # These stay visible even when they are a tiny share of the budget.
    keep = {"crown", "parliament", "constitutional", "audit", "council", "courts", "embassies", "judicial_council"}
    shown: dict[str, dict[str, float]] = {}
    shown_gdp: dict[str, dict[str, float]] = {}
    for parent, pieces in summed.items():
        parent_share = shares.get(parent)
        total = sum(pieces.values())
        if not parent_share or total <= 0:
            continue
        rounded = {part: round(parent_share * amount / total, 2) for part, amount in pieces.items()}
        for part, amount in pieces.items():
            if part in keep and amount > 0 and rounded.get(part, 0) <= 0:
                rounded[part] = 0.01
        rounded = {part: value for part, value in rounded.items() if value > 0}
        if not rounded:
            continue
        gap = round(parent_share - sum(rounded.values()), 2)
        host = max(rounded, key=rounded.get)
        rounded[host] = round(rounded[host] + gap, 2)
        if rounded[host] <= 0:
            del rounded[host]
        if not rounded:
            continue
        shown[parent] = rounded
        if economy > 0:
            gdp_parts = {}
            for part, amount in pieces.items():
                if part not in rounded:
                    continue
                value = round(100 * amount / economy, 2)
                if value > 0:
                    gdp_parts[part] = value
            if gdp_parts:
                shown_gdp[parent] = gdp_parts
    if shown:
        shares["parts"] = shown
    if shown_gdp:
        shares["parts_gdp"] = shown_gdp


def window_budget(
    budget: dict[str, dict[int, dict[str, float]]],
    slug: str,
    start: int,
    end: int,
    gdp_years: dict[int, dict] | None = None,
    part_years: dict[int, dict[str, dict[str, float]]] | None = None,
) -> dict | None:
    rows = []
    present = set()
    for year in range(start, end + 1):
        row = budget.get(slug, {}).get(year)
        if row is None:
            continue
        rows.append(row)
        present.update(name for name in SHARE_ORDER if name in row)
    if not rows:
        return None
    policies = tuple(name for name in SHARE_ORDER if name in present)
    totals = {name: 0.0 for name in policies}
    years = []
    for year in range(start, end + 1):
        row = budget.get(slug, {}).get(year)
        if row is None:
            continue
        years.append(year)
        for name in policies:
            totals[name] += row.get(name, 0.0)
    # A remainder under one million euros is rounding dust, not a policy.
    if totals.get("rest", 0) < 1000:
        totals.pop("rest", None)
    policies = tuple(name for name in policies if totals.get(name, 0) > 0)
    shares = policy_shares(totals, policies)
    if shares is None:
        return None
    shares["from"] = years[0]
    shares["to"] = years[-1]
    shares["complete"] = years == list(range(start, end + 1))
    of_gdp = policy_gdp(totals, policies, gdp_years, years)
    if of_gdp:
        shares["of_gdp"] = of_gdp
    attach_parts(shares, part_years, years, gdp_years)
    return shares


def window_balance(
    balance: dict[str, dict[int, dict]],
    gdp: dict[str, dict[int, dict]],
    slug: str,
    label: str,
    start: int,
    end: int,
) -> float | None:
    weighted = 0.0
    weight = 0.0
    years = []
    for year in range(start, end + 1):
        row = balance.get(slug, {}).get(year) or {}
        percent = row.get("percent")
        valor = gdp.get(label, {}).get(year, {}).get("valor")
        if percent is None or valor in (None, 0):
            continue
        weighted += percent * valor
        weight += valor
        years.append(year)
    if weight == 0 or years != list(range(start, end + 1)):
        return None
    return round(weighted / weight, 1)


def load_transfers(path: Path) -> dict[str, dict[int, dict[str, float]]]:
    series: dict[str, dict[int, dict[str, float]]] = {}
    if not path.exists():
        return series
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            series.setdefault(row["slug"], {})[int(row["year"])] = {
                "received": float(row["received"]),
                "paid": float(row["paid"]),
            }
    return series


def load_spain(path: Path, balance: dict[str, dict[int, dict]]) -> tuple[dict[int, float], dict[int, float]]:
    """All public administrations, then the central administration. Both in miles de euros."""
    spent: dict[int, float] = {}
    central: dict[int, float] = {}
    if not path.exists():
        return spent, central
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            year = int(row["year"])
            balance.setdefault("espana", {})[year] = {
                "percent": float(row["percent"]),
                "million": float(row["million"]),
            }
            if row.get("spent"):
                spent[year] = float(row["spent"]) * 1000
            if row.get("central"):
                central[year] = float(row["central"]) * 1000
    return spent, central


def load_spain_eu(path: Path) -> dict[int, dict[str, float]]:
    """EU budget in Spain and Spain's payment into it, converted to miles de euros."""
    flows: dict[int, dict[str, float]] = {}
    if not path.exists():
        return flows
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            flows[int(row["year"])] = {
                "received": float(row["received"]) * 1000,
                "paid": float(row["paid"]) * 1000,
            }
    return flows


def load_spain_debt(path: Path) -> dict[int, dict[str, float | None]]:
    """December PDE debt of every public administration, already in miles de euros."""
    stock: dict[int, dict[str, float | None]] = {}
    if not path.exists():
        return stock
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            stock[int(row["year"])] = {
                "total": float(row["total"]),
                "bonds": float(row["bonds"]),
                "bonds_short": float(row["bonds_short"]),
                "bonds_long": float(row["bonds_long"]),
                "loans": float(row["loans"]),
                "fund": None,
            }
    return stock


def window_flow(
    transfers: dict[str, dict[int, dict[str, float]]],
    slug: str,
    start: int,
    end: int,
) -> dict | None:
    """Sum of the block, in miles de euros. Missing years are left out of the sum."""
    received = 0.0
    paid = 0.0
    years = []
    for year in range(start, end + 1):
        row = transfers.get(slug, {}).get(year)
        if row is None:
            continue
        years.append(year)
        received += row["received"]
        paid += row["paid"]
    if not years:
        return None
    return {
        "received": money(received),
        "paid": money(paid),
        "net": money(paid - received),
        "from": years[0],
        "to": years[-1],
    }


def window_community_flow(
    transfers: dict[str, dict[int, dict[str, float]]],
    start: int,
    end: int,
) -> dict | None:
    """What the communities record with the state, summed, in miles de euros."""
    given = 0.0
    back = 0.0
    years = []
    for year in range(start, end + 1):
        year_given = 0.0
        year_back = 0.0
        seen = False
        for slug, by_year in transfers.items():
            if slug == "espana":
                continue
            row = by_year.get(year)
            if row is None:
                continue
            seen = True
            year_given += row["received"]
            year_back += row["paid"]
        if not seen:
            continue
        years.append(year)
        given += year_given
        back += year_back
    if not years:
        return None
    return {
        "given": money(given),
        "back": money(back),
        "net": money(back - given),
        "from": years[0],
        "to": years[-1],
    }


def window_balance_end(balance: dict[str, dict[int, dict]], slug: str, end: int) -> float | None:
    """Last year of the block, in miles de euros."""
    row = balance.get(slug, {}).get(end) or {}
    million = row.get("million")
    if million is None:
        return None
    return money(million * 1000)


def money(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 1)


def window_debt(stock: dict[str, dict[int, dict[str, float | None]]], code: str | None, start: int, end: int) -> dict | None:
    if code is None:
        return None
    series = stock.get(code) or {}
    before = series.get(start - 1) or {}
    after = series.get(end) or {}
    if before.get("total") is None or after.get("total") is None:
        return None
    return {
        "change": money(after["total"] - before["total"]),
        "total": money(after.get("total")),
        "bonds": money(after.get("bonds")),
        "bonds_short": money(after.get("bonds_short")),
        "bonds_long": money(after.get("bonds_long")),
        "loans": money(after.get("loans")),
        "fund": money(after.get("fund")),
    }


def debt_share(total: float | None, gdp_year: dict | None) -> float | None:
    valor = None if gdp_year is None else gdp_year.get("valor")
    if total is None or valor in (None, 0):
        return None
    return round(100 * total / valor, 1)


def window_scale(
    gdp_year: dict | None,
    budget_year: dict | None,
    debt: dict | None,
    end: int,
    gdp_before: dict | None = None,
    debt_before: float | None = None,
) -> dict:
    """Last year of the block, and how the debt ratio moved from the previous block's end."""
    valor = None if gdp_year is None else gdp_year.get("valor")
    spent = None if budget_year is None else budget_year.get("spent")
    total = None if debt is None else debt.get("total")
    share = debt_share(total, gdp_year)
    before = debt_share(debt_before, gdp_before)
    share_change = None if share is None or before is None else round(share - before, 1)
    return {
        "year": end,
        "gdp": money(valor),
        "spent": money(spent),
        "share": share,
        "share_change": share_change,
    }


def load_eu_volume(path: Path) -> dict[str, dict[int, float]]:
    series: dict[str, dict[int, float]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            series.setdefault(row["geo"], {})[int(row["year"])] = float(row["index"])
    return series


def relative_volume(region_index: dict[int, float], baseline_index: dict[int, float]) -> list[dict]:
    """100 means the same level as the baseline in 2000."""
    origin_region = region_index.get(FIRST_YEAR)
    origin_base = baseline_index.get(FIRST_YEAR)
    points = []
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        region = region_index.get(year)
        base = baseline_index.get(year)
        if region is None or base in (None, 0) or origin_region in (None, 0) or origin_base in (None, 0):
            level = None
        else:
            level = round(100 * (region / origin_region) / (base / origin_base), 2)
        points.append({"year": year, "level": level})
    return points


def community_volume(rates: dict[int, float], spain_rates: dict[int, float]) -> list[dict]:
    points = []
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        region = chain_index(rates, year)
        spain = chain_index(spain_rates, year)
        level = None if region is None or spain in (None, 0) else round(100 * region / spain, 2)
        points.append({"year": year, "level": level})
    return points


def region_blocks(
    slug: str,
    label: str,
    rates: dict[int, float],
    spain_volume: dict[int, float],
    gdp: dict[str, dict[int, dict]],
    stock: dict[str, dict[int, dict[str, float | None]]],
    balance: dict[str, dict[int, dict]],
    budget: dict[str, dict[int, dict[str, float]]],
    transfers: dict[str, dict[int, dict[str, float]]],
    windows: list[dict],
    expenditure: dict[int, float] | None = None,
    baseline_index: dict[int, float] | None = None,
    central: dict[int, float] | None = None,
    parts: dict[str, dict[int, dict[str, dict[str, float]]]] | None = None,
) -> list[dict]:
    blocks = []
    for window in windows:
        before_year = FIRST_YEAR if window["start"] == FIRST_YEAR else window["start"] - 1
        region_before = chain_index(rates, before_year)
        region_end = chain_index(rates, window["end"])
        if baseline_index is None:
            base_before = chain_index(spain_volume, before_year)
            base_end = chain_index(spain_volume, window["end"])
        else:
            base_before = baseline_index.get(before_year)
            base_end = baseline_index.get(window["end"])
        during = level_change(region_before, region_end, base_before, base_end)
        growth = relative_percent(region_before, region_end)
        later = None
        later_growth = None
        if window["later_ready"]:
            region_later = chain_index(rates, window["later_end"])
            base_later = chain_index(spain_volume, window["later_end"]) if baseline_index is None else baseline_index.get(window["later_end"])
            later = level_change(region_end, region_later, base_end, base_later)
            later_growth = relative_percent(region_end, region_later)
        debt_code = "APU" if slug == "espana" else DEBT_CODES.get(slug)
        debt = window_debt(stock, debt_code, window["start"], window["end"])
        budget_year = None if slug == "espana" else budget.get(slug, {}).get(window["end"])
        if budget_year is None and expenditure and expenditure.get(window["end"]) is not None:
            budget_year = {"spent": expenditure[window["end"]]}
        blocks.append(
            {
                "id": window["id"],
                "start": window["start"],
                "end": window["end"],
                "open": window["open"],
                "during": during,
                "growth": growth,
                "later": later,
                "later_growth": later_growth,
                "later_ready": window["later_ready"],
                "later_start": window["later_start"],
                "later_end": window["later_end"],
                "balance": window_balance(balance, gdp, slug, label, window["start"], window["end"]),
                "balance_end": window_balance_end(balance, slug, window["end"]),
                "budget": window_budget(
                    budget,
                    slug,
                    window["start"],
                    window["end"],
                    gdp.get(label),
                    None if parts is None else parts.get(slug),
                ),
                "debt": debt,
                "flow": window_flow(transfers, slug, window["start"], window["end"]),
                "state": None if central is None else {
                    "spent": money(central.get(window["end"])),
                    **(window_community_flow(transfers, window["start"], window["end"]) or {"given": None, "back": None, "net": None, "from": None, "to": None}),
                },
                "scale": window_scale(
                    gdp.get(label, {}).get(window["end"]),
                    budget_year,
                    debt,
                    window["end"],
                    gdp.get(label, {}).get(window["start"] - 1),
                    money(((stock.get(debt_code) or {}).get(window["start"] - 1) or {}).get("total")) if debt_code else None,
                ),
            }
        )
    return blocks


def build_communities(
    regions: list[dict],
    volume: dict[str, dict[int, float]],
    spain_volume: dict[int, float],
    gdp: dict[str, dict[int, dict]],
    stock: dict[str, dict[int, dict[str, float | None]]],
    balance: dict[str, dict[int, dict]],
    budget: dict[str, dict[int, dict[str, float]]],
    transfers: dict[str, dict[int, dict[str, float]]],
    expenditure: dict[int, float] | None = None,
    eu_index: dict[int, float] | None = None,
    central: dict[int, float] | None = None,
    parts: dict[str, dict[int, dict[str, dict[str, float]]]] | None = None,
) -> dict:
    windows = community_windows()
    built = []
    for region in regions:
        slug = region["slug"]
        label = INE_LABELS[slug]
        built.append(
            {
                "slug": slug,
                "name": region["name"],
                "foral": slug in FORAL,
                "reference": False,
                "volume": community_volume(volume[volume_name(label)], spain_volume),
                "blocks": region_blocks(
                    slug,
                    label,
                    volume[volume_name(label)],
                    spain_volume,
                    gdp,
                    stock,
                    balance,
                    budget,
                    transfers,
                    windows,
                    parts=parts,
                ),
            }
        )
    spain_label = "Total Nacional"
    spain_index = {year: chain_index(spain_volume, year) for year in range(FIRST_YEAR, LAST_YEAR + 1)}
    built.insert(
        0,
        {
            "slug": "espana",
            "name": "España",
            "foral": False,
            "reference": True,
            "volume": relative_volume(spain_index, eu_index or {}),
            "blocks": region_blocks(
                "espana",
                spain_label,
                spain_volume,
                spain_volume,
                gdp,
                stock,
                balance,
                budget,
                transfers,
                windows,
                expenditure,
                eu_index,
                central,
                parts,
            ),
        },
    )
    return {"windows": windows, "regions": built}


def volume_name(ine_label: str) -> str:
    if ine_label == "Total Nacional":
        return "TOTAL NACIONAL"
    return ine_label.split(" ", 1)[1]


def debt_ratio(debt_thousands: float | None, gdp_thousands: float | None) -> float | None:
    if debt_thousands is None or gdp_thousands in (None, 0):
        return None
    return 100 * debt_thousands / gdp_thousands


def ratio(part: float | None, whole: float | None) -> float | None:
    if part is None or whole in (None, 0):
        return None
    return part / whole


def combine(real: float | None, debt: float | None) -> float | None:
    if real is None or debt is None:
        return None
    return round(real - DEBT_WEIGHT * debt, 1)


def career_result(
    real: float | None,
    debt: float | None,
    schools: float | None,
    health: float | None,
    care: float | None,
) -> float | None:
    if None in (real, debt, schools, health, care):
        return None
    raw = (
        Decimal(str(real))
        - Decimal(str(DEBT_WEIGHT)) * Decimal(str(debt))
        - Decimal(str(schools))
        - Decimal(str(health)) / Decimal(HEALTH_DAYS_PER_POINT)
        - Decimal(str(care))
    )
    return float(raw.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def relative_percent(before: float | None, after: float | None) -> float | None:
    if before in (None, 0) or after is None:
        return None
    return round(100 * (after / before - 1), 1)


def headcount(gdp_thousands: float | None, euros_per_person: float | None) -> float | None:
    if gdp_thousands is None or euros_per_person in (None, 0):
        return None
    return gdp_thousands * 1000 / euros_per_person


def slugify(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    slug = "".join(character if character.isalnum() else "-" for character in folded)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def as_date(value: str | None, fallback: date) -> date:
    return date.fromisoformat(value) if value else fallback


def days_in_year(started: date, ended: date, year: int) -> int:
    first = date(year, 1, 1)
    last = date(year, 12, 31)
    start = max(started, first)
    end = min(ended, last)
    if end < start:
        return 0
    return (end - start).days + 1


def year_length(year: int) -> int:
    return 366 if date(year, 12, 31).timetuple().tm_yday == 366 else 365


def gaps(terms: list[dict]) -> list[tuple[date, date]]:
    cursor = date(2001, 1, 1)
    limit = date(LAST_YEAR, 12, 31)
    found = []
    for term in terms:
        started = date.fromisoformat(term["started_on"])
        if started > cursor:
            found.append((cursor, started - timedelta(days=1)))
        ended = as_date(term["ended_on"], limit)
        if ended >= cursor:
            cursor = ended + timedelta(days=1)
    if cursor <= limit:
        found.append((cursor, limit))
    return found


def cabinet_for(term: dict, members: list[dict]) -> list[dict]:
    term_start = term["started_on"]
    term_end = term["ended_on"] or "9999-12-31"
    chosen = []
    for member in members:
        if not member.get("started_on"):
            continue
        member_end = member["ended_on"] or "9999-12-31"
        if member["started_on"] <= term_end and member_end >= term_start:
            chosen.append(
                {
                    "name": member["name"],
                    "office": member["office"],
                    "started_on": member["started_on"],
                    "ended_on": member["ended_on"],
                    "wikidata_id": member.get("wikidata_id") or "",
                }
            )
    chosen.sort(key=lambda member: (member["started_on"], member["name"]))
    return chosen


def load_levels(path: Path, value: str) -> dict[str, dict[int, float]]:
    series: dict[str, dict[int, float]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            series.setdefault(row["slug"], {})[int(row["year"])] = float(row[value])
    return series


def point_gap(
    region: dict[int, float] | None,
    spain: dict[int, float],
    before: int,
    after: int,
) -> tuple[float | None, float | None, float | None]:
    """How the region's level moved against Spain, in the series' own units.

    A negative result means the region improved more than Spain when a lower
    level is better: fewer waiting days, a lower school-leaving rate, or a
    smaller share of dependent people still waiting.
    """
    if region is None:
        return None, None, None
    region_before = region.get(before)
    region_after = region.get(after)
    spain_before = spain.get(before)
    spain_after = spain.get(after)
    if None in (region_before, region_after, spain_before, spain_after):
        return None, None, None
    change = (region_after - spain_after) - (region_before - spain_before)
    return round(region_before, 1), round(region_after, 1), round(change, 1)


def level_change(before: float | None, after: float | None, spain_before: float | None, spain_after: float | None) -> float | None:
    return relative_percent(ratio(before, spain_before), ratio(after, spain_after))


def score_term(
    term: dict,
    per_capita: dict[int, dict],
    total: dict[int, dict],
    spain_per_capita: dict[int, dict],
    spain_total: dict[int, dict],
    volume: dict[int, float],
    spain_volume: dict[int, float],
    jobs: dict[int, dict[str, float]],
    spain_jobs: dict[int, dict[str, float]],
    debt: dict[int, float] | None,
    health: dict[int, float] | None,
    spain_health: dict[int, float],
    schools: dict[int, float] | None,
    spain_schools: dict[int, float],
    care: dict[int, float] | None,
    spain_care: dict[int, float],
    health_break_year: int | None = None,
) -> dict:
    started = date.fromisoformat(term["started_on"])
    ended = as_date(term["ended_on"], date(LAST_YEAR, 12, 31))
    years = []
    for year in range(max(FIRST_YEAR, started.year), min(LAST_YEAR, ended.year) + 1):
        held = days_in_year(started, ended, year)
        majority = held * 2 > year_length(year)
        region_growth = total.get(year, {}).get("growth")
        spain_growth = spain_total.get(year, {}).get("growth")
        counted = majority and region_growth is not None and spain_growth is not None
        share = ratio(total.get(year, {}).get("valor"), spain_total.get(year, {}).get("valor"))
        years.append(
            {
                "year": year,
                "days": held,
                "counted": counted,
                "region_growth": region_growth,
                "spain_growth": spain_growth,
                "excess": round(region_growth - spain_growth, 2) if counted else None,
                "index": per_capita.get(year, {}).get("index"),
                "share": round(share * 100, 3) if share is not None else None,
            }
        )
    counted_years = [year for year in years if year["counted"]]
    scored = {
        "years": years,
        "scored_years": len(counted_years),
        "first_year": counted_years[0]["year"] if counted_years else None,
        "last_year": counted_years[-1]["year"] if counted_years else None,
        "avg_region_growth": None,
        "avg_spain_growth": None,
        "excess_growth": None,
        "output_change": None,
        "share_before": None,
        "share_after": None,
        "index_before": None,
        "index_after": None,
        "index_change": None,
        "people_change": None,
        "population_before": None,
        "population_after": None,
        "real_change": None,
        "public_jobs_change": None,
        "private_jobs_change": None,
        "debt_before": None,
        "debt_after": None,
        "debt_change": None,
        "health_before": None,
        "health_after": None,
        "health_change": None,
        "health_break": False,
        "health_starts_on_break": False,
        "health_break_open_days": None,
        "health_old_days": None,
        "schools_before": None,
        "schools_after": None,
        "schools_change": None,
        "care_before": None,
        "care_after": None,
        "care_change": None,
        "result": None,
        "verdict": "short",
        "versus_spain": None,
        "peer_rank": None,
        "peer_count": None,
    }
    if not counted_years:
        return scored
    scored["avg_region_growth"] = round(sum(year["region_growth"] for year in counted_years) / len(counted_years), 2)
    scored["avg_spain_growth"] = round(sum(year["spain_growth"] for year in counted_years) / len(counted_years), 2)
    scored["excess_growth"] = round(scored["avg_region_growth"] - scored["avg_spain_growth"], 2)
    before_year = scored["first_year"] - 1
    after_year = scored["last_year"]
    share_before = ratio(total.get(before_year, {}).get("valor"), spain_total.get(before_year, {}).get("valor"))
    share_after = ratio(total.get(after_year, {}).get("valor"), spain_total.get(after_year, {}).get("valor"))
    scored["output_change"] = relative_percent(share_before, share_after)
    if share_before is not None:
        scored["share_before"] = round(share_before * 100, 2)
    if share_after is not None:
        scored["share_after"] = round(share_after * 100, 2)
    before_index = per_capita.get(before_year, {})
    after_index = per_capita.get(after_year, {})
    scored["index_before"] = before_index.get("index")
    scored["index_after"] = after_index.get("index")
    if scored["index_before"] is not None and scored["index_after"] is not None:
        scored["index_change"] = round(scored["index_after"] - scored["index_before"], 1)
    pop_before = headcount(total.get(before_year, {}).get("valor"), before_index.get("valor"))
    pop_after = headcount(total.get(after_year, {}).get("valor"), after_index.get("valor"))
    spain_pop_before = headcount(spain_total.get(before_year, {}).get("valor"), spain_per_capita.get(before_year, {}).get("valor"))
    spain_pop_after = headcount(spain_total.get(after_year, {}).get("valor"), spain_per_capita.get(after_year, {}).get("valor"))
    scored["people_change"] = relative_percent(ratio(pop_before, spain_pop_before), ratio(pop_after, spain_pop_after))
    if pop_before is not None:
        scored["population_before"] = round(pop_before)
    if pop_after is not None:
        scored["population_after"] = round(pop_after)
    scored["real_change"] = level_change(
        chain_index(volume, before_year),
        chain_index(volume, after_year),
        chain_index(spain_volume, before_year),
        chain_index(spain_volume, after_year),
    )
    for sector, key in (("public", "public_jobs_change"), ("private", "private_jobs_change")):
        scored[key] = level_change(
            jobs.get(before_year, {}).get(sector),
            jobs.get(after_year, {}).get(sector),
            spain_jobs.get(before_year, {}).get(sector),
            spain_jobs.get(after_year, {}).get(sector),
        )
    if debt is not None:
        before_ratio = debt_ratio(debt.get(before_year), total.get(before_year, {}).get("valor"))
        after_ratio = debt_ratio(debt.get(after_year), total.get(after_year, {}).get("valor"))
        if before_ratio is not None and after_ratio is not None:
            scored["debt_before"] = round(before_ratio, 1)
            scored["debt_after"] = round(after_ratio, 1)
            scored["debt_change"] = round(after_ratio - before_ratio, 1)
    health_before, health_after, health_change = point_gap(
        health, spain_health, before_year, after_year
    )
    crosses_break = (
        health_change is not None
        and health_break_year is not None
        and before_year < health_break_year <= after_year
    )
    starts_on_break = (
        health_change is not None
        and health_break_year is not None
        and before_year == health_break_year
    )
    if crosses_break:
        health_before = health_after = health_change = None
    scored["health_before"] = health_before
    scored["health_after"] = health_after
    scored["health_change"] = health_change
    scored["health_break"] = crosses_break
    scored["health_starts_on_break"] = starts_on_break
    open_days = health.get(health_break_year) if starts_on_break and health else None
    old_days = health.get(health_break_year - 1) if starts_on_break and health else None
    scored["health_break_open_days"] = round(open_days) if open_days is not None else None
    scored["health_old_days"] = round(old_days) if old_days is not None else None
    scored["schools_before"], scored["schools_after"], scored["schools_change"] = point_gap(
        schools, spain_schools, before_year, after_year
    )
    scored["care_before"], scored["care_after"], scored["care_change"] = point_gap(
        care, spain_care, before_year, after_year
    )
    scored["result"] = combine(scored["real_change"], scored["debt_change"])
    excess = scored["excess_growth"]
    if excess > 0.5:
        scored["versus_spain"] = "faster"
    elif excess < -0.5:
        scored["versus_spain"] = "slower"
    else:
        scored["versus_spain"] = "similar"
    return scored


def assign_peers(terms: list[dict]) -> None:
    judged = [term for term in terms if term["score"]["scored_years"] >= 2]
    judged.sort(key=lambda term: (-term["score"]["excess_growth"], term["started_on"], term["name"]))
    total = len(judged)
    ahead_cut = math.ceil(total / 3)
    mid_cut = math.ceil(2 * total / 3)
    previous_excess = None
    previous_rank = 0
    for index, term in enumerate(judged, start=1):
        excess = term["score"]["excess_growth"]
        rank = previous_rank if excess == previous_excess else index
        previous_excess = excess
        previous_rank = rank
        if rank <= ahead_cut:
            verdict = "ahead"
        elif rank <= mid_cut:
            verdict = "mid"
        else:
            verdict = "behind"
        term["score"]["verdict"] = verdict
        term["score"]["peer_rank"] = rank
        term["score"]["peer_count"] = total


def build_leaders(terms: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = {}
    for term in terms:
        grouped.setdefault((term["name"], term["region_slug"]), []).append(term)
    leaders = []
    for spells in grouped.values():
        spells.sort(key=lambda term: term["started_on"])
        counted = [
            year
            for spell in spells
            for year in spell["score"]["years"]
            if year["counted"] and year["excess"] is not None
        ]
        incomplete = any(
            spell["score"]["scored_years"] and spell["score"]["output_change"] is None
            for spell in spells
        )
        output_changes = [spell["score"]["output_change"] for spell in spells if spell["score"]["output_change"] is not None]
        index_changes = [spell["score"]["index_change"] for spell in spells if spell["score"]["index_change"] is not None]
        scored_spells = [spell for spell in spells if spell["score"]["scored_years"]]
        people_values = [spell["score"]["people_change"] for spell in scored_spells]
        output_gained = round(sum(output_changes), 1) if output_changes and not incomplete else None
        index_gained = round(sum(index_changes), 1) if index_changes else None
        people_change = sum_complete(people_values)
        real_gained = sum_complete([spell["score"]["real_change"] for spell in scored_spells])
        public_jobs_change = sum_complete([spell["score"]["public_jobs_change"] for spell in scored_spells])
        private_jobs_change = sum_complete([spell["score"]["private_jobs_change"] for spell in scored_spells])
        debt_change = sum_complete([spell["score"]["debt_change"] for spell in scored_spells])
        health_change = sum_complete([spell["score"]["health_change"] for spell in scored_spells])
        schools_change = sum_complete([spell["score"]["schools_change"] for spell in scored_spells])
        care_change = sum_complete([spell["score"]["care_change"] for spell in scored_spells])
        break_start = next((spell["score"] for spell in scored_spells if spell["score"]["health_starts_on_break"]), None)
        result = combine(real_gained, debt_change)
        worst = min(counted, key=lambda year: (year["excess"], year["year"])) if counted else None
        parties = []
        for spell in spells:
            if spell["party"] and spell["party"] not in parties:
                parties.append(spell["party"])
        leaders.append(
            {
                "slug": spells[0]["slug"],
                "name": spells[0]["name"],
                "party": " · ".join(parties),
                "region_slug": spells[0]["region_slug"],
                "region_name": spells[0]["region_name"],
                "spells": [
                    {
                        "slug": spell["slug"],
                        "started_on": spell["started_on"],
                        "ended_on": spell["ended_on"],
                        "counted_years": spell["score"]["scored_years"],
                        "first_year": spell["score"]["first_year"],
                        "last_year": spell["score"]["last_year"],
                        "index_before": spell["score"]["index_before"],
                        "index_after": spell["score"]["index_after"],
                        "index_change": spell["score"]["index_change"],
                        "output_change": spell["score"]["output_change"],
                        "share_before": spell["score"]["share_before"],
                        "share_after": spell["score"]["share_after"],
                        "people_change": spell["score"]["people_change"],
                        "population_before": spell["score"]["population_before"],
                        "population_after": spell["score"]["population_after"],
                        "real_change": spell["score"]["real_change"],
                        "public_jobs_change": spell["score"]["public_jobs_change"],
                        "private_jobs_change": spell["score"]["private_jobs_change"],
                        "debt_before": spell["score"]["debt_before"],
                        "debt_after": spell["score"]["debt_after"],
                        "debt_change": spell["score"]["debt_change"],
                        "health_before": spell["score"]["health_before"],
                        "health_after": spell["score"]["health_after"],
                        "health_change": spell["score"]["health_change"],
                        "schools_before": spell["score"]["schools_before"],
                        "schools_after": spell["score"]["schools_after"],
                        "schools_change": spell["score"]["schools_change"],
                        "care_before": spell["score"]["care_before"],
                        "care_after": spell["score"]["care_after"],
                        "care_change": spell["score"]["care_change"],
                        "health_break": spell["score"]["health_break"],
                        "health_starts_on_break": spell["score"]["health_starts_on_break"],
                        "health_break_open_days": spell["score"]["health_break_open_days"],
                        "health_old_days": spell["score"]["health_old_days"],
                        "result": spell["score"]["result"],
                    }
                    for spell in spells
                ],
                "counted_years": len(counted),
                "output_gained": output_gained,
                "index_gained": index_gained,
                "people_change": people_change,
                "real_gained": real_gained,
                "public_jobs_change": public_jobs_change,
                "private_jobs_change": private_jobs_change,
                "debt_change": debt_change,
                "health_change": health_change,
                "health_starts_on_break": break_start is not None,
                "health_break_open_days": None if break_start is None else break_start["health_break_open_days"],
                "health_old_days": None if break_start is None else break_start["health_old_days"],
                "schools_change": schools_change,
                "care_change": care_change,
                "health_for_score": health_change,
                "schools_for_score": schools_change,
                "care_for_score": care_change,
                "health_filled": False,
                "schools_filled": False,
                "care_filled": False,
                "result": result,
                "excess_sum": round(sum(year["excess"] for year in counted), 2) if counted else None,
                "worst_year": worst["year"] if worst else None,
                "worst_excess": worst["excess"] if worst else None,
                "eligible": False,
                "rank": None,
                "ranked_count": None,
            }
        )
    assign_ranks(leaders)
    return leaders


def worst_measured(leaders: list[dict], key: str) -> dict | None:
    pool = [leader for leader in leaders if leader[key] is not None]
    if not pool:
        return None
    return max(pool, key=lambda leader: (leader[key], leader["name"]))


def apply_service_scores(leaders: list[dict]) -> dict[str, dict | None]:
    """Score a missing service as the worst measured career change.

    The column stays the measured figure. The fill is used only in the score.
    A career is missing when any spell lacks that series, and the fill replaces
    the whole career once.
    """
    worsts = {
        "health_change": worst_measured(leaders, "health_change"),
        "schools_change": worst_measured(leaders, "schools_change"),
        "care_change": worst_measured(leaders, "care_change"),
    }
    for leader in leaders:
        for key, worst in worsts.items():
            short = key.removesuffix("_change")
            if leader[key] is None and worst is not None:
                leader[f"{short}_for_score"] = worst[key]
                leader[f"{short}_filled"] = True
            else:
                leader[f"{short}_for_score"] = leader[key]
                leader[f"{short}_filled"] = False
        leader["result"] = career_result(
            leader["real_gained"],
            leader["debt_change"],
            leader["schools_for_score"],
            leader["health_for_score"],
            leader["care_for_score"],
        )
    assign_ranks(leaders)
    return worsts


def assign_ranks(leaders: list[dict]) -> None:
    for leader in leaders:
        leader["eligible"] = leader["result"] is not None and leader["counted_years"] >= MIN_CAREER_YEARS
        leader["rank"] = None
        leader["ranked_count"] = None
    ranked = [leader for leader in leaders if leader["eligible"]]
    ranked.sort(key=lambda leader: (-leader["result"], leader["name"]))
    total = len(ranked)
    previous_gained = None
    previous_rank = 0
    for index, leader in enumerate(ranked, start=1):
        gained = leader["result"]
        rank = previous_rank if gained == previous_gained else index
        previous_gained = gained
        previous_rank = rank
        leader["rank"] = rank
        leader["ranked_count"] = total
    leaders.sort(key=lambda leader: (leader["rank"] is None, leader["rank"] or 0, leader["name"]))


def sum_complete(values: list[float | None]) -> float | None:
    if not values or any(value is None for value in values):
        return None
    return round(sum(values), 1)


def public_series(
    per_capita: dict[int, dict],
    total: dict[int, dict],
    spain_total: dict[int, dict],
) -> dict[str, dict]:
    exported = {}
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        person = per_capita.get(year, {})
        economy = total.get(year, {})
        share = ratio(economy.get("valor"), spain_total.get(year, {}).get("valor"))
        exported[str(year)] = {
            "valor": person.get("valor"),
            "index": person.get("index"),
            "gdp": economy.get("valor"),
            "growth": economy.get("growth"),
            "share": round(share * 100, 3) if share is not None else None,
            "population": (
                round(headcount(economy.get("valor"), person.get("valor")))
                if headcount(economy.get("valor"), person.get("valor")) is not None
                else None
            ),
        }
    return exported


def main() -> None:
    if not PEOPLE_PATH.exists():
        raise SystemExit("Missing data/people.json. Run ./download.sh first.")
    required = (GDP_PATH, PER_CAPITA_PATH, VOLUME_PATH, JOBS_PATH, DEBT_PATH, HEALTH_PATH, SCHOOLS_PATH, CARE_PATH)
    missing = [path.name for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Missing {', '.join(missing)}. Run ./download.sh first.")
    per_capita = load_table(PER_CAPITA_PATH, PER_CAPITA_MAGNITUDES)
    total = load_table(GDP_PATH, GDP_MAGNITUDES)
    volume = load_volume(VOLUME_PATH)
    jobs = load_jobs(JOBS_PATH)
    debt = load_debt(DEBT_PATH)
    health = load_levels(HEALTH_PATH, "days")
    schools = load_levels(SCHOOLS_PATH, "rate")
    care = load_levels(CARE_PATH, "rate")
    people = json.loads(PEOPLE_PATH.read_text(encoding="utf-8"))
    spain_per_capita = per_capita["Total Nacional"]
    spain_total = total["Total Nacional"]
    spain_volume = volume["TOTAL NACIONAL"]
    spain_jobs = jobs["Total Nacional"]
    used_slugs: set[str] = set()
    all_terms: list[dict] = []
    regions = []
    gap_problems = []

    for region in people["regions"]:
        label = INE_LABELS[region["slug"]]
        regional_per_capita = per_capita[label]
        regional_total = total[label]
        regional_volume = volume[volume_name(label)]
        regional_jobs = jobs[EPA_LABELS[region["slug"]]]
        regional_debt = debt.get(DEBT_CODES[region["slug"]]) if region["slug"] in DEBT_CODES else None
        state_run = region["slug"] in STATE_SERVICES
        regional_health = None if state_run else health.get(region["slug"])
        regional_schools = None if state_run else schools.get(region["slug"])
        regional_care = None if state_run else care.get(region["slug"])
        terms = []
        for source in region["presidents"]:
            base = slugify(source["name"])
            slug = base
            if slug in used_slugs:
                slug = f"{base}-{region['slug']}"
            suffix = 2
            while slug in used_slugs:
                slug = f"{base}-{region['slug']}-{suffix}"
                suffix += 1
            used_slugs.add(slug)
            term = {
                "slug": slug,
                "name": source["name"],
                "party": source.get("party") or "",
                "region_slug": region["slug"],
                "region_name": region["name"],
                "started_on": source["started_on"],
                "ended_on": source.get("ended_on"),
                "wikidata_id": source.get("wikidata_id") or "",
                "president_source": region.get("president_source") or "",
                "cabinet": cabinet_for(source, region.get("members") or []),
                "score": score_term(
                    source,
                    regional_per_capita,
                    regional_total,
                    spain_per_capita,
                    spain_total,
                    regional_volume,
                    spain_volume,
                    regional_jobs,
                    spain_jobs,
                    regional_debt,
                    regional_health,
                    health["spain"],
                    regional_schools,
                    schools["spain"],
                    regional_care,
                    care["spain"],
                    HEALTH_BREAKS.get(region["slug"]),
                ),
            }
            terms.append(term)
            all_terms.append(term)
        for start, end in gaps(region["presidents"]):
            length = (end - start).days + 1
            if length >= GAP_NOTE_DAYS:
                print(f"gap {region['slug']:20} {start.isoformat()} → {end.isoformat()} ({length} days)")
                if length > 100 and region["slug"] != "cataluna":
                    gap_problems.append(region["slug"])
        regions.append(
            {
                "slug": region["slug"],
                "name": region["name"],
                "ine_label": label,
                "president_source": region.get("president_source") or "",
                "series": public_series(regional_per_capita, regional_total, spain_total),
                "presidents": [
                    {
                        "slug": term["slug"],
                        "name": term["name"],
                        "party": term["party"],
                        "started_on": term["started_on"],
                        "ended_on": term["ended_on"],
                    }
                    for term in terms
                ],
                "members": region.get("members") or [],
            }
        )

    assign_peers(all_terms)
    leaders = build_leaders(all_terms)
    service_worsts = apply_service_scores(leaders)
    balance = load_balance(BALANCE_PATH)
    expenditure, central = load_spain(SPAIN_PATH, balance)
    transfers = load_transfers(TRANSFERS_PATH)
    transfers["espana"] = load_spain_eu(SPAIN_EU_PATH)
    stock = load_debt_stock(DEBT_PATH)
    stock["APU"] = load_spain_debt(SPAIN_DEBT_PATH)
    eu_volume = load_eu_volume(EU_VOLUME_PATH)
    eu_index = eu_volume["EU27_2020"]
    state_budget = load_budget(SPAIN_BUDGET_PATH)
    state_budget_years = sorted(state_budget.get("espana", {}))
    communities = build_communities(
        people["regions"],
        volume,
        spain_volume,
        total,
        stock,
        balance,
        load_budget(BUDGET_PATH) | state_budget,
        transfers,
        expenditure,
        eu_index,
        central,
        load_parts(PARTS_PATH),
    )
    store = {
        "meta": {
            "gdp_table": "80109",
            "gdp_url": "https://www.ine.es/jaxiT3/Tabla.htm?t=80109&L=0",
            "gdp_title": "PIB a precios de mercado, precios corrientes",
            "per_capita_table": "80110",
            "per_capita_url": "https://www.ine.es/jaxiT3/Tabla.htm?t=80110&L=0",
            "per_capita_title": "PIB per cápita a precios corrientes",
            "volume_url": "https://www.ine.es/daco/daco42/cre00/b2024/pr_cre_26.xls",
            "volume_title": "Contabilidad Regional de España, variaciones de volumen",
            "jobs_table": "65321",
            "jobs_url": "https://www.ine.es/jaxiT3/Tabla.htm?t=65321&L=0",
            "jobs_title": "Ocupados por tipo de sector (público o privado)",
            "jobs_first_year": JOBS_FIRST_YEAR,
            "debt_url": "https://www.bde.es/webbe/es/estadisticas/temas/administraciones-publicas.html",
            "debt_file": "https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/be1306.csv",
            "debt_title": "Deuda según el Protocolo de Déficit Excesivo, comunidades autónomas",
            "health_url": "https://www.sanidad.gob.es/estadEstudios/estadisticas/inforRecopilaciones/listaEspera.htm",
            "health_title": "Tiempo medio de espera quirúrgica, 31 de diciembre",
            "health_first_year": min(health["spain"]),
            "schools_url": "https://ec.europa.eu/eurostat/databrowser/view/edat_lfse_16/default/table",
            "schools_title": "Abandono temprano de la educación-formación, 18 a 24 años",
            "schools_first_year": min(schools["spain"]),
            "care_url": "https://imserso.es/el-imserso/documentacion/estadisticas/sistema-autonomia-atencion-dependencia-saad",
            "care_title": "Personas con derecho a dependencia pendientes de un plan de atención",
            "care_first_year": min(care["spain"]),
            "balance_url": "https://www.igae.pap.hacienda.gob.es/sitios/igae/es-ES/Contabilidad/ContabilidadNacional/Publicaciones/Paginas/ianofinancierasCA.aspx",
            "balance_title": "Capacidad o necesidad de financiación de la administración regional",
            "budget_url": "https://serviciostelematicosext.hacienda.gob.es/SGCIEF/PublicacionLiquidaciones/aspx/menuInicio.aspx",
            "budget_title": "Liquidación de los presupuestos de las comunidades autónomas, clasificación funcional",
            "state_budget_url": "https://www.igae.pap.hacienda.gob.es/sitios/igae/es-ES/Contabilidad/ContabilidadPublica/CPE/EjecucionPresupuestaria/Paginas/ialiquidacionestado.aspx",
            "state_budget_title": "Liquidación del presupuesto del Estado",
            "state_budget_from": state_budget_years[0],
            "state_budget_to": state_budget_years[-1],
            "spain_url": "https://www.igae.pap.hacienda.gob.es/sitios/igae/es-ES/Contabilidad/ContabilidadNacional/Publicaciones/Paginas/ianofinancierasTotal.aspx",
            "spain_title": "Cuentas de las administraciones públicas",
            "central_url": "https://www.igae.pap.hacienda.gob.es/sitios/igae/es-ES/Contabilidad/ContabilidadNacional/Publicaciones/Documents/AACC-A/A_AACC.xlsx",
            "central_title": "Administración central, operaciones no financieras",
            "central_from": min(central) if central else None,
            "central_to": max(central) if central else None,
            "flow_url": "https://serviciostelematicosext.hacienda.gob.es/SGCIEF/PublicacionLiquidaciones/aspx/menuInicio.aspx",
            "flow_title": "Liquidación de los presupuestos de las comunidades autónomas, ingresos y gastos",
            "flow_last_year": max((year for slug, by_year in transfers.items() if slug != "espana" for year in by_year), default=None),
            "spain_debt_url": "https://www.bde.es/webbe/es/estadisticas/temas/administraciones-publicas.html",
            "spain_debt_file": "https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/be1112.csv",
            "spain_debt_title": "Deuda según el Protocolo de Déficit Excesivo, todas las administraciones públicas",
            "eu_url": "https://commission.europa.eu/strategy-and-policy/eu-budget/long-term-eu-budget/2021-2027/spending-and-revenue_en",
            "eu_title": "EU budget spending and revenue, 2000–2025",
            "eu_volume_url": "https://ec.europa.eu/eurostat/databrowser/view/nama_10_gdp/default/table",
            "eu_volume_title": "PIB, volumen encadenado, índice 2015=100",
            "eu_volume_from": min(eu_index),
            "eu_volume_to": max(eu_index),
            "years": [FIRST_YEAR, LAST_YEAR],
            "people_file": "data/people.json",
            "min_career_years": MIN_CAREER_YEARS,
            "debt_weight": DEBT_WEIGHT,
            "health_days_per_point": HEALTH_DAYS_PER_POINT,
            "health_break_year": HEALTH_BREAKS["andalucia"],
            "health_worst": None if service_worsts["health_change"] is None else service_worsts["health_change"]["health_change"],
            "health_worst_name": None if service_worsts["health_change"] is None else service_worsts["health_change"]["name"],
            "health_worst_years": None if service_worsts["health_change"] is None else service_worsts["health_change"]["counted_years"],
            "schools_worst": None if service_worsts["schools_change"] is None else service_worsts["schools_change"]["schools_change"],
            "schools_worst_name": None if service_worsts["schools_change"] is None else service_worsts["schools_change"]["name"],
            "schools_worst_years": None if service_worsts["schools_change"] is None else service_worsts["schools_change"]["counted_years"],
            "care_worst": None if service_worsts["care_change"] is None else service_worsts["care_change"]["care_change"],
            "care_worst_name": None if service_worsts["care_change"] is None else service_worsts["care_change"]["name"],
            "care_worst_years": None if service_worsts["care_change"] is None else service_worsts["care_change"]["counted_years"],
            "method": (
                "One row is one person. A year counts when they held the job for most of it. "
                "The score is real growth against Spain, minus half the rise in the debt "
                "ratio, minus school leaving, minus the care queue, minus surgical waits "
                "with ten days counted as one point. A missing service figure uses the worst "
                "measured change. Four counted years are required, and the community has to "
                "be in the debt series. Current-price GDP, GDP per person, population, and "
                "jobs are shown beside the score and do not change it."
            ),
        },
        "spain": public_series(spain_per_capita, spain_total, spain_total),
        "regions": regions,
        "terms": all_terms,
        "leaders": leaders,
        "communities": communities,
    }
    OUT.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ranked = [leader for leader in leaders if leader["eligible"]]
    print(f"Wrote {OUT} ({len(all_terms)} terms, {len(ranked)} ranked people)")
    for leader in ranked:
        spells = len(leader["spells"])
        def fmt(value: float | None) -> str:
            return f"{value:+6.1f}" if value is not None else "   n/a"
        print(
            f"{leader['rank']:3} score {leader['result']:+6.1f}  "
            f"out {leader['output_gained']:+6.1f}  "
            f"real {fmt(leader['real_gained'])}  "
            f"person {fmt(leader['index_gained'])}  "
            f"people {fmt(leader['people_change'])}  "
            f"pub {fmt(leader['public_jobs_change'])}  "
            f"priv {fmt(leader['private_jobs_change'])}  "
            f"debt {fmt(leader['debt_change'])}  "
            f"hea {fmt(leader['health_change'])}  "
            f"sch {fmt(leader['schools_change'])}  "
            f"care {fmt(leader['care_change'])}  "
            f"{leader['counted_years']:2}y {spells}sp  "
            f"{leader['name'][:28]:28} {leader['region_name'][:22]:22} worst {leader['worst_year']}"
        )
    if gap_problems:
        raise SystemExit(f"Unexplained gaps in: {', '.join(gap_problems)}")


if __name__ == "__main__":
    main()
