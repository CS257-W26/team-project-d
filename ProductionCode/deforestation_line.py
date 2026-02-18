"""
deforestation_line.py
Command-line interface for deforestation queries.

Usage examples:
    python3 deforestation_line.py search --entity "Brazil" --year 2020
    python3 deforestation_line.py range --entity "Brazil" --year1 2000 --year2 2020
    python3 deforestation_line.py list --year 2020
    python3 deforestation_line.py aggregate --year 2020 --entities "Brazil" "Peru" "Chile"
    python3 deforestation_line.py chart --year 2020 --order top --n 10
"""

from __future__ import annotations

import argparse
import sys
from typing import List

from deforestation_queries import DeforestationDataSource, DeforestationRow


def _print_row(row: DeforestationRow) -> None:
    print(f"{row.entity} ({row.year}): {row.annual_change_forest_area}")


def _print_rows(rows: List[DeforestationRow]) -> None:
    for r in rows:
        _print_row(r)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deforestation_line.py",
        description="Query annual change in forest area from the database.",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_search = sub.add_parser("search", help="Get value for one entity in one year.")
    p_search.add_argument("--entity", required=True, help="Entity name, e.g., 'Brazil'")
    p_search.add_argument("--year", required=True, type=int, help="Year, e.g., 2020")

    p_range = sub.add_parser("range", help="Get values for an entity across a year range.")
    p_range.add_argument("--entity", required=True)
    p_range.add_argument("--year1", required=True, type=int)
    p_range.add_argument("--year2", required=True, type=int)

    p_list = sub.add_parser("list", help="List entities available in a year.")
    p_list.add_argument("--year", required=True, type=int)

    p_agg = sub.add_parser("aggregate", help="Get multiple entities' values for a year and sum them.")
    p_agg.add_argument("--year", required=True, type=int)
    p_agg.add_argument("--entities", nargs="+", required=True, help="One or more entity names.")

    p_chart = sub.add_parser("chart", help="Top/bottom N entities for a year.")
    p_chart.add_argument("--year", required=True, type=int)
    p_chart.add_argument("--order", choices=["top", "bottom"], required=True)
    p_chart.add_argument("--n", type=int, default=10)

    return parser


def main(argv: List[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    ds = DeforestationDataSource()

    try:
        if args.cmd == "search":
            row = ds.get_value(args.entity, args.year)
            _print_row(row)
            return 0

        if args.cmd == "range":
            rows = ds.range_values(args.entity, args.year1, args.year2)
            _print_rows(rows)
            return 0

        if args.cmd == "list":
            entities = ds.list_entities(args.year)
            print("\n".join(entities))
            return 0

        if args.cmd == "aggregate":
            rows, total = ds.aggregate_sum(args.entities, args.year)
            _print_rows(rows)
            print(f"Sum: {total}")
            return 0

        if args.cmd == "chart":
            rows = ds.top_or_bottom(args.year, args.n, args.order)
            _print_rows(rows)
            return 0

        parser.error("Unknown command.")
        return 2

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))