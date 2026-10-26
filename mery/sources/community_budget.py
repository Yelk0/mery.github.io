from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from mery.datasets import Dataset
from mery.layout import remove_flat, restore_slug, scatter_slug
from mery.paths import DATA
from mery.places import REGION_SLUGS, Place
from mery.source import Handler
from mery.support import python, run


class CommunityBudget(Handler):
    """Settled community budgets from the Hacienda liquidation portal.

    Every community uses that portal, so this is one handler. A command that
    names a single community downloads that community only. The sub-bars of
    general services come from the same workbooks and are written beside the budget.
    """

    datasets: ClassVar[frozenset[Dataset]] = frozenset({Dataset.BUDGET, Dataset.BUDGET_PARTS})
    place_slugs: ClassVar[frozenset[str]] = REGION_SLUGS

    def download(self, places: Sequence[Place], datasets: frozenset[Dataset]) -> None:
        if not datasets:
            return
        restore_slug(Dataset.BUDGET_PARTS.file_name, DATA / "budget-parts.csv")
        run(python("download-budget.py"), places=places, covered=REGION_SLUGS)
        scatter_slug(DATA / "budget.csv", Dataset.BUDGET.file_name)
        scatter_slug(DATA / "budget-parts.csv", Dataset.BUDGET_PARTS.file_name)
        remove_flat("budget.csv")
        remove_flat("budget-parts.csv")
