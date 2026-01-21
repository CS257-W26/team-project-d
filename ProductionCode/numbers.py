# number parsing and formatting helpers

from __future__ import annotations

from typing import Optional

# parse an integer from a string.
def parse_int(value: str) -> int:
    return int(value.strip())

# parse a float from a string, returning None for blanks
def parse_float(value: str) -> Optional[float]:
    stripped = value.strip()
    if stripped == "":
        return None
    return float(stripped)

# format a number for user-facing output.
def format_number(value: float, decimals: int = 2) -> str:
    # use fewer decimals for values that are effectively integers
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value)):,}"
    return f"{value:,.{decimals}f}"
