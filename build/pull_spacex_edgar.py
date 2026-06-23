#!/usr/bin/env python3
"""Pull SpaceX issuer filings from EDGAR; parse latest 8-K for bond/cash/debt facts."""
import json
import os
import re
from datetime import datetime

from edgar_common import DATA, fetch, get_recent_filings, html_to_text

CIK = "0001181412"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "spacex_events.json")
INDEX_OUT = os.path.join(DATA, "spacex_filings_index.csv")


def parse_8k_facts(text, meta):
    facts = {"basis": "b", "accession": meta["accession"], "url": meta["url"],
             "filing_date": meta["filingDate"], "form": meta["form"]}
    t = text.lower()

    cash = re.search(
        r"(?:held )?approximately \$\s*([\d,.]+)\s*billion in cash and cash equivalents as of "
        r"([A-Za-z]+ \d{1,2}, \d{4})",
        text, re.I)
    if not cash:
        cash = re.search(
            r"approximately \$\s*([\d,.]+)\s*billion in cash and cash equivalents",
            text, re.I)
        if cash:
            facts["cash_disclosed_b"] = float(cash.group(1).replace(",", ""))
            date_m = re.search(r"as of ([A-Za-z]+ \d{1,2}, \d{4})", text, re.I)
            if date_m:
                try:
                    facts["cash_as_of"] = datetime.strptime(date_m.group(1), "%B %d, %Y").strftime("%Y-%m-%d")
                except ValueError:
                    facts["cash_as_of"] = date_m.group(1)
    else:
        facts["cash_disclosed_b"] = float(cash.group(1).replace(",", ""))
        try:
            facts["cash_as_of"] = datetime.strptime(cash.group(2), "%B %d, %Y").strftime("%Y-%m-%d")
        except ValueError:
            facts["cash_as_of"] = cash.group(2)

    if "senior unsecured notes" in t or "inaugural offering" in t or "offering of senior unsecured" in t:
        amt = re.search(r"at least \$\s*([\d,.]+)\s*billion", text, re.I)
        facts["event"] = "Senior unsecured notes offering"
        if amt:
            facts["target_b"] = float(amt.group(1).replace(",", ""))
            facts["event"] += f" (target at least ${facts['target_b']:.0f}B)"
        facts["bond_offering"] = True

    if "bridge loan" in t or "bridge facility" in t:
        bridge = re.search(r"\$\s*([\d,.]+)\s*billion[^.]{0,60}bridge", text, re.I)
        if bridge:
            facts["bridge_loan_b"] = float(bridge.group(1).replace(",", ""))
        if "repay" in t and "bridge" in t:
            facts["use_of_proceeds"] = "Repay bridge loan facility; fees; general corporate purposes"

    if "use the net proceeds" in t:
        m = re.search(r"use the net proceeds from the notes[^.]{0,200}\.", text, re.I)
        if m:
            facts["use_of_proceeds"] = re.sub(r"\s+", " ", m.group(0))[:220]

    return facts


def fetch_8k_text(filing):
    acc = filing["accession"].replace("-", "")
    cik_int = str(int(CIK))
    primary = filing.get("primaryDocument")
    idx_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc}/index.json"
    idx = fetch(idx_url)
    name = primary
    if idx:
        data = json.loads(idx)
        items = data.get("directory", {}).get("item", [])
        if isinstance(items, dict):
            items = [items]
        htm_items = [
            it for it in items
            if it.get("name", "").endswith((".htm", ".html"))
            and "index" not in it.get("name", "").lower()
        ]
        if primary and any(it.get("name") == primary for it in htm_items):
            name = primary
        elif htm_items:
            name = max(htm_items, key=lambda it: int(it.get("size") or 0))["name"]
    if not name:
        return fetch(filing["url"], raw=True)
    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc}/{name}"
    raw = fetch(doc_url, raw=True)
    return raw


def main():
    filings = get_recent_filings(CIK, limit=80)
    os.makedirs(DATA, exist_ok=True)
    with open(INDEX_OUT, "w", encoding="utf-8") as f:
        f.write("filing_date,form,accession,url\n")
        for fl in filings:
            f.write(f"{fl['filingDate']},{fl['form']},{fl['accession']},{fl['url']}\n")

    events = []
    bond = None
    latest_8k = None
    for fl in filings:
        if not fl["form"].startswith("8-K"):
            continue
        raw = fetch_8k_text(fl)
        if not raw:
            continue
        text = html_to_text(raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw)
        facts = parse_8k_facts(text, fl)
        if facts.get("bond_offering") or facts.get("cash_disclosed_b"):
            events.append(facts)
            if not bond or fl["filingDate"] >= bond.get("filing_date", ""):
                bond = {
                    "date": fl["filingDate"],
                    "event": facts.get("event", "Material 8-K event"),
                    "cash_disclosed_b": facts.get("cash_disclosed_b"),
                    "cash_as_of": facts.get("cash_as_of"),
                    "target_b": facts.get("target_b"),
                    "bridge_loan_b": facts.get("bridge_loan_b"),
                    "use_of_proceeds": facts.get("use_of_proceeds"),
                    "basis": "b",
                    "url": fl["url"],
                    "accession": fl["accession"],
                }
        if not latest_8k or fl["filingDate"] >= latest_8k["filingDate"]:
            latest_8k = fl

    out = {
        "cik": CIK,
        "issuer": "Space Exploration Technologies Corp. (SPCX)",
        "latest_8k": latest_8k,
        "bond": bond,
        "events": events[:10],
    }
    json.dump(out, open(OUT, "w"), indent=2)
    print("wrote", OUT)
    if bond:
        print(f"bond: {bond.get('event')} cash={bond.get('cash_disclosed_b')}B url={bond.get('url')}")


if __name__ == "__main__":
    main()
