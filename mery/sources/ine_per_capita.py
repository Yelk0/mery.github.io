from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from mery.datasets import Dataset
from mery.layout import remove_flat, scatter_labels
from mery.paths import DATA
from mery.places import EVERY_SLUG, INE_LABELS, Place
from mery.source import Handler
from mery.support import run

_LABELS = INE_LABELS | {"spain": "Total Nacional"}
_REQUIRED = frozenset(_LABELS.values())


class InePerCapita(Handler):
    """INE table 80110, current-price GDP per person."""

    datasets: ClassVar[frozenset[Dataset]] = frozenset({Dataset.PER_CAPITA})
    place_slugs: ClassVar[frozenset[str]] = EVERY_SLUG

    def download(self, places: Sequence[Place], datasets: frozenset[Dataset]) -> None:
        if not datasets:
            return
        run(["./download-ine-80110.sh"], places=places, covered=EVERY_SLUG)
        scatter_labels(
            DATA / "80110.csv",
            Dataset.PER_CAPITA.file_name,
            column="Comunidades y Ciudades Autónomas y Provincias",
            labels=_LABELS,
            required=_REQUIRED,
        )
        remove_flat("80110.csv")
