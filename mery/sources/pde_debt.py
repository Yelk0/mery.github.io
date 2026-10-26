from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from mery.datasets import Dataset
from mery.places import Place
from mery.source import Handler
from mery.sources.spain_bundle import fetch_spain_bundle

_SPAIN = frozenset({"spain"})


class PdeDebt(Handler):
    """Excessive-deficit debt of every Spanish public administration. Bank of Spain table be1112, not the community table."""

    datasets: ClassVar[frozenset[Dataset]] = frozenset({Dataset.PDE_DEBT})
    place_slugs: ClassVar[frozenset[str]] = _SPAIN

    def download(self, places: Sequence[Place], datasets: frozenset[Dataset]) -> None:
        del places
        if not datasets:
            return
        fetch_spain_bundle()
