# Queries for the CO₂ emissions per capita dataset

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from ProductionCode.entity_utils import match_entity_name
from ProductionCode.io_utils import read_csv_records
from ProductionCode.numbers import parse_float, parse_int

CO2_FILENAME = "co-emissions-per-capita.csv"
CO2_COLUMN = "Annual CO₂ emissions (per capita)"


@dataclass(frozen=True)
# a typed row from the CO₂ per-capita dataset
class Co2Row:
    entity: str
    year: int
    value_tonnes_per_capita: float

# load CO₂ per-capita rows from the data directory
def load_co2_rows(data_dir: Path) -> List[Co2Row]:
    csv_path = data_dir / CO2_FILENAME
    raw = read_csv_records(csv_path)

    rows: List[Co2Row] = []
    for record in raw:
        value = parse_float(record.get(CO2_COLUMN, ""))
        if value is None:
            continue
        rows.append(
            Co2Row(
                entity=record.get("Entity", "").strip(),
                year=parse_int(record.get("Year", "0")),
                value_tonnes_per_capita=value,
            )
        )
    return rows

# list unique entity names in the CO₂ dataset
def entities(rows: Sequence[Co2Row], only_countries: bool, country_entities: Optional[Iterable[str]]) -> List[str]:
    allowed = set(country_entities) if (only_countries and country_entities is not None) else None

    seen = set()
    result: List[str] = []
    for row in rows:
        if allowed is not None and row.entity not in allowed:
            continue
        if row.entity not in seen:
            seen.add(row.entity)
            result.append(row.entity)
    return result

# return the most recent year with data for an entity
def latest_year_for_entity(rows: Sequence[Co2Row], entity: str) -> int:
    years = [row.year for row in rows if row.entity == entity]
    if not years:
        raise ValueError(f"No data found for entity: {entity}")
    return max(years)

# return the most recent year with any data
def latest_year(rows: Sequence[Co2Row], only_countries: bool, country_entities: Optional[Iterable[str]]) -> int:
    allowed = set(country_entities) if (only_countries and country_entities is not None) else None
    years = [row.year for row in rows if (allowed is None or row.entity in allowed)]
    if not years:
        raise ValueError("No data available.")
    return max(years)


def value_for_entity_year(
    rows: Sequence[Co2Row],
    entity_query: str,
    year: Optional[int],
    only_countries: bool,
    country_entities: Optional[Iterable[str]],
) -> Tuple[str, int, float]:
    # get a CO₂ per-capita value for an entity and year
    entity_name = match_entity_name(entity_query, entities(rows, only_countries, country_entities))
    year_to_use = year if year is not None else latest_year_for_entity(rows, entity_name)

    for row in rows:
        if row.entity == entity_name and row.year == year_to_use:
            return entity_name, year_to_use, row.value_tonnes_per_capita

    raise ValueError(f"No CO₂ per-capita data for {entity_name} in {year_to_use}.")


def top_emitters(
    rows: Sequence[Co2Row],
    year: int,
    top_n: int,
    only_countries: bool,
    country_entities: Optional[Iterable[str]],
) -> List[Tuple[str, float]]:
    # return the top N entities by CO₂ emissions per capita for a year
    allowed = set(country_entities) if (only_countries and country_entities is not None) else None
    year_rows = [
        row for row in rows
        if row.year == year and (allowed is None or row.entity in allowed)
    ]
    if not year_rows:
        raise ValueError(f"No CO₂ per-capita data found for year {year}.")

    year_rows_sorted = sorted(year_rows, key=lambda r: (r.value_tonnes_per_capita, r.entity), reverse=True)
    return [(row.entity, row.value_tonnes_per_capita) for row in year_rows_sorted[:top_n]]
