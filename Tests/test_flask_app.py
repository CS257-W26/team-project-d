"""
Unit tests for Flask routes.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

import flask_app


class BaseFlaskTest(unittest.TestCase):
    """shared setup for flask route tests"""
    def setUp(self) -> None:
        """Create a Flask test client and inject a mock repository."""
        self.app = flask_app.create_app(db=MagicMock())
        self.app.testing = True

        self.repo = MagicMock()
        self.app.config["REPO"] = self.repo

        self.client = self.app.test_client()


class TestFlaskHtmlRoutes(BaseFlaskTest):
    """tests for html endpoints"""
    def test_homepage_renders(self) -> None:
        """The homepage should render and contain at least one example link."""
        resp = self.client.get("/")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"/deforestation/United_States", resp.data)

    def test_deforestation_value(self) -> None:
        """A single-entity deforestation query should call the repository correctly."""
        self.repo.forest_value_for_entity_year.return_value = (
            "United States",
            2021,
            -72000.0,
        )

        resp = self.client.get("/deforestation/United_States?year=2021")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"Annual change in forest area for United States in 2021", resp.data)
        self.assertIn(b"-72,000 ha", resp.data)

        self.repo.forest_value_for_entity_year.assert_called_once_with(
            entity_query="United States",
            year=2021,
            only_countries=True,
        )

    def test_deforestation_list_uses_latest_year_when_missing(self) -> None:
        """If year is omitted, the route should use the repository's latest-year helper."""
        self.repo.forest_latest_year.return_value = 2021
        self.repo.forest_rank_entities.return_value = [("Brazil", -10.0), ("Canada", 2.0)]

        resp = self.client.get("/deforestation?top=2&order=loss")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"Top 2 entities", resp.data)

        self.repo.forest_latest_year.assert_called_once_with(True)
        self.repo.forest_rank_entities.assert_called_once_with(
            year=2021,
            order="loss",
            top_n=2,
            only_countries=True,
        )

    def test_co2_value(self) -> None:
        """A single-entity CO2 query should call the repository correctly."""
        self.repo.co2_value_for_entity_year.return_value = ("Canada", 2021, 14.25)

        resp = self.client.get("/co2/Canada?year=2021")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"Canada in 2021", resp.data)
        self.assertIn(b"t/person", resp.data)

        self.repo.co2_value_for_entity_year.assert_called_once_with(
            entity_query="Canada",
            year=2021,
            only_countries=True,
        )

    def test_ranking_value(self) -> None:
        """Ranking page should render a rank card for a specific entity."""
        self.repo.forest_rank_for_entity.return_value = ("Brazil", 2021, 1, -10.0)
        self.repo.forest_count_entities_for_year.return_value = 200

        resp = self.client.get("/ranking/Brazil?year=2021&order=loss")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"Brazil rank in 2021", resp.data)
        self.assertIn(b"1 of 200", resp.data)

        self.repo.forest_rank_for_entity.assert_called_once_with(
            entity_query="Brazil",
            year=2021,
            order="loss",
            only_countries=True,
        )
        self.repo.forest_count_entities_for_year.assert_called_once_with(
            year=2021,
            only_countries=True,
        )

    def test_include_aggregates_allows_world(self) -> None:
        """include_aggregates should allow querying non-country entities like World."""

        def side_effect(entity_query, year, only_countries):
            if entity_query == "World" and only_countries:
                raise ValueError("Unknown entity name.")
            return ("World", year, -123.0)

        self.repo.forest_value_for_entity_year.side_effect = side_effect

        resp_default = self.client.get("/deforestation/World?year=2021")
        self.assertEqual(404, resp_default.status_code)

        resp_ok = self.client.get("/deforestation/World?year=2021&include_aggregates=1")
        self.assertEqual(200, resp_ok.status_code)
        self.assertIn(b"World", resp_ok.data)

    def test_invalid_query_params_return_404(self) -> None:
        """Invalid query-string parameters should return 404 with a helpful message."""
        resp = self.client.get("/co2/Canada?year=not-a-year")
        self.assertEqual(404, resp.status_code)
        self.assertIn(b"year must be an integer", resp.data)

    def test_404_handler(self) -> None:
        """Unknown routes should return the custom 404 page."""
        resp = self.client.get("/this-route-does-not-exist")
        self.assertEqual(404, resp.status_code)
        self.assertIn(b"Try one of these working examples", resp.data)

    def test_500_handler_callable(self) -> None:
        """The internal server error handler should return 500 status."""
        body, status = flask_app.internal_server_error(Exception("boom"))
        self.assertEqual(500, status)
        self.assertIn("Caterpie", body)


class TestFlaskApiRoutes(BaseFlaskTest):
    """tests for json api endpoints"""

    def test_api_deforestation_value(self) -> None:
        """API should return JSON payload for a single deforestation query."""
        self.repo.forest_value_for_entity_year.return_value = ("United States", 2021, -72000.0)

        resp = self.client.get("/api/deforestation/United_States?year=2021")
        self.assertEqual(200, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual("United States", data["entity"])
        self.assertEqual(2021, data["year"])
        self.assertEqual("ha", data["unit"])

    def test_api_co2_list(self) -> None:
        """API should return a ranked list of CO2 emitters."""
        self.repo.co2_top_emitters.return_value = [("Qatar", 40.0)]

        resp = self.client.get("/api/co2?year=2021&top=1")
        self.assertEqual(200, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual("co2", data["feature"])
        self.assertEqual(1, len(data["rows"]))
        self.assertEqual("Qatar", data["rows"][0]["entity"])

        self.repo.co2_top_emitters.assert_called_once_with(
            year=2021,
            top_n=1,
            only_countries=True,
        )

    def test_api_ranking_value(self) -> None:
        """API should return rank payload for a specific entity."""
        self.repo.forest_rank_for_entity.return_value = ("Brazil", 2021, 1, -10.0)
        self.repo.forest_count_entities_for_year.return_value = 200

        resp = self.client.get("/api/ranking/Brazil?year=2021&order=loss")
        self.assertEqual(200, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual("Brazil", data["entity"])
        self.assertEqual(1, data["rank"])
        self.assertEqual(200, data["total"])

    def test_api_unknown_entity_returns_json_error(self) -> None:
        """Repository ValueError should become 404 JSON error."""
        self.repo.co2_value_for_entity_year.side_effect = ValueError("Unknown entity name.")

        resp = self.client.get("/api/co2/Atlantis?year=2021")
        self.assertEqual(404, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertIn("error", data)

    def test_api_invalid_order_returns_json_error(self) -> None:
        """Invalid order parameter should return 404 JSON error."""
        resp = self.client.get("/api/ranking?year=2021&order=not-valid")
        self.assertEqual(404, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
