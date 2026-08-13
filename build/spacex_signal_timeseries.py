#!/usr/bin/env python3
"""
SpaceX / SPCX daily time series: SEC events × price × inventory (float unlocks).

Tracks how the scarcity premium is tested as lock-up inventory becomes free to trade.

  data/spacex_signal_timeseries.json   — ledger
  data/spacex_signal_timeseries.jsonl  — append log

  python3 build/spacex_signal_timeseries.py --upsert
  python3 build/spacex_signal_timeseries.py --backfill
  python3 build/spacex_signal_timeseries.py --print
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data"
STORE = DATA / "spacex_signal_timeseries.json"
LOG = DATA / "spacex_signal_timeseries.jsonl"
SPCX_MARKET = DATA / "spcx_market.json"
SPACEX_EVENTS = DATA / "spacex_events.json"
MATERIAL = DATA / "material_dates.json"
FILING_LOG = DATA / "filing_alerts.log"
PUBLIC_OUT = ROOT / "public" / "spacex_timeseries.json"

UA = "Watts Advisor research kiran@conformingcredit.org"
IPO_PRICE = 135.0
IPO_DATE = "2026-06-13"
# Tradable float % of company (filing-backed ladder; V5 lock-up calendar).
# Each step is cumulative inventory free to trade after that date.
FLOAT_LADDER = [
    {"date": IPO_DATE, "float_pct": 4.86, "label": "IPO float (~4.86%)", "basis": "b"},
    {
        "date": "2026-08-20",
        "float_pct": 9.72,
        "label": "First major lock-up unlock (~7% pool; float ~doubles)",
        "basis": "b",
    },
    {
        "date": "2026-12-08",
        "float_pct": 15.0,
        "label": "Remainder 180-day lock-up release (est. cumulative float)",
        "basis": "b",
        "estimate": True,
    },
    {
        "date": "2027-06-16",
        "float_pct": 42.0,
        "label": "Musk block unlock (~6.4B shares, largest tranche; est. cumulative)",
        "basis": "b",
        "estimate": True,
    },
]
SPARK = "▁▂▃▄▅▆▇█"


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load_store() -> dict:
    if STORE.exists():
        try:
            return json.loads(STORE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "updated_utc": None,
        "ticker": "SPCX",
        "ipo_price": IPO_PRICE,
        "ipo_date": IPO_DATE,
        "status": "research_only",
        "note": (
            "Daily SPCX price + cumulative tradable float (inventory free to trade) "
            "+ SEC events. Grades the Aug 20 unlock test and later supply steps."
        ),
        "float_ladder": FLOAT_LADDER,
        "series": [],
    }


def _save_store(store: dict) -> None:
    store["updated_utc"] = utcnow()
    store["float_ladder"] = FLOAT_LADDER
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(store, indent=2), encoding="utf-8")
    try:
        PUBLIC_OUT.parent.mkdir(parents=True, exist_ok=True)
        PUBLIC_OUT.write_text(json.dumps(store, indent=2), encoding="utf-8")
    except Exception:
        pass


def _append_log(row: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def float_state(asof: str) -> dict:
    """Cumulative unlocked float % and next inventory-freeing step as of asof."""
    active = None
    next_step = None
    for step in FLOAT_LADDER:
        if step["date"] <= asof:
            active = step
        elif next_step is None:
            next_step = step
    if active is None:
        active = {"date": asof, "float_pct": 0.0, "label": "pre-IPO", "basis": "c"}
    days_to_next = None
    if next_step:
        try:
            days_to_next = (date.fromisoformat(next_step["date"]) - date.fromisoformat(asof)).days
        except Exception:
            days_to_next = None
    return {
        "float_pct": float(active.get("float_pct") or 0),
        "float_label": active.get("label"),
        "float_step_date": active.get("date"),
        "float_estimate": bool(active.get("estimate")),
        "next_unlock_date": (next_step or {}).get("date"),
        "next_unlock_label": (next_step or {}).get("label"),
        "next_unlock_float_pct": (next_step or {}).get("float_pct"),
        "days_to_next_unlock": days_to_next,
    }


def _pct(a, b):
    if a is None or b in (None, 0):
        return None
    try:
        return round(100.0 * (float(a) - float(b)) / float(b), 2)
    except Exception:
        return None


def sparkline(closes: list, *, width: int = 14) -> str:
    vals = [float(x) for x in closes if x is not None]
    if len(vals) < 2:
        return "." if vals else "-"
    if len(vals) > width:
        step = (len(vals) - 1) / (width - 1)
        vals = [vals[int(round(i * step))] for i in range(width)]
    lo, hi = min(vals), max(vals)
    if hi <= lo:
        return SPARK[0] * len(vals)
    out = []
    for v in vals:
        idx = int(round((v - lo) / (hi - lo) * (len(SPARK) - 1)))
        out.append(SPARK[max(0, min(len(SPARK) - 1, idx))])
    return "".join(out)


def fetch_spcx_history(range_: str = "3mo") -> list[dict]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/SPCX?interval=1d&range={range_}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = json.loads(urllib.request.urlopen(req, timeout=30).read())
    r = raw["chart"]["result"][0]
    ts = r["timestamp"]
    closes = r["indicators"]["quote"][0]["close"]
    vols = (r["indicators"]["quote"][0].get("volume") or [None] * len(ts))
    out = []
    for t, c, v in zip(ts, closes, vols):
        if c is None:
            continue
        out.append(
            {
                "date": datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d"),
                "price": round(float(c), 2),
                "volume": int(v) if v is not None else None,
            }
        )
    return out


def load_market_snapshot() -> dict | None:
    if not SPCX_MARKET.exists():
        return None
    try:
        return (json.loads(SPCX_MARKET.read_text(encoding="utf-8")) or {}).get("market")
    except Exception:
        return None


def sec_events_for_day(asof: str) -> list[dict]:
    """SEC / material events on this calendar day (SpaceX/SPCX focused)."""
    events: list[dict] = []
    if SPACEX_EVENTS.exists():
        try:
            data = json.loads(SPACEX_EVENTS.read_text(encoding="utf-8"))
            for e in data.get("events") or []:
                if (e.get("filing_date") or "")[:10] == asof:
                    events.append(
                        {
                            "kind": "spacex_8k",
                            "form": e.get("form") or "8-K",
                            "label": e.get("event") or "SpaceX filing",
                            "url": e.get("url"),
                            "accession": e.get("accession"),
                            "bond_offering": bool(e.get("bond_offering")),
                        }
                    )
            latest = data.get("latest_8k") or {}
            if (latest.get("filingDate") or "")[:10] == asof:
                if not any(x.get("accession") == latest.get("accession") for x in events):
                    events.append(
                        {
                            "kind": "spacex_8k",
                            "form": latest.get("form") or "8-K",
                            "label": f"Latest SpaceX {latest.get('form')}",
                            "url": latest.get("url"),
                            "accession": latest.get("accession"),
                        }
                    )
        except Exception:
            pass

    if MATERIAL.exists():
        try:
            for item in json.loads(MATERIAL.read_text(encoding="utf-8")):
                ent = (item.get("entity") or "").upper()
                if "SPCX" not in ent and "SPACE" not in ent:
                    continue
                if (item.get("date") or "")[:10] == asof:
                    events.append(
                        {
                            "kind": "calendar",
                            "form": item.get("type") or "date",
                            "label": item.get("event"),
                            "url": item.get("url"),
                            "major": bool(item.get("major")),
                        }
                    )
        except Exception:
            pass

    if FILING_LOG.exists():
        try:
            for line in FILING_LOG.read_text(encoding="utf-8").splitlines():
                parts = line.strip().split("\t")
                if len(parts) < 5:
                    continue
                # ts, date, form, desc, url, entity?
                fdate = parts[1][:10]
                if fdate != asof:
                    continue
                blob = " ".join(parts[2:]).upper()
                if "SPCX" not in blob and "SPACE" not in blob and "1181412" not in blob:
                    # still capture Musk Form 4s around unlock windows as inventory-adjacent
                    if "FORM 4" in blob or parts[2] in {"4", "4/A"}:
                        events.append(
                            {
                                "kind": "musk_form4",
                                "form": parts[2],
                                "label": parts[3][:120],
                                "url": parts[4],
                                "entity": parts[5] if len(parts) > 5 else "Musk",
                            }
                        )
                    continue
                events.append(
                    {
                        "kind": "alert",
                        "form": parts[2],
                        "label": parts[3][:120],
                        "url": parts[4],
                        "entity": parts[5] if len(parts) > 5 else "",
                    }
                )
        except Exception:
            pass

    # de-dupe by label+form
    seen = set()
    out = []
    for e in events:
        key = (e.get("form"), (e.get("label") or "")[:80], e.get("accession") or e.get("url"))
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def _row_for_day(*, asof: str, price: float | None, volume: int | None = None, ath: float | None = None) -> dict:
    fs = float_state(asof)
    events = sec_events_for_day(asof)
    unlock_today = any(
        e.get("kind") == "calendar" and "unlock" in (e.get("label") or "").lower() for e in events
    ) or (fs.get("float_step_date") == asof and asof != IPO_DATE)
    return {
        "date": asof,
        "price": price,
        "volume": volume,
        "pct_vs_ipo": _pct(price, IPO_PRICE),
        "pct_vs_ath": _pct(price, ath) if ath else None,
        "ath_ref": ath,
        **fs,
        "inventory_freeing_today": bool(unlock_today),
        "sec_event_count": len(events),
        "sec_events": events[:8],
        "sec_headline": (events[0].get("label") if events else None),
    }


def upsert_day(store: dict, row: dict) -> dict:
    series = store.setdefault("series", [])
    asof = row["date"]
    if series and series[-1].get("date") == asof:
        series[-1] = {**series[-1], **row}
    else:
        # keep sorted
        series.append(row)
        series.sort(key=lambda r: r.get("date") or "")
        # collapse dupes
        by_date = {}
        for r in series:
            by_date[r["date"]] = r
        store["series"] = [by_date[k] for k in sorted(by_date)]
    return row


def upsert_from_live(*, asof: str | None = None) -> dict:
    """One daily point from spcx_market.json + SEC/calendar context. Returns store."""
    store = _load_store()
    asof = asof or today_utc()
    mkt = load_market_snapshot() or {}
    price = mkt.get("price")
    ath = mkt.get("ath_price")
    volume = None
    # Prefer Yahoo history for exact asof close when available
    try:
        hist = fetch_spcx_history("5d")
        for h in reversed(hist):
            if h["date"] <= asof:
                price = h["price"]
                volume = h.get("volume")
                break
    except Exception:
        pass
    row = _row_for_day(asof=asof, price=price, volume=volume, ath=ath)
    upsert_day(store, row)
    _save_store(store)
    _append_log({**row, "logged_utc": utcnow()})
    return store


def upsert_today(*, asof: str | None = None) -> dict:
    """Compatibility helper: upsert and return the day's row."""
    store = upsert_from_live(asof=asof)
    series = store.get("series") or []
    return series[-1] if series else {}


def backfill(range_: str = "3mo") -> dict:
    """Backfill daily closes + float state + SEC events from IPO window."""
    store = _load_store()
    hist = fetch_spcx_history(range_)
    ath = max((h["price"] for h in hist), default=None)
    mkt = load_market_snapshot() or {}
    if mkt.get("ath_price"):
        ath = max(ath or 0, float(mkt["ath_price"])) or ath
    for h in hist:
        if h["date"] < IPO_DATE:
            continue
        row = _row_for_day(
            asof=h["date"],
            price=h["price"],
            volume=h.get("volume"),
            ath=ath,
        )
        upsert_day(store, row)
    # Ensure today exists even if Yahoo lagging
    today = today_utc()
    if not any(r.get("date") == today for r in store.get("series") or []):
        mkt = load_market_snapshot() or {}
        if mkt.get("price"):
            upsert_day(
                store,
                _row_for_day(asof=today, price=mkt.get("price"), ath=mkt.get("ath_price") or ath),
            )
    _save_store(store)
    return store


def tracker_table(store: dict | None = None, *, limit: int = 14) -> list[dict]:
    store = store or _load_store()
    series = list(store.get("series") or [])
    if not series:
        return []
    closes = [r.get("price") for r in series]
    spark = sparkline(closes)
    # return most recent first for email
    rows = []
    for r in reversed(series[-limit:]):
        rows.append({**r, "sparkline_full": spark})
    return rows


def scorecard(store: dict | None = None) -> dict:
    store = store or _load_store()
    series = store.get("series") or []
    if not series:
        return {"plain": "SpaceX tracker: no daily points yet."}
    last = series[-1]
    first = series[0]
    fs = float_state(last.get("date") or today_utc())
    plain = (
        f"SPCX tracker: ${last.get('price')} · {last.get('pct_vs_ipo'):+.1f}% vs IPO ${IPO_PRICE} · "
        f"tradable float ~{fs.get('float_pct')}% ({fs.get('float_label')})"
    )
    if fs.get("next_unlock_date"):
        plain += (
            f" · next inventory free-up {fs.get('next_unlock_date')} "
            f"({fs.get('days_to_next_unlock')}d → ~{fs.get('next_unlock_float_pct')}% float)"
        )
    # since first major unlock if past
    unlock = next((s for s in FLOAT_LADDER if s["date"] == "2026-08-20"), None)
    if unlock and last.get("date") >= unlock["date"]:
        pre = [r for r in series if r.get("date") < unlock["date"] and r.get("price")]
        post = [r for r in series if r.get("date") >= unlock["date"] and r.get("price")]
        if pre and post:
            plain += (
                f" · since Aug-20 unlock: {_pct(post[-1]['price'], pre[-1]['price']):+.1f}% "
                f"(price vs last close before unlock)"
            )
    elif fs.get("days_to_next_unlock") is not None and fs.get("next_unlock_date") == "2026-08-20":
        plain += " · Aug-20 unlock test not graded yet (date still ahead)"
    return {
        "plain": plain,
        "last": last,
        "first": first,
        "float": fs,
        "n_days": len(series),
    }


def format_digest_section(store: dict | None = None, *, limit: int = 10) -> str:
    store = store or _load_store()
    sc = scorecard(store)
    rows = tracker_table(store, limit=limit)
    lines = [
        "SPCX TIME SERIES — price × SEC × inventory (float unlocks)",
        "",
        sc.get("plain") or "",
        "",
        f"{'Date':<12} {'Price':>8} {'vsIPO':>7} {'Float%':>7} {'Inv':>4} {'SEC':>3}  Event",
    ]
    for r in rows:
        inv = "YES" if r.get("inventory_freeing_today") else "-"
        lines.append(
            f"{r.get('date'):<12} "
            f"${r.get('price') if r.get('price') is not None else '-':>7} "
            f"{(str(r.get('pct_vs_ipo'))+'%') if r.get('pct_vs_ipo') is not None else '-':>7} "
            f"{r.get('float_pct') if r.get('float_pct') is not None else '-':>7} "
            f"{inv:>4} "
            f"{r.get('sec_event_count') or 0:>3}  "
            f"{(r.get('sec_headline') or '-')[:48]}"
        )
    lines += [
        "",
        "Inv=YES means a lock-up / float step lands that day (inventory free to trade).",
        "Float% is cumulative tradable share of the company from the V5 lock-up ladder.",
        "Research only — not investment advice.",
    ]
    return "\n".join(lines)


def format_digest_html(store: dict | None = None, *, limit: int = 10) -> str:
    store = store or _load_store()
    sc = scorecard(store)
    rows = tracker_table(store, limit=limit)

    def esc(s):
        return (
            str(s or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    trs = []
    for r in rows:
        inv = "YES" if r.get("inventory_freeing_today") else "—"
        bg = "background:#fff7ed;" if r.get("inventory_freeing_today") else ""
        price = f"${r.get('price')}" if r.get("price") is not None else "—"
        vs_ipo = f"{r.get('pct_vs_ipo')}%" if r.get("pct_vs_ipo") is not None else "—"
        flt = f"{r.get('float_pct')}%" if r.get("float_pct") is not None else "—"
        trs.append(
            f"<tr style=\"{bg}\">"
            f"<td style=\"padding:6px 8px\">{esc(r.get('date'))}</td>"
            f"<td style=\"padding:6px 8px;text-align:right\">{esc(price)}</td>"
            f"<td style=\"padding:6px 8px;text-align:right\">{esc(vs_ipo)}</td>"
            f"<td style=\"padding:6px 8px;text-align:right\">{esc(flt)}</td>"
            f"<td style=\"padding:6px 8px;text-align:center\">{esc(inv)}</td>"
            f"<td style=\"padding:6px 8px;text-align:right\">{esc(r.get('sec_event_count') or 0)}</td>"
            f"<td style=\"padding:6px 8px;font-size:12px\">{esc((r.get('sec_headline') or '—')[:64])}</td>"
            "</tr>"
        )
    return f"""
<div style="margin:18px 0;padding:14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
  <div style="font-weight:700;margin-bottom:6px;">SPCX time series — price × SEC × inventory</div>
  <p style="margin:0 0 12px;font-size:14px;line-height:1.45;color:#334155;">{esc(sc.get('plain'))}</p>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <thead><tr style="border-bottom:2px solid #0f172a;text-align:left;">
      <th style="padding:6px 8px;">Date</th>
      <th style="padding:6px 8px;text-align:right;">Price</th>
      <th style="padding:6px 8px;text-align:right;">vs IPO</th>
      <th style="padding:6px 8px;text-align:right;">Float%</th>
      <th style="padding:6px 8px;text-align:center;">Inv free</th>
      <th style="padding:6px 8px;text-align:right;">SEC</th>
      <th style="padding:6px 8px;">Event</th>
    </tr></thead>
    <tbody>{''.join(trs)}</tbody>
  </table>
  <p style="margin:10px 0 0;font-size:12px;color:#64748b;">
    Inv free = lock-up / float step that day. Float% = cumulative tradable inventory from V5 calendar.
  </p>
</div>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="SpaceX SPCX price × SEC × float unlock time series")
    ap.add_argument("--upsert", action="store_true", help="Append/refresh today's point")
    ap.add_argument("--backfill", action="store_true", help="Backfill from Yahoo + calendar")
    ap.add_argument("--print", action="store_true", help="Print digest section")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    store = _load_store()
    if args.backfill:
        store = backfill()
        print(f"backfill days={len(store.get('series') or [])} -> {STORE}")
    if args.upsert or not (args.backfill or args.print or args.json):
        store = upsert_from_live()
        last = (store.get("series") or [{}])[-1]
        print(
            f"upsert {last.get('date')} SPCX ${last.get('price')} "
            f"float={last.get('float_pct')}% sec={last.get('sec_event_count')}"
        )
    if args.print:
        print(format_digest_section(store))
    if args.json:
        print(json.dumps(scorecard(store), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
