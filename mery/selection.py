"""Let a national downloader fetch one community when the command asks for one."""

from __future__ import annotations

import os
from collections.abc import Mapping


def limit(communities: Mapping[str, str]) -> dict[str, str]:
    """Keep the community codes named by MERY_PLACES. An empty variable keeps them all."""
    raw = os.environ.get("MERY_PLACES", "").strip()
    if not raw:
        return dict(communities)
    wanted = {item for item in raw.split(",") if item}
    chosen = {code: slug for code, slug in communities.items() if slug in wanted}
    if not chosen:
        raise SystemExit(f"MERY_PLACES does not name a community: {raw}")
    return chosen
