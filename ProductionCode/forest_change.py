# Queries for the annual change in forest area dataset

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from ProductionCode.entity_utils import match_entity_name
from ProductionCode.io_utils import read_csv_records
from ProductionCode.numbers import parse_float, parse_int

FOREST_CHANGE_FILENAME = "annual-change-forest-area.csv"
FOREST_CHANGE_COLUMN = "Annual change in forest area"
COUNTRY_CODE_PATTERN = "^[A-Z]{3}$"


@dataclass(frozen=True)
# a typed row from the forest change dataset
class ForestChangeRow:
    entity: str
    code: str
    year: int
    value_ha: float

# load forest change rows from the data directory
def load_forest_change_rows(data_dir: Path) -> List[ForestChangeRow]:
    csv_path = data_dir / FOREST_CHANGE_FILENAME
    raw = read_csv_records(csv_path)
    rows: List[ForestChangeRow] = []

    for record in raw:
        value = parse_float(record.get(FOREST_CHANGE_COLUMN, ""))
        if value is None:
            continue
        rows.append(
            ForestChangeRow(
                entity=record.get("Entity", "").strip(),
                code=record.get("Code", "").strip(),
                year=parse_int(record.get("Year", "0")),
                value_ha=value,
            )
        )
    return rows

# return True if the row represents a country (ISO alpha-3 code)
def is_country_row(row: ForestChangeRow) -> bool:
    return len(row.code) == 3 and row.code.isalpha() and row.code.isupper()

# list unique entity names in the dataset
def entities(rows: Sequence[ForestChangeRow], only_countries: bool) -> List[str]:
    seen = set()
    result: List[str] = []

    for row in rows:
        if only_countries and not is_country_row(row):
            continue
        if row.entity not in seen:
            seen.add(row.entity)
            result.append(row.entity)
    return result

# return the most recent year with data for an entity
def latest_year_for_entity(rows: Sequence[ForestChangeRow], entity: str) -> int:
    years = [row.year for row in rows if row.entity == entity]

    if not years:
        raise ValueError(f"No data found for entity: {entity}")
    return max(years)

def value_for_entity_year(
    rows: Sequence[ForestChangeRow],
    entity_query: str,
    year: Optional[int],
    only_countries: bool,
) -> Tuple[str, int, float]:
    # get a forest change value for an entity and year
    entity_name = match_entity_name(entity_query, entities(rows, only_countries=only_countries))
    year_to_use = year if year is not None else latest_year_for_entity(rows, entity_name)

    for row in rows:
        if row.entity == entity_name and row.year == year_to_use:
            return entity_name, year_to_use, row.value_ha
    raise ValueError(f"No forest change data for {entity_name} in {year_to_use}.")

# return the most recent year with any data
def latest_year(rows: Sequence[ForestChangeRow], only_countries: bool) -> int:
    filtered = [row.year for row in rows if (not only_countries or is_country_row(row))]

    if not filtered:
        raise ValueError("No data available.")
    return max(filtered)

def rank_entities(
    rows: Sequence[ForestChangeRow],
    year: int,
    order: str,
    top_n: int,
    only_countries: bool,
) -> List[Tuple[str, float]]:
    # rank entities by forest change for a specific year
    if order not in {"loss", "gain"}:
        raise ValueError("order must be 'loss' or 'gain'.")
    year_rows = [
        row for row in rows
        if row.year == year and (not only_countries or is_country_row(row))
    ]
    
    if not year_rows:
        raise ValueError(f"No forest change data found for year {year}.")
    reverse = (order == "gain")
    year_rows_sorted = sorted(year_rows, key=lambda r: (r.value_ha, r.entity), reverse=reverse)
    return [(row.entity, row.value_ha) for row in year_rows_sorted[:top_n]]


def rank_for_entity(
    rows: Sequence[ForestChangeRow],
    entity_query: str,
    year: Optional[int],
    order: str,
    only_countries: bool,
) -> Tuple[str, int, int, float]:
    # return the rank of a single entity for a given year
    entity_name = match_entity_name(entity_query, entities(rows, only_countries=only_countries))
    year_used = year if year is not None else latest_year_for_entity(rows, entity_name)

    year_rows = [
        row for row in rows
        if row.year == year_used and (not only_countries or is_country_row(row))
    ]
    if not year_rows:
        raise ValueError(f"No forest change data found for year {year_used}.")

    reverse = (order == "gain")
    year_rows_sorted = sorted(year_rows, key=lambda r: (r.value_ha, r.entity), reverse=reverse)

    for idx, row in enumerate(year_rows_sorted, start=1):
        if row.entity == entity_name:
            return entity_name, year_used, idx, row.value_ha

    raise ValueError(f"No forest change data for {entity_name} in {year_used}.")
