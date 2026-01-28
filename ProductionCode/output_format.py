"""
Formatting helpers for turning query results into CLI output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

from ProductionCode.numbers import format_number


@dataclass(frozen=True)
class RankResult:
    """ranking result for a single entity in a specific year"""
    entity: str
    year: int
    metric: str
    order: str
    rank: int
    total: int
    value: float
    unit: str


def format_single_value(entity: str, year: int, metric: str, value: float, unit: str) -> str:
    """format a single numeric value for display"""
    formatted_value = format_number(value)
    return f"{metric} for {entity} in {year}: {formatted_value} {unit}"


def format_rank_result(result: RankResult) -> str:
    """format a ``RankResult`` into a one-line CLI string"""
    formatted_value = format_number(result.value)
    return (
        f"{result.entity} rank in {result.year} "
        f"({result.metric}, order={result.order}): "
        f"{result.rank} of {result.total} | value: {formatted_value} {result.unit}"
    )


def format_top_list(title: str, rows: Sequence[Tuple[str, float]], unit: str) -> str:
    """format a numbered list of entity/value pairs"""
    lines: List[str] = [title]
    for idx, (entity, value) in enumerate(rows, start=1):
        lines.append(f"{idx}. {entity}: {format_number(value)} {unit}")
    return "\n".join(lines)

