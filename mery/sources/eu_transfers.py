from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from mery.datasets import Dataset
from mery.places import Place
from mery.source import Handler
from mery.sources.spain_bundle import fetch_spain_bundle

_SPAIN = frozenset({"spain"})


class EuTransfers(Handler):
    """What Spain receives from the EU budget and what it pays in. A different workbook from the Spanish accounts."""

    datasets: ClassVar[frozenset[Dataset]] = frozenset({Dataset.EU_TRANSFERS})
    place_slugs: ClassVar[frozenset[str]] = _SPAIN

    def download(self, places: Sequence[Place], datasets: frozenset[Dataset]) -> None:
        del places
        if not datasets:
            return
        fetch_spain_bundle()
