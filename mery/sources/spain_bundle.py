"""The Spain accounts script also fetches the EU budget and the national debt stock.

Those are three publications. They still share one program, so asking for any of
them downloads all three and writes each series to its own file.
"""

from __future__ import annotations

from mery.layout import copy_file, remove_flat, scatter_spain_accounts
from mery.paths import DATA
from mery.support import python, run

_done = False


def fetch_spain_bundle() -> None:
    global _done
    if _done:
        return
    run(python("download-spain.py"), places=(), covered=frozenset())
    scatter_spain_accounts(DATA / "spain.csv")
    copy_file(DATA / "spain-eu.csv", "spain", "eu-transfers.csv")
    copy_file(DATA / "spain-debt.csv", "spain", "pde-debt.csv")
    remove_flat("spain.csv")
    remove_flat("spain-eu.csv")
    remove_flat("spain-debt.csv")
    _done = True
