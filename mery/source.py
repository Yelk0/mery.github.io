from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from mery.datasets import Dataset
from mery.places import Place


class Handler:
    """One publication. It fills one or more datasets for the places it covers."""

    datasets: ClassVar[frozenset[Dataset]]
    place_slugs: ClassVar[frozenset[str]]

    def covers(self, place: Place, dataset: Dataset) -> bool:
        return dataset in type(self).datasets and place.slug in type(self).place_slugs

    def download(self, places: Sequence[Place], datasets: frozenset[Dataset]) -> None:
        raise NotImplementedError(type(self).__name__)
