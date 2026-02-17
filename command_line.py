"""
Command-line interface

3 features:

1) Deforestation / forest change lookup
2) CO₂ emissions per capita lookup
3) Forest change ranking

Queries a Postgres database
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from ProductionCode.climate_repository import (
    CO2_COLUMN,
    FOREST_CHANGE_COLUMN,
    ClimateRepository,
)
from ProductionCode.db import get_db
from ProductionCode.output_format import (
    RankContext,
    RankResult,
    format_rank_result,
    format_single_value,
    format_top_list,
)

DEFAULT_TOP_N = 10


def build_parser() -> argparse.ArgumentParser:
    """build and return the CLI argument parser"""
    description = (
        "Query environmental datasets (forest change and CO₂ per capita) "
        "from the command line."
    )

    epilog = (
        "Examples:\n"
        "  python3 command_line.py --deforestation Brazil --year 2020\n"
        "  python3 command_line.py --co2 Canada --year 2021\n"
        "  python3 command_line.py --ranking Brazil --year 2020\n"
        "  python3 command_line.py --ranking --year 2020 --top 10\n"
        "\n"
        "Tip: add --include-aggregates to include regions like 'World' or 'Africa'."
    )

    parser = argparse.ArgumentParser(
        prog="command_line.py",
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    feature = parser.add_mutually_exclusive_group(required=True)
    feature.add_argument(
        "--deforestation",
        nargs="?",
        const="",
        metavar="COUNTRY",
        help=(
            "Show annual change in forest area (net change). "
            "Provide COUNTRY for a single value, or omit COUNTRY to list a ranking."
        ),
    )
    feature.add_argument(
        "--co2",
        nargs="?",
        const="",
        metavar="COUNTRY",
        help=(
            "Show annual CO₂ emissions per capita. "
            "Provide COUNTRY for a single value, or omit COUNTRY to list top emitters."
        ),
    )
    feature.add_argument(
        "--ranking",
        nargs="?",
        const="",
        metavar="COUNTRY",
        help=(
            "Rank countries by annual change in forest area. "
            "Provide COUNTRY to see its rank, or omit COUNTRY to list top entries."
        ),
    )

    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Year to query (defaults to the most recent available year).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=DEFAULT_TOP_N,
        help=f"Number of results to show for list outputs (default {DEFAULT_TOP_N}).",
    )
    parser.add_argument(
        "--order",
        choices=["loss", "gain"],
        default="loss",
        help=(
            "Ranking order for forest change: 'loss' (most negative first) "
            "or 'gain' (most positive first)."
        ),
    )
    parser.add_argument(
        "--include-aggregates",
        action="store_true",
        help=(
            "Include aggregates/regions (e.g., World, Africa) "
            "instead of only countries."
        ),
    )

    return parser


def run_deforestation(repo: ClimateRepository, args: argparse.Namespace) -> str:
    """implement the --deforestation feature"""
    only_countries = not args.include_aggregates

    if args.deforestation:
        entity, year, value = repo.forest_value_for_entity_year(
            entity_query=args.deforestation,
            year=args.year,
            only_countries=only_countries,
        )
        return format_single_value(
            entity=entity,
            year=year,
            metric=FOREST_CHANGE_COLUMN,
            value=value,
            unit="ha",
        )

    year = args.year if args.year is not None else repo.forest_latest_year(only_countries)

    ranked = repo.forest_rank_entities(
        year=year,
        order=args.order,
        top_n=args.top,
        only_countries=only_countries,
    )
    title = (
        f"Top {min(args.top, len(ranked))} entities for {FOREST_CHANGE_COLUMN} in {year} "
        f"(order={args.order}, "
        f"{'countries only' if only_countries else 'including aggregates'}):"
    )
    return format_top_list(title=title, rows=ranked, unit="ha")


def run_ranking(repo: ClimateRepository, args: argparse.Namespace) -> str:
    """implement the --ranking feature"""
    only_countries = not args.include_aggregates

    if args.ranking:
        entity, year, rank, value = repo.forest_rank_for_entity(
            entity_query=args.ranking,
            year=args.year,
            order=args.order,
            only_countries=only_countries,
        )
        total = repo.forest_count_entities_for_year(year=year, only_countries=only_countries)
        context = RankContext(metric=FOREST_CHANGE_COLUMN, unit="ha", order=args.order)
        result = RankResult(
            entity=entity,
            year=year,
            context=context,
            rank=rank,
            total=total,
            value=value,
        )
        return format_rank_result(result)

    year = args.year if args.year is not None else repo.forest_latest_year(only_countries)

    ranked = repo.forest_rank_entities(
        year=year,
        order=args.order,
        top_n=args.top,
        only_countries=only_countries,
    )
    title = (
        f"Forest change ranking for {year} (order={args.order}, "
        f"{'countries only' if only_countries else 'including aggregates'}):"
    )
    return format_top_list(title=title, rows=ranked, unit="ha")


def run_co2(repo: ClimateRepository, args: argparse.Namespace) -> str:
    """implement the --co2 feature"""
    only_countries = not args.include_aggregates

    if args.co2:
        entity, year, value = repo.co2_value_for_entity_year(
            entity_query=args.co2,
            year=args.year,
            only_countries=only_countries,
        )
        return format_single_value(
            entity=entity,
            year=year,
            metric=CO2_COLUMN,
            value=value,
            unit="t/person",
        )

    year = args.year if args.year is not None else repo.co2_latest_year(only_countries)

    top_rows = repo.co2_top_emitters(
        year=year,
        top_n=args.top,
        only_countries=only_countries,
    )
    title = (
        f"Top {min(args.top, len(top_rows))} entities for {CO2_COLUMN} in {year} "
        f"({'countries only' if only_countries else 'including aggregates'}):"
    )
    return format_top_list(title=title, rows=top_rows, unit="t/person")


def main(argv: Optional[List[str]] = None) -> int:
    """run the CLI and return a process exit code"""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        db = get_db()
        repo = ClimateRepository(db)

        if args.deforestation is not None:
            output = run_deforestation(repo, args)
        elif args.co2 is not None:
            output = run_co2(repo, args)
        else:
            output = run_ranking(repo, args)

    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
