from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from mery.datasets import Dataset
from mery.layout import remove_flat, scatter_slug
from mery.paths import DATA
from mery.places import EVERY_SLUG, Place
from mery.source import Handler
from mery.support import python, run


class Care(Handler):
    """Dependency-care queue. IMSERSO publishes one national workbook."""

    datasets: ClassVar[frozenset[Dataset]] = frozenset({Dataset.CARE})
    place_slugs: ClassVar[frozenset[str]] = EVERY_SLUG

    def download(self, places: Sequence[Place], datasets: frozenset[Dataset]) -> None:
        if not datasets:
            return
        run(python("download-care.py"), places=places, covered=EVERY_SLUG)
        scatter_slug(DATA / "care.csv", Dataset.CARE.file_name)
        remove_flat("care.csv")
