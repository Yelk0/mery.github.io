from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from mery.datasets import Dataset
from mery.layout import remove_flat, restore_slug, scatter_slug
from mery.paths import DATA
from mery.places import Place
from mery.source import Handler
from mery.support import python, run

_SPAIN = frozenset({"spain"})


class StateBudget(Handler):
    """Settled State budget (PGE liquidation). A different page from the community budgets."""

    datasets: ClassVar[frozenset[Dataset]] = frozenset({Dataset.BUDGET, Dataset.BUDGET_PARTS})
    place_slugs: ClassVar[frozenset[str]] = _SPAIN

    def download(self, places: Sequence[Place], datasets: frozenset[Dataset]) -> None:
        if not datasets:
            return
        restore_slug(Dataset.BUDGET_PARTS.file_name, DATA / "budget-parts.csv")
        run(python("download-state-budget.py"), places=places, covered=_SPAIN)
        scatter_slug(DATA / "spain-budget.csv", Dataset.BUDGET.file_name)
        scatter_slug(DATA / "budget-parts.csv", Dataset.BUDGET_PARTS.file_name)
        remove_flat("spain-budget.csv")
        remove_flat("budget-parts.csv")
