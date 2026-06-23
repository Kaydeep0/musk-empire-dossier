#!/usr/bin/env python3
"""Pull SPCX market snapshot from Yahoo + bond facts from parsed SpaceX 8-K."""
import json
import os
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "spcx_market.json")
SPACEX_EVENTS = os.path.join(DATA, "spacex_events.json")
IPO_PRICE = 135.0
UA = "Watts Advisor research kiran@conformingcredit.org"


def load_bond_from_edgar():
    if not os.path.exists(SPACEX_EVENTS):
        return None
    data = json.load(open(SPACEX_EVENTS, encoding="utf-8"))
    bond = data.get("bond")
    if not bond:
        return None
    event = bond.get("event") or "SpaceX material 8-K event"
    out = {
        "date": bond.get("date"),
        "event": event,
        "cash_disclosed_b": bond.get("cash_disclosed_b"),
        "cash_as_of": bond.get("cash_as_of"),
        "use_of_proceeds": bond.get("use_of_proceeds"),
        "basis": "b",
        "url": bond.get("url"),
        "accession": bond.get("accession"),
    }
    return out


def fetch_spcx():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/SPCX?interval=1d&range=3mo"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = json.loads(urllib.request.urlopen(req, timeout=30).read())
    r = raw["chart"]["result"][0]
    ts = r["timestamp"]
    closes = r["indicators"]["quote"][0]["close"]
    pairs = [(t, c) for t, c in zip(ts, closes) if c is not None]
    if not pairs:
        return None
    ath_t, ath_p = max(pairs, key=lambda x: x[1])
    last_t, last_p = pairs[-1]
    prev_p = pairs[-2][1] if len(pairs) >= 2 else last_p
    return {
        "ticker": "SPCX",
        "price": round(last_p, 2),
        "previous_close": round(prev_p, 2),
        "change_pct_1d": round((last_p / prev_p - 1) * 100, 2),
        "ipo_price": IPO_PRICE,
        "pct_vs_ipo": round((last_p / IPO_PRICE - 1) * 100, 2),
        "ath_price": round(ath_p, 2),
        "ath_date": datetime.utcfromtimestamp(ath_t).strftime("%Y-%m-%d"),
        "pct_vs_ath": round((last_p / ath_p - 1) * 100, 2),
        "as_of_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "basis": "m",
        "source": "Yahoo Finance chart API (point-in-time; re-pull before citing)",
    }


def main():
    bond = load_bond_from_edgar()
    snap = {"bond": bond, "market": fetch_spcx()}
    if os.path.exists(SPACEX_EVENTS):
        snap["spacex_edgar"] = json.load(open(SPACEX_EVENTS, encoding="utf-8"))
    os.makedirs(DATA, exist_ok=True)
    json.dump(snap, open(OUT, "w"), indent=2)
    print("wrote", OUT)
    if bond:
        print(f"bond (EDGAR): {bond.get('event')} acc={bond.get('accession')}")
    if snap.get("market"):
        m = snap["market"]
        print(f"SPCX ${m['price']} ({m['change_pct_1d']:+.1f}% 1d) vs IPO {m['pct_vs_ipo']:+.1f}%")


if __name__ == "__main__":
    main()
