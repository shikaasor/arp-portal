#!/usr/bin/env python3
"""Build the state / LGA / ward list (geo.json) from GRID3 NGA Operational Wards.

The portal's location dropdowns and reviewer matching read geo.json. This script regenerates it
from the GRID3 feature service, so it can be refreshed when GRID3 publishes an update:

    python3 scripts/build_geo.py

It writes identical copies to backend/app/geo.json and frontend/src/lib/geo.json, then prints the
LGA and ward counts per state. Only the Python standard library is needed.

To build from records saved earlier (a JSON list of objects with the GRID3 fields state,
statecode, lga, lga_alt_names and ward), pass --records FILE instead of fetching.

Data: GRID3 NGA Operational Wards, CC BY-SA 4.0. Anything built from it, including geo.json, is
shared under the same licence and must credit GRID3 (see the credits page and README).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = (ROOT / "backend" / "app" / "geo.json", ROOT / "frontend" / "src" / "lib" / "geo.json")
ALIASES = Path(__file__).with_name("geo_aliases.json")

SERVICE = (
    "https://services3.arcgis.com/BU6Aadhn6tbBEdyk/arcgis/rest/services/"
    "GRID3_NGA_operational_wards_v4_0/FeatureServer/0/query"
)
SOURCE = {
    "dataset": "GRID3 NGA - Operational Wards v4.0",
    "url": "https://data.grid3.org/datasets/GRID3::grid3-nga-operational-wards-v4-0/about",
    "doi": "https://doi.org/10.7916/3v3g-f998",
    "service": SERVICE.removesuffix("/query"),
    "licence": "CC BY-SA 4.0",
    "licence_url": "https://creativecommons.org/licenses/by-sa/4.0/",
    "citation": (
        "Center for Integrated Earth System Information (CIESIN), Columbia University 2026. "
        "GRID3 NGA - Operational Wards v4.0. New York: Columbia University. "
        "https://doi.org/10.7916/3v3g-f998."
    ),
    "notice": (
        "State, LGA and ward names derived from GRID3 NGA Operational Wards v4.0 (CIESIN, "
        "Columbia University), licensed CC BY-SA 4.0. This file is shared under the same licence."
    ),
}

# GRID3 state code -> the state name used across the portal (backend/app/constants.py), in the
# portal's order. GRID3 spells the capital "FCT, Abuja".
STATES = {
    "AD": "Adamawa",
    "BA": "Bauchi",
    "BE": "Benue",
    "BR": "Borno",
    "GO": "Gombe",
    "JI": "Jigawa",
    "KD": "Kaduna",
    "KN": "Kano",
    "KT": "Katsina",
    "KB": "Kebbi",
    "KO": "Kogi",
    "KW": "Kwara",
    "NA": "Nasarawa",
    "NI": "Niger",
    "PL": "Plateau",
    "SO": "Sokoto",
    "TA": "Taraba",
    "YO": "Yobe",
    "ZA": "Zamfara",
    "FC": "FCT Abuja",
}

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def key(value: str) -> str:
    """Same matching key as backend/app/geo.py and the lga_key / ward_key columns."""
    return _NON_ALNUM.sub("", value.lower())


def tidy(value: str) -> str:
    return " ".join(value.split())


def fetch(statecode: str) -> list[dict]:
    """Every ward polygon in one state, paging through the service."""
    records: list[dict] = []
    while True:
        params = {
            "where": f"statecode='{statecode}'",
            "outFields": "state,statecode,lga,lga_alt_names,ward",
            "returnGeometry": "false",
            "orderByFields": "OBJECTID",
            "resultOffset": str(len(records)),
            "resultRecordCount": "1000",
            "f": "json",
        }
        url = f"{SERVICE}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=60) as res:  # noqa: S310 (fixed https URL)
            body = json.load(res)
        if "error" in body:
            raise SystemExit(f"GRID3 service error for {statecode}: {body['error']}")
        page = [f["attributes"] for f in body.get("features", [])]
        records += page
        if not page or not body.get("exceededTransferLimit"):
            return records


def build(records: list[dict], manual_aliases: dict[str, dict[str, str]]) -> dict:
    wards: dict[str, dict[str, set[str]]] = {name: defaultdict(set) for name in STATES.values()}
    alt_names: dict[str, dict[str, set[str]]] = {name: defaultdict(set) for name in STATES.values()}
    for r in records:
        state = STATES.get(r.get("statecode") or "")
        if state is None:
            continue
        lga, ward = tidy(r["lga"]), tidy(r["ward"])
        wards[state][lga].add(ward)
        for alt in (r.get("lga_alt_names") or "").split(","):
            if tidy(alt):
                alt_names[state][lga].add(tidy(alt))

    states: dict[str, dict] = {}
    aliases: dict[str, dict[str, str]] = {}
    code = {name: c for c, name in STATES.items()}
    for state in STATES.values():
        if not wards[state]:
            raise SystemExit(f"No GRID3 records for {state}.")
        lgas = {
            lga: sorted(wards[state][lga], key=str.casefold)
            for lga in sorted(wards[state], key=str.casefold)
        }
        for lga, names in lgas.items():
            if len({key(n) for n in names}) != len(names):
                raise SystemExit(f"Two wards in {state} / {lga} differ only in punctuation.")
        if len({key(lga) for lga in lgas}) != len(lgas):
            raise SystemExit(f"Two LGAs in {state} differ only in punctuation.")
        states[state] = {"code": code[state], "lgas": lgas}

        # Other spellings that should resolve to an LGA: GRID3's alternative names plus the
        # portal's own earlier spellings. Skip any that already match, or that would match
        # a different LGA.
        taken = {key(lga): lga for lga in lgas}
        found: dict[str, str] = {}
        candidates = [(alt, lga) for lga, alts in alt_names[state].items() for alt in alts]
        candidates += list(manual_aliases.get(state, {}).items())
        for alt, lga in sorted(candidates):
            if lga not in lgas:
                raise SystemExit(f"Alias {alt!r} points at unknown LGA {state} / {lga}.")
            k = key(alt)
            if not k or k in taken or found.get(k, lga) != lga:
                continue
            found[k] = lga
            aliases.setdefault(state, {})[alt] = lga

    lga_count = sum(len(s["lgas"]) for s in states.values())
    ward_count = sum(len(w) for s in states.values() for w in s["lgas"].values())
    meta = {
        **SOURCE,
        "retrieved": datetime.now(UTC).date().isoformat(),
        "counts": {"states": len(states), "lgas": lga_count, "wards": ward_count},
    }
    return {"meta": meta, "states": states, "lga_aliases": aliases}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--records", type=Path, help="build from saved GRID3 records (JSON list)")
    parser.add_argument("--retrieved", help="date the records were retrieved (YYYY-MM-DD)")
    args = parser.parse_args()

    if args.records:
        records = json.loads(args.records.read_text(encoding="utf-8"))
    else:
        records = [r for code in STATES for r in fetch(code)]
    manual = json.loads(ALIASES.read_text(encoding="utf-8"))
    manual.pop("_comment", None)
    data = build(records, manual)
    if args.retrieved:
        data["meta"]["retrieved"] = args.retrieved

    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    for path in OUTPUTS:
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}", file=sys.stderr)
    for state, info in data["states"].items():
        n = sum(len(w) for w in info["lgas"].values())
        print(f"{state:12} {len(info['lgas']):3} LGAs {n:4} wards")
    counts = data["meta"]["counts"]
    print(f"{'Total':12} {counts['lgas']:3} LGAs {counts['wards']:4} wards")


if __name__ == "__main__":
    main()
