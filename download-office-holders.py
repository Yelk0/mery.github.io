#!/usr/bin/env python3
"""Download who governed each Spanish region.

Writes data/people.json: regional presidents, and the cabinet members
(consejeros, consellers, vicepresidents) Wikidata records for each community.
GDP stays in data/80110.csv. interpret.py joins the two and writes data/store.json.

Presidents come from Wikidata position-held statements. Where the Spanish
Wikipedia list is cleaner, that list replaces Wikidata. data/office-corrections.json
fills holes Wikidata still leaves (a missing term, or a year stored as 1 January).
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "people.json"
CORRECTIONS = ROOT / "data" / "office-corrections.json"
CACHE = ROOT / "data" / "wikipedia"
PRESIDENTS_RAW = ROOT / "data" / "wikidata-presidents-raw.json"
MEMBERS_RAW = ROOT / "data" / "wikidata-members-raw.json"
API = "https://es.wikipedia.org/api/rest_v1/page/html/{}"
USER_AGENT = "plan-mery/1.0 (regional GDP comparison; local research)"

# slug, display name, Wikipedia titles to try in order
REGIONS = [
    ("andalucia", "Andalucía", ["Anexo:Presidentes de la Junta de Andalucía", "Presidente de la Junta de Andalucía"]),
    ("aragon", "Aragón", ["Anexo:Presidentes del Gobierno de Aragón", "Presidente del Gobierno de Aragón"]),
    ("asturias", "Asturias", ["Anexo:Presidentes del Principado de Asturias"]),
    ("baleares", "Illes Balears", ["Anexo:Presidentes de las Islas Baleares", "Presidente del Gobierno de las Islas Baleares"]),
    ("canarias", "Canarias", ["Anexo:Presidentes del Gobierno de Canarias", "Presidente del Gobierno de Canarias"]),
    ("cantabria", "Cantabria", ["Anexo:Presidentes de Cantabria"]),
    ("castilla-y-leon", "Castilla y León", ["Anexo:Presidentes de la Junta de Castilla y León", "Presidente de la Junta de Castilla y León"]),
    (
        "castilla-la-mancha",
        "Castilla-La Mancha",
        [
            "Anexo:Presidentes de la Junta de Comunidades de Castilla-La Mancha",
            "Presidente de la Junta de Comunidades de Castilla-La Mancha",
        ],
    ),
    ("cataluna", "Cataluña", ["Anexo:Presidentes de la Generalidad de Cataluña", "Presidente de la Generalidad de Cataluña"]),
    ("valencia", "Comunitat Valenciana", ["Anexo:Presidentes de la Generalidad Valenciana", "Presidente de la Generalidad Valenciana"]),
    ("extremadura", "Extremadura", ["Anexo:Presidentes de la Junta de Extremadura", "Presidente de la Junta de Extremadura"]),
    (
        "galicia",
        "Galicia",
        ["Anexo:Presidentes de la Xunta de Galicia", "Presidente de la Xunta de Galicia"],
    ),
    ("madrid", "Comunidad de Madrid", ["Anexo:Presidentes de la Comunidad de Madrid"]),
    ("murcia", "Región de Murcia", ["Presidente de la Región de Murcia"]),
    ("navarra", "Navarra", ["Anexo:Presidentes del Gobierno de Navarra", "Presidente del Gobierno de Navarra"]),
    ("pais-vasco", "País Vasco", ["Anexo:Lehendakaris"]),
    ("la-rioja", "La Rioja", ["Anexo:Presidentes de La Rioja", "Presidente de La Rioja"]),
    (
        "ceuta",
        "Ceuta",
        ["Anexo:Presidentes de Ceuta", "Presidente de Ceuta"],
    ),
    (
        "melilla",
        "Melilla",
        ["Anexo:Presidentes de Melilla", "Presidente de Melilla"],
    ),
]

MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}
# "6 de junio de 1983", "6 de juniode 1983", and "22 de abril1978".
DATE_RE = re.compile(
    r"(\d{1,2})\s+de\s+(" + "|".join(MONTHS) + r")\s*(?:de\s*)?(\d{4})",
    re.IGNORECASE,
)
NUM_RE = re.compile(r"\b(\d{1,2})-(\d{1,2})-(\d{4})\b")
PARTY_RE = re.compile(
    r"\b(PSOE|FSA|PP|PNV|EAJ|IU|UCD|CDS|CC|PAR|PRC|CiU|JxCat|ERC|PSC|UPN|"
    r"Geroa|Cs|Vox|FORO|FAC|NC|CpM|GIL|Podemos|Sumar|CHA|UV|BNG|CCa)\b",
    re.IGNORECASE,
)
# Keep terms that can touch the GDP series (2000–latest) or the year before it.
KEEP_FROM = date(1999, 1, 1)


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_table = 0
        self.skip = 0
        self.in_cell = False
        self.tables: list[list[list[str]]] = []
        self.rows: list[list[str]] = []
        self.row: list[str] = []
        self.buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.in_table += 1
            if self.in_table == 1:
                self.rows = []
        if tag in {"sup", "style", "script"}:
            self.skip += 1
        if self.in_table == 1 and self.skip == 0 and tag == "tr":
            self.row = []
        if self.in_table == 1 and self.skip == 0 and tag in {"td", "th"}:
            self.in_cell = True
            self.buf = []
        if self.in_cell and self.skip == 0 and tag in {"a", "br"}:
            self.buf.append(" ")

    def handle_endtag(self, tag):
        if tag in {"sup", "style", "script"} and self.skip:
            self.skip -= 1
        if tag in {"td", "th"} and self.in_cell:
            text = " ".join("".join(self.buf).split())
            self.row.append(text)
            self.in_cell = False
        if tag == "tr" and self.in_table == 1 and self.row:
            self.rows.append(self.row)
            self.row = []
        if tag == "table" and self.in_table:
            if self.in_table == 1 and self.rows:
                self.tables.append(self.rows)
            self.in_table -= 1

    def handle_data(self, data):
        if self.in_cell and self.skip == 0:
            self.buf.append(data)


def fetch(title: str, attempts: int = 2) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE / (title.replace("/", "_").replace(" ", "_") + ".html")
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")
    url = API.format(urllib.request.quote(title.replace(" ", "_")))
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                html = response.read().decode("utf-8")
            cache_path.write_text(html, encoding="utf-8")
            return html
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code == 404:
                raise
            time.sleep(2)
        except urllib.error.URLError as error:
            last_error = error
            time.sleep(2)
    raise RuntimeError(f"Failed to download {title}: {last_error}")


def cleaned_date_text(text: str) -> str:
    without_notes = re.sub(r"\([^)]*\)", " ", text)
    return " ".join(without_notes.split())


def parse_date(text: str) -> date | None:
    cleaned = cleaned_date_text(text)
    lowered = cleaned.lower()
    match = DATE_RE.search(lowered)
    if match:
        leftover = DATE_RE.sub(" ", lowered)
        leftover = re.sub(r"[^a-záéíóúüñ0-9]", "", leftover)
        if leftover:
            return None
        return date(int(match.group(3)), MONTHS[match.group(2).lower()], int(match.group(1)))
    matches = list(NUM_RE.finditer(cleaned))
    if len(matches) != 1:
        return None
    leftover = NUM_RE.sub(" ", lowered)
    leftover = re.sub(r"[^a-záéíóúüñ]", "", leftover)
    if leftover not in {"", "actualidad", "enelcargo", "presente"}:
        return None
    day, month, year = matches[0].groups()
    return date(int(year), int(month), int(day))


ROMAN_RE = re.compile(r"^(?:i|ii|iii|iv|v|vi|vii|viii|ix|x)$", re.IGNORECASE)


def looks_like_name(text: str) -> str:
    """Return a cleaned person name, or "" if this cell is not one."""
    cleaned = " ".join(text.split()).strip(" ,")
    cleaned = re.sub(
        r"\s+(?:diputad[oa]s?|procurador(?:a|es)?)\s+por\b.*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s*\((?:primer|segundo|tercer|cuarto)\s+mandato\)\s*$", "", cleaned, flags=re.IGNORECASE)
    note = re.fullmatch(r"(.+?)\s*\(([^)]*)\)", cleaned)
    if note:
        aside = note.group(2).strip().lower()
        if any(word in aside for word in ("funcion", "dimis", "interin", "interina")):
            cleaned = note.group(1).strip()
        elif len(note.group(1).split()) < 2:
            return ""
    if len(cleaned) < 5 or parse_date(cleaned):
        return ""
    lowered = cleaned.lower()
    if (
        "provincia" in lowered
        or "en funciones" in lowered
        or lowered in {"presidente", "president", "lehendakari", "lendakari", "nombre"}
    ):
        return ""
    if re.search(r"\d", cleaned) or PARTY_RE.search(cleaned):
        return ""
    words = [word for word in re.split(r"\s+", cleaned) if word.strip(".")]
    if len(words) < 2 or ROMAN_RE.match(words[-1]):
        return ""
    letters = re.sub(r"[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", "", cleaned)
    if len(letters) < 5:
        return ""
    return cleaned


def is_holder_table(rows: list[list[str]]) -> bool:
    for row in rows[:3]:
        joined = " ".join(row).lower()
        has_person = any(word in joined for word in ("presidente", "president", "lehendakari", "lendakari", "nombre"))
        has_when = any(word in joined for word in ("inicio", "mandato", "nombramiento", "cese", "desde", "hasta"))
        if has_person and has_when:
            return True
    return False


def party_of(cells: list[str]) -> str:
    candidates = []
    for cell in cells:
        text = " ".join(cell.split()).strip(" -–—")
        if not text or parse_date(text) or text.lower().startswith("ver notas") or len(text) > 80:
            continue
        matches = PARTY_RE.findall(text)
        if matches:
            candidates.append("+".join(dict.fromkeys(matches)))
    if not candidates:
        return ""
    return min(candidates, key=len)


def terms_from_table(rows: list[list[str]]) -> list[dict]:
    found = []
    carried_name = ""
    for cells in rows:
        dated = []
        for index, cell in enumerate(cells):
            parsed = parse_date(cell)
            if parsed is not None and len(cell) < 80:
                dated.append((index, parsed))
        if not dated:
            continue
        start_index, started = dated[0]
        ended = dated[1][1] if len(dated) > 1 else None
        name = ""
        for cell in cells[:start_index]:
            candidate = looks_like_name(cell)
            if candidate:
                name = candidate
        row_text = " ".join(cells)
        if name:
            carried_name = name
        elif re.search(r"en funciones", row_text, re.IGNORECASE) and len(dated) == 1 and found and found[-1]["ended_on"] is None:
            found[-1]["ended_on"] = dated[0][1].isoformat()
            continue
        elif carried_name:
            name = carried_name
        if not name:
            continue
        if ended is not None and ended < started:
            continue
        found.append(
            {
                "name": name,
                "started_on": started.isoformat(),
                "ended_on": ended.isoformat() if ended else None,
                "party": party_of(cells),
            }
        )
    return found


def relevant(term: dict) -> bool:
    started = date.fromisoformat(term["started_on"])
    ended = date.fromisoformat(term["ended_on"]) if term["ended_on"] else None
    if started.year < 1978:
        return False
    if ended is not None and ended < KEEP_FROM:
        return False
    return True


def download_region(slug: str, name: str, titles: list[str], attempts: int = 1) -> dict:
    last_error: Exception | None = None
    for title in titles:
        try:
            html = fetch(title, attempts=attempts)
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError) as error:
            last_error = error
            continue
        parser = TableParser()
        parser.feed(html)
        terms: list[dict] = []
        for table in parser.tables:
            if is_holder_table(table):
                terms.extend(terms_from_table(table))
        terms = [term for term in terms if relevant(term)]
        terms.sort(key=lambda term: (term["started_on"], term["ended_on"] or "9999"))
        # Same person can appear twice if a pre-autonomy table overlaps the autonomy table.
        deduped = []
        seen = set()
        for term in terms:
            key = (term["name"], term["started_on"], term["ended_on"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(term)
        if not deduped:
            last_error = RuntimeError(f"No office-holder rows parsed from {title}")
            continue
        return {
            "slug": slug,
            "name": name,
            "source_title": title,
            "source_url": "https://es.wikipedia.org/wiki/" + title.replace(" ", "_"),
            "terms": deduped,
        }
    raise RuntimeError(f"No Wikipedia page for {name}: {last_error}")


POSITIONS = {
    "Q2748453": "andalucia",
    "Q3133842": "aragon",
    "Q3320056": "asturias",
    "Q967418": "canarias",
    "Q47358": "cantabria",
    "Q4892213": "castilla-y-leon",
    "Q3272746": "castilla-la-mancha",
    "Q16933549": "cataluna",
    "Q15971570": "valencia",
    "Q3049413": "extremadura",
    "Q3409188": "galicia",
    "Q3133837": "madrid",
    "Q5199072": "murcia",
    "Q3753803": "navarra",
    "Q1124265": "pais-vasco",
    "Q3049394": "la-rioja",
    "Q13710953": "baleares",
    "Q6745827": "ceuta",
    "Q30727487": "melilla",
}
MEMBER_REGIONS = {
    "Andalucía": "andalucia",
    "Aragón": "aragon",
    "Principado de Asturias": "asturias",
    "Asturias": "asturias",
    "Islas Baleares": "baleares",
    "Canarias": "canarias",
    "Cantabria": "cantabria",
    "Castilla y León": "castilla-y-leon",
    "Castilla-La Mancha": "castilla-la-mancha",
    "Cataluña": "cataluna",
    "Comunidad Valenciana": "valencia",
    "Extremadura": "extremadura",
    "Galicia": "galicia",
    "Comunidad de Madrid": "madrid",
    "Región de Murcia": "murcia",
    "Comunidad Foral de Navarra": "navarra",
    "Navarra": "navarra",
    "País Vasco": "pais-vasco",
    "La Rioja": "la-rioja",
}


def sparql(query: str) -> dict:
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": query})
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/sparql-results+json", "User-Agent": USER_AGENT},
    )
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            last_error = error
            time.sleep(3 * (attempt + 1))
        except urllib.error.URLError as error:
            last_error = error
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"Wikidata query failed: {last_error}")


def fold(name: str) -> str:
    import unicodedata

    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", text)


def clean_terms(terms: list[dict]) -> list[dict]:
    from datetime import timedelta

    rows = []
    for term in terms:
        started = (term.get("started_on") or "")[:10]
        if not started:
            continue
        ended = (term.get("ended_on") or "")[:10] or None
        rows.append(
            {
                "name": re.sub(
                    r"\s+(?:diputad[oa]s?|procurador(?:a|es)?)\s+por\b.*$",
                    "",
                    re.sub(r"\s+", " ", term["name"]).strip(),
                    flags=re.IGNORECASE,
                ),
                "party": term.get("party") or "",
                "started_on": started,
                "ended_on": ended,
                "wikidata_id": term.get("wikidata_id") or "",
            }
        )
    rows.sort(key=lambda term: (term["started_on"], term["ended_on"] or "9999-12-31"))
    for index, term in enumerate(rows[:-1]):
        if term["ended_on"] is None:
            term["ended_on"] = rows[index + 1]["started_on"]
    for index in range(len(rows) - 1):
        current = rows[index]
        nxt = rows[index + 1]
        if current["ended_on"] and current["ended_on"] >= nxt["started_on"]:
            current["ended_on"] = (date.fromisoformat(nxt["started_on"]) - timedelta(days=1)).isoformat()
    rows = [term for term in rows if term["ended_on"] is None or term["ended_on"] >= term["started_on"]]
    rows = [term for term in rows if term["ended_on"] is None or term["ended_on"] >= "2000-01-01"]
    merged: list[dict] = []
    for term in rows:
        if merged and fold(merged[-1]["name"]) == fold(term["name"]):
            previous = merged[-1]
            previous_end = previous["ended_on"] or "9999-12-31"
            boundary = (date.fromisoformat(previous_end) + timedelta(days=1)).isoformat()
            if term["started_on"] <= boundary:
                if term["ended_on"] is None or (previous["ended_on"] and term["ended_on"] > previous["ended_on"]):
                    previous["ended_on"] = term["ended_on"]
                if not previous["party"] and term["party"]:
                    previous["party"] = term["party"]
                if len(term["name"]) > len(previous["name"]):
                    previous["name"] = term["name"]
                if term["wikidata_id"] and not previous["wikidata_id"]:
                    previous["wikidata_id"] = term["wikidata_id"]
                continue
        merged.append(term)
    return merged


def longest_gap_days(terms: list[dict]) -> int:
    from datetime import timedelta

    cursor = date(2001, 1, 1)
    limit = date(2025, 12, 31)
    longest = 0
    for term in terms:
        started = date.fromisoformat(term["started_on"])
        if started > cursor:
            longest = max(longest, (started - cursor).days)
        ended = date.fromisoformat(term["ended_on"]) if term["ended_on"] else limit
        if ended >= cursor:
            cursor = ended + timedelta(days=1)
    if cursor <= limit:
        longest = max(longest, (limit - cursor).days + 1)
    return longest


def download_presidents_raw() -> dict:
    values = " ".join(f"wd:{qid}" for qid in POSITIONS)
    query = f"""
    SELECT ?position ?person ?personLabel ?start ?end WHERE {{
      VALUES ?position {{ {values} }}
      ?person p:P39 ?st .
      ?st ps:P39 ?position .
      OPTIONAL {{ ?st pq:P580 ?start }}
      OPTIONAL {{ ?st pq:P582 ?end }}
      FILTER(!BOUND(?end) || ?end >= "1998-01-01T00:00:00Z"^^xsd:dateTime)
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es". }}
    }}
    """
    print("Downloading presidents from Wikidata...")
    data = sparql(query)
    PRESIDENTS_RAW.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def download_members_raw() -> dict:
    query = """
    SELECT ?regionLabel ?person ?personLabel ?officeLabel ?start ?end WHERE {
      ?region wdt:P31 wd:Q10742 .
      ?office wdt:P1001 ?region .
      ?office rdfs:label ?officeLabel .
      FILTER(LANG(?officeLabel)="es")
      FILTER(REGEX(?officeLabel, "(consejer[oa]|conseller|vicepresident)", "i"))
      FILTER(!REGEX(?officeLabel, "(consultivo|audiovisual|viceconsejer|parlamento|tribunal|sindic)", "i"))
      ?person p:P39 ?st .
      ?st ps:P39 ?office .
      OPTIONAL { ?st pq:P580 ?start }
      OPTIONAL { ?st pq:P582 ?end }
      FILTER(!BOUND(?end) || ?end >= "1999-01-01T00:00:00Z"^^xsd:dateTime)
      FILTER(!BOUND(?start) || ?start >= "1978-01-01T00:00:00Z"^^xsd:dateTime)
      SERVICE wikibase:label { bd:serviceParam wikibase:language "es". }
    }
    """
    print("Downloading cabinet members from Wikidata...")
    data = sparql(query)
    MEMBERS_RAW.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def presidents_from_wikidata(data: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {slug: [] for slug in POSITIONS.values()}
    for row in data["results"]["bindings"]:
        def value(key: str) -> str:
            return row.get(key, {}).get("value", "")

        slug = POSITIONS.get(value("position").rsplit("/", 1)[-1])
        if not slug or not value("start"):
            continue
        grouped[slug].append(
            {
                "name": value("personLabel"),
                "party": "",
                "started_on": value("start")[:10],
                "ended_on": value("end")[:10] or None,
                "wikidata_id": value("person").rsplit("/", 1)[-1],
            }
        )
    return grouped


def members_from_wikidata(data: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {slug: [] for slug, _, _ in REGIONS}
    seen = set()
    for row in data["results"]["bindings"]:
        def value(key: str) -> str:
            return row.get(key, {}).get("value", "")

        slug = MEMBER_REGIONS.get(value("regionLabel"))
        if not slug:
            continue
        member = {
            "name": value("personLabel"),
            "office": value("officeLabel"),
            "started_on": value("start")[:10] or None,
            "ended_on": value("end")[:10] or None,
            "wikidata_id": value("person").rsplit("/", 1)[-1],
        }
        key = (slug, member["wikidata_id"], member["office"], member["started_on"], member["ended_on"])
        if key in seen:
            continue
        seen.add(key)
        grouped[slug].append(member)
    for members in grouped.values():
        members.sort(key=lambda member: (member["started_on"] or "9999", member["name"]))
    return grouped


def apply_party(terms: list[dict], parties: list[dict], slug: str) -> None:
    for term in terms:
        if term["party"]:
            continue
        folded = fold(term["name"])
        for entry in parties:
            if entry["region"] == slug and fold(entry["match"]) in folded:
                term["party"] = entry["party"]
                break


def wikipedia_terms(slug: str, name: str, titles: list[str]) -> list[dict] | None:
    ordered = sorted(titles, key=lambda title: not (CACHE / (title.replace("/", "_").replace(" ", "_") + ".html")).exists())
    best: list[dict] | None = None
    best_gap = 10**9
    best_title = ""
    for title in ordered:
        try:
            downloaded = download_region(slug, name, [title])
        except (RuntimeError, urllib.error.HTTPError, urllib.error.URLError):
            continue
        terms = clean_terms(downloaded["terms"])
        gap = longest_gap_days(terms)
        if gap < best_gap:
            best, best_gap, best_title = terms, gap, downloaded["source_title"]
        if gap <= 45:
            break
    if best is None:
        print(f"  Wikipedia unavailable for {name}")
        return None
    print(f"  Wikipedia {best_title}: {len(best)} terms, longest gap {best_gap} days")
    if best_gap > 45:
        return None
    return best


def main() -> None:
    corrections = json.loads(CORRECTIONS.read_text(encoding="utf-8"))
    presidents = presidents_from_wikidata(download_presidents_raw())
    members = members_from_wikidata(download_members_raw())
    parties = list(corrections.get("parties", []))

    regions = []
    for slug, name, titles in REGIONS:
        print(f"{name}")
        terms = wikipedia_terms(slug, name, titles)
        source = "wikipedia" if terms is not None else "wikidata"
        if terms is None:
            terms = clean_terms(presidents.get(slug, []))
            replacement = corrections.get("replace", {}).get(slug)
            if replacement:
                terms = clean_terms(replacement)
                source = "correction"
            print(f"  {source}: {len(terms)} terms, longest gap {longest_gap_days(terms)} days")
        for patch in corrections.get("patch", []):
            if patch["region"] != slug:
                continue
            for term in terms:
                if fold(patch["match"]) in fold(term["name"]):
                    term["ended_on"] = patch["ended_on"]
                    print(f"  patched {term['name']} end → {patch['ended_on']}")
        extra = [dict(term) for term in corrections.get("add", []) if term["region"] == slug]
        if extra:
            terms.extend(extra)
            print(f"  added {len(extra)} corrected term(s)")
        drop_matches = [fold(item["match"]) for item in corrections.get("drop", []) if item["region"] == slug]
        if drop_matches:
            before = len(terms)
            terms = [term for term in terms if not any(match in fold(term["name"]) for match in drop_matches)]
            print(f"  dropped {before - len(terms)} term(s) that are not the regional president")
        terms = clean_terms(terms)
        print(f"  {len(terms)} terms after corrections, longest gap {longest_gap_days(terms)} days")
        apply_party(terms, parties, slug)
        regions.append(
            {
                "slug": slug,
                "name": name,
                "president_source": source,
                "presidents": terms,
                "members": members.get(slug, []),
            }
        )
        time.sleep(0.2)

    payload = {
        "presidents_source": "Wikidata P39, replaced by Spanish Wikipedia when that list covers 2000–2025",
        "members_source": "Wikidata cabinet posts (consejero, conseller, vicepresidente) for autonomous communities. Coverage is uneven; Ceuta and Melilla have no cabinet extract.",
        "corrections": "data/office-corrections.json",
        "regions": regions,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    president_count = sum(len(region["presidents"]) for region in regions)
    member_count = sum(len(region["members"]) for region in regions)
    print(f"Wrote {OUT} ({president_count} presidential terms, {member_count} cabinet records)")


if __name__ == "__main__":
    main()
