import unittest
from flask_app import create_app


class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        """
        Testing client
        """
        self.app = create_app({"TESTING": True})
        self.client = self.app.test_client()

    def test_home_route_returns_200(self):
        """
        test for home page
        """
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Carbon & Forests Dashboard", res.data)

    def test_deforestation_entity_requires_year_400(self):
        """
        Test for missing a year in deforestation to trigger and test 400 error
        Input: without a year
        Output: 400 error
        """
        res = self.client.get("/deforestation/Afghanistan")
        self.assertEqual(res.status_code, 400)
        self.assertIn(b"400", res.data)

    def test_co2_entity_requires_year_400(self):
        """
        Test for CO2 emission search error missing year
        """
        res = self.client.get("/co2/Afghanistan")
        self.assertEqual(res.status_code, 400)
        self.assertIn(b"400", res.data)

    def test_deforestation_entity_with_year(self):
        """
        Test code for deforestation working properly
        """
        res = self.client.get("/deforestation/Afghanistan?year=2020")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Afghanistan", res.data)

    def test_co2_entity_with_year_200(self):
        """
        Test code for co2 working properly
        """
        res = self.client.get("/co2/Afghanistan?year=2020")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Afghanistan", res.data)

    def test_api_deforestation_entity_returns_json(self):
        """
        Test code for deforestation API
        """
        res = self.client.get("/api/deforestation/Afghanistan?year=2020")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.is_json)
        data = res.get_json()
        self.assertEqual(data["entity"], "Afghanistan")
        self.assertEqual(data["year"], 2020)
        self.assertIn("forest_change", data)

    def test_api_co2_entity_returns_json(self):
        """
        Test code for CO2 API
        """
        res = self.client.get("/api/co2/Afghanistan?year=2020")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.is_json)
        data = res.get_json()
        self.assertEqual(data["entity"], "Afghanistan")
        self.assertEqual(data["year"], 2020)
        self.assertIn("co2", data)

    def test_404_custom_handler(self):
        """
        Test code for 404 error
        """
        res = self.client.get("/this-route-does-not-exist")
        self.assertEqual(res.status_code, 404)
        self.assertIn(b"404", res.data)
        self.assertIn(b"Page Not Found", res.data)


if __name__ == "__main__":
    unittest.main()
