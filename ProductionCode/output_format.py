# format helpers for turning query results into CLI output

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

from ProductionCode.numbers import format_number

# format a single numeric result for printing
def format_single_value(entity: str, year: int, metric: str, value: float, unit: str) -> str:
    formatted_value = format_number(value)
    return f"{metric} for {entity} in {year}: {formatted_value} {unit}"

# format a ranking result for one entity
def format_rank_result(entity: str, year: int, rank: int, total: int, metric: str, value: float, unit: str, order: str) -> str:
    formatted_value = format_number(value)
    return (
        f"{entity} rank in {year} ({metric}, order={order}): "
        f"{rank} of {total} | value: {formatted_value} {unit}"
    )

# format a numbered list of entity/value pairs
def format_top_list(title: str, rows: Sequence[Tuple[str, float]], unit: str) -> str:
    lines: List[str] = [title]
    for idx, (entity, value) in enumerate(rows, start=1):
        lines.append(f"{idx}. {entity}: {format_number(value)} {unit}")
    return "\n".join(lines)
