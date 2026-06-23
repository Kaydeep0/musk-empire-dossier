#!/usr/bin/env python3
"""Pull SPCX market snapshot from Yahoo + merge known 8-K bond facts. Writes data/spcx_market.json."""
import json
import os
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "spcx_market.json")
IPO_PRICE = 135.0
UA = "Watts Advisor research kiran@conformingcredit.org"

# From SpaceX 8-K / press release (June 22, 2026) - basis b/c
BOND_EVENT = {
    "date": "2026-06-22",
    "event": "Inaugural senior unsecured notes offering (target at least $20B)",
    "cash_disclosed_b": 100.8,
    "cash_as_of": "2026-06-19",
    "use_of_proceeds": "Repay $20B bridge loan in full; fees; general corporate purposes",
    "basis": "b",
    "sources": [
        "SpaceX 8-K material event (June 22, 2026)",
        "https://finance.yahoo.com/markets/stocks/articles/spacex-debuts-bond-sale-raise-134201086.html",
    ],
}


def fetch_spcx():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/SPCX?interval=1d&range=3mo"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = json.loads(urllib.request.urlopen(req, timeout=30).read())
    r = raw["chart"]["result"][0]
    meta = r["meta"]
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
    snap = {"bond": BOND_EVENT, "market": fetch_spcx()}
    os.makedirs(DATA, exist_ok=True)
    json.dump(snap, open(OUT, "w"), indent=2)
    print("wrote", OUT)
    if snap.get("market"):
        m = snap["market"]
        print(f"SPCX ${m['price']} ({m['change_pct_1d']:+.1f}% 1d) vs IPO {m['pct_vs_ipo']:+.1f}% vs ATH {m['pct_vs_ath']:+.1f}%")


if __name__ == "__main__":
    main()
