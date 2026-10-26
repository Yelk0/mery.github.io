from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from mery.datasets import Dataset
from mery.places import Place
from mery.source import Handler
from mery.sources.spain_bundle import fetch_spain_bundle

_SPAIN = frozenset({"spain"})


class SpainAccounts(Handler):
    """All-administration balance, all-administration spending, and central spending."""

    datasets: ClassVar[frozenset[Dataset]] = frozenset(
        {Dataset.BALANCE, Dataset.SPENDING, Dataset.CENTRAL_SPENDING}
    )
    place_slugs: ClassVar[frozenset[str]] = _SPAIN

    def download(self, places: Sequence[Place], datasets: frozenset[Dataset]) -> None:
        del places
        if not datasets:
            return
        fetch_spain_bundle()
