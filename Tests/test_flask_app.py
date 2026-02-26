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
        """create a flask test client and inject a mock repository"""
        self.app = flask_app.create_app(db=MagicMock())
        self.app.testing = True

        self.repo = MagicMock()
        self.app.config["REPO"] = self.repo

        self.client = self.app.test_client()


class TestFlaskHtmlRoutes(BaseFlaskTest):
    """tests for html endpoints"""
    def test_homepage_renders(self) -> None:
        """homepage should render and contain at least one example link"""
        resp = self.client.get("/")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"/deforestation/United_States", resp.data)

    def test_homepage_has_navbar(self) -> None:
        """homepage should include a navigation bar with key links"""
        resp = self.client.get("/")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"<nav", resp.data)
        self.assertIn(b"Deforestation", resp.data)
        self.assertIn(b"Ranking", resp.data)

    def test_homepage_forms_have_labels(self) -> None:
        """homepage feature forms should have accessible labels"""
        resp = self.client.get("/")
        self.assertIn(b'for="def_entity"', resp.data)
        self.assertIn(b'id="def_entity"', resp.data)

    def test_deforestation_value(self) -> None:
        """a single-entity deforestation query should call the repository correctly"""
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
        """if year is omitted, the route should use the repository's latest-year helper"""
        self.repo.forest_latest_year.return_value = 2021
        self.repo.forest_rank_entities.return_value = [("Brazil", -10.0), ("Canada", 2.0)]

        resp = self.client.get("/deforestation?top=2&order=loss")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"Top 2 countries", resp.data)

        self.repo.forest_latest_year.assert_called_once_with(True)
        self.repo.forest_rank_entities.assert_called_once_with(
            year=2021,
            order="loss",
            top_n=2,
            only_countries=True,
        )

    def test_co2_value(self) -> None:
        """a single-entity CO2 query should call the repository correctly"""
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
        """ranking page should render a rank card for a specific entity"""
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

    def test_invalid_query_params_return_404(self) -> None:
        """invalid query-string parameters should return 404 with a helpful message"""
        resp = self.client.get("/co2/Canada?year=not-a-year")
        self.assertEqual(404, resp.status_code)
        self.assertIn(b"year must be an integer", resp.data)

    def test_ranking_invalid_order_returns_404(self) -> None:
        """invalid order should hit the ValueError->404 branch"""
        resp = self.client.get("/ranking?year=2021&order=not-valid")
        self.assertEqual(404, resp.status_code)
        self.assertIn(b"order must be", resp.data)
        self.assertIn(b"loss", resp.data)
        self.assertIn(b"gain", resp.data)

    def test_co2_list_uses_latest_year_when_missing(self) -> None:
        """if year is omitted, /co2 should call co2_latest_year + co2_top_emitters"""
        self.repo.co2_latest_year.return_value = 2021
        self.repo.co2_top_emitters.return_value = [("Qatar", 40.0), ("Canada", 14.25)]

        resp = self.client.get("/co2?top=2")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"Top 2 countries", resp.data)

        self.repo.co2_latest_year.assert_called_once_with(True)
        self.repo.co2_top_emitters.assert_called_once_with(
            year=2021,
            top_n=2,
            only_countries=True,
        )

    def test_ranking_list_route_renders(self) -> None:
        """/ranking without an entity should render a list ranking"""
        self.repo.forest_latest_year.return_value = 2021
        self.repo.forest_rank_entities.return_value = [("Brazil", -10.0), ("Canada", 2.0)]

        resp = self.client.get("/ranking?top=2&order=loss")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"Forest change ranking for 2021", resp.data)

        self.repo.forest_latest_year.assert_called_once_with(True)
        self.repo.forest_rank_entities.assert_called_once_with(
            year=2021,
            order="loss",
            top_n=2,
            only_countries=True,
        )

    def test_invalid_top_param_returns_404(self) -> None:
        """top must be a positive integer (route should return 404 on invalid input)"""
        resp = self.client.get("/deforestation?year=2021&top=0")
        self.assertEqual(404, resp.status_code)
        self.assertIn(b"top must be a positive integer", resp.data)

    def test_404_handler(self) -> None:
        """unknown routes should return the custom 404 page"""
        resp = self.client.get("/this-route-does-not-exist")
        self.assertEqual(404, resp.status_code)
        self.assertIn(b"Try one of these working examples", resp.data)

    def test_500_handler_callable(self) -> None:
        """the internal server error handler should return 500 status"""
        with self.app.test_request_context("/"):
            body, status = flask_app.internal_server_error(Exception("boom"))
        self.assertEqual(500, status)
        self.assertIn("Caterpie", body)


class TestFlaskApiRoutes(BaseFlaskTest):
    """tests for json api endpoints"""

    def test_api_deforestation_value(self) -> None:
        """api should return json payload for a single deforestation query"""
        self.repo.forest_value_for_entity_year.return_value = ("United States", 2021, -72000.0)

        resp = self.client.get("/api/deforestation/United_States?year=2021")
        self.assertEqual(200, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual("United States", data["entity"])
        self.assertEqual(2021, data["year"])
        self.assertEqual("ha", data["unit"])

    def test_api_deforestation_invalid_year_returns_json_error(self) -> None:
        """bad query params should return json error with status 404"""
        resp = self.client.get("/api/deforestation?year=not-a-year")
        self.assertEqual(404, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertIn("error", data)

    def test_api_co2_list(self) -> None:
        """api should return a ranked list of CO2 emitters"""
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

    def test_api_deforestation_list(self) -> None:
        """api should return a ranked list of deforestation values"""
        self.repo.forest_rank_entities.return_value = [("Brazil", -10.0)]

        resp = self.client.get("/api/deforestation?year=2021&top=1&order=loss")
        self.assertEqual(200, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual("deforestation", data["feature"])
        self.assertEqual(1, len(data["rows"]))

        self.repo.forest_rank_entities.assert_called_once_with(
            year=2021,
            order="loss",
            top_n=1,
            only_countries=True,
        )

    def test_api_co2_value(self) -> None:
        """api should return json payload for a single co2 query"""
        self.repo.co2_value_for_entity_year.return_value = ("Canada", 2021, 14.25)

        resp = self.client.get("/api/co2/Canada?year=2021")
        self.assertEqual(200, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual("co2", data["feature"])
        self.assertEqual("Canada", data["entity"])
        self.assertEqual(2021, data["year"])

    def test_api_ranking_list(self) -> None:
        """api should return JSON for the ranking list endpoint"""
        self.repo.forest_rank_entities.return_value = [("Brazil", -10.0)]

        resp = self.client.get("/api/ranking?year=2021&top=1&order=loss")
        self.assertEqual(200, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual("ranking", data["feature"])
        self.assertEqual(1, len(data["rows"]))

        self.repo.forest_rank_entities.assert_called_once_with(
            year=2021,
            order="loss",
            top_n=1,
            only_countries=True,
        )

    def test_api_ranking_value(self) -> None:
        """api should return rank payload for a specific entity"""
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
        """repository ValueError should become 404 json error"""
        self.repo.co2_value_for_entity_year.side_effect = ValueError("Unknown entity name.")

        resp = self.client.get("/api/co2/Atlantis?year=2021")
        self.assertEqual(404, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertIn("error", data)

    def test_api_invalid_order_returns_json_error(self) -> None:
        """invalid order parameter should return 404 json error"""
        resp = self.client.get("/api/ranking?year=2021&order=not-valid")
        self.assertEqual(404, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertIn("error", data)


class TestFlaskParsingHelpers(unittest.TestCase):
    """unit tests for small parsing helpers in flask_app"""

    def test_parse_optional_int_blank_string_returns_none(self) -> None:
        """blank query params should be treated as missing"""
        self.assertIsNone(flask_app.parse_optional_int("   ", "year"))

    def test_repo_missing_raises_runtime_error(self) -> None:
        """routes should raise RuntimeError if the repository is not configured"""
        app = flask_app.create_app(db=MagicMock())
        app.testing = True
        app.config["REPO"] = None

        client = app.test_client()
        with self.assertRaises(RuntimeError):
            client.get("/co2/Canada?year=2021")


if __name__ == "__main__":
    unittest.main()
