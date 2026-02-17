"""
Database-backed query functions for the project datasets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from ProductionCode.entity_utils import match_entity_name

FOREST_CHANGE_COLUMN = "Annual change in forest area"
CO2_COLUMN = "Annual CO₂ emissions (per capita)"

_FOREST_TABLE = "forest_change"
_CO2_TABLE = "co2_per_capita"
_COUNTRIES_TABLE = "countries"


@dataclass(frozen=True)
class RankRow:
    """a single (entity, value) row in a ranked list"""

    entity: str
    value: float


class ClimateRepository:
    """repository that queries the climate datasets from a SQL database"""

    def __init__(self, db: Any):
        """create the repository"""
        self._db = db

    @staticmethod
    def _order_by(metric_column: str, entity_column: str, order: str) -> str:
        """return an order by clause for the given order"""
        if order == "loss":
            return f"{metric_column} ASC, {entity_column} ASC"
        if order == "gain":
            return f"{metric_column} DESC, {entity_column} DESC"
        raise ValueError("order must be 'loss' or 'gain'.")

    @staticmethod
    def _rank_where_clause(metric_column: str, entity_column: str, order: str) -> str:
        """return SQL used to count rows that come before a given row"""
        if order == "loss":
            return (
                f"({metric_column} < :value OR "
                f"({metric_column} = :value AND {entity_column} < :entity))"
            )
        if order == "gain":
            return (
                f"({metric_column} > :value OR "
                f"({metric_column} = :value AND {entity_column} > :entity))"
            )
        raise ValueError("order must be 'loss' or 'gain'.")

    @staticmethod
    def _countries_join_sql(only_countries: bool) -> str:
        """return the join clause needed to restrict to countries"""
        if only_countries:
            return f"JOIN {_COUNTRIES_TABLE} c ON c.entity = t.entity"
        return ""

    def forest_entities(self, only_countries: bool) -> List[str]:
        """return all entity names present in the forest-change dataset"""
        join_sql = self._countries_join_sql(only_countries)
        rows = self._db.query(
            f"""
            SELECT DISTINCT t.entity
            FROM {_FOREST_TABLE} t
            {join_sql}
            ORDER BY t.entity
            """
        )
        return [r["entity"] for r in rows]

    def forest_latest_year(self, only_countries: bool) -> int:
        """return the most recent year present in the forest-change dataset"""
        join_sql = self._countries_join_sql(only_countries)
        row = self._db.query(
            f"""
            SELECT MAX(t.year) AS year
            FROM {_FOREST_TABLE} t
            {join_sql}
            """
        ).first()
        if row is None or row["year"] is None:
            raise ValueError("No forest-change data available.")
        return int(row["year"])

    def forest_latest_year_for_entity(self, entity: str, only_countries: bool) -> int:
        """return the latest year with data for entity in the forest dataset"""
        join_sql = self._countries_join_sql(only_countries)
        row = self._db.query(
            f"""
            SELECT MAX(t.year) AS year
            FROM {_FOREST_TABLE} t
            {join_sql}
            WHERE t.entity = :entity
            """,
            entity=entity,
        ).first()
        if row is None or row["year"] is None:
            raise ValueError(f"No forest-change data found for entity: {entity}")
        return int(row["year"])

    def forest_value_for_entity_year(
        self,
        entity_query: str,
        year: Optional[int],
        only_countries: bool,
    ) -> Tuple[str, int, float]:
        """look up a forest-change value for an entity and year"""
        entity_name = match_entity_name(entity_query, self.forest_entities(only_countries))
        year_used = (
            year
            if year is not None
            else self.forest_latest_year_for_entity(entity_name, only_countries=only_countries)
        )

        join_sql = self._countries_join_sql(only_countries)
        row = self._db.query(
            f"""
            SELECT t.forest_change_ha AS value
            FROM {_FOREST_TABLE} t
            {join_sql}
            WHERE t.entity = :entity AND t.year = :year
            """,
            entity=entity_name,
            year=year_used,
        ).first()

        if row is None:
            raise ValueError(f"No forest change data for {entity_name} in {year_used}.")

        return entity_name, int(year_used), float(row["value"])

    def forest_count_entities_for_year(self, year: int, only_countries: bool) -> int:
        """return how many entities have forest-change data for a given year"""
        join_sql = self._countries_join_sql(only_countries)
        row = self._db.query(
            f"""
            SELECT COUNT(*) AS count
            FROM {_FOREST_TABLE} t
            {join_sql}
            WHERE t.year = :year
            """,
            year=year,
        ).first()

        return int(row["count"]) if row is not None else 0

    def forest_rank_entities(
        self,
        year: int,
        order: str,
        top_n: int,
        only_countries: bool,
    ) -> List[Tuple[str, float]]:
        """return top n entities by forest-change value for year"""
        if top_n <= 0:
            raise ValueError("top_n must be a positive integer.")

        order_by = self._order_by("t.forest_change_ha", "t.entity", order)
        join_sql = self._countries_join_sql(only_countries)

        rows = self._db.query(
            f"""
            SELECT t.entity, t.forest_change_ha AS value
            FROM {_FOREST_TABLE} t
            {join_sql}
            WHERE t.year = :year
            ORDER BY {order_by}
            LIMIT :top_n
            """,
            year=year,
            top_n=top_n,
        )

        results = [(r["entity"], float(r["value"])) for r in rows]
        if not results:
            raise ValueError(f"No forest change data found for year {year}.")
        return results

    def forest_rank_for_entity(
        self,
        entity_query: str,
        year: Optional[int],
        order: str,
        only_countries: bool,
    ) -> Tuple[str, int, int, float]:
        """return the rank of a single entity for a given year"""
        entity_name = match_entity_name(entity_query, self.forest_entities(only_countries))
        year_used = (
            year
            if year is not None
            else self.forest_latest_year_for_entity(entity_name, only_countries=only_countries)
        )

        """first get the entity's value"""
        _, _, value = self.forest_value_for_entity_year(
            entity_query=entity_name,
            year=year_used,
            only_countries=only_countries,
        )

        join_sql = self._countries_join_sql(only_countries)
        where_before = self._rank_where_clause("t.forest_change_ha", "t.entity", order)

        row = self._db.query(
            f"""
            SELECT 1 + COUNT(*) AS rank
            FROM {_FOREST_TABLE} t
            {join_sql}
            WHERE t.year = :year
              AND {where_before}
            """,
            year=year_used,
            value=value,
            entity=entity_name,
        ).first()

        if row is None or row["rank"] is None:
            raise ValueError(f"No forest change data for {entity_name} in {year_used}.")

        return entity_name, int(year_used), int(row["rank"]), float(value)

    def co2_entities(self, only_countries: bool) -> List[str]:
        """return all entity names present in the co2 per-capita dataset"""
        join_sql = self._countries_join_sql(only_countries)
        rows = self._db.query(
            f"""
            SELECT DISTINCT t.entity
            FROM {_CO2_TABLE} t
            {join_sql}
            ORDER BY t.entity
            """
        )
        return [r["entity"] for r in rows]

    def co2_latest_year(self, only_countries: bool) -> int:
        """return the most recent year present in the co2 dataset"""
        join_sql = self._countries_join_sql(only_countries)
        row = self._db.query(
            f"""
            SELECT MAX(t.year) AS year
            FROM {_CO2_TABLE} t
            {join_sql}
            """
        ).first()
        if row is None or row["year"] is None:
            raise ValueError("No CO₂ per-capita data available.")
        return int(row["year"])

    def co2_latest_year_for_entity(self, entity: str, only_countries: bool) -> int:
        """return the latest year with co2 data for entity"""
        join_sql = self._countries_join_sql(only_countries)
        row = self._db.query(
            f"""
            SELECT MAX(t.year) AS year
            FROM {_CO2_TABLE} t
            {join_sql}
            WHERE t.entity = :entity
            """,
            entity=entity,
        ).first()
        if row is None or row["year"] is None:
            raise ValueError(f"No CO₂ per-capita data found for entity: {entity}")
        return int(row["year"])

    def co2_value_for_entity_year(
        self,
        entity_query: str,
        year: Optional[int],
        only_countries: bool,
    ) -> Tuple[str, int, float]:
        """look up a co2 per-capita value for an entity and year"""
        entity_name = match_entity_name(entity_query, self.co2_entities(only_countries))
        year_used = (
            year
            if year is not None
            else self.co2_latest_year_for_entity(entity_name, only_countries=only_countries)
        )

        join_sql = self._countries_join_sql(only_countries)
        row = self._db.query(
            f"""
            SELECT t.co2_tonnes_per_capita AS value
            FROM {_CO2_TABLE} t
            {join_sql}
            WHERE t.entity = :entity AND t.year = :year
            """,
            entity=entity_name,
            year=year_used,
        ).first()

        if row is None:
            raise ValueError(f"No CO₂ per-capita data for {entity_name} in {year_used}.")

        return entity_name, int(year_used), float(row["value"])

    def co2_top_emitters(
        self,
        year: int,
        top_n: int,
        only_countries: bool,
    ) -> List[Tuple[str, float]]:
        """return top n entities by co2 per-capita emissions for year"""
        if top_n <= 0:
            raise ValueError("top_n must be a positive integer.")

        join_sql = self._countries_join_sql(only_countries)
        rows = self._db.query(
            f"""
            SELECT t.entity, t.co2_tonnes_per_capita AS value
            FROM {_CO2_TABLE} t
            {join_sql}
            WHERE t.year = :year
            ORDER BY t.co2_tonnes_per_capita DESC, t.entity DESC
            LIMIT :top_n
            """,
            year=year,
            top_n=top_n,
        )

        results = [(r["entity"], float(r["value"])) for r in rows]
        if not results:
            raise ValueError(f"No CO₂ per-capita data found for year {year}.")
        return results
