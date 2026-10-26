from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from mery.datasets import Dataset
from mery.layout import copy_file, remove_flat
from mery.paths import DATA
from mery.places import Place
from mery.source import Handler
from mery.support import python, run

_SPAIN = frozenset({"spain"})


class EuVolume(Handler):
    """Eurostat chain-volume index for Spain and the EU. Spain's real growth is compared with this, not with itself."""

    datasets: ClassVar[frozenset[Dataset]] = frozenset({Dataset.EU_VOLUME})
    place_slugs: ClassVar[frozenset[str]] = _SPAIN

    def download(self, places: Sequence[Place], datasets: frozenset[Dataset]) -> None:
        if not datasets:
            return
        run(python("download-eu-volume.py"), places=places, covered=_SPAIN)
        copy_file(DATA / "eu-volume.csv", "spain", Dataset.EU_VOLUME.file_name)
        remove_flat("eu-volume.csv")
