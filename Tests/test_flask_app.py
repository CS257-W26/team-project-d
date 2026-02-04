"""
Tests for Flask app
"""

from __future__ import annotations

import unittest

import flask_app


class TestFlaskAppRoutes(unittest.TestCase):
    """integration tests for html routes in flask_app.py"""

    def setUp(self) -> None:
        """create a flask test client"""
        flask_app.app.testing = True
        self.client = flask_app.app.test_client()

    def test_homepage_renders(self) -> None:
        """homepage should load and include at least one example route"""
        resp = self.client.get("/")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"/deforestation/United_States", resp.data)

    def test_deforestation_value(self) -> None:
        """/deforestation/<entity> should render a single value"""
        resp = self.client.get("/deforestation/United_States?year=2021")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"Annual change in forest area for United States in 2021", resp.data)
        self.assertIn(b"-72,000 ha", resp.data)

    def test_deforestation_list(self) -> None:
        """/deforestation should render a top list when no entity is provided"""
        resp = self.client.get("/deforestation?year=2021&top=3&order=loss")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"Top 3 entities", resp.data)
        self.assertIn(b"1. Brazil:", resp.data)

    def test_co2_value(self) -> None:
        """/co2/<entity> should render a single co2 per-capita value"""
        resp = self.client.get("/co2/Canada?year=2021")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"CO", resp.data)
        self.assertIn(b"Canada in 2021", resp.data)
        self.assertIn(b"t/person", resp.data)

    def test_co2_list(self) -> None:
        """/co2 should render a list of top emitters when no entity is provided"""
        resp = self.client.get("/co2?year=2021&top=2")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"Top 2 entities", resp.data)
        self.assertIn(b"Qatar", resp.data)

    def test_ranking_value(self) -> None:
        """/ranking/<entity> should render the entity's rank"""
        resp = self.client.get("/ranking/Brazil?year=2021&order=loss")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"Brazil rank in 2021", resp.data)
        self.assertIn(b"1 of", resp.data)

    def test_ranking_list(self) -> None:
        """/ranking should render a list when no entity is provided"""
        resp = self.client.get("/ranking?year=2021&top=3&order=gain")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b"Forest change ranking for 2021", resp.data)
        self.assertIn(b"China", resp.data)

    def test_include_aggregates_allows_world(self) -> None:
        """include_aggregates=1 should allow non-country entities like world"""
        resp_default = self.client.get("/deforestation/World?year=2021")
        self.assertEqual(404, resp_default.status_code)

        resp_ok = self.client.get("/deforestation/World?year=2021&include_aggregates=1")
        self.assertEqual(200, resp_ok.status_code)
        self.assertIn(b"World", resp_ok.data)

    def test_invalid_query_params_return_404(self) -> None:
        """bad query params (e.g. non-int year) should produce a 404"""
        resp = self.client.get("/co2/Canada?year=not-a-year")
        self.assertEqual(404, resp.status_code)
        self.assertIn(b"year must be an integer", resp.data)

    def test_404_handler(self) -> None:
        """non-existent routes should return the custom 404 page"""
        resp = self.client.get("/this-route-does-not-exist")
        self.assertEqual(404, resp.status_code)
        self.assertIn(b"Try one of these working examples", resp.data)

    def test_500_handler_callable(self) -> None:
        """500 handler should return the Caterpie message"""
        body, status = flask_app.internal_server_error(Exception("boom"))
        self.assertEqual(500, status)
        self.assertIn("Caterpie", body)


class TestFlaskApiRoutes(unittest.TestCase):
    """integration tests for json api routes under /api"""

    def setUp(self) -> None:
        """create a Flask test client"""
        flask_app.app.testing = True
        self.client = flask_app.app.test_client()

    def test_api_deforestation_value(self) -> None:
        """/api/deforestation/<entity> should return JSON for single value"""
        resp = self.client.get("/api/deforestation/United_States?year=2021")
        self.assertEqual(200, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual("United States", data["entity"])
        self.assertEqual(2021, data["year"])
        self.assertEqual("ha", data["unit"])

    def test_api_co2_list(self) -> None:
        """/api/co2 should return JSON rows for list output"""
        resp = self.client.get("/api/co2?year=2021&top=1")
        self.assertEqual(200, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual("co2", data["feature"])
        self.assertEqual(1, len(data["rows"]))
        self.assertIn("entity", data["rows"][0])

    def test_api_ranking_value(self) -> None:
        """/api/ranking/<entity> should return JSON for rank output"""
        resp = self.client.get("/api/ranking/Brazil?year=2021&order=loss")
        self.assertEqual(200, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual("Brazil", data["entity"])
        self.assertEqual(1, data["rank"])

    def test_api_unknown_entity_returns_json_error(self) -> None:
        """api should return a json error for unknown entities"""
        resp = self.client.get("/api/co2/Atlantis?year=2021")
        self.assertEqual(404, resp.status_code)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
