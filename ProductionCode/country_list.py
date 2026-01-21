# helper for deriving a list of countries from datasets

from __future__ import annotations

from pathlib import Path
from typing import Set

from ProductionCode.forest_change import is_country_row, load_forest_change_rows

# load the set of country entity names from forest data
def load_country_entities(data_dir: Path) -> Set[str]:
    rows = load_forest_change_rows(data_dir)
    return {row.entity for row in rows if is_country_row(row)}
