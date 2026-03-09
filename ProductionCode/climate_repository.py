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
    """Repository wrapping SQL queries for the project datasets."""

    def __init__(self, db: Any):
        self._db = db

    @staticmethod
    def _first(rows: Any) -> Optional[Any]:
        """Return the first row from a records result or list-like collection."""
        if hasattr(rows, "first"):
            return rows.first()
        return rows[0] if rows else None

    @staticmethod
    def _item(row: Optional[Any], key: str) -> Optional[Any]:
        """Return a value from a row object, or None when unavailable."""
        if row is None:
            return None
        try:
            return row[key]
        except (KeyError, TypeError):
            return None

    @staticmethod
    def _years_from_rows(rows: Any) -> list[int]:
        """Extract non-null integer years from an iterable of rows."""
        years = []
        for row in rows:
            year = row["year"]
            if year is not None:
                years.append(int(year))
        return years

    def _latest_year(self, sql: str, entity: str) -> int:
        """Return the year from a MAX(year) query, or 0 if none exists."""
        row = self._first(self._db.query(sql, entity=entity))
        year = self._item(row, "year")
        return int(year) if year is not None else 0

    def _metric_value(self, sql: str, entity: str, year: int) -> Optional[float]:
        """Return a single numeric metric value for a country and year."""
        row = self._first(self._db.query(sql, entity=entity, year=year))
        value = self._item(row, "value")
        return float(value) if value is not None else None

    def countries(self) -> list[str]:
        """Return the list of countries supported by this app."""
        rows = self._db.query(_SQL_COUNTRIES)
        return [row["entity"] for row in rows]

    def resolve_country(self, raw: str) -> Optional[str]:
        """Match user input to a canonical country name, if possible."""
        try:
            return match_entity_name(raw, self.countries())
        except ValueError:
            return None

    def common_years(self) -> list[int]:
        """Return years where both datasets have data for at least one country."""
        return self._years_from_rows(self._db.query(_SQL_COMMON_YEARS))

    def common_years_for_country(self, entity: str) -> list[int]:
        """Return years where both datasets have data for the given country."""
        rows = self._db.query(_SQL_COMMON_YEARS_ENTITY, entity=entity)
        return self._years_from_rows(rows)

    def forest_latest_year_for_country(self, entity: str) -> int:
        """Return the latest forest-change year available for a country."""
        return self._latest_year(_SQL_FOREST_LATEST_YEAR_ENTITY, entity)

    def co2_latest_year_for_country(self, entity: str) -> int:
        """Return the latest CO₂ per-capita year available for a country."""
        return self._latest_year(_SQL_CO2_LATEST_YEAR_ENTITY, entity)

    def common_latest_year_for_country(self, entity: str) -> int:
        """Return the latest year where both datasets have values for a country."""
        return self._latest_year(_SQL_COMMON_LATEST_YEAR_ENTITY, entity)

    def forest_value(self, entity: str, year: int) -> Optional[float]:
        """Return forest-change value for a country/year."""
        return self._metric_value(_SQL_FOREST_VALUE, entity, year)

    def co2_value(self, entity: str, year: int) -> Optional[float]:
        """Return CO₂ per-capita value for a country/year."""
        return self._metric_value(_SQL_CO2_VALUE, entity, year)

    def snapshot(self, entity: str, year: int) -> Optional[dict[str, float]]:
        """Return both metrics for a country/year, if available."""
        row = self._first(self._db.query(_SQL_SNAPSHOT, entity=entity, year=year))
        if row is None:
            return None
        co2_value = self._item(row, "co2_per_capita")
        forest_value = self._item(row, "forest_change")
        if co2_value is None or forest_value is None:
            return None
        return {
            "co2_per_capita": float(co2_value),
            "forest_change": float(forest_value),
        }

    def series(self, entity: str) -> list[dict[str, float]]:
        """Return year-by-year data with both metrics for a country."""
        rows = self._db.query(_SQL_SERIES, entity=entity)
        return [
            {
                "year": int(row["year"]),
                "co2_per_capita": float(row["co2_per_capita"]),
                "forest_change": float(row["forest_change"]),
            }
            for row in rows
        ]
