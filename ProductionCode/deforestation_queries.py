"""
deforestation_queries.py
Database-backed queries for deforestation (annual change in forest area).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import records
import ProductionCode.psql_config as config

@dataclass(frozen=True)
class DeforestationRow:
    """
    deforestation queries
    """
    entity: str
    year: int
    annual_change_forest_area: float
    code: Optional[str] = None


class DeforestationDataSource:
    """
    Data access layer for deforestation.
    """

    def __init__(self, db: Optional[records.Database] = None) -> None:
        """
        Initialize the datasource.

        Input:
            db: Optional injected records.Database for testing.
        """
        if db is not None:
            self.db = db
            return

        if config is None:
            raise RuntimeError(
                "psql_config not available"
            )

        connect = f"postgresql://{config.USER}:{config.PASSWORD}@localhost:5432/{config.DATABASE}"
        self.db = records.Database(connect)

    def year_exists(self, year: int) -> bool:
        """
        Return True if the year exists in forest_change
        """
        row = self.db.query(
            "SELECT 1 FROM forest_change WHERE year = :year LIMIT 1",
            year=year,
        ).first()
        return row is not None

    def entity_exists(self, entity: str) -> bool:
        """
        Return True if entity exists in forest_change
        """
        row = self.db.query(
            "SELECT 1 FROM forest_change WHERE entity = :entity LIMIT 1",
            entity=entity,
        ).first()
        return row is not None

    def get_value(self, entity: str, year: int) -> DeforestationRow:
        """
        Get deforestation value for one entity in a year
        Input:
            entity: Country/region name
            year: Year

        Returns:
            DeforestationRow

        Raises:
            ValueError if not found
        """
        row = self.db.query(
            """
            SELECT entity, code, year, annual_change_forest_area
            FROM forest_change
            WHERE entity = :entity AND year = :year
            LIMIT 1
            """,
            entity=entity,
            year=year,
        ).first(as_dict=True)

        if row is None:
            # Provide more helpful errors than the current version does.
            if not self.entity_exists(entity):
                raise ValueError(f"Entity '{entity}' does not exist in dataset.")
            if not self.year_exists(year):
                raise ValueError(f"Year '{year}' does not exist in dataset.")
            raise ValueError(f"No record for '{entity}' in year {year}.")

        return DeforestationRow(
            entity=row["entity"],
            code=row.get("code"),
            year=row["year"],
            annual_change_forest_area=row["annual_change_forest_area"],
        )

    def list_entities(self, year: int) -> List[str]:
        """
        List all entities available for a given year

        Input:
            year: year as int

        Returns:
            list[str] of entities
        """
        rows = self.db.query(
            """
            SELECT entity
            FROM forest_change
            WHERE year = :year
            ORDER BY entity ASC
            """,
            year=year,
        ).all(as_dict=True)

        if not rows:
            if not self.year_exists(year):
                raise ValueError(f"Year '{year}' does not exist in dataset.")
            return []

        return [r["entity"] for r in rows]

    def range_values(self, entity: str, year1: int, year2: int) -> List[DeforestationRow]:
        """
        Get values for an entity in two years (is inclusive)

        Input:
            entity: entity name
            year1: first year
            year2: second year

        Returns:
            list[DeforestationRow] sorted by year asc
        """
        y_lo, y_hi = (year1, year2) if year1 <= year2 else (year2, year1)
        rows = self.db.query(
            """
            SELECT entity, code, year, annual_change_forest_area
            FROM forest_change
            WHERE entity = :entity AND year BETWEEN :y_lo AND :y_hi
            ORDER BY year ASC
            """,
            entity=entity,
            y_lo=y_lo,
            y_hi=y_hi,
        ).all(as_dict=True)

        if not rows:
            if not self.entity_exists(entity):
                raise ValueError(f"Entity '{entity}' does not exist in dataset.")
            if not (self.year_exists(year1) and self.year_exists(year2)):
                raise ValueError(f"One of the years ({year1}, {year2}) does not exist in dataset.")
            raise ValueError(f"No records found for '{entity}' between {y_lo} and {y_hi}.")

        return [
            DeforestationRow(
                entity=r["entity"],
                code=r.get("code"),
                year=r["year"],
                annual_change_forest_area=r["annual_change_forest_area"],
            )
            for r in rows
        ]

    def aggregate_sum(self, entities: List[str], year: int) -> Tuple[List[DeforestationRow], float]:
        """
        Gets values for multiple entities in a year and also return their sum

        Input:
            entities: list of entity names
            year: year

        Returns:
            (rows, total_sum)
        """
        if not entities:
            raise ValueError("At least one entity is required for aggregate.")

        # SQL IN with bind params: create a param per entity
        params: Dict[str, Any] = {"year": year}
        placeholders = []
        for i, e in enumerate(entities):
            key = f"e{i}"
            params[key] = e
            placeholders.append(f":{key}")

        sql = f"""
            SELECT entity, code, year, annual_change_forest_area
            FROM forest_change
            WHERE year = :year AND entity IN ({", ".join(placeholders)})
            ORDER BY entity ASC
        """

        rows = self.db.query(sql, **params).all(as_dict=True)
        if len(rows) != len(set(entities)):
            # Find missing entities for clearer error
            found = {r["entity"] for r in rows}
            missing = [e for e in entities if e not in found]
            if missing:
                raise ValueError(f"Entities not found for year {year}: {', '.join(missing)}")

        parsed = [
            DeforestationRow(
                entity=r["entity"],
                code=r.get("code"),
                year=r["year"],
                annual_change_forest_area=r["annual_change_forest_area"],
            )
            for r in rows
        ]
        total = sum(r.annual_change_forest_area for r in parsed)
        return parsed, total

    def top_or_bottom(
        self, year: int, n: int, order: str
    ) -> List[DeforestationRow]:
        """
        Get top/bottom N entities by annual_change_forest_area in a given year

        Input:
            year: year
            n: number of rows
            order: "top" (DESC) or "bottom" (ASC)

        Returns:
            list[DeforestationRow]
        """
        if n <= 0:
            raise ValueError("n must be > 0")
        if order not in {"top", "bottom"}:
            raise ValueError("order must be 'top' or 'bottom'")

        if not self.year_exists(year):
            raise ValueError(f"Year '{year}' does not exist in dataset.")

        direction = "DESC" if order == "top" else "ASC"
        rows = self.db.query(
            f"""
            SELECT entity, code, year, annual_change_forest_area
            FROM forest_change
            WHERE year = :year
            ORDER BY annual_change_forest_area {direction}
            LIMIT :n
            """,
            year=year,
            n=n,
        ).all(as_dict=True)

        return [
            DeforestationRow(
                entity=r["entity"],
                code=r.get("code"),
                year=r["year"],
                annual_change_forest_area=r["annual_change_forest_area"],
            )
            for r in rows
        ]