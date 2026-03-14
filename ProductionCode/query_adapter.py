"""
Adapter objects that normalize database query results and rows.
"""

from __future__ import annotations

from typing import Any, Iterator, Optional


class RowAdapter:
    """Wrap one row-like object behind a stable dictionary-style interface."""

    def __init__(self, row: Optional[Any]):
        self._row = row

    def get(self, key: str) -> Optional[Any]:
        """Return a value for a key, or None when it is unavailable."""
        if self._row is None:
            return None
        try:
            return self._row[key]
        except (KeyError, TypeError, IndexError):
            return None


class QueryResultAdapter:
    """Wrap query results so repository code can treat them uniformly."""

    def __init__(self, rows: Any):
        self._rows = rows

    def __iter__(self) -> Iterator[RowAdapter]:
        """Yield adapted rows from the underlying query result."""
        for row in self._rows:
            yield RowAdapter(row)

    def first(self) -> RowAdapter:
        """Return the first adapted row, even for records-style results."""
        if hasattr(self._rows, "first"):
            return RowAdapter(self._rows.first())
        if self._rows:
            return RowAdapter(self._rows[0])
        return RowAdapter(None)
