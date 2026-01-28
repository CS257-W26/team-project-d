"""
Helpers for deriving a list of countries from the datasets
"""

from __future__ import annotations

from pathlib import Path
from typing import Set

from ProductionCode.forest_change import is_country_row, load_forest_change_rows


def load_country_entities(data_dir: Path) -> Set[str]:
    """return the set of country entity names found in the forest dataset"""
    rows = load_forest_change_rows(data_dir)

    countries: Set[str] = set()
    for row in rows:
        if is_country_row(row):
            countries.add(row.entity)
    return countries

