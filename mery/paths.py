from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def place_paths(filename: str) -> list[Path]:
    """Every data/<place>/<filename>, in place-name order."""
    return sorted(path for path in DATA.glob(f"*/{filename}") if path.is_file())
