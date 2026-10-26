from __future__ import annotations

import argparse
from collections.abc import Sequence

from mery.datasets import Dataset
from mery.places import Place, known_place_names, resolve
from mery.registry import SOURCES
from mery.source import Handler


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="mery",
        description="Download the figures for a place. spain includes its communities.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    download = commands.add_parser("download", help="Fetch one place, or one dataset of that place.")
    download.add_argument("place", help="spain, or a community slug such as andalucia")
    download.add_argument(
        "dataset",
        nargs="?",
        choices=[item.value for item in Dataset],
        help="Limit the download to one kind of figure. Omit it to fetch every kind.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command != "download":
        raise SystemExit(f"Unknown command {args.command}")
    dataset_name = None if args.dataset is None else str(args.dataset)
    run_download(str(args.place), dataset_name)


def run_download(place_name: str, dataset_name: str | None) -> None:
    try:
        places = resolve(place_name)
    except KeyError:
        raise SystemExit(
            f"Unknown place '{place_name}'. Known places: {known_place_names()}"
        ) from None
    dataset = _dataset(dataset_name)
    selected = _handlers(places, dataset)
    if not selected:
        target = "any dataset" if dataset is None else dataset.value
        raise SystemExit(f"No publication writes {target} for {place_name}.")
    for source, covered, datasets in selected:
        names = ", ".join(sorted(item.value for item in datasets))
        print(f"mery: {type(source).__name__} ({names})")
        source.download(covered, datasets)


def _dataset(name: str | None) -> Dataset | None:
    if name is None:
        return None
    try:
        return Dataset(name)
    except ValueError:
        known = ", ".join(item.value for item in Dataset)
        raise SystemExit(f"Unknown dataset '{name}'. Known datasets: {known}") from None


def _handlers(
    places: Sequence[Place],
    dataset: Dataset | None,
) -> list[tuple[Handler, list[Place], frozenset[Dataset]]]:
    chosen: list[tuple[Handler, list[Place], frozenset[Dataset]]] = []
    for source in SOURCES:
        matched: list[Place] = []
        found: set[Dataset] = set()
        for place in places:
            for item in source.datasets:
                if dataset is not None and item is not dataset:
                    continue
                if source.covers(place, item):
                    matched.append(place)
                    found.add(item)
        if not matched:
            continue
        chosen.append((source, list(dict.fromkeys(matched)), frozenset(found)))
    return chosen
