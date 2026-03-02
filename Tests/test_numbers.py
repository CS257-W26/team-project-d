"""
Unit tests for number parsing/formatting helpers.
"""

from __future__ import annotations

import unittest

from ProductionCode.numbers import format_number, parse_float, parse_int


class TestNumbers(unittest.TestCase):
    """tests for ProductionCode.numbers"""

    def test_parse_int_strips_whitespace(self) -> None:
        """parse_int should strip whitespace before converting"""
        self.assertEqual(42, parse_int("  42  "))

    def test_parse_float_blank_returns_none(self) -> None:
        """parse_float should treat blank strings as missing values"""
        self.assertIsNone(parse_float(""))
        self.assertIsNone(parse_float("   "))

    def test_parse_float_parses_valid_numbers(self) -> None:
        """parse_float should parse non-blank numeric strings"""
        self.assertEqual(3.14, parse_float("3.14"))

    def test_format_number_integer_like_values_drop_decimals(self) -> None:
        """format_number should show integer-like floats without decimal places"""
        self.assertEqual("1,000", format_number(1000.0))

    def test_format_number_formats_floats(self) -> None:
        """format_number should include decimals for non-integer values"""
        self.assertEqual("1,000.5", format_number(1000.5, decimals=1))


if __name__ == "__main__":
    unittest.main()
