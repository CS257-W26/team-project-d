"""
Queries for the CO₂ emissions per capita dataset.

Load the CO₂ emissions dataset and provides 
helper functions to look up values and list the top emitters.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from ProductionCode.entity_utils import match_entity_name
from ProductionCode.io_utils import read_csv_records
from ProductionCode.numbers import parse_float, parse_int
from ProductionCode.row_utils import latest_year as rows_latest_year
from ProductionCode.row_utils import latest_year_for_entity as rows_latest_year_for_entity
from ProductionCode.row_utils import unique_entities as rows_unique_entities

CO2_FILENAME = "co-emissions-per-capita.csv"
CO2_COLUMN = "Annual CO₂ emissions (per capita)"


@dataclass(frozen=True)
class Co2Row:
    """a single (entity, year) data point for CO₂ per-capita emissions"""
    entity: str
    year: int
    value_tonnes_per_capita: float


def load_co2_rows(data_dir: Path) -> List[Co2Row]:
    """load co2-per-capita data"""
    csv_path = data_dir / CO2_FILENAME
    raw_records = read_csv_records(csv_path)

    rows: List[Co2Row] = []
    for record in raw_records:
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


def _allowed_entity_set(
    only_countries: bool,
    country_entities: Optional[Iterable[str]],
) -> Optional[set[str]]:
    """return the allowed entity set if filtering to countries, otherwise None"""
    if not only_countries:
        return None
    if country_entities is None:
        return None
    return set(country_entities)


def entities(
    rows: Sequence[Co2Row],
    only_countries: bool,
    country_entities: Optional[Iterable[str]],
) -> List[str]:
    """return unique entity names in the CO₂ dataset"""
    allowed = _allowed_entity_set(only_countries, country_entities)

    def row_allowed(r: Co2Row) -> bool:
        return allowed is None or r.entity in allowed

    return rows_unique_entities(rows, row_filter=row_allowed)


def latest_year_for_entity(
    rows: Sequence[Co2Row],
    entity: str,
    only_countries: bool,
    country_entities: Optional[Iterable[str]],
) -> int:
    """return the most recent year with data for an entity"""
    allowed = _allowed_entity_set(only_countries, country_entities)

    def row_allowed(r: Co2Row) -> bool:
        return allowed is None or r.entity in allowed

    return rows_latest_year_for_entity(rows, entity, row_filter=row_allowed)


def latest_year(
    rows: Sequence[Co2Row],
    only_countries: bool,
    country_entities: Optional[Iterable[str]],
) -> int:
    """return the most recent year present in the dataset"""
    allowed = _allowed_entity_set(only_countries, country_entities)

    def row_allowed(r: Co2Row) -> bool:
        return allowed is None or r.entity in allowed

    return rows_latest_year(rows, row_filter=row_allowed)


def value_for_entity_year(
    rows: Sequence[Co2Row],
    entity_query: str,
    year: Optional[int],
    only_countries: bool,
    country_entities: Optional[Iterable[str]],
) -> Tuple[str, int, float]:
    """look up a co2 per-capita value for an entity and year"""
    entity_name = match_entity_name(
        entity_query,
        entities(rows, only_countries=only_countries, country_entities=country_entities),
    )

    year_to_use = (
        year
        if year is not None
        else latest_year_for_entity(
            rows,
            entity=entity_name,
            only_countries=only_countries,
            country_entities=country_entities,
        )
    )

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
    """return the top N entities by CO₂ per-capita emissions for *year*"""
    allowed = _allowed_entity_set(only_countries, country_entities)

    year_rows: List[Co2Row] = []
    for row in rows:
        if row.year != year:
            continue
        if allowed is not None and row.entity not in allowed:
            continue
        year_rows.append(row)

    if not year_rows:
        raise ValueError(f"No CO₂ per-capita data found for year {year}.")

    year_rows_sorted = sorted(
        year_rows,
        key=lambda r: (r.value_tonnes_per_capita, r.entity),
        reverse=True,
    )

    results: List[Tuple[str, float]] = []
    for row in year_rows_sorted[:top_n]:
        results.append((row.entity, row.value_tonnes_per_capita))
    return results
