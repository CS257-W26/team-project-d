"""
Queries for the annual change in forest area dataset.

Load annual change in forest area dataset and provides 
helper functions to look up values, compute rankings, and find default years.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from ProductionCode.entity_utils import match_entity_name
from ProductionCode.io_utils import read_csv_records
from ProductionCode.numbers import parse_float, parse_int
from ProductionCode.row_utils import latest_year as rows_latest_year
from ProductionCode.row_utils import latest_year_for_entity as rows_latest_year_for_entity
from ProductionCode.row_utils import unique_entities as rows_unique_entities

FOREST_CHANGE_FILENAME = "annual-change-forest-area.csv"
FOREST_CHANGE_COLUMN = "Annual change in forest area"


@dataclass(frozen=True)
class ForestChangeRow:
    """a single (entity, year) data point for forest-area change"""
    entity: str
    code: str
    year: int
    value_ha: float


def load_forest_change_rows(data_dir: Path) -> List[ForestChangeRow]:
    """load forest-change data"""
    csv_path = data_dir / FOREST_CHANGE_FILENAME
    raw_records = read_csv_records(csv_path)

    rows: List[ForestChangeRow] = []
    for record in raw_records:
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


def is_country_row(row: ForestChangeRow) -> bool:
    """return true if row looks like a country"""
    return len(row.code) == 3 and row.code.isalpha() and row.code.isupper()


def entities(rows: Sequence[ForestChangeRow], only_countries: bool) -> List[str]:
    """return unique entity names in the dataset"""

    def row_allowed(r: ForestChangeRow) -> bool:
        return (not only_countries) or is_country_row(r)

    return rows_unique_entities(rows, row_filter=row_allowed)


def latest_year_for_entity(rows: Sequence[ForestChangeRow], entity: str) -> int:
    """return the most recent year with data for entity"""
    return rows_latest_year_for_entity(rows, entity)


def latest_year(rows: Sequence[ForestChangeRow], only_countries: bool) -> int:
    """return the most recent year present in the dataset"""

    def row_allowed(r: ForestChangeRow) -> bool:
        return (not only_countries) or is_country_row(r)

    return rows_latest_year(rows, row_filter=row_allowed)


def value_for_entity_year(
    rows: Sequence[ForestChangeRow],
    entity_query: str,
    year: Optional[int],
    only_countries: bool,
) -> Tuple[str, int, float]:
    """look up a forest-change value for an entity and year"""
    entity_name = match_entity_name(
        entity_query,
        entities(rows, only_countries=only_countries),
    )
    year_to_use = year if year is not None else latest_year_for_entity(rows, entity_name)

    for row in rows:
        if row.entity == entity_name and row.year == year_to_use:
            return entity_name, year_to_use, row.value_ha

    raise ValueError(f"No forest change data for {entity_name} in {year_to_use}.")


def _year_rows(
    rows: Sequence[ForestChangeRow],
    year: int,
    only_countries: bool,
) -> List[ForestChangeRow]:
    """return all rows for a specific year, respecting the country filter"""
    year_rows: List[ForestChangeRow] = []
    for row in rows:
        if row.year != year:
            continue
        if only_countries and not is_country_row(row):
            continue
        year_rows.append(row)
    return year_rows


def _sorted_year_rows(
    rows: Sequence[ForestChangeRow],
    year: int,
    order: str,
    only_countries: bool,
) -> List[ForestChangeRow]:
    """return year rows sorted by forest change value"""
    if order not in {"loss", "gain"}:
        raise ValueError("order must be 'loss' or 'gain'.")

    year_rows = _year_rows(rows, year=year, only_countries=only_countries)
    if not year_rows:
        raise ValueError(f"No forest change data found for year {year}.")

    reverse = order == "gain"
    return sorted(
        year_rows,
        key=lambda r: (r.value_ha, r.entity),
        reverse=reverse,
    )


def count_entities_for_year(
    rows: Sequence[ForestChangeRow],
    year: int,
    only_countries: bool,
) -> int:
    """return the number of entities with data for a given year"""
    return len(_year_rows(rows, year=year, only_countries=only_countries))


def rank_entities(
    rows: Sequence[ForestChangeRow],
    year: int,
    order: str,
    top_n: int,
    only_countries: bool,
) -> List[Tuple[str, float]]:
    """return the top N entities by forest change for a year"""
    sorted_rows = _sorted_year_rows(
        rows,
        year=year,
        order=order,
        only_countries=only_countries,
    )

    results: List[Tuple[str, float]] = []
    for row in sorted_rows[:top_n]:
        results.append((row.entity, row.value_ha))
    return results


def rank_for_entity(
    rows: Sequence[ForestChangeRow],
    entity_query: str,
    year: Optional[int],
    order: str,
    only_countries: bool,
) -> Tuple[str, int, int, float]:
    """return the rank of one entity for a given year"""
    entity_name = match_entity_name(
        entity_query,
        entities(rows, only_countries=only_countries),
    )
    year_used = year if year is not None else latest_year_for_entity(rows, entity_name)

    sorted_rows = _sorted_year_rows(
        rows,
        year=year_used,
        order=order,
        only_countries=only_countries,
    )

    for idx, row in enumerate(sorted_rows, start=1):
        if row.entity == entity_name:
            return entity_name, year_used, idx, row.value_ha

    raise ValueError(f"No forest change data for {entity_name} in {year_used}.")
