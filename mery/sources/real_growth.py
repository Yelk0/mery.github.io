from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from mery.datasets import Dataset
from mery.layout import remove_flat, scatter_labels
from mery.paths import DATA
from mery.places import EVERY_SLUG, INE_LABELS, Place, volume_name
from mery.source import Handler
from mery.support import python, run

_LABELS = {slug: volume_name(label) for slug, label in INE_LABELS.items()}
_LABELS["spain"] = "TOTAL NACIONAL"
_REQUIRED = frozenset(_LABELS.values())


class RealGrowth(Handler):
    """Unrounded real-growth rates from the regional-accounts workbook."""

    datasets: ClassVar[frozenset[Dataset]] = frozenset({Dataset.REAL_GROWTH})
    place_slugs: ClassVar[frozenset[str]] = EVERY_SLUG

    def download(self, places: Sequence[Place], datasets: frozenset[Dataset]) -> None:
        if not datasets:
            return
        run(python("download-cre-volume.py"), places=places, covered=EVERY_SLUG)
        scatter_labels(
            DATA / "cre-volume.csv",
            Dataset.REAL_GROWTH.file_name,
            column="Comunidad Autónoma",
            labels=_LABELS,
            required=_REQUIRED,
        )
        remove_flat("cre-volume.csv")
