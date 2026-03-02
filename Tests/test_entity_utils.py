"""
Unit tests for entity name matching utilities.
"""

from __future__ import annotations

import unittest

from ProductionCode.entity_utils import match_entity_name


class TestEntityUtils(unittest.TestCase):
    """tests for ProductionCode.entity_utilst"""

    def test_match_entity_name_suggests_close_matches(self) -> None:
        """if a close match exists, the error should include suggestions"""
        entities = ["Canada", "Cameroon", "Brazil"]

        with self.assertRaises(ValueError) as ctx:
            match_entity_name("Canda", entities)

        message = str(ctx.exception)
        self.assertIn("Did you mean", message)
        self.assertIn("Canada", message)


if __name__ == "__main__":
    unittest.main()
