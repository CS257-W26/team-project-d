"""
Database-backed query layer for the Climate Data Explorer.
"""

from __future__ import annotations

from typing import Any, Optional

from ProductionCode.entity_utils import match_entity_name

FOREST_CHANGE_COLUMN = "Annual change in forest area"
CO2_COLUMN = "Annual CO₂ emissions (per capita)"

_COUNTRIES_TABLE = "countries"
_FOREST_TABLE = "forest_change"
_CO2_TABLE = "co2_per_capita"

_SQL_COUNTRIES = f"SELECT c.entity FROM {_COUNTRIES_TABLE} c ORDER BY c.entity"

_SQL_FOREST_VALUE = (
    "SELECT f.forest_change_ha AS value "
    f"FROM {_FOREST_TABLE} f "
    f"INNER JOIN {_COUNTRIES_TABLE} c ON c.entity = f.entity "
    "WHERE f.entity = :entity AND f.year = :year"
)
_SQL_CO2_VALUE = (
    "SELECT t.co2_tonnes_per_capita AS value "
    f"FROM {_CO2_TABLE} t "
    f"INNER JOIN {_COUNTRIES_TABLE} c ON c.entity = t.entity "
    "WHERE t.entity = :entity AND t.year = :year"
)

_SQL_FOREST_LATEST_YEAR_ENTITY = (
    "SELECT MAX(f.year) AS year "
    f"FROM {_FOREST_TABLE} f "
    f"INNER JOIN {_COUNTRIES_TABLE} c ON c.entity = f.entity "
    "WHERE f.entity = :entity"
)
_SQL_CO2_LATEST_YEAR_ENTITY = (
    "SELECT MAX(t.year) AS year "
    f"FROM {_CO2_TABLE} t "
    f"INNER JOIN {_COUNTRIES_TABLE} c ON c.entity = t.entity "
    "WHERE t.entity = :entity"
)

_SQL_COMMON_YEARS = (
    "SELECT DISTINCT f.year AS year "
    f"FROM {_FOREST_TABLE} f "
    f"INNER JOIN {_CO2_TABLE} t ON t.entity = f.entity AND t.year = f.year "
    f"INNER JOIN {_COUNTRIES_TABLE} c ON c.entity = f.entity "
    "ORDER BY year"
)
_SQL_COMMON_YEARS_ENTITY = (
    "SELECT DISTINCT f.year AS year "
    f"FROM {_FOREST_TABLE} f "
    f"INNER JOIN {_CO2_TABLE} t ON t.entity = f.entity AND t.year = f.year "
    f"INNER JOIN {_COUNTRIES_TABLE} c ON c.entity = f.entity "
    "WHERE f.entity = :entity "
    "ORDER BY year"
)
_SQL_COMMON_LATEST_YEAR_ENTITY = (
    "SELECT MAX(f.year) AS year "
    f"FROM {_FOREST_TABLE} f "
    f"INNER JOIN {_CO2_TABLE} t ON t.entity = f.entity AND t.year = f.year "
    f"INNER JOIN {_COUNTRIES_TABLE} c ON c.entity = f.entity "
    "WHERE f.entity = :entity"
)
_SQL_SNAPSHOT = (
    "SELECT t.co2_tonnes_per_capita AS co2_per_capita, "
    "f.forest_change_ha AS forest_change "
    f"FROM {_FOREST_TABLE} f "
    f"INNER JOIN {_CO2_TABLE} t ON t.entity = f.entity AND t.year = f.year "
    f"INNER JOIN {_COUNTRIES_TABLE} c ON c.entity = f.entity "
    "WHERE f.entity = :entity AND f.year = :year"
)
_SQL_SERIES = (
    "SELECT f.year AS year, "
    "t.co2_tonnes_per_capita AS co2_per_capita, "
    "f.forest_change_ha AS forest_change "
    f"FROM {_FOREST_TABLE} f "
    f"INNER JOIN {_CO2_TABLE} t ON t.entity = f.entity AND t.year = f.year "
    f"INNER JOIN {_COUNTRIES_TABLE} c ON c.entity = f.entity "
    "WHERE f.entity = :entity "
    "ORDER BY year"
)


class ClimateRepository:
    """repository wrapping SQL queries for the project datasets"""

    def __init__(self, db: Any):
        self._db = db

    def _first(self, rows: Any) -> Optional[Any]:
        """return the first row in a records result, if present"""
        return rows[0] if rows else None

    def countries(self) -> list[str]:
        """return the list of countries supported by this app"""
        rows = self._db.query(_SQL_COUNTRIES)
        return [row["entity"] for row in rows]

    def resolve_country(self, raw: str) -> Optional[str]:
        """match user input to a canonical country name, if possible"""
        return match_entity_name(raw, self.countries())

    def common_years(self) -> list[int]:
        """return years where both datasets have data for at least one country"""
        rows = self._db.query(_SQL_COMMON_YEARS)
        return [int(r["year"]) for r in rows if r.get("year") is not None]

    def common_years_for_country(self, entity: str) -> list[int]:
        """return years where both datasets have data for the given country"""
        rows = self._db.query(_SQL_COMMON_YEARS_ENTITY, entity=entity)
        return [int(r["year"]) for r in rows if r.get("year") is not None]

    def forest_latest_year_for_country(self, entity: str) -> int:
        """return the latest forest-change year available for a country"""
        row = self._first(self._db.query(_SQL_FOREST_LATEST_YEAR_ENTITY, entity=entity))
        return int(row["year"]) if row and row.get("year") is not None else 0

    def co2_latest_year_for_country(self, entity: str) -> int:
        """return the latest CO₂ per-capita year available for a country"""
        row = self._first(self._db.query(_SQL_CO2_LATEST_YEAR_ENTITY, entity=entity))
        return int(row["year"]) if row and row.get("year") is not None else 0

    def common_latest_year_for_country(self, entity: str) -> int:
        """return the latest year where both datasets have values for a country"""
        row = self._first(self._db.query(_SQL_COMMON_LATEST_YEAR_ENTITY, entity=entity))
        return int(row["year"]) if row and row.get("year") is not None else 0

    def forest_value(self, entity: str, year: int) -> Optional[float]:
        """return forest-change value for a country/year"""
        row = self._first(self._db.query(_SQL_FOREST_VALUE, entity=entity, year=year))
        return float(row["value"]) if row else None

    def co2_value(self, entity: str, year: int) -> Optional[float]:
        """return CO₂ per-capita value for a country/year"""
        row = self._first(self._db.query(_SQL_CO2_VALUE, entity=entity, year=year))
        return float(row["value"]) if row else None

    def snapshot(self, entity: str, year: int) -> Optional[dict[str, float]]:
        """return both metrics for a country/year, if available"""
        row = self._first(self._db.query(_SQL_SNAPSHOT, entity=entity, year=year))
        if not row:
            return None
        return {
            "co2_per_capita": float(row["co2_per_capita"]),
            "forest_change": float(row["forest_change"]),
        }

    def series(self, entity: str) -> list[dict[str, float]]:
        """return year-by-year data (both metrics) for a country"""
        rows = self._db.query(_SQL_SERIES, entity=entity)
        return [
            {
                "year": int(r["year"]),
                "co2_per_capita": float(r["co2_per_capita"]),
                "forest_change": float(r["forest_change"]),
            }
            for r in rows
        ]
