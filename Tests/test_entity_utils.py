"""Unit tests for entity name matching utilities."""

from __future__ import annotations

import unittest

from ProductionCode.entity_utils import match_entity_name


class TestEntityUtils(unittest.TestCase):
    """Tests for ProductionCode.entity_utils."""

    def test_match_entity_name_returns_exact_match(self) -> None:
        """Exact matches should return the canonical entity name."""
        entities = ["Canada", "Cameroon", "Brazil"]

        self.assertEqual(match_entity_name("canada", entities), "Canada")

    def test_match_entity_name_suggests_close_matches(self) -> None:
        """If a close match exists, the error should include suggestions."""
        entities = ["Canada", "Cameroon", "Brazil"]

        with self.assertRaises(ValueError) as ctx:
            match_entity_name("Canda", entities)

        message = str(ctx.exception)
        self.assertIn("Did you mean", message)
        self.assertIn("Canada", message)

    def test_match_entity_name_reports_generic_error_for_distant_name(self) -> None:
        """A distant unknown name should raise the generic error message."""
        entities = ["Canada", "Cameroon", "Brazil"]

        with self.assertRaises(ValueError) as ctx:
            match_entity_name("zzzzzz", entities)

        self.assertEqual(str(ctx.exception), "Unknown entity name.")


if __name__ == "__main__":
    unittest.main()
