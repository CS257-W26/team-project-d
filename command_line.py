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
from dataclasses import dataclass
from typing import Callable, Optional

from ProductionCode.climate_repository import (
    CO2_COLUMN,
    FOREST_CHANGE_COLUMN,
    ClimateRepository,
)
from ProductionCode.db import get_db
from ProductionCode.output_format import format_single_value

FOREST_UNIT = "ha"
CO2_UNIT = "t/person"


@dataclass(frozen=True)
class MetricSpec:
    """Describe how one CLI feature resolves years and numeric values."""

    column_name: str
    unit: str
    latest_year_for_country: Callable[[str], int]
    value_for_year: Callable[[str, int], Optional[float]]


def _add_features(parser: argparse.ArgumentParser) -> None:
    """Add mutually-exclusive feature flags."""
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
    """Add shared options used across features."""
    parser.add_argument("--year", type=int, default=None, help="Year (default: latest).")


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="command_line.py",
        description="Query climate datasets.",
    )
    _add_features(parser)
    _add_options(parser)
    return parser


def _resolve_country(repo: ClimateRepository, raw: str) -> Optional[str]:
    """Resolve a user-supplied country string to a canonical database name."""
    normalized = raw.replace("_", " ").strip()
    return repo.resolve_country(normalized)


def _print_error(message: str) -> int:
    """Print an error to stderr and return a non-zero exit code."""
    print(message, file=sys.stderr)
    return 2


def _metric_specs(repo: ClimateRepository) -> dict[str, MetricSpec]:
    """Return the lookup behavior for each CLI feature."""
    return {
        "deforestation": MetricSpec(
            FOREST_CHANGE_COLUMN,
            FOREST_UNIT,
            repo.forest_latest_year_for_country,
            repo.forest_value,
        ),
        "co2": MetricSpec(
            CO2_COLUMN,
            CO2_UNIT,
            repo.co2_latest_year_for_country,
            repo.co2_value,
        ),
    }


def _selected_metric(
    args: argparse.Namespace,
    specs: dict[str, MetricSpec],
) -> tuple[MetricSpec, str]:
    """Return the chosen metric spec and raw country argument."""
    for argument_name, spec in specs.items():
        raw_entity = getattr(args, argument_name)
        if raw_entity:
            return spec, raw_entity
    raise ValueError("No feature selected")


def _lookup_metric(
    repo: ClimateRepository,
    spec: MetricSpec,
    raw_entity: str,
    year: Optional[int],
) -> tuple[str, int, float]:
    """Return the resolved country, chosen year, and numeric value."""
    entity = _resolve_country(repo, raw_entity)
    if not entity:
        raise ValueError("Unknown country")
    chosen_year = year or spec.latest_year_for_country(entity)
    value = spec.value_for_year(entity, chosen_year)
    if value is None:
        raise ValueError("No data for that year")
    return entity, chosen_year, value


def main(argv: Optional[list[str]] = None) -> int:
    """Run the CLI and return an exit code."""
    args = build_parser().parse_args(argv)
    repo = ClimateRepository(get_db())
    specs = _metric_specs(repo)

    try:
        spec, raw_entity = _selected_metric(args, specs)
        entity, year, value = _lookup_metric(repo, spec, raw_entity, args.year)
        print(format_single_value(entity, year, spec.column_name, value, spec.unit))
        return 0
    except ValueError as exc:
        return _print_error(f"Error: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
