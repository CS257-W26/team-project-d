"""Unit tests for ProductionCode.climate_repository."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from ProductionCode.climate_repository import ClimateRepository


class TestClimateRepository(unittest.TestCase):
    """Tests for the SQL repository."""

    def test_countries_returns_entity_list(self) -> None:
        """countries() should return a list of country names."""
        db = MagicMock()
        db.query.return_value = [{"entity": "Canada"}, {"entity": "United States"}]
        repo = ClimateRepository(db)

        countries = repo.countries()

        self.assertEqual(countries, ["Canada", "United States"])
        sql = db.query.call_args[0][0]
        self.assertIn("FROM countries", sql)

    def test_resolve_country_returns_match_and_none(self) -> None:
        """resolve_country() should match known names and ignore unknown ones."""
        db = MagicMock()
        db.query.return_value = [{"entity": "Canada"}, {"entity": "United States"}]
        repo = ClimateRepository(db)

        self.assertEqual(repo.resolve_country("canada"), "Canada")
        self.assertIsNone(repo.resolve_country("Narnia"))

    def test_common_years_returns_ints(self) -> None:
        """common_years() should return sorted integer years."""
        db = MagicMock()
        db.query.return_value = [{"year": 2019}, {"year": 2020}]
        repo = ClimateRepository(db)

        years = repo.common_years()

        self.assertEqual(years, [2019, 2020])

    def test_common_years_for_country_filters_missing_years(self) -> None:
        """common_years_for_country() should skip rows where year is null."""
        db = MagicMock()
        db.query.return_value = [{"year": None}, {"year": 2020}]
        repo = ClimateRepository(db)

        years = repo.common_years_for_country("Canada")

        self.assertEqual(years, [2020])
        self.assertEqual(db.query.call_args.kwargs, {"entity": "Canada"})

    def test_latest_year_helpers_return_zero_for_missing_rows(self) -> None:
        """The latest-year helpers should return 0 when no year exists."""
        db = MagicMock()
        db.query.side_effect = [[], [{"year": None}], []]
        repo = ClimateRepository(db)

        self.assertEqual(repo.forest_latest_year_for_country("Canada"), 0)
        self.assertEqual(repo.co2_latest_year_for_country("Canada"), 0)
        self.assertEqual(repo.common_latest_year_for_country("Canada"), 0)

    def test_value_helpers_return_none_when_query_is_empty(self) -> None:
        """Value helpers should return None when the query has no rows."""
        db = MagicMock()
        db.query.side_effect = [[], []]
        repo = ClimateRepository(db)

        self.assertIsNone(repo.forest_value("Canada", 2020))
        self.assertIsNone(repo.co2_value("Canada", 2020))

    def test_snapshot_returns_both_metrics(self) -> None:
        """snapshot() should return both values for a country and year."""
        db = MagicMock()
        db.query.return_value = [{"co2_per_capita": 1.2, "forest_change": -50.0}]
        repo = ClimateRepository(db)

        snapshot = repo.snapshot("Canada", 2020)

        self.assertEqual(snapshot, {"co2_per_capita": 1.2, "forest_change": -50.0})
        sql = db.query.call_args[0][0]
        params = db.query.call_args.kwargs
        self.assertIn("INNER JOIN", sql)
        self.assertEqual(params, {"entity": "Canada", "year": 2020})

    def test_snapshot_returns_none_when_no_joined_row_exists(self) -> None:
        """snapshot() should return None when the query is empty."""
        db = MagicMock()
        db.query.return_value = []
        repo = ClimateRepository(db)

        self.assertIsNone(repo.snapshot("Canada", 2020))

    def test_series_returns_rows(self) -> None:
        """series() should return a list of dict rows."""
        db = MagicMock()
        db.query.return_value = [
            {"year": 2019, "co2_per_capita": 1.0, "forest_change": 10.0},
            {"year": 2020, "co2_per_capita": 1.1, "forest_change": 12.0},
        ]
        repo = ClimateRepository(db)

        rows = repo.series("Canada")

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["year"], 2019)
        self.assertIn("co2_per_capita", rows[0])
        self.assertIn("forest_change", rows[0])
