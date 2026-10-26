from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from mery.datasets import Dataset
from mery.layout import remove_flat, scatter_slug
from mery.paths import DATA
from mery.places import REGION_SLUGS, Place
from mery.source import Handler
from mery.support import python, run


class Transfers(Handler):
    """Money each community records with the State, from the same liquidation portal as the budgets."""

    datasets: ClassVar[frozenset[Dataset]] = frozenset({Dataset.TRANSFERS})
    place_slugs: ClassVar[frozenset[str]] = REGION_SLUGS

    def download(self, places: Sequence[Place], datasets: frozenset[Dataset]) -> None:
        if not datasets:
            return
        run(python("download-transfers.py"), places=places, covered=REGION_SLUGS)
        scatter_slug(DATA / "transfers.csv", Dataset.TRANSFERS.file_name)
        remove_flat("transfers.csv")
