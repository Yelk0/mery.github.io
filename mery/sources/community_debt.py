from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from mery.datasets import Dataset
from mery.layout import remove_flat, scatter_debt
from mery.paths import DATA
from mery.places import DEBT_SLUGS, Place
from mery.source import Handler
from mery.support import run

_URL = "https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/be1306.csv"


class CommunityDebt(Handler):
    """Bank of Spain table 13.6. One national file, then debt.csv for each community."""

    datasets: ClassVar[frozenset[Dataset]] = frozenset({Dataset.DEBT})
    place_slugs: ClassVar[frozenset[str]] = DEBT_SLUGS

    def download(self, places: Sequence[Place], datasets: frozenset[Dataset]) -> None:
        if not datasets:
            return
        destination = DATA / "be1306.csv"
        run(
            [
                "curl",
                "--fail",
                "--location",
                "--retry",
                "3",
                "--retry-delay",
                "2",
                "--silent",
                "--show-error",
                "--user-agent",
                "plan-mery/bde-downloader",
                "--output",
                str(destination),
                _URL,
            ],
            places=places,
            covered=DEBT_SLUGS,
        )
        scatter_debt(destination)
        remove_flat("be1306.csv")
