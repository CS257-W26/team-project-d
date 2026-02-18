"""
Command-line interface for querying the project climate database.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from ProductionCode.climate_repository import CO2_COLUMN, FOREST_CHANGE_COLUMN, ClimateRepository
from ProductionCode.db import get_db
from ProductionCode.output_format import RankContext, RankResult
from ProductionCode.output_format import format_rank_result, format_single_value, format_top_list

DEFAULT_TOP_N = 10
FOREST_UNIT = "ha"
CO2_UNIT = "t/person"


def _add_features(parser: argparse.ArgumentParser) -> None:
    """add the three mutually-exclusive feature flags"""
    group = parser.add_mutually_exclusive_group(required=True)
    for flag, help_text in (
        ("--deforestation", "Forest change lookup (ha)."),
        ("--co2", "CO₂ per-capita lookup (t/person)."),
        ("--ranking", "Forest change ranking (ha)."),
    ):
        group.add_argument(flag, nargs="?", const="", metavar="COUNTRY", help=help_text)


def _add_options(parser: argparse.ArgumentParser) -> None:
    """add shared options used across features"""
    parser.add_argument("--year", type=int, default=None, help="Year (default: latest).")
    parser.add_argument("--top", type=int, default=DEFAULT_TOP_N, help="List size.")
    parser.add_argument("--order", choices=("loss", "gain"), default="loss", help="Ranking order.")
    parser.add_argument(
        "--include-aggregates",
        action="store_true",
        help="Include aggregates/regions (e.g., World).",
    )


def build_parser() -> argparse.ArgumentParser:
    """build and return the cli argument parser"""
    parser = argparse.ArgumentParser(prog="command_line.py", description="Query climate datasets.")
    _add_features(parser)
    _add_options(parser)
    return parser


def _only_countries(args: argparse.Namespace) -> bool:
    """return True if the query should be restricted to countries"""
    return not args.include_aggregates


def _deforestation_value(repo: ClimateRepository, args: argparse.Namespace) -> str:
    """return a single forest-change value output"""
    entity, year, value = repo.forest_value_for_entity_year(
        entity_query=args.deforestation,
        year=args.year,
        only_countries=_only_countries(args),
    )
    return format_single_value(entity, year, FOREST_CHANGE_COLUMN, value, FOREST_UNIT)


def _deforestation_list(repo: ClimateRepository, args: argparse.Namespace) -> str:
    """return a forest-change top list output"""
    only = _only_countries(args)
    year = args.year or repo.forest_latest_year(only)
    rows = repo.forest_rank_entities(
        year=year,
        order=args.order,
        top_n=args.top,
        only_countries=only,
    )
    title = (
        f"Top {min(args.top, len(rows))} entities for {FOREST_CHANGE_COLUMN} "
        f"in {year} (order={args.order})"
    )
    return format_top_list(title, rows, FOREST_UNIT)


def run_deforestation(repo: ClimateRepository, args: argparse.Namespace) -> str:
    """implement the --deforestation feature"""
    if args.deforestation:
        return _deforestation_value(repo, args)
    return _deforestation_list(repo, args)


def _co2_value(repo: ClimateRepository, args: argparse.Namespace) -> str:
    """return a single co2 per-capita value output"""
    entity, year, value = repo.co2_value_for_entity_year(
        entity_query=args.co2,
        year=args.year,
        only_countries=_only_countries(args),
    )
    return format_single_value(entity, year, CO2_COLUMN, value, CO2_UNIT)


def _co2_list(repo: ClimateRepository, args: argparse.Namespace) -> str:
    """return a co2 per-capita top list output"""
    only = _only_countries(args)
    year = args.year or repo.co2_latest_year(only)
    rows = repo.co2_top_emitters(year=year, top_n=args.top, only_countries=only)
    title = f"Top {min(args.top, len(rows))} entities for {CO2_COLUMN} in {year}"
    return format_top_list(title, rows, CO2_UNIT)


def run_co2(repo: ClimateRepository, args: argparse.Namespace) -> str:
    """implement the --co2 feature"""
    return _co2_value(repo, args) if args.co2 else _co2_list(repo, args)


def _ranking_value(repo: ClimateRepository, args: argparse.Namespace) -> str:
    """return a single-entity ranking output"""
    only = _only_countries(args)
    entity, year, rank, value = repo.forest_rank_for_entity(
        entity_query=args.ranking,
        year=args.year,
        order=args.order,
        only_countries=only,
    )
    total = repo.forest_count_entities_for_year(year=year, only_countries=only)
    ctx = RankContext(metric=FOREST_CHANGE_COLUMN, unit=FOREST_UNIT, order=args.order)
    return format_rank_result(RankResult(entity, year, ctx, rank, total, value))


def _ranking_list(repo: ClimateRepository, args: argparse.Namespace) -> str:
    """return the ranking top list output"""
    only = _only_countries(args)
    year = args.year or repo.forest_latest_year(only)
    rows = repo.forest_rank_entities(
        year=year,
        order=args.order,
        top_n=args.top,
        only_countries=only,
    )
    title = f"Forest change ranking for {year} (order={args.order})"
    return format_top_list(title, rows, FOREST_UNIT)


def run_ranking(repo: ClimateRepository, args: argparse.Namespace) -> str:
    """implement the --ranking feature"""
    return _ranking_value(repo, args) if args.ranking else _ranking_list(repo, args)


def _run(args: argparse.Namespace) -> str:
    """create a repository and run the selected cli feature"""
    repo = ClimateRepository(get_db())
    if args.deforestation is not None:
        return run_deforestation(repo, args)
    if args.co2 is not None:
        return run_co2(repo, args)
    return run_ranking(repo, args)


def main(argv: Optional[List[str]] = None) -> int:
    """run the cli and return a process exit code"""
    try:
        output = _run(build_parser().parse_args(argv))
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
