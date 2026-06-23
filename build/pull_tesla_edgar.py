#!/usr/bin/env python3
"""Pull Tesla issuer filings; parse material 8-K / proxy facts."""
import json
import os
import re

from edgar_common import DATA, fetch, get_recent_filings, html_to_text

CIK = "0001318605"
OUT = os.path.join(DATA, "tesla_events.json")
INDEX_OUT = os.path.join(DATA, "tesla_filings_index.csv")


def parse_filing_facts(text, meta):
    facts = {"accession": meta["accession"], "url": meta["url"],
             "filing_date": meta["filingDate"], "form": meta["form"], "basis": "b"}
    t = text.lower()
    if "related party" in t or "related-party" in t:
        facts["related_party"] = True
    if "pledged" in t and "share" in t:
        facts["pledged_shares"] = True
    if "performance award" in t or "ceo award" in t or "compensation" in t:
        facts["compensation"] = True
    if "megapack" in t or "xai" in t or "spacex" in t:
        facts["cross_entity"] = True
    m = re.search(r"approximately \$\s*([\d,.]+)\s*(million|billion)", text, re.I)
    if m and ("related" in t or "megapack" in t):
        val = float(m.group(1).replace(",", ""))
        if m.group(2).lower().startswith("b"):
            val *= 1000
        facts["amount_disclosed_m"] = round(val, 1)
    return facts


def fetch_doc(filing):
    acc = filing["accession"].replace("-", "")
    cik_int = str(int(CIK))
    primary = filing.get("primaryDocument")
    idx = fetch(f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc}/index.json")
    name = primary
    if idx:
        data = json.loads(idx)
        items = data.get("directory", {}).get("item", [])
        if isinstance(items, dict):
            items = [items]
        htm = [it for it in items if it.get("name", "").endswith((".htm", ".html"))
               and "index" not in it.get("name", "").lower()]
        if primary and any(it.get("name") == primary for it in htm):
            name = primary
        elif htm:
            name = max(htm, key=lambda it: int(it.get("size") or 0))["name"]
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc}/{name}"
    raw = fetch(url, raw=True)
    if not raw:
        return ""
    return html_to_text(raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw)


def main():
    filings = get_recent_filings(CIK, limit=100)
    os.makedirs(DATA, exist_ok=True)
    with open(INDEX_OUT, "w", encoding="utf-8") as f:
        f.write("filing_date,form,accession,url\n")
        for fl in filings:
            f.write(f"{fl['filingDate']},{fl['form']},{fl['accession']},{fl['url']}\n")

    events = []
    latest_material = None
    for fl in filings:
        form = fl["form"]
        if not (form.startswith("8-K") or form.startswith("DEF") or form.startswith("10-")):
            continue
        text = fetch_doc(fl)
        if not text:
            continue
        facts = parse_filing_facts(text, fl)
        if any(facts.get(k) for k in ("related_party", "pledged_shares", "compensation", "cross_entity")):
            facts["headline"] = _headline(facts, form)
            events.append(facts)
            if not latest_material or fl["filingDate"] >= latest_material.get("filing_date", ""):
                latest_material = facts

    out = {"cik": CIK, "issuer": "Tesla Inc (TSLA)", "latest_material": latest_material,
           "events": events[:15]}
    json.dump(out, open(OUT, "w"), indent=2)
    print("wrote", OUT)
    if latest_material:
        print("latest:", latest_material.get("headline"))


def _headline(facts, form):
    bits = [form]
    if facts.get("cross_entity"):
        bits.append("cross-entity (SpaceX/xAI/Megapack)")
    if facts.get("related_party"):
        bits.append("related-party")
    if facts.get("pledged_shares"):
        bits.append("pledged shares")
    if facts.get("compensation"):
        bits.append("CEO comp")
    if facts.get("amount_disclosed_m"):
        bits.append(f"~${facts['amount_disclosed_m']}M disclosed")
    return " · ".join(bits)


if __name__ == "__main__":
    main()
