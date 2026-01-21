# Utilities for matching user-provided entity names to dataset values

from __future__ import annotations

import difflib
import re
import unicodedata
from typing import Iterable, List


_NON_ALNUM = re.compile(r"[^a-z0-9]+")

# normalize a country/entity name for forgiving comparisons
# lowercases, removes diacritics, keeps only a-z and 0-9
def normalize_entity_name(name: str) -> str:
    # Normalize unicode (strip accents) then lowercase.
    normalized = unicodedata.normalize("NFKD", name)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = _NON_ALNUM.sub("", normalized)
    return normalized

# find the best exact match for a user query among known entities.
def match_entity_name(query: str, entities: Iterable[str]) -> str:
    entity_list = list(entities)
    normalized_to_entity = {normalize_entity_name(e): e for e in entity_list}

    key = normalize_entity_name(query)
    if key in normalized_to_entity:
        return normalized_to_entity[key]

    # Provide suggestions to make CLI friendlier.
    suggestions = difflib.get_close_matches(key, normalized_to_entity.keys(), n=5, cutoff=0.6)
    suggestion_names: List[str] = [normalized_to_entity[s] for s in suggestions]
    if suggestion_names:
        raise ValueError(
            "Unknown entity name. Did you mean one of: " + ", ".join(suggestion_names)
        )
    raise ValueError("Unknown entity name.")
