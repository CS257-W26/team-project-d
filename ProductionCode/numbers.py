"""
Number parsing and formatting helpers used by the CLI.
"""

from __future__ import annotations

from typing import Optional


def parse_int(value: str) -> int:
    """parse an integer from a string"""
    return int(value.strip())


def parse_float(value: str) -> Optional[float]:
    """parse a float from a string"""
    stripped = value.strip()
    if stripped == "":
        return None
    return float(stripped)


def format_number(value: float, decimals: int = 2) -> str:
    """format a numeric value for user-facing output"""
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value)):,}"
    return f"{value:,.{decimals}f}"

