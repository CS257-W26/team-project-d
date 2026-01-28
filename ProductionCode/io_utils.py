"""
File I/O helper functions for reading CSV datasets.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List


def read_csv_records(csv_path: Path) -> List[Dict[str, str]]:
    """read a CSV file into a list of dict records"""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header row: {csv_path}")
        return list(reader)

