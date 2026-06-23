#!/usr/bin/env python3
"""
Append live snapshots and publish public/timeseries.json for site charts.

Called after pull_portfolio_live.py on each sync (~30 min).

  data/timeseries/live.jsonl   — raw sync points
  public/timeseries.json       — merged series for Chart.js
"""
import csv
import json
import os
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
TS_DIR = os.path.join(DATA, "timeseries")
LIVE_LOG = os.path.join(TS_DIR, "live.jsonl")
PUBLIC_TS = os.path.join(HERE, "..", "public", "timeseries.json")
PORTFOLIO = os.path.join(DATA, "portfolio_live.json")
TX = os.path.join(DATA, "transactions.csv")
ANCHORS = os.path.join(DATA, "tesla_holdings_anchors.csv")
UA = "Watts Advisor research kiran@conformingcredit.org"

SPCX_IPO_PRICE = 135.0
SPCX_IPO_CAP_B = 2410.0
SPCX_TOTAL_SHARES = SPCX_IPO_CAP_B * 1e9 / SPCX_IPO_PRICE
MUSK_SPCX_ECON_PCT = 0.36


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tesla_shares():
    if not os.path.isfile(ANCHORS):
        return 710e6
    rows = list(csv.DictReader(open(ANCHORS, encoding="utf-8")))
    rows.sort(key=lambda r: r["date"])
    return float(rows[-1]["shares_mm_adjusted"]) * 1e6


def cash_from_sales():
    total = 0.0
    if not os.path.isfile(TX):
        return total
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


def fetch_yahoo_daily(ticker, range_="3mo"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range={range_}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = json.loads(urllib.request.urlopen(req, timeout=30).read())
    r = raw["chart"]["result"][0]
    ts = r["timestamp"]
    closes = r["indicators"]["quote"][0]["close"]
    out = []
    for t, c in zip(ts, closes):
        if c is not None:
            out.append({"date": datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"), "close": round(c, 2)})
    return out


def append_live_point():
    """Append one row from portfolio_live.json if present."""
    if not os.path.isfile(PORTFOLIO):
        return None
    p = json.load(open(PORTFOLIO, encoding="utf-8"))
    comps = p.get("components_usd_b") or {}
    spcx = tsla = None
    for h in p.get("holdings", []):
        if h.get("ticker") == "SPCX":
            spcx = h.get("price")
        if h.get("ticker") == "TSLA":
            tsla = h.get("price")
    row = {
        "ts": p.get("as_of_utc") or utcnow(),
        "spcx": spcx,
        "tsla": tsla,
        "net_worth_b": p.get("net_worth_proxy_usd_b"),
        "spacex_stake_b": comps.get("spacex_stake_usd_b"),
        "tesla_stake_b": comps.get("tesla_stake_usd_b"),
        "cash_b": comps.get("cash_realized_usd_b"),
    }
    os.makedirs(TS_DIR, exist_ok=True)
    with open(LIVE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return row


def load_live_points():
    if not os.path.isfile(LIVE_LOG):
        return []
    out = []
    for line in open(LIVE_LOG, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def build_historical_networth(spcx_series, tsla_series):
    """Daily net-worth proxy from Yahoo closes (pre-sync backfill)."""
    tsla_sh = tesla_shares()
    cash_b = cash_from_sales() / 1e9
    musk_sh = SPCX_TOTAL_SHARES * MUSK_SPCX_ECON_PCT
    tsla_by_date = {r["date"]: r["close"] for r in tsla_series}
    spcx_by_date = {r["date"]: r["close"] for r in spcx_series}
    dates = sorted(set(tsla_by_date) | set(spcx_by_date))
    series = []
    for d in dates:
        sp = spcx_by_date.get(d)
        tp = tsla_by_date.get(d)
        if sp is None and tp is None:
            continue
        spacex_b = (musk_sh * sp / 1e9) if sp else None
        tesla_b = (tsla_sh * tp / 1e9) if tp else None
        parts = [cash_b]
        if tesla_b is not None:
            parts.append(tesla_b)
        if spacex_b is not None:
            parts.append(spacex_b)
        series.append({
            "date": d,
            "net_worth_b": round(sum(parts), 2),
            "spcx": sp,
            "tsla": tp,
            "spacex_stake_b": round(spacex_b, 2) if spacex_b else None,
            "tesla_stake_b": round(tesla_b, 2) if tesla_b else None,
            "cash_b": round(cash_b, 2),
        })
    return series


def merge_sync_points(daily, live_points):
    """Overlay high-frequency sync points onto daily series."""
    by_ts = {r["date"]: dict(r) for r in daily}
    for pt in live_points:
        ts = pt.get("ts", "")[:10]
        if not ts:
            continue
        row = by_ts.get(ts, {"date": ts})
        row.update({
            "date": ts,
            "sync_ts": pt.get("ts"),
            "spcx": pt.get("spcx") if pt.get("spcx") is not None else row.get("spcx"),
            "tsla": pt.get("tsla") if pt.get("tsla") is not None else row.get("tsla"),
            "net_worth_b": pt.get("net_worth_b") if pt.get("net_worth_b") is not None else row.get("net_worth_b"),
            "spacex_stake_b": pt.get("spacex_stake_b") if pt.get("spacex_stake_b") is not None else row.get("spacex_stake_b"),
            "tesla_stake_b": pt.get("tesla_stake_b") if pt.get("tesla_stake_b") is not None else row.get("tesla_stake_b"),
            "cash_b": pt.get("cash_b") if pt.get("cash_b") is not None else row.get("cash_b"),
        })
        by_ts[ts] = row
    return [by_ts[d] for d in sorted(by_ts)]


def load_catalyst_annotations():
    path = os.path.join(DATA, "catalyst_calendar.json")
    if not os.path.isfile(path):
        return []
    out = []
    for ev in json.load(open(path, encoding="utf-8")):
        out.append({
            "date": ev.get("date"),
            "label": (ev.get("event") or "")[:60],
            "entity": ev.get("entity"),
            "type": "catalyst",
        })
    return out


def load_filing_events():
    path = os.path.join(DATA, "spacex_events.json")
    if not os.path.isfile(path):
        return []
    data = json.load(open(path, encoding="utf-8"))
    out = []
    for ev in data.get("events") or []:
        out.append({
            "date": ev.get("filing_date"),
            "label": (ev.get("event") or ev.get("form") or "8-K")[:50],
            "url": ev.get("url"),
            "type": "filing",
        })
    return out


def publish():
    spcx = fetch_yahoo_daily("SPCX", "3mo")
    tsla = fetch_yahoo_daily("TSLA", "3mo")
    daily = build_historical_networth(spcx, tsla)
    live = load_live_points()
    merged = merge_sync_points(daily, live)

    payload = {
        "updated_at": utcnow(),
        "disclaimer": "Educational proxy. Yahoo daily + sync snapshots. Not investment advice.",
        "ipo_price": SPCX_IPO_PRICE,
        "series": merged,
        "live_sync_count": len(live),
        "annotations": {
            "catalysts": load_catalyst_annotations(),
            "filings": load_filing_events(),
        },
        "latest": merged[-1] if merged else {},
    }
    os.makedirs(os.path.dirname(PUBLIC_TS), exist_ok=True)
    json.dump(payload, open(PUBLIC_TS, "w"), indent=2)
    return payload


def main():
    pt = append_live_point()
    payload = publish()
    print(f"wrote {PUBLIC_TS} ({len(payload['series'])} points, {payload['live_sync_count']} sync rows)")
    if pt:
        print(f"  latest SPCX ${pt.get('spcx')} TSLA ${pt.get('tsla')} NW ${pt.get('net_worth_b')}B")


if __name__ == "__main__":
    main()
