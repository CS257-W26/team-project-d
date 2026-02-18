"""
Database-backed query functions for the project datasets.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

from ProductionCode.entity_utils import match_entity_name

FOREST_CHANGE_COLUMN = "Annual change in forest area"
CO2_COLUMN = "Annual CO₂ emissions (per capita)"

_FOREST_TABLE = "forest_change"
_CO2_TABLE = "co2_per_capita"
_COUNTRIES_TABLE = "countries"

_SQL_ENTITIES = "SELECT DISTINCT t.entity FROM {table} t {join} ORDER BY t.entity"
_SQL_MAX_YEAR = "SELECT MAX(t.year) AS year FROM {table} t {join}"
_SQL_MAX_YEAR_ENTITY = _SQL_MAX_YEAR + " WHERE t.entity = :entity"

_SQL_FOREST_VALUE = (
    "SELECT t.forest_change_ha AS value "
    f"FROM {_FOREST_TABLE} t {{join}} "
    "WHERE t.entity = :entity AND t.year = :year"
)
_SQL_FOREST_COUNT = (
    "SELECT COUNT(*) AS count "
    f"FROM {_FOREST_TABLE} t {{join}} "
    "WHERE t.year = :year"
)
_SQL_FOREST_RANK_LIST = (
    "SELECT t.entity, t.forest_change_ha AS value "
    f"FROM {_FOREST_TABLE} t {{join}} "
    "WHERE t.year = :year "
    "ORDER BY {order_by} "
    "LIMIT :top_n"
)
_SQL_FOREST_RANK = (
    "SELECT 1 + COUNT(*) AS rank "
    f"FROM {_FOREST_TABLE} t {{join}} "
    "WHERE t.year = :year AND {before_where}"
)

_SQL_CO2_VALUE = (
    "SELECT t.co2_tonnes_per_capita AS value "
    f"FROM {_CO2_TABLE} t {{join}} "
    "WHERE t.entity = :entity AND t.year = :year"
)
_SQL_CO2_TOP = (
    "SELECT t.entity, t.co2_tonnes_per_capita AS value "
    f"FROM {_CO2_TABLE} t {{join}} "
    "WHERE t.year = :year "
    "ORDER BY t.co2_tonnes_per_capita DESC, t.entity DESC "
    "LIMIT :top_n"
)

_FOREST_ORDER_BY = {
    "loss": "t.forest_change_ha ASC, t.entity ASC",
    "gain": "t.forest_change_ha DESC, t.entity DESC",
}
_FOREST_BEFORE_WHERE = {
    "loss": (
        "(t.forest_change_ha < :value OR "
        "(t.forest_change_ha = :value AND t.entity < :entity))"
    ),
    "gain": (
        "(t.forest_change_ha > :value OR "
        "(t.forest_change_ha = :value AND t.entity > :entity))"
    ),
}


class ClimateRepository:
    """repository that queries the climate datasets from a SQL database"""

    def __init__(self, db: Any):
        """create a repository bound to a records.Database -like object"""
        self._db = db

    @staticmethod
    def _join(only_countries: bool) -> str:
        """return optional join clause used to restrict to countries"""
        return f"JOIN {_COUNTRIES_TABLE} c ON c.entity = t.entity" if only_countries else ""

    def _first(self, sql: str, **params):
        """return db.query(...).first() for convenience"""
        return self._db.query(sql, **params).first()

    def _year(self, sql: str, error: str, **params) -> int:
        """return an integer year from a query, or raise ValueError"""
        row = self._first(sql, **params)
        if row and row["year"] is not None:
            return int(row["year"])
        raise ValueError(error)

    def _float(self, sql: str, error: str, **params) -> float:
        """return a float value from a query, or raise ValueError"""
        row = self._first(sql, **params)
        if row:
            return float(row["value"])
        raise ValueError(error)

    def _entities(self, table: str, only_countries: bool) -> List[str]:
        """return all entities present in a dataset table"""
        sql = _SQL_ENTITIES.format(table=table, join=self._join(only_countries))
        return [r["entity"] for r in self._db.query(sql)]

    def forest_entities(self, only_countries: bool) -> List[str]:
        """return entity names present in the forest-change dataset"""
        return self._entities(_FOREST_TABLE, only_countries)

    def co2_entities(self, only_countries: bool) -> List[str]:
        """return entity names present in the CO₂ per-capita dataset"""
        return self._entities(_CO2_TABLE, only_countries)

    def forest_latest_year(self, only_countries: bool) -> int:
        """return the most recent year in the forest-change dataset"""
        sql = _SQL_MAX_YEAR.format(table=_FOREST_TABLE, join=self._join(only_countries))
        return self._year(sql, "No forest-change data available.")

    def co2_latest_year(self, only_countries: bool) -> int:
        """return the most recent year in the CO₂ per-capita dataset"""
        sql = _SQL_MAX_YEAR.format(table=_CO2_TABLE, join=self._join(only_countries))
        return self._year(sql, "No CO₂ per-capita data available.")

    def forest_latest_year_for_entity(self, entity: str, only_countries: bool) -> int:
        """return the latest year with forest-change data for an entity"""
        sql = _SQL_MAX_YEAR_ENTITY.format(table=_FOREST_TABLE, join=self._join(only_countries))
        return self._year(sql, f"No forest-change data found for entity: {entity}", entity=entity)

    def co2_latest_year_for_entity(self, entity: str, only_countries: bool) -> int:
        """return the latest year with CO₂ per-capita data for an entity"""
        sql = _SQL_MAX_YEAR_ENTITY.format(table=_CO2_TABLE, join=self._join(only_countries))
        return self._year(sql, f"No CO₂ per-capita data found for entity: {entity}", entity=entity)

    def _forest_value(self, entity: str, year: int, only_countries: bool) -> float:
        """return forest-change value for a known entity and year"""
        sql = _SQL_FOREST_VALUE.format(join=self._join(only_countries))
        return self._float(
            sql,
            f"No forest change data for {entity} in {year}.",
            entity=entity,
            year=year,
        )

    def _co2_value(self, entity: str, year: int, only_countries: bool) -> float:
        """return co2 per-capita value for a known entity and year"""
        sql = _SQL_CO2_VALUE.format(join=self._join(only_countries))
        return self._float(
            sql,
            f"No CO₂ per-capita data for {entity} in {year}.",
            entity=entity,
            year=year,
        )

    def forest_value_for_entity_year(
        self, entity_query: str, year: Optional[int], only_countries: bool
    ) -> Tuple[str, int, float]:
        """look up a forest-change value for an entity and year"""
        entity = match_entity_name(entity_query, self.forest_entities(only_countries))
        year_used = year or self.forest_latest_year_for_entity(entity, only_countries)
        return entity, year_used, self._forest_value(entity, year_used, only_countries)

    def co2_value_for_entity_year(
        self, entity_query: str, year: Optional[int], only_countries: bool
    ) -> Tuple[str, int, float]:
        """look up a co2 per-capita value for an entity and year"""
        entity = match_entity_name(entity_query, self.co2_entities(only_countries))
        year_used = year or self.co2_latest_year_for_entity(entity, only_countries)
        return entity, year_used, self._co2_value(entity, year_used, only_countries)

    def forest_count_entities_for_year(self, year: int, only_countries: bool) -> int:
        """return how many entities have forest-change data in a given year"""
        sql = _SQL_FOREST_COUNT.format(join=self._join(only_countries))
        row = self._first(sql, year=year)
        return int(row["count"]) if row else 0

    @staticmethod
    def _forest_order_by(order: str) -> str:
        """return order by clause for forest ranking"""
        if order in _FOREST_ORDER_BY:
            return _FOREST_ORDER_BY[order]
        raise ValueError("order must be 'loss' or 'gain'.")

    @staticmethod
    def _forest_before_where(order: str) -> str:
        """return where fragment used to count rows before a target row"""
        if order in _FOREST_BEFORE_WHERE:
            return _FOREST_BEFORE_WHERE[order]
        raise ValueError("order must be 'loss' or 'gain'.")

    def _forest_rank(
        self, entity: str, year: int, order: str, value: float, only_countries: bool
    ) -> int:
        """return the rank for a known entity/year/value triple"""
        sql = _SQL_FOREST_RANK.format(
            join=self._join(only_countries), before_where=self._forest_before_where(order)
        )
        row = self._first(sql, year=year, value=value, entity=entity)
        if row and row["rank"] is not None:
            return int(row["rank"])
        raise ValueError(f"No forest change data for {entity} in {year}.")

    def forest_rank_entities(
        self, year: int, order: str, top_n: int, only_countries: bool
    ) -> List[Tuple[str, float]]:
        """return top N entities by forest-change value for a given year"""
        if top_n <= 0:
            raise ValueError("top_n must be a positive integer.")
        sql = _SQL_FOREST_RANK_LIST.format(
            join=self._join(only_countries), order_by=self._forest_order_by(order)
        )
        rows = self._db.query(sql, year=year, top_n=top_n)
        result = [(r["entity"], float(r["value"])) for r in rows]
        if not result:
            raise ValueError(f"No forest change data found for year {year}.")
        return result

    def forest_rank_for_entity(
        self, entity_query: str, year: Optional[int], order: str, only_countries: bool
    ) -> Tuple[str, int, int, float]:
        """return (entity, year, rank, value) for forest-change ranking"""
        entity = match_entity_name(entity_query, self.forest_entities(only_countries))
        year_used = year or self.forest_latest_year_for_entity(entity, only_countries)
        value = self._forest_value(entity, year_used, only_countries)
        rank = self._forest_rank(entity, year_used, order, value, only_countries)
        return entity, year_used, rank, value

    def co2_top_emitters(
        self, year: int, top_n: int, only_countries: bool
    ) -> List[Tuple[str, float]]:
        """return top n entities by co2 per-capita emissions for a given year"""
        if top_n <= 0:
            raise ValueError("top_n must be a positive integer.")
        sql = _SQL_CO2_TOP.format(join=self._join(only_countries))
        rows = self._db.query(sql, year=year, top_n=top_n)
        result = [(r["entity"], float(r["value"])) for r in rows]
        if not result:
            raise ValueError(f"No CO₂ per-capita data found for year {year}.")
        return result
