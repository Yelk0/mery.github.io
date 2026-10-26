"""Spain and the communities the command can name.

The label tables are the same strings interpret.py uses to find a row.
A label that does not match is a province or a national total, not a second copy of a community.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class PlaceKind(enum.Enum):
    COUNTRY = "country"
    REGION = "region"


@dataclass(frozen=True, slots=True)
class Place:
    slug: str
    name: str
    kind: PlaceKind


SPAIN = Place("spain", "España", PlaceKind.COUNTRY)

REGIONS: tuple[Place, ...] = (
    Place("andalucia", "Andalucía", PlaceKind.REGION),
    Place("aragon", "Aragón", PlaceKind.REGION),
    Place("asturias", "Asturias", PlaceKind.REGION),
    Place("baleares", "Illes Balears", PlaceKind.REGION),
    Place("canarias", "Canarias", PlaceKind.REGION),
    Place("cantabria", "Cantabria", PlaceKind.REGION),
    Place("castilla-y-leon", "Castilla y León", PlaceKind.REGION),
    Place("castilla-la-mancha", "Castilla-La Mancha", PlaceKind.REGION),
    Place("cataluna", "Cataluña", PlaceKind.REGION),
    Place("valencia", "Comunitat Valenciana", PlaceKind.REGION),
    Place("extremadura", "Extremadura", PlaceKind.REGION),
    Place("galicia", "Galicia", PlaceKind.REGION),
    Place("madrid", "Comunidad de Madrid", PlaceKind.REGION),
    Place("murcia", "Región de Murcia", PlaceKind.REGION),
    Place("navarra", "Navarra", PlaceKind.REGION),
    Place("pais-vasco", "País Vasco", PlaceKind.REGION),
    Place("la-rioja", "La Rioja", PlaceKind.REGION),
    Place("ceuta", "Ceuta", PlaceKind.REGION),
    Place("melilla", "Melilla", PlaceKind.REGION),
)

EVERY_PLACE: tuple[Place, ...] = (SPAIN, *REGIONS)
EVERY_SLUG = frozenset(place.slug for place in EVERY_PLACE)
REGION_SLUGS = frozenset(place.slug for place in REGIONS)

_BY_SLUG = {place.slug: place for place in EVERY_PLACE}

# INE regional accounts, table 80109 and table 80110.
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

# INE labour-force survey, table 65321. The wording differs from the regional accounts.
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

# Bank of Spain table 13.6. The suffix is the community, not the country.
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

DEBT_INSTRUMENTS = {
    "P00000": "total",
    "F30000": "bonds",
    "F31000": "bonds_short",
    "F32000": "bonds_long",
    "F40000": "loans",
    "F42116": "fund",
}

DEBT_SLUGS = frozenset(DEBT_CODES)


def volume_name(ine_label: str) -> str:
    """Regional-accounts workbook name for an INE community label."""
    if ine_label == "Total Nacional":
        return "TOTAL NACIONAL"
    return ine_label.split(" ", 1)[1]


def resolve(name: str) -> tuple[Place, ...]:
    """spain includes every community. A community name is that community only."""
    key = "spain" if name == "espana" else name
    place = _BY_SLUG.get(key)
    if place is None:
        raise KeyError(name)
    if place.kind is PlaceKind.COUNTRY:
        return EVERY_PLACE
    return (place,)


def known_place_names() -> str:
    return ", ".join(place.slug for place in EVERY_PLACE)


if set(INE_LABELS) != REGION_SLUGS or set(EPA_LABELS) != REGION_SLUGS:
    raise RuntimeError("Place labels do not match the communities")
if set(DEBT_CODES) - REGION_SLUGS:
    raise RuntimeError("A debt code names an unknown community")
_volume_labels = [volume_name(label) for label in INE_LABELS.values()]
if len(_volume_labels) != len(set(_volume_labels)):
    raise RuntimeError("Two communities share a volume label")
