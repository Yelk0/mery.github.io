from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from mery.datasets import Dataset
from mery.layout import scatter_office
from mery.paths import DATA
from mery.places import REGION_SLUGS, Place
from mery.source import Handler
from mery.support import python, run


class Office(Handler):
    """Presidents and cabinet members. data/people.json stays, and each community also gets office.json."""

    datasets: ClassVar[frozenset[Dataset]] = frozenset({Dataset.OFFICE})
    place_slugs: ClassVar[frozenset[str]] = REGION_SLUGS

    def download(self, places: Sequence[Place], datasets: frozenset[Dataset]) -> None:
        if not datasets:
            return
        run(python("download-office-holders.py"), places=places, covered=REGION_SLUGS)
        scatter_office(DATA / "people.json")
