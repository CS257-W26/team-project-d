"""
Unit tests for the SQL repository layer.
"""

from __future__ import annotations

import unittest
from typing import Any

from ProductionCode.climate_repository import ClimateRepository


class FakeRows(list):
    """Tiny stand-in for ``records.RecordCollection`` returned by ``db.query``."""

    def first(self):
        """Return the first row (dict-like) or ``None`` if the collection is empty."""
        return self[0] if self else None


def _norm_sql(sql: str) -> str:
    """Normalize SQL to make substring matching stable."""
    return " ".join(sql.split()).lower()


def _match_all(sql: str, *parts: str) -> bool:
    """Return True if every substring in parts is present in sql."""
    return all(part in sql for part in parts)


def _apply_rules(sql: str, rules: list[tuple[tuple[str, ...], list[dict[str, Any]]]]) -> FakeRows:
    """Return FakeRows for the first matching rule in rules."""
    for parts, rows in rules:
        if _match_all(sql, *parts):
            return FakeRows(rows)
    return FakeRows([])


_FOREST_RULES: list[tuple[tuple[str, ...], list[dict[str, Any]]]] = [
    (
        ("select distinct t.entity",),
        [{"entity": "Brazil"}, {"entity": "Canada"}, {"entity": "World"}],
    ),
    (("select max(t.year) as year", "where t.entity"), [{"year": 2020}]),
    (("select max(t.year) as year",), [{"year": 2021}]),
    (("select t.forest_change_ha as value",), [{"value": -2.5}]),
    (("select count(*) as count",), [{"count": 3}]),
    (
        ("select t.entity, t.forest_change_ha as value",),
        [
            {"entity": "Brazil", "value": -10.0},
            {"entity": "Canada", "value": 2.0},
            {"entity": "World", "value": -1.0},
        ],
    ),
    (("select 1 + count(*) as rank",), [{"rank": 1}]),
]

_CO2_RULES: list[tuple[tuple[str, ...], list[dict[str, Any]]]] = [
    (
        ("select distinct t.entity",),
        [{"entity": "Canada"}, {"entity": "Qatar"}, {"entity": "World"}],
    ),
    (("select max(t.year) as year", "where t.entity"), [{"year": 2021}]),
    (("select max(t.year) as year",), [{"year": 2021}]),
    (("select t.co2_tonnes_per_capita as value",), [{"value": 14.25}]),
    (
        ("order by t.co2_tonnes_per_capita desc",),
        [{"entity": "Qatar", "value": 40.0}, {"entity": "Canada", "value": 14.25}],
    ),
]


class FakeDb:
    """Fake database returning deterministic rows based on the SQL string."""

    def __init__(self):
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def query(self, sql: str, **params):
        """Simulate ``records.Database.query``.

        The repository under test only uses ``.query(...).first()`` and list
        iteration over rows, so FakeRows is sufficient.
        """
        normalized = _norm_sql(sql)
        self.calls.append((normalized, dict(params)))

        if "from forest_change" in normalized:
            return _apply_rules(normalized, _FOREST_RULES)
        if "from co2_per_capita" in normalized:
            return _apply_rules(normalized, _CO2_RULES)
        return FakeRows([])


class TestClimateRepository(unittest.TestCase):
    """Repository unit tests."""

    def setUp(self) -> None:
        """Create a repository backed by a FakeDb."""
        self.db = FakeDb()
        self.repo = ClimateRepository(self.db)

    def test_countries_join_is_added_when_only_countries_true(self) -> None:
        """Queries should join countries when only_countries=True."""
        self.repo.forest_entities(only_countries=True)
        sql, _params = self.db.calls[-1]
        self.assertIn("join countries", sql)

        self.repo.forest_entities(only_countries=False)
        sql2, _params2 = self.db.calls[-1]
        self.assertNotIn("join countries", sql2)

    def test_forest_latest_year(self) -> None:
        """forest_latest_year should return the max year from the table."""
        year = self.repo.forest_latest_year(only_countries=True)
        self.assertEqual(2021, year)

    def test_forest_value_for_entity_year(self) -> None:
        """forest_value_for_entity_year should return entity, year and value."""
        entity, year, value = self.repo.forest_value_for_entity_year(
            entity_query="Brazil",
            year=2020,
            only_countries=False,
        )

        self.assertEqual("Brazil", entity)
        self.assertEqual(2020, year)
        self.assertEqual(-2.5, value)

    def test_forest_value_defaults_to_entity_latest_year(self) -> None:
        """If year is None, the entity's latest year should be used."""
        entity, year, value = self.repo.forest_value_for_entity_year(
            entity_query="Brazil",
            year=None,
            only_countries=False,
        )

        self.assertEqual("Brazil", entity)
        self.assertEqual(2020, year)
        self.assertEqual(-2.5, value)

    def test_forest_rank_entities_rejects_non_positive_top_n(self) -> None:
        """Rank list queries should reject top_n <= 0."""
        with self.assertRaises(ValueError):
            self.repo.forest_rank_entities(year=2021, order="loss", top_n=0, only_countries=False)

    def test_forest_rank_for_entity_returns_rank(self) -> None:
        """forest_rank_for_entity should return a rank integer for the entity."""
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
        """co2_top_emitters should return a list of (entity, value) tuples."""
        top = self.repo.co2_top_emitters(year=2021, top_n=2, only_countries=False)
        self.assertEqual([("Qatar", 40.0), ("Canada", 14.25)], top)

    def test_unknown_entity_raises_helpful_error(self) -> None:
        """Unknown entities should raise a ValueError with a helpful message."""
        with self.assertRaises(ValueError) as ctx:
            self.repo.co2_value_for_entity_year(
                entity_query="Atlantis",
                year=2021,
                only_countries=False,
            )

        self.assertIn("Unknown entity", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
