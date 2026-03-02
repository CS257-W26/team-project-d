"""
Command-line interface for querying the climate database.

This CLI supports two user-facing queries:

1. Forest change (ha) for a country and year
2. CO₂ emissions per capita (t/person) for a country and year

If the year is omitted, the CLI defaults to the latest year available for that
metric for the chosen country.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from ProductionCode.climate_repository import (
    CO2_COLUMN,
    FOREST_CHANGE_COLUMN,
    ClimateRepository,
)
from ProductionCode.db import get_db
from ProductionCode.output_format import format_single_value

FOREST_UNIT = "ha"
CO2_UNIT = "t/person"


def _add_features(parser: argparse.ArgumentParser) -> None:
    """add mutually-exclusive feature flags"""
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--deforestation",
        metavar="COUNTRY",
        help="Forest change lookup (ha).",
    )
    group.add_argument(
        "--co2",
        metavar="COUNTRY",
        help="CO₂ per-capita lookup (t/person).",
    )


def _add_options(parser: argparse.ArgumentParser) -> None:
    """add shared options used across features"""
    parser.add_argument("--year", type=int, default=None, help="Year (default: latest).")


def build_parser() -> argparse.ArgumentParser:
    """build and return the CLI argument parser"""
    parser = argparse.ArgumentParser(
        prog="command_line.py",
        description="Query climate datasets.",
    )
    _add_features(parser)
    _add_options(parser)
    return parser


def _resolve_country(repo: ClimateRepository, raw: str) -> Optional[str]:
    """resolve a user-supplied country string to a canonical database name"""
    normalized = raw.replace("_", " ").strip()
    return repo.resolve_country(normalized)


def _print_error(message: str) -> int:
    """print an error to stderr and return a non-zero exit code"""
    print(message, file=sys.stderr)
    return 2


def _deforestation(
    repo: ClimateRepository,
    raw_entity: str,
    year: Optional[int],
) -> tuple[str, int, float]:
    """get forest change for a country and year (defaulting year if needed)"""
    entity = _resolve_country(repo, raw_entity)
    if not entity:
        raise ValueError("Unknown country")
    chosen_year = year or repo.forest_latest_year_for_country(entity)
    value = repo.forest_value(entity, chosen_year)
    if value is None:
        raise ValueError("No data for that year")
    return entity, chosen_year, value


def _co2(
    repo: ClimateRepository,
    raw_entity: str,
    year: Optional[int],
) -> tuple[str, int, float]:
    """get CO₂ per-capita for a country and year (defaulting year if needed)"""
    entity = _resolve_country(repo, raw_entity)
    if not entity:
        raise ValueError("Unknown country")
    chosen_year = year or repo.co2_latest_year_for_country(entity)
    value = repo.co2_value(entity, chosen_year)
    if value is None:
        raise ValueError("No data for that year")
    return entity, chosen_year, value


def main(argv: Optional[list[str]] = None) -> int:
    """run the CLI and return an exit code"""
    args = build_parser().parse_args(argv)
    repo = ClimateRepository(get_db())

    try:
        if args.deforestation:
            entity, year, value = _deforestation(
                repo,
                args.deforestation,
                args.year,
            )
            print(
                format_single_value(
                    entity,
                    year,
                    FOREST_CHANGE_COLUMN,
                    value,
                    FOREST_UNIT,
                )
            )
            return 0

        entity, year, value = _co2(repo, args.co2, args.year)
        print(
            format_single_value(
                entity,
                year,
                CO2_COLUMN,
                value,
                CO2_UNIT,
            )
        )
        return 0
    except ValueError as exc:
        return _print_error(f"Error: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
