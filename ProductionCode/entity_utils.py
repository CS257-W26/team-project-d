"""
Utilities for matching user-provided entity names to dataset values
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from typing import Iterable, List


_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_entity_name(name: str) -> str:
    """normalize an entity name for forgiving comparisons"""
    normalized = unicodedata.normalize("NFKD", name)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = _NON_ALNUM.sub("", normalized)
    return normalized


def match_entity_name(query: str, entities: Iterable[str]) -> str:
    """match a user query to the best entity name from a dataset"""
    entity_list = list(entities)
    normalized_to_entity = {normalize_entity_name(e): e for e in entity_list}

    key = normalize_entity_name(query)
    if key in normalized_to_entity:
        return normalized_to_entity[key]

    suggestions = difflib.get_close_matches(
        key,
        normalized_to_entity.keys(),
        n=5,
        cutoff=0.6,
    )
    suggestion_names: List[str] = [normalized_to_entity[s] for s in suggestions]

    if suggestion_names:
        suggestion_text = ", ".join(suggestion_names)
        raise ValueError(f"Unknown entity name. Did you mean one of: {suggestion_text}")

    raise ValueError("Unknown entity name.")

