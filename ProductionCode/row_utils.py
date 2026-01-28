"""
Shared helpers for working with dataset rows
"""

from __future__ import annotations

from typing import Callable, List, Optional, Protocol, Sequence, TypeVar


class EntityYearRow(Protocol):
    """a row that contains an entity name and a year"""
    entity: str
    year: int


RowT = TypeVar("RowT", bound=EntityYearRow)


def unique_entities(
    rows: Sequence[RowT],
    row_filter: Optional[Callable[[RowT], bool]] = None,
) -> List[str]:
    """return unique entity names found in rows"""
    seen: set[str] = set()
    result: List[str] = []

    for row in rows:
        if row_filter is not None and not row_filter(row):
            continue
        if row.entity in seen:
            continue
        seen.add(row.entity)
        result.append(row.entity)

    return result


def latest_year_for_entity(
    rows: Sequence[RowT],
    entity: str,
    row_filter: Optional[Callable[[RowT], bool]] = None,
) -> int:
    """return the most recent year for a specific entity"""
    latest: Optional[int] = None

    for row in rows:
        if row_filter is not None and not row_filter(row):
            continue
        if row.entity != entity:
            continue
        if latest is None or row.year > latest:
            latest = row.year

    if latest is None:
        raise ValueError(f"No data found for entity: {entity}")

    return latest


def latest_year(
    rows: Sequence[RowT],
    row_filter: Optional[Callable[[RowT], bool]] = None,
) -> int:
    """return the most recent year present in the dataset"""
    latest: Optional[int] = None

    for row in rows:
        if row_filter is not None and not row_filter(row):
            continue
        if latest is None or row.year > latest:
            latest = row.year

    if latest is None:
        raise ValueError("No data available.")

    return latest
