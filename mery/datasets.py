from __future__ import annotations

import enum


class Dataset(enum.StrEnum):
    """One kind of figure. The value is the file name under data/<place>/."""

    GDP = "gdp"
    PER_CAPITA = "per-capita"
    REAL_GROWTH = "real-growth"
    JOBS = "jobs"
    DEBT = "debt"
    PDE_DEBT = "pde-debt"
    BALANCE = "balance"
    SPENDING = "spending"
    CENTRAL_SPENDING = "central-spending"
    BUDGET = "budget"
    BUDGET_PARTS = "budget-parts"
    TRANSFERS = "transfers"
    EU_TRANSFERS = "eu-transfers"
    HEALTH = "health"
    SCHOOLS = "schools"
    CARE = "care"
    EU_VOLUME = "eu-volume"
    OFFICE = "office"

    @property
    def file_name(self) -> str:
        if self is Dataset.OFFICE:
            return "office.json"
        return f"{self.value}.csv"
