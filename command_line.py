"""
Examples:
    python3 command_line.py deforestation --country "Algeria" --year 2020
    python3 command_line.py co2 --country "Germany" --year 2020
    python3 command_line.py ranking --country "Germany" --year 2020
"""
from __future__ import annotations
import argparse
import sys

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="command_line.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_country_year(sp):
        sp.add_argument("--country", required=True, help="Country / Entity name (e.g., Algeria)")
        sp.add_argument("--year", required=True, type=int, help="Year (e.g., 2020)")

    sp1 = sub.add_parser("deforestation", help="Lookup annual forest area change (ha) for a country/year")
    add_country_year(sp1)

    sp2 = sub.add_parser("co2", help="Lookup CO2 emissions per capita for a country/year")
    add_country_year(sp2)

    sp3 = sub.add_parser("ranking", help="Get both ranks for a country/year")
    add_country_year(sp3)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    from ProductionCode.co2_queries import DataSource
    ds = DataSource()

    if args.cmd == "deforestation":
        rows = ds.query_forest([args.country, str(args.year)])
        if not rows:
            print("Not found.")
            return 1
        val = next(v for k, v in rows[0].items() if k not in ("entity", "year", "code"))
        print(f"Deforestation area of {args.country} in {args.year} is {val} ha")
        return 0

    if args.cmd == "co2":
        rows = ds.query_co2([args.country, str(args.year)])
        if not rows:
            print("Not found.")
            return 1
        val = next(v for k, v in rows[0].items() if k not in ("entity", "year", "code"))
        print(f"CO₂ emissions per capita of {args.country} in {args.year} is {val}")
        return 0

    if args.cmd == "ranking":
        # deforestation ascending, co2 descending
        # to make consistent
        def_rows = ds.db.query(
            "SELECT Entity, Annual_Forest_Change FROM forest_change WHERE Year = :y",
            y=args.year,
        ).all(as_dict=True)
        def_vals = [(r["entity"], float(r["annual_forest_change"])) for r in def_rows if r.get("annual_forest_change") is not None]
        def_vals.sort(key=lambda t: t[1])
        def_rank = next((i for i, (e, _) in enumerate(def_vals, start=1) if e == args.country), None)

        co2_rows = ds.db.query(
            "SELECT Entity, co2_per_capita FROM co2 WHERE Year = :y",
            y=args.year,
        ).all(as_dict=True)
        co2_vals = [(r["entity"], float(r["co2_per_capita"])) for r in co2_rows if r.get("co2_per_capita") is not None]
        co2_vals.sort(key=lambda t: t[1], reverse=True)
        co2_rank = next((i for i, (e, _) in enumerate(co2_vals, start=1) if e == args.country), None)

        if def_rank is None or co2_rank is None:
            print("Not found.")
            return 1
        print(f"In {args.year}, {args.country} ranks #{def_rank} in deforestation and #{co2_rank} in CO₂ emissions per capita.")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
