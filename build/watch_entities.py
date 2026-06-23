#!/usr/bin/env python3
"""
Watch Musk + SpaceX + Tesla SEC filings. Alerts, pipeline rebuild, site publish.

Replaces musk-only watching for the live dossier. State per entity in data/.watch_state_*.json
"""
import os
import subprocess
import sys
import time

from edgar_common import (
    DATA, alert_filing, get_recent_filings, load_state, save_state,
)

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")

ENTITIES = [
    {"key": "musk", "cik": "0001494730", "label": "Elon Musk"},
    {"key": "spacex", "cik": "0001181412", "label": "SpaceX"},
    {"key": "tesla", "cik": "0001318605", "label": "Tesla"},
]

MATERIAL_FORMS = {
    "4", "4/A", "3", "5", "8-K", "8-K/A", "424B4", "424B5",
    "DEF 14A", "DEFA14A", "DEFM14A", "SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A",
    "10-K", "10-Q", "S-1", "S-4",
}


def check_entity(entity, seed=False):
    key, cik, label = entity["key"], entity["cik"], entity["label"]
    seen = load_state(key)
    filings = get_recent_filings(cik)
    if not filings:
        return []
    new = [f for f in filings if f["accession"] not in seen]
    if seed:
        save_state(key, seen | {f["accession"] for f in filings})
        print(f"[{label}] seeded {len(filings)} filings")
        return []
    if not seen:
        save_state(key, {f["accession"] for f in filings})
        print(f"[{label}] first run seeded {len(filings)} filings")
        return []
    new.sort(key=lambda f: f["filingDate"])
    for f in new:
        linkedin = f["form"] in {"8-K", "8-K/A", "4", "4/A"} or entity["key"] == "spacex"
        alert_filing(label, f, trigger_linkedin=linkedin)
    save_state(key, seen | {f["accession"] for f in filings})
    return new


def run_pipeline(new_by_entity):
    if os.environ.get("MUSK_WATCH_PIPELINE", "1") == "0":
        return
    forms = set()
    entities = []
    for ent, new in new_by_entity.items():
        if new:
            entities.append(ent)
            forms |= {f["form"] for f in new}
    if not entities and not forms:
        return
    cmd = [sys.executable, os.path.join(HERE, "on_new_filing.py"),
           "--forms", ",".join(sorted(forms)) or "8-K",
           "--entities", ",".join(entities) or "spacex"]
    try:
        subprocess.run(cmd, cwd=ROOT, timeout=900, check=False)
    except Exception as e:
        print(f"pipeline failed: {e}", file=sys.stderr)


def main():
    os.makedirs(DATA, exist_ok=True)
    seed = "--seed" in sys.argv
    all_new = {}
    for ent in ENTITIES:
        all_new[ent["key"]] = check_entity(ent, seed=seed)
    if not seed:
        any_new = [f for flist in all_new.values() for f in flist]
        if any_new:
            run_pipeline(all_new)
        else:
            print(f"{time.strftime('%H:%M:%S')}  no new filings across {len(ENTITIES)} entities")


if __name__ == "__main__":
    main()
