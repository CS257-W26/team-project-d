"""
Unit tests for ProductionCode.climate_repository
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from ProductionCode.climate_repository import ClimateRepository


class TestClimateRepository(unittest.TestCase):
    """tests for the SQL repository"""

    def test_countries_returns_entity_list(self) -> None:
        """countries() should return a list of country names"""
        db = MagicMock()
        db.query.return_value = [{"entity": "Canada"}, {"entity": "United States"}]
        repo = ClimateRepository(db)

        countries = repo.countries()

        self.assertEqual(countries, ["Canada", "United States"])
        sql = db.query.call_args[0][0]
        self.assertIn("FROM countries", sql)

    def test_common_years_returns_ints(self) -> None:
        """common_years() should return sorted integer years"""
        db = MagicMock()
        db.query.return_value = [{"year": 2019}, {"year": 2020}]
        repo = ClimateRepository(db)

        years = repo.common_years()

        self.assertEqual(years, [2019, 2020])

    def test_snapshot_returns_both_metrics(self) -> None:
        """snapshot() should return both values for a country/year"""
        db = MagicMock()
        db.query.return_value = [{"co2_per_capita": 1.2, "forest_change": -50.0}]
        repo = ClimateRepository(db)

        snapshot = repo.snapshot("Canada", 2020)

        self.assertEqual(snapshot, {"co2_per_capita": 1.2, "forest_change": -50.0})
        sql = db.query.call_args[0][0]
        params = db.query.call_args.kwargs
        self.assertIn("INNER JOIN", sql)
        self.assertEqual(params, {"entity": "Canada", "year": 2020})

    def test_series_returns_rows(self) -> None:
        """series() should return a list of dict rows"""
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

