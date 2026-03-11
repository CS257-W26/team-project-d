"""Unit tests for ProductionCode.query_adapter."""

from __future__ import annotations

import unittest

from ProductionCode.query_adapter import QueryResultAdapter, RowAdapter


class FakeResult:
    """Minimal records-like result for adapter tests."""

    def __init__(self, rows):
        """Store rows for later iteration in adapter tests."""
        self._rows = rows

    def __iter__(self):
        """Yield stored rows one at a time."""
        return iter(self._rows)

    def first(self):
        """Return the first stored row, if one exists."""
        return self._rows[0] if self._rows else None


class TestRowAdapter(unittest.TestCase):
    """Tests for adapting individual rows."""

    def test_get_returns_none_for_missing_or_unusable_rows(self) -> None:
        """Missing keys and missing rows should both produce None."""
        self.assertIsNone(RowAdapter(None).get("year"))
        self.assertIsNone(RowAdapter({}).get("year"))
        self.assertIsNone(RowAdapter(object()).get("year"))

    def test_get_reads_dictionary_style_rows(self) -> None:
        """Dictionary-backed rows should still return stored values."""
        row = RowAdapter({"entity": "Canada"})

        self.assertEqual(row.get("entity"), "Canada")


class TestQueryResultAdapter(unittest.TestCase):
    """Tests for adapting full query results."""

    def test_first_supports_records_style_results(self) -> None:
        """Results with first() should return their first adapted row."""
        rows = QueryResultAdapter(FakeResult([{"year": 2020}]))

        self.assertEqual(rows.first().get("year"), 2020)

    def test_iteration_wraps_each_row(self) -> None:
        """Iterating should yield row adapters in the original order."""
        rows = QueryResultAdapter([{"entity": "Canada"}, {"entity": "Chile"}])

        entities = [row.get("entity") for row in rows]

        self.assertEqual(entities, ["Canada", "Chile"])


if __name__ == "__main__":
    unittest.main()
