#!/usr/bin/env python3
"""
Registry-driven SEC watcher: Musk + all v1_scope entities with CIKs.
Alerts via email, SMS, ntfy; triggers pipeline on new filings.
"""
import os
import subprocess
import sys
import time

from edgar_common import DATA, alert_filing, get_recent_filings, load_state, save_state
from load_registry import load_watch_entities, MATERIAL_FORMS

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")


def form_allowed(entity, form):
    if entity.get("key") == "musk":
        return True
    allowed = entity.get("forms") or MATERIAL_FORMS
    return form in allowed or form.split("/")[0] in allowed


def check_entity(entity, seed=False):
    key, cik, label = entity["key"], entity["cik"], entity["label"]
    seen = load_state(key)
    filings = get_recent_filings(cik)
    filings = [f for f in filings if form_allowed(entity, f["form"])]
    if not filings:
        return []
    if seed:
        save_state(key, seen | {f["accession"] for f in filings})
        print(f"[{label}] seeded {len(filings)} filings")
        return []
    if not seen:
        save_state(key, {f["accession"] for f in filings})
        print(f"[{label}] first run seeded {len(filings)} filings")
        return []
    new = [f for f in filings if f["accession"] not in seen]
    new.sort(key=lambda f: f["filingDate"])
    for f in new:
        linkedin = f["form"] in {"8-K", "8-K/A", "4", "4/A", "DEF 14A", "DEFA14A"}
        alert_filing(label, f, trigger_linkedin=linkedin)
    save_state(key, seen | {f["accession"] for f in new})
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
    if not entities:
        return
    cmd = [sys.executable, os.path.join(HERE, "on_new_filing.py"),
           "--forms", ",".join(sorted(forms)) or "8-K",
           "--entities", ",".join(entities)]
    try:
        subprocess.run(cmd, cwd=ROOT, timeout=900, check=False)
    except Exception as e:
        print(f"pipeline failed: {e}", file=sys.stderr)


def main():
    os.makedirs(DATA, exist_ok=True)
    seed = "--seed" in sys.argv
    entities = load_watch_entities()
    all_new = {}
    for ent in entities:
        all_new[ent["key"]] = check_entity(ent, seed=seed)
    if not seed:
        any_new = [f for flist in all_new.values() for f in flist]
        if any_new:
            run_pipeline(all_new)
        else:
            print(f"{time.strftime('%H:%M:%S')}  no new filings across {len(entities)} entities")


if __name__ == "__main__":
    main()
