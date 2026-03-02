"""
Formatting helpers for command-line output.
"""

from __future__ import annotations

from ProductionCode.numbers import format_number


def format_single_value(entity: str, year: int, metric: str, value: float, unit: str) -> str:
    """format a single numeric value for display"""
    return f"{metric} for {entity} in {year}: {format_number(value)} {unit}"
