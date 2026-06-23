#!/usr/bin/env python3
"""Load watchable entities from registry/entities.csv."""
import csv
import os

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
REGISTRY = os.path.join(ROOT, "registry", "entities.csv")

# Forms we care about by entity kind
PERSON_FORMS = {
    "4", "4/A", "3", "5", "8-K", "8-K/A",
    "SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A", "SCHEDULE 13G/A",
    "DEF 14A", "DEFA14A", "DEFM14A", "424B4", "424B5", "S-1", "S-4",
}
ISSUER_FORMS = {
    "8-K", "8-K/A", "10-K", "10-Q", "DEF 14A", "DEFA14A", "DEFM14A",
    "424B4", "424B5", "S-1", "S-1/A", "S-4", "SC 13D", "SC 13D/A",
    "SC 13G", "SC 13G/A", "FWP", "425",
}
MATERIAL_FORMS = PERSON_FORMS | ISSUER_FORMS


def load_watch_entities(scope="yes"):
    """Return list of dicts: key, cik, label, kind, ticker, forms."""
    if not os.path.exists(REGISTRY):
        return []
    out = []
    with open(REGISTRY, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if scope and row.get("v1_scope", "").lower() != scope:
                continue
            cik = (row.get("cik") or "").strip()
            if not cik:
                continue
            entity = row.get("entity", "").strip()
            kind = row.get("kind", "issuer").strip()
            key = entity.lower()
            key = key.replace(" ", "_").replace("(", "").replace(")", "")
            key = key.replace(".", "").replace("/", "_")[:40]
            if "musk" in key and "reporting" in key:
                key = "musk"
            elif "spacex" in key or "space_exploration" in key:
                key = "spacex"
            elif "tesla" in key:
                key = "tesla"
            elif "twitter" in key:
                key = "twitter"
            elif "solarcity" in key:
                key = "solarcity"
            elif "paypal" in key:
                key = "paypal"
            forms = PERSON_FORMS if kind == "person" else ISSUER_FORMS
            out.append({
                "key": key,
                "cik": cik.zfill(10),
                "label": entity,
                "kind": kind,
                "ticker": row.get("ticker", ""),
                "forms": forms,
            })
    return out


if __name__ == "__main__":
    for e in load_watch_entities():
        print(e["key"], e["cik"], e["label"], e["kind"])
