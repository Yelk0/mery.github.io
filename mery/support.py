from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Sequence

from mery.paths import ROOT
from mery.places import Place


def run(command: Sequence[str], *, places: Sequence[Place], covered: frozenset[str]) -> None:
    """Run a downloader from the repository root.

    A publication that can fetch one community reads MERY_PLACES. A command
    that already asks for every community that publication covers leaves the
    variable unset, so the downloader fetches the whole table once.
    """
    env = os.environ.copy()
    requested = frozenset(place.slug for place in places) & covered
    if requested and requested != covered:
        env["MERY_PLACES"] = ",".join(sorted(requested))
    else:
        env.pop("MERY_PLACES", None)
    try:
        subprocess.run(command, cwd=ROOT, check=True, env=env)
    except subprocess.CalledProcessError as error:
        rendered = " ".join(command)
        raise SystemExit(f"Download failed ({error.returncode}): {rendered}") from error


def python(script: str) -> list[str]:
    return [sys.executable, script]
