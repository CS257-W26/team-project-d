"""
Integration-style tests for flask_app routes.
"""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock

import flask_app


class TestFlaskHtmlRoutes(unittest.TestCase):
    """tests for the user-facing website routes"""

    def setUp(self) -> None:
        self.app = flask_app.create_app(db=MagicMock())
        self.app.testing = True
        self.repo = MagicMock()
        self.app.config["REPO"] = self.repo
        self.client = self.app.test_client()

    def test_homepage_renders(self) -> None:
        """homepage should render with a country/year form"""
        self.repo.countries.return_value = ["Canada", "United States"]
        self.repo.common_years.return_value = [2019, 2020]
        self.repo.common_latest_year_for_country.return_value = 2020

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Explore climate signals", response.data)
        self.assertIn(b"Canada", response.data)

    def test_country_page_renders_selected_country(self) -> None:
        """/country should render a dashboard with metrics and a table"""
        self.repo.countries.return_value = ["Canada", "United States"]
        self.repo.common_years_for_country.return_value = [2019, 2020]
        self.repo.common_years.return_value = [2019, 2020]
        self.repo.common_latest_year_for_country.return_value = 2020
        self.repo.snapshot.return_value = {"co2_per_capita": 1.23, "forest_change": 1000.0}
        self.repo.series.return_value = [
            {"year": 2019, "co2_per_capita": 1.0, "forest_change": 900.0},
            {"year": 2020, "co2_per_capita": 1.23, "forest_change": 1000.0},
        ]

        response = self.client.get("/country?entity=Canada&year=2020")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Canada", response.data)
        self.assertIn(b"2020", response.data)
        self.assertIn(b"1.2", response.data)
        self.assertIn(b"1,000", response.data)

    def test_about_page_renders(self) -> None:
        """/about should render"""
        self.repo.countries.return_value = ["Canada"]
        self.repo.common_years.return_value = [2020]
        self.repo.common_latest_year_for_country.return_value = 2020

        response = self.client.get("/about")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"About this site", response.data)

    def test_404_page_renders(self) -> None:
        """unknown routes should return the custom 404 page"""
        response = self.client.get("/this-page-does-not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"How to use the site", response.data)


class TestFlaskApiRoutes(unittest.TestCase):
    """tests for JSON API routes"""

    def setUp(self) -> None:
        self.app = flask_app.create_app(db=MagicMock())
        self.app.testing = True
        self.repo = MagicMock()
        self.app.config["REPO"] = self.repo
        self.client = self.app.test_client()

    def test_api_co2_defaults_year(self) -> None:
        """/api/co2 should default to the latest year when not provided"""
        self.repo.resolve_country.return_value = "Canada"
        self.repo.co2_latest_year_for_country.return_value = 2020
        self.repo.co2_value.return_value = 1.5

        response = self.client.get("/api/co2/Canada")
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.data.decode("utf-8"))
        self.assertEqual(payload["entity"], "Canada")
        self.assertEqual(payload["year"], 2020)
        self.assertIn("value", payload)

    def test_api_dashboard_returns_both_metrics(self) -> None:
        """/api/dashboard should return both metrics"""
        self.repo.resolve_country.return_value = "Canada"
        self.repo.common_years_for_country.return_value = [2019, 2020]
        self.repo.common_latest_year_for_country.return_value = 2020
        self.repo.snapshot.return_value = {"co2_per_capita": 1.2, "forest_change": -5.0}

        response = self.client.get("/api/dashboard/Canada?year=2019")
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.data.decode("utf-8"))
        self.assertIn("co2_per_capita", payload)
        self.assertIn("forest_change", payload)
        self.assertEqual(payload["year"], 2019)

