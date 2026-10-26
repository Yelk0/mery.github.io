from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from mery.datasets import Dataset
from mery.layout import remove_flat, scatter_labels
from mery.paths import DATA
from mery.places import EPA_LABELS, EVERY_SLUG, Place
from mery.source import Handler
from mery.support import run

_LABELS = EPA_LABELS | {"spain": "Total Nacional"}
_REQUIRED = frozenset(_LABELS.values())


class IneJobs(Handler):
    """INE labour-force table 65321, public and private jobs."""

    datasets: ClassVar[frozenset[Dataset]] = frozenset({Dataset.JOBS})
    place_slugs: ClassVar[frozenset[str]] = EVERY_SLUG

    def download(self, places: Sequence[Place], datasets: frozenset[Dataset]) -> None:
        if not datasets:
            return
        run(["./download-ine-80110.sh", "-t", "65321"], places=places, covered=EVERY_SLUG)
        scatter_labels(
            DATA / "65321.csv",
            Dataset.JOBS.file_name,
            column="Comunidades y Ciudades Autónomas",
            labels=_LABELS,
            required=_REQUIRED,
        )
        remove_flat("65321.csv")
