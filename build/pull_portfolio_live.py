#!/usr/bin/env python3
"""Live quotes for Musk public holdings + net-worth proxy (TSLA + SPCX + cash)."""
import csv
import json
import os
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "portfolio_live.json")
REGISTRY = os.path.join(DATA, "holdings_registry.csv")
ANCHORS = os.path.join(DATA, "tesla_holdings_anchors.csv")
TX = os.path.join(DATA, "transactions.csv")
UA = "Watts Advisor research kiran@conformingcredit.org"

# SPCX 424(b)(4): ~$2.41T IPO cap at $135 => total class A shares outstanding proxy
SPCX_IPO_PRICE = 135.0
SPCX_IPO_CAP_B = 2410.0
SPCX_TOTAL_SHARES = SPCX_IPO_CAP_B * 1e9 / SPCX_IPO_PRICE
MUSK_SPCX_ECON_PCT = 0.36


def fetch_quote(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = json.loads(urllib.request.urlopen(req, timeout=30).read())
    r = raw["chart"]["result"][0]
    meta = r.get("meta", {})
    ts = r["timestamp"]
    closes = r["indicators"]["quote"][0]["close"]
    pairs = [(t, c) for t, c in zip(ts, closes) if c is not None]
    if not pairs:
        return None
    last_t, last_p = pairs[-1]
    prev_p = pairs[-2][1] if len(pairs) >= 2 else last_p
    return {
        "ticker": ticker,
        "price": round(last_p, 2),
        "previous_close": round(prev_p, 2),
        "change_pct_1d": round((last_p / prev_p - 1) * 100, 2),
        "currency": meta.get("currency", "USD"),
        "exchange": meta.get("exchangeName", ""),
        "as_of_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "basis": "m",
        "source": "Yahoo Finance chart API (delayed; re-pull before citing)",
    }


def tesla_shares():
    rows = list(csv.DictReader(open(ANCHORS, encoding="utf-8")))
    if not rows:
        return 710e6
    rows.sort(key=lambda r: r["date"])
    return float(rows[-1]["shares_mm_adjusted"]) * 1e6


def cash_from_sales():
    total = 0.0
    for r in csv.DictReader(open(TX, encoding="utf-8")):
        if r.get("code") != "S":
            continue
        try:
            v = float(r.get("value_usd") or 0)
        except ValueError:
            continue
        if v > 0:
            total += v
    return total


def build_portfolio():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tsla_sh = tesla_shares()
    cash = cash_from_sales()
    holdings = []
    components = {"cash_realized_usd_b": round(cash / 1e9, 2)}

    tsla_q = fetch_quote("TSLA")
    if tsla_q:
        tsla_val = tsla_sh * tsla_q["price"]
        components["tesla_stake_usd_b"] = round(tsla_val / 1e9, 2)
        holdings.append({
            "entity": "Tesla Inc",
            "ticker": "TSLA",
            "kind": "public",
            "shares": int(tsla_sh),
            "price": tsla_q["price"],
            "change_pct_1d": tsla_q["change_pct_1d"],
            "value_usd_b": round(tsla_val / 1e9, 2),
            "basis": "b+m",
            "note": "Beneficial shares from Form 4 anchor x live price",
        })

    spcx_q = fetch_quote("SPCX")
    if spcx_q:
        musk_sh = SPCX_TOTAL_SHARES * MUSK_SPCX_ECON_PCT
        spcx_val = musk_sh * spcx_q["price"]
        ipo_stake_b = SPCX_IPO_CAP_B * MUSK_SPCX_ECON_PCT
        components["spacex_stake_usd_b"] = round(spcx_val / 1e9, 2)
        holdings.append({
            "entity": "SpaceX (SPCX)",
            "ticker": "SPCX",
            "kind": "public",
            "musk_econ_pct": MUSK_SPCX_ECON_PCT,
            "implied_shares": int(musk_sh),
            "price": spcx_q["price"],
            "change_pct_1d": spcx_q["change_pct_1d"],
            "pct_vs_ipo": round((spcx_q["price"] / SPCX_IPO_PRICE - 1) * 100, 2),
            "value_usd_b": round(spcx_val / 1e9, 2),
            "value_at_ipo_usd_b": round(ipo_stake_b, 1),
            "basis": "b+m",
            "note": f"~{MUSK_SPCX_ECON_PCT*100:.0f}% econ x {int(SPCX_TOTAL_SHARES/1e9)}B total shares proxy at IPO",
        })

    holdings.append({
        "entity": "Cash (Tesla sales)",
        "ticker": "",
        "kind": "cash",
        "value_usd_b": round(cash / 1e9, 2),
        "basis": "b",
        "note": "Cumulative Form 4 open-market sales, not salary or dividends",
    })

    private = [
        ("Twitter / X", "Private; debt traveled to SpaceX"),
        ("xAI", "Absorbed into SpaceX (no separate mark)"),
        ("The Boring Company", "Private; no public price"),
        ("Neuralink", "Private; no public price"),
    ]
    for name, note in private:
        holdings.append({
            "entity": name,
            "ticker": "",
            "kind": "private",
            "value_usd_b": None,
            "basis": "c",
            "note": note,
        })

    total_b = sum(v for k, v in components.items() if v)
    out = {
        "as_of_utc": now,
        "refresh_note": "Updated each sync (~30 min via GitHub Actions). Yahoo data is delayed, not tick-by-tick.",
        "net_worth_proxy_usd_b": round(total_b, 2),
        "components_usd_b": components,
        "holdings": holdings,
        "disclaimer": "Educational proxy only. Private stakes excluded. Not investment advice.",
    }
    return out


def main():
    os.makedirs(DATA, exist_ok=True)
    out = build_portfolio()
    json.dump(out, open(OUT, "w"), indent=2)
    print("wrote", OUT)
    print(f"net worth proxy: ${out['net_worth_proxy_usd_b']}B")
    for h in out["holdings"]:
        if h.get("price"):
            print(f"  {h['ticker']}: ${h['price']} -> ${h.get('value_usd_b')}B")


if __name__ == "__main__":
    main()
