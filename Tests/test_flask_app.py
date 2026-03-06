"""Integration-style tests for flask_app routes and helpers."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock

import flask_app


class TestFlaskRouteFallbacks(unittest.TestCase):
    """Tests that route behavior covers the small helper cases."""

    def setUp(self) -> None:
        self.app = flask_app.create_app(db=MagicMock())
        self.app.testing = True
        self.repo = MagicMock()
        self.app.config["REPO"] = self.repo
        self.client = self.app.test_client()

    def test_country_page_rejects_invalid_entity_and_year(self) -> None:
        """Invalid dashboard query values should return the custom 404 page."""
        self.repo.countries.return_value = ["Canada", "United States"]
        self.repo.common_years_for_country.return_value = [2019, 2020]
        self.repo.common_latest_year_for_country.return_value = 2020

        response = self.client.get("/country?entity=Brazil&year=oops")

        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Page not found", response.data)

    def test_country_page_rejects_unknown_query_args(self) -> None:
        """Unexpected dashboard query arguments should return 404."""
        self.repo.countries.return_value = ["Canada", "United States"]

        response = self.client.get("/country?entisdhwuo")

        self.assertEqual(response.status_code, 404)


class TestFlaskHtmlRoutes(unittest.TestCase):
    """Tests for the user-facing website routes."""

    def setUp(self) -> None:
        self.app = flask_app.create_app(db=MagicMock())
        self.app.testing = True
        self.repo = MagicMock()
        self.app.config["REPO"] = self.repo
        self.client = self.app.test_client()

    def test_homepage_renders(self) -> None:
        """Homepage should render with a country and year form."""
        self.repo.countries.return_value = ["Canada", "United States"]
        self.repo.common_years.return_value = [2019, 2020]
        self.repo.common_latest_year_for_country.return_value = 2020

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Explore climate signals", response.data)
        self.assertIn(b"Canada", response.data)

    def test_country_page_renders_selected_country(self) -> None:
        """The dashboard should render with metrics and a table."""
        self.repo.countries.return_value = ["Canada", "United States"]
        self.repo.common_years_for_country.return_value = [2019, 2020]
        self.repo.common_years.return_value = [2019, 2020]
        self.repo.common_latest_year_for_country.return_value = 2020
        self.repo.snapshot.return_value = {
            "co2_per_capita": 1.23,
            "forest_change": 1000.0,
        }
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

    def test_country_page_defaults_latest_year_when_year_is_missing(self) -> None:
        """The dashboard should use the latest matching year when year is omitted."""
        self.repo.countries.return_value = ["Canada", "United States"]
        self.repo.common_years_for_country.return_value = [2019, 2020]
        self.repo.common_years.return_value = [2019, 2020]
        self.repo.common_latest_year_for_country.return_value = 2020
        self.repo.snapshot.return_value = {
            "co2_per_capita": 1.23,
            "forest_change": 1000.0,
        }
        self.repo.series.return_value = [
            {"year": 2019, "co2_per_capita": 1.0, "forest_change": 900.0},
            {"year": 2020, "co2_per_capita": 1.23, "forest_change": 1000.0},
        ]

        response = self.client.get("/country?entity=Canada")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Canada", response.data)
        self.assertIn(b"2020", response.data)

    def test_country_page_missing_snapshot_returns_404(self) -> None:
        """The dashboard should 404 when no joined data exists."""
        self.repo.countries.return_value = ["Canada", "United States"]
        self.repo.common_years_for_country.return_value = [2019, 2020]
        self.repo.common_years.return_value = [2019, 2020]
        self.repo.common_latest_year_for_country.return_value = 2020
        self.repo.snapshot.return_value = None

        response = self.client.get("/country?entity=Canada&year=2020")

        self.assertEqual(response.status_code, 404)

    def test_about_page_renders(self) -> None:
        """The about page should render."""
        self.repo.countries.return_value = ["Canada"]
        self.repo.common_years.return_value = [2020]
        self.repo.common_latest_year_for_country.return_value = 2020

        response = self.client.get("/about")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"About this site", response.data)

    def test_404_page_renders(self) -> None:
        """Unknown routes should return the custom 404 page."""
        response = self.client.get("/this-page-does-not-exist")

        self.assertEqual(response.status_code, 404)
        self.assertIn(b"How to use the site", response.data)

    def test_404_page_shows_example_from_real_repository(self) -> None:
        """The 404 handler should build an example URL when a repository exists."""
        db = MagicMock()
        db.query.side_effect = [
            [{"entity": "Canada"}, {"entity": "United States"}],
            [{"year": 2020}],
        ]
        app = flask_app.create_app(db=db)
        app.testing = True
        client = app.test_client()

        response = client.get("/missing")

        self.assertEqual(response.status_code, 404)
        self.assertIn(b"/country?entity=United%20States&amp;year=2020", response.data)


class TestFlaskApiRoutes(unittest.TestCase):
    """Tests for JSON API routes."""

    def setUp(self) -> None:
        self.app = flask_app.create_app(db=MagicMock())
        self.app.testing = True
        self.repo = MagicMock()
        self.app.config["REPO"] = self.repo
        self.client = self.app.test_client()

    def test_api_deforestation_defaults_invalid_year_to_latest(self) -> None:
        """The deforestation API should fall back when year is not an int."""
        self.repo.resolve_country.return_value = "Canada"
        self.repo.forest_latest_year_for_country.return_value = 2020
        self.repo.forest_value.return_value = 12.5

        response = self.client.get("/api/deforestation/Canada?year=oops")
        payload = json.loads(response.data.decode("utf-8"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["year"], 2020)
        self.assertEqual(payload["value"], 12.5)

    def test_api_deforestation_unknown_country_returns_404(self) -> None:
        """The deforestation API should 404 for unknown countries."""
        self.repo.resolve_country.return_value = None

        response = self.client.get("/api/deforestation/Narnia")

        self.assertEqual(response.status_code, 404)

    def test_api_deforestation_missing_value_returns_404(self) -> None:
        """The deforestation API should 404 when the query has no value."""
        self.repo.resolve_country.return_value = "Canada"
        self.repo.forest_latest_year_for_country.return_value = 2020
        self.repo.forest_value.return_value = None

        response = self.client.get("/api/deforestation/Canada")

        self.assertEqual(response.status_code, 404)

    def test_api_route_uses_safe_country_resolution(self) -> None:
        """API routes should turn repository matching errors into 404s."""
        self.repo.resolve_country.side_effect = ValueError("bad country")

        response = self.client.get("/api/co2/Bad_Country")

        self.assertEqual(response.status_code, 404)

    def test_api_co2_defaults_year(self) -> None:
        """The CO₂ API should default to the latest year when not provided."""
        self.repo.resolve_country.return_value = "Canada"
        self.repo.co2_latest_year_for_country.return_value = 2020
        self.repo.co2_value.return_value = 1.5

        response = self.client.get("/api/co2/Canada")
        payload = json.loads(response.data.decode("utf-8"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["entity"], "Canada")
        self.assertEqual(payload["year"], 2020)
        self.assertIn("value", payload)

    def test_api_co2_unknown_country_returns_404(self) -> None:
        """The CO₂ API should 404 for unknown countries."""
        self.repo.resolve_country.return_value = None

        response = self.client.get("/api/co2/Atlantis")

        self.assertEqual(response.status_code, 404)

    def test_api_co2_missing_value_returns_404(self) -> None:
        """The CO₂ API should 404 when the query has no value."""
        self.repo.resolve_country.return_value = "Canada"
        self.repo.co2_latest_year_for_country.return_value = 2020
        self.repo.co2_value.return_value = None

        response = self.client.get("/api/co2/Canada")

        self.assertEqual(response.status_code, 404)

    def test_api_dashboard_returns_both_metrics(self) -> None:
        """The dashboard API should return both metrics."""
        self.repo.resolve_country.return_value = "Canada"
        self.repo.common_years_for_country.return_value = [2019, 2020]
        self.repo.common_latest_year_for_country.return_value = 2020
        self.repo.snapshot.return_value = {
            "co2_per_capita": 1.2,
            "forest_change": -5.0,
        }

        response = self.client.get("/api/dashboard/Canada?year=2019")
        payload = json.loads(response.data.decode("utf-8"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("co2_per_capita", payload)
        self.assertIn("forest_change", payload)
        self.assertEqual(payload["year"], 2019)

    def test_api_dashboard_unknown_country_returns_404(self) -> None:
        """The dashboard API should 404 for unknown countries."""
        self.repo.resolve_country.return_value = None

        response = self.client.get("/api/dashboard/Narnia")

        self.assertEqual(response.status_code, 404)

    def test_api_dashboard_missing_snapshot_returns_404(self) -> None:
        """The dashboard API should 404 when the snapshot query is empty."""
        self.repo.resolve_country.return_value = "Canada"
        self.repo.common_years_for_country.return_value = [2019, 2020]
        self.repo.common_latest_year_for_country.return_value = 2020
        self.repo.snapshot.return_value = None

        response = self.client.get("/api/dashboard/Canada")

        self.assertEqual(response.status_code, 404)
