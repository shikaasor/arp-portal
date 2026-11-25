"""Local Government Areas and the matching rules used to scope reviewers.

`lgas.json` holds the official LGAs for every state the programme covers. The frontend ships an
identical copy (frontend/src/lib/lgas.json); a test keeps the two in step.

Applicants pick their LGA from that list, so it is stored with one canonical spelling. Wards are
typed, so every comparison uses `geo_key`, which ignores case, spaces and punctuation. The
database computes the same key in the generated columns `lga_key` and `ward_key`.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def geo_key(value: str | None) -> str:
    """Matching key: lowercase letters and digits only. Mirrors the SQL in the migrations."""
    return _NON_ALNUM.sub("", (value or "").lower())


def tidy(value: str) -> str:
    """Collapse runs of whitespace, as typed values are stored."""
    return " ".join(value.split())


@lru_cache
def lgas_by_state() -> dict[str, tuple[str, ...]]:
    raw = json.loads((Path(__file__).parent / "lgas.json").read_text(encoding="utf-8"))
    return {state: tuple(lgas) for state, lgas in raw.items()}


def canonical_lga(state: str | None, lga: str | None) -> str | None:
    """The official spelling of `lga` in `state`, or None if it is not one of that state's LGAs."""
    key = geo_key(lga)
    if not key:
        return None
    return next(
        (name for name in lgas_by_state().get(state or "", ()) if geo_key(name) == key), None
    )
