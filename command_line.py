'''
The eventual location for the command line interface (CLI) for the project.
This will be the entry point for the project when run from the command line.
'''

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import List, Optional

from ProductionCode.co2 import (
    CO2_COLUMN,
    load_co2_rows,
    top_emitters,
    value_for_entity_year as co2_value_for_entity_year,
)
from ProductionCode.country_list import load_country_entities
from ProductionCode.forest_change import (
    FOREST_CHANGE_COLUMN,
    load_forest_change_rows,
    latest_year as forest_latest_year,
    rank_entities as forest_rank_entities,
    rank_for_entity as forest_rank_for_entity,
    value_for_entity_year as forest_value_for_entity_year,
)
from ProductionCode.output_format import (
    format_rank_result,
    format_single_value,
    format_top_list,
)

DEFAULT_TOP_N = 10

# build the argparse CLI parser, will return a configured ArgumentParser
def build_parser() -> argparse.ArgumentParser:
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
        help="Ranking order for forest change: 'loss' (most negative first) or 'gain' (most positive first). ",
    )
    parser.add_argument(
        "--include-aggregates",
        action="store_true",
        help="Include aggregates/regions (e.g., World, Africa) instead of only countries.",
    )
    parser.add_argument(
        "--data-dir",
        default=str(Path(__file__).resolve().parent / "Data"),
        help="Path to the directory containing CSV files (default: ./Data). ",
    )

    return parser

# run the --deforestation feature
def run_deforestation(args: argparse.Namespace) -> str:
    data_dir = Path(args.data_dir)
    rows = load_forest_change_rows(data_dir)

    only_countries = not args.include_aggregates

    # if user provided a country name, show a single value.
    if args.deforestation:
        entity, year, value = forest_value_for_entity_year(
            rows=rows,
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

    # otherwise list a ranking
    year = args.year if args.year is not None else forest_latest_year(rows, only_countries=only_countries)
    ranked = forest_rank_entities(
        rows=rows,
        year=year,
        order=args.order,
        top_n=args.top,
        only_countries=only_countries,
    )
    title = (
        f"Top {min(args.top, len(ranked))} entities for {FOREST_CHANGE_COLUMN} in {year} "
        f"(order={args.order}, {'countries only' if only_countries else 'including aggregates'}):"
    )
    return format_top_list(title=title, rows=ranked, unit="ha")

# run the --ranking feature.
def run_ranking(args: argparse.Namespace) -> str:
    data_dir = Path(args.data_dir)
    rows = load_forest_change_rows(data_dir)

    only_countries = not args.include_aggregates

    if args.ranking:
        entity, year, rank, value = forest_rank_for_entity(
            rows=rows,
            entity_query=args.ranking,
            year=args.year,
            order=args.order,
            only_countries=only_countries,
        )

        # total depends on year and filters
        year_rows = forest_rank_entities(
            rows=rows,
            year=year,
            order=args.order,
            # just a big number to get all (no specific meaning)
            top_n=10**9,  
            only_countries=only_countries,
        )
        total = len(year_rows)
        return format_rank_result(
            entity=entity,
            year=year,
            rank=rank,
            total=total,
            metric=FOREST_CHANGE_COLUMN,
            value=value,
            unit="ha",
            order=args.order,
        )

    year = args.year if args.year is not None else forest_latest_year(rows, only_countries=only_countries)
    ranked = forest_rank_entities(
        rows=rows,
        year=year,
        order=args.order,
        top_n=args.top,
        only_countries=only_countries,
    )
    title = (
        f"Forest change ranking for {year} "
        f"(order={args.order}, {'countries only' if only_countries else 'including aggregates'}):"
    )
    return format_top_list(title=title, rows=ranked, unit="ha")

# run the --co2 feature
def run_co2(args: argparse.Namespace) -> str:
    data_dir = Path(args.data_dir)
    rows = load_co2_rows(data_dir)

    # use the forest dataset to determine which entities count as countries
    country_entities = load_country_entities(data_dir)
    only_countries = not args.include_aggregates

    if args.co2:
        entity, year, value = co2_value_for_entity_year(
            rows=rows,
            entity_query=args.co2,
            year=args.year,
            only_countries=only_countries,
            country_entities=country_entities,
        )
        return format_single_value(
            entity=entity,
            year=year,
            metric=CO2_COLUMN,
            value=value,
            unit="t/person",
        )

    year = args.year if args.year is not None else max(r.year for r in rows)
    top_rows = top_emitters(
        rows=rows,
        year=year,
        top_n=args.top,
        only_countries=only_countries,
        country_entities=country_entities,
    )
    title = (
        f"Top {min(args.top, len(top_rows))} entities for {CO2_COLUMN} in {year} "
        f"({'countries only' if only_countries else 'including aggregates'}):"
    )
    return format_top_list(title=title, rows=top_rows, unit="t/person")

# entry point for the CLI
def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.deforestation is not None:
            output = run_deforestation(args)
        elif args.co2 is not None:
            output = run_co2(args)
        else:
            output = run_ranking(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
