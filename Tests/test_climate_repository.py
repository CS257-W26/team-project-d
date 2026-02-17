"""
Unit tests for the SQL repository layer.
"""

from __future__ import annotations

import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ProductionCode.climate_repository import ClimateRepository


class FakeRows(list):
    """a tiny stand-in for records.RecordCollection"""
    def first(self):
        """return the first row dict, or none"""
        return self[0] if self else None


def _norm_sql(sql: str) -> str:
    """normalize SQL for matching in tests"""
    return " ".join(sql.split()).lower()


class FakeDb:
    """a fake database that returns hard-coded rows based on the SQL"""
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    def query(self, sql: str, **params):
        normalized = _norm_sql(sql)
        self.calls.append((normalized, dict(params)))

        if "from forest_change" in normalized:
            if "select distinct t.entity" in normalized:
                return FakeRows([
                    {"entity": "Brazil"},
                    {"entity": "Canada"},
                    {"entity": "World"},
                ])

            if "select max(t.year) as year" in normalized and "where" not in normalized:
                return FakeRows([{"year": 2021}])

            if "select max(t.year) as year" in normalized and "where t.entity" in normalized:
                return FakeRows([{"year": 2020}])

            if "select t.forest_change_ha as value" in normalized:
                return FakeRows([{"value": -2.5}])

            if "select count(*) as count" in normalized:
                return FakeRows([{"count": 3}])

            if "select t.entity, t.forest_change_ha as value" in normalized:
                return FakeRows([
                    {"entity": "Brazil", "value": -10.0},
                    {"entity": "Canada", "value": 2.0},
                    {"entity": "World", "value": -1.0},
                ])

            if "select 1 + count(*) as rank" in normalized:
                return FakeRows([{"rank": 1}])

        if "from co2_per_capita" in normalized:
            if "select distinct t.entity" in normalized:
                return FakeRows([
                    {"entity": "Canada"},
                    {"entity": "Qatar"},
                    {"entity": "World"},
                ])

            if "select max(t.year) as year" in normalized and "where" not in normalized:
                return FakeRows([{"year": 2021}])

            if "select max(t.year) as year" in normalized and "where t.entity" in normalized:
                return FakeRows([{"year": 2021}])

            if "select t.co2_tonnes_per_capita as value" in normalized:
                return FakeRows([{"value": 14.25}])

            if "order by t.co2_tonnes_per_capita desc" in normalized:
                return FakeRows([
                    {"entity": "Qatar", "value": 40.0},
                    {"entity": "Canada", "value": 14.25},
                ])

        return FakeRows([])


class TestClimateRepository(unittest.TestCase):
    """repository unit tests"""
    def setUp(self) -> None:
        self.db = FakeDb()
        self.repo = ClimateRepository(self.db)

    def test_countries_join_is_added_when_only_countries_true(self) -> None:
        self.repo.forest_entities(only_countries=True)
        sql, _params = self.db.calls[-1]
        self.assertIn("join countries", sql)

        self.repo.forest_entities(only_countries=False)
        sql2, _params2 = self.db.calls[-1]
        self.assertNotIn("join countries", sql2)

    def test_forest_latest_year(self) -> None:
        year = self.repo.forest_latest_year(only_countries=True)
        self.assertEqual(2021, year)

    def test_forest_value_for_entity_year(self) -> None:
        entity, year, value = self.repo.forest_value_for_entity_year(
            entity_query="Brazil",
            year=2020,
            only_countries=False,
        )

        self.assertEqual("Brazil", entity)
        self.assertEqual(2020, year)
        self.assertEqual(-2.5, value)

    def test_forest_value_defaults_to_entity_latest_year(self) -> None:
        entity, year, value = self.repo.forest_value_for_entity_year(
            entity_query="Brazil",
            year=None,
            only_countries=False,
        )

        self.assertEqual("Brazil", entity)
        self.assertEqual(2020, year)
        self.assertEqual(-2.5, value)

    def test_forest_rank_entities_rejects_non_positive_top_n(self) -> None:
        with self.assertRaises(ValueError):
            self.repo.forest_rank_entities(year=2021, order="loss", top_n=0, only_countries=False)

    def test_forest_rank_for_entity_returns_rank(self) -> None:
        entity, year, rank, value = self.repo.forest_rank_for_entity(
            entity_query="Brazil",
            year=2020,
            order="loss",
            only_countries=False,
        )

        self.assertEqual("Brazil", entity)
        self.assertEqual(2020, year)
        self.assertEqual(1, rank)
        self.assertEqual(-2.5, value)

    def test_co2_top_emitters(self) -> None:
        top = self.repo.co2_top_emitters(year=2021, top_n=2, only_countries=False)
        self.assertEqual([("Qatar", 40.0), ("Canada", 14.25)], top)

    def test_unknown_entity_raises_helpful_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            self.repo.co2_value_for_entity_year(entity_query="Atlantis", year=2021, only_countries=False)

        self.assertIn("Unknown entity", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
