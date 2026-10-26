"""Which publication fills a place and a dataset.

Two handlers for the same pair are a mistake and are rejected at startup.
Adding a dataset is a new module under mery/sources/ and one line in this tuple.
"""

from __future__ import annotations

from mery.datasets import Dataset
from mery.source import Handler
from mery.sources.balance import RegionalBalance
from mery.sources.care import Care
from mery.sources.community_budget import CommunityBudget
from mery.sources.community_debt import CommunityDebt
from mery.sources.eu_transfers import EuTransfers
from mery.sources.eu_volume import EuVolume
from mery.sources.health import Health
from mery.sources.ine_gdp import IneGdp
from mery.sources.ine_jobs import IneJobs
from mery.sources.ine_per_capita import InePerCapita
from mery.sources.office import Office
from mery.sources.pde_debt import PdeDebt
from mery.sources.real_growth import RealGrowth
from mery.sources.schools import Schools
from mery.sources.spain_accounts import SpainAccounts
from mery.sources.state_budget import StateBudget
from mery.sources.transfers import Transfers

SOURCES: tuple[Handler, ...] = (
    IneGdp(),
    InePerCapita(),
    RealGrowth(),
    IneJobs(),
    CommunityDebt(),
    Health(),
    Schools(),
    Care(),
    RegionalBalance(),
    CommunityBudget(),
    Transfers(),
    StateBudget(),
    SpainAccounts(),
    EuTransfers(),
    PdeDebt(),
    EuVolume(),
    Office(),
)


def _reject_duplicates(sources: tuple[Handler, ...]) -> None:
    seen: dict[tuple[str, Dataset], str] = {}
    for source in sources:
        owner = type(source).__name__
        for slug in source.place_slugs:
            for dataset in source.datasets:
                key = (slug, dataset)
                previous = seen.get(key)
                if previous is not None:
                    raise RuntimeError(
                        f"{slug} {dataset.value} is claimed by {previous} and {owner}"
                    )
                seen[key] = owner


_reject_duplicates(SOURCES)
