from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from mery.datasets import Dataset
from mery.layout import remove_flat, scatter_slug
from mery.paths import DATA
from mery.places import REGION_SLUGS, Place
from mery.source import Handler
from mery.support import python, run


class RegionalBalance(Handler):
    """National-accounts surplus or deficit of each regional administration. IGAE, one workbook a year."""

    datasets: ClassVar[frozenset[Dataset]] = frozenset({Dataset.BALANCE})
    place_slugs: ClassVar[frozenset[str]] = REGION_SLUGS

    def download(self, places: Sequence[Place], datasets: frozenset[Dataset]) -> None:
        if not datasets:
            return
        run(python("download-balance.py"), places=places, covered=REGION_SLUGS)
        scatter_slug(DATA / "balance.csv", Dataset.BALANCE.file_name)
        remove_flat("balance.csv")
