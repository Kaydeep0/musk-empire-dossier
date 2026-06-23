#!/usr/bin/env python3
"""Post-mortem outcomes after major dates pass.

Captures market + filing evidence, grades vs thesis, logs to timeline, emails once.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
LOG_PATH = os.path.join(DATA, "material_dates_log.jsonl")
OUTCOMES_PATH = os.path.join(DATA, "material_date_outcomes.json")
SENT_PATH = os.path.join(DATA, "material_dates_reminders.json")
ALERTS_LOG = os.path.join(DATA, "filing_alerts.log")
SITE = os.environ.get("MUSK_DOSSIER_URL", "https://kaydeep0.github.io/musk-empire-dossier/")

sys.path.insert(0, HERE)
from material_dates import sync_material_dates, is_major_date, explain_date  # noqa: E402
from date_reminders import log_event  # noqa: E402


def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_sent():
    if os.path.isfile(SENT_PATH):
        try:
            return json.load(open(SENT_PATH, encoding="utf-8"))
        except Exception:
            pass
    return {"sent": [], "passed_logged": [], "outcomes_logged": []}


def _save_sent(state):
    os.makedirs(DATA, exist_ok=True)
    json.dump(state, open(SENT_PATH, "w"), indent=2)


def _spcx_series():
    path = os.path.join(ROOT, "public", "timeseries.json")
    if not os.path.isfile(path):
        return {}
    data = json.load(open(path, encoding="utf-8"))
    out = {}
    for row in data.get("series") or []:
        p = row.get("spcx")
        if p is not None:
            out[row["date"]] = float(p)
    m = (json.load(open(os.path.join(DATA, "spcx_market.json"), encoding="utf-8")).get("market") or {})
    if m.get("price"):
        day = (m.get("as_of_utc") or _utc_now())[:10]
        out[day] = float(m["price"])
    return out


def _price_on_or_near(series, target, max_slip=3):
    if target in series:
        return target, series[target]
    try:
        from datetime import timedelta
        t = datetime.strptime(target, "%Y-%m-%d")
    except ValueError:
        return None, None
    for delta in range(1, max_slip + 1):
        for sign in (-1, 1):
            day = (t + timedelta(days=sign * delta)).strftime("%Y-%m-%d")
            if day in series:
                return day, series[day]
    return None, None


def _filings_since(since_date, entity_hint=""):
    if not os.path.isfile(ALERTS_LOG):
        return []
    out = []
    for line in open(ALERTS_LOG, encoding="utf-8"):
        parts = line.strip().split("\t")
        if len(parts) < 5:
            continue
        fdate = parts[1][:10]
        if fdate >= since_date:
            out.append({
                "date": fdate,
                "form": parts[2],
                "desc": parts[3],
                "url": parts[4],
                "entity": parts[5] if len(parts) > 5 else "",
            })
    return out[-8:]


def _grade_outcome(item, metrics):
    typ = (item.get("type") or "").lower()
    ev = (item.get("event") or "").lower()
    pct_vs_ipo = metrics.get("pct_vs_ipo")
    chg = metrics.get("change_1d_pct")
    filings = metrics.get("new_filings") or []

    if typ == "settlement" or "settlement" in ev:
        bridge_8k = any("8-k" in (f.get("form") or "").lower() for f in filings)
        if bridge_8k:
            return "supports", "New 8-K landed after settlement; watch for bridge payoff language."
        if pct_vs_ipo is not None and pct_vs_ipo >= 0:
            return "neutral", "Price still at or above IPO after refi settlement; no equity supply added."
        return "watch", "Settlement day passed; confirm bridge retirement in next footnotes."

    if "unlock" in ev or "lock-up" in ev:
        if chg is not None and chg <= -3:
            return "contradicts", f"SPCX down {chg:.1f}% into/after unlock window; supply pressure visible."
        if pct_vs_ipo is not None and pct_vs_ipo >= 10:
            return "supports", "Scarcity premium largely held vs $135 IPO despite float step."
        if pct_vs_ipo is not None and pct_vs_ipo < 0:
            return "contradicts", "Price below IPO after unlock step; scarcity thesis under pressure."
        return "watch", "Unlock window active; need volume + Form 4 data over the next week."

    if "bridge" in ev or "maturity" in ev or "cliff" in ev:
        debt_filing = any("8-k" in (f.get("form") or "").lower() for f in filings)
        if debt_filing:
            return "supports", "New debt/refi filing appeared around the cliff date."
        return "watch", "Cliff date passed; monitor credit spreads and refi 8-Ks."

    return "neutral", "Date passed; review filings and price action manually."


def build_outcome(item, today=None):
    today = today or datetime.utcnow().strftime("%Y-%m-%d")
    series = _spcx_series()
    ipo = 135.0
    event_day, price_event = _price_on_or_near(series, item["date"])
    _, price_now = _price_on_or_near(series, today)
    if price_event is None and series:
        price_event = list(series.values())[-1]
        event_day = list(series.keys())[-1]
    if price_now is None:
        price_now = price_event

    metrics = {
        "spcx_event_day": event_day,
        "spcx_price_event": price_event,
        "spcx_price_now": price_now,
        "ipo_price": ipo,
    }
    if price_event:
        metrics["pct_vs_ipo_event"] = round((price_event / ipo - 1) * 100, 1)
    if price_now:
        metrics["pct_vs_ipo"] = round((price_now / ipo - 1) * 100, 1)
    if price_event and price_now:
        metrics["change_1d_pct"] = round((price_now / price_event - 1) * 100, 2)

    filings = _filings_since(item["date"])
    metrics["new_filings"] = filings
    grade, summary = _grade_outcome(item, metrics)
    ctx = item.get("context") or explain_date(item)

    return {
        "date": item["date"],
        "entity": item.get("entity"),
        "type": item.get("type"),
        "event": item.get("event"),
        "hypothesis": item.get("hypothesis"),
        "grade": grade,
        "summary": summary,
        "metrics": metrics,
        "context": ctx,
        "assessed_at": _utc_now(),
    }


def format_outcome_email(outcome):
    m = outcome.get("metrics") or {}
    grade = outcome.get("grade", "neutral").upper()
    title = f"OUTCOME ({grade}): {outcome.get('entity')} — {(outcome.get('event') or '')[:55]}"

    lines = [
        f"The major date has passed: {outcome.get('date')}",
        "",
        "WHAT WE EXPECTED",
        (outcome.get("context") or {}).get("why_it_matters", ""),
        "",
        "WHAT HAPPENED",
        outcome.get("summary", ""),
        "",
        "MARKET SNAPSHOT (basis m)",
    ]
    if m.get("spcx_price_event"):
        lines.append(f"SPCX on event window: ${m['spcx_price_event']} ({m.get('pct_vs_ipo_event', 'n/a')}% vs IPO)")
    if m.get("spcx_price_now"):
        lines.append(f"SPCX now: ${m['spcx_price_now']} ({m.get('pct_vs_ipo', 'n/a')}% vs IPO)")
    if m.get("change_1d_pct") is not None:
        lines.append(f"Move since event snapshot: {m['change_1d_pct']:+.1f}%")

    filings = m.get("new_filings") or []
    if filings:
        lines += ["", "NEW FILINGS SINCE DATE"]
        for f in filings[-4:]:
            lines.append(f"- {f.get('date')} {f.get('form')}: {f.get('desc', '')[:80]}")

    lines += [
        "",
        f"THESIS GRADE: {grade} ({outcome.get('hypothesis', '')})",
        "",
        f"Dossier timeline + calendar: {SITE}",
        "",
        "Logged for longitudinal tracking. Educational only. Not investment advice.",
    ]
    return title, "\n".join(lines)


def format_outcome_html(outcome):
    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    grade = outcome.get("grade", "neutral")
    color = {"supports": "#16a34a", "contradicts": "#dc2626", "watch": "#d97706"}.get(grade, "#666")
    m = outcome.get("metrics") or {}
    ctx = outcome.get("context") or {}
    return f"""<!DOCTYPE html>
<html><body style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:16px;">
<p style="color:{color};font-weight:700;">OUTCOME · {esc(grade.upper())}</p>
<h1 style="font-size:20px;">{esc(outcome.get('entity'))} · {esc(outcome.get('date'))}</h1>
<p>{esc(outcome.get('event'))}</p>
<h2 style="font-size:14px;">What we expected</h2>
<p style="line-height:1.55;">{esc(ctx.get('why_it_matters'))}</p>
<h2 style="font-size:14px;">What happened</h2>
<p style="line-height:1.55;">{esc(outcome.get('summary'))}</p>
<p>SPCX event: ${esc(str(m.get('spcx_price_event')))} · now: ${esc(str(m.get('spcx_price_now')))}</p>
<p style="margin-top:20px;"><a href="{SITE}">Live dossier</a></p>
</body></html>"""


def send_outcome(outcome, force=False):
    state = _load_sent()
    keys = state.setdefault("outcomes_logged", [])
    key = f"outcome|{outcome['date']}|{outcome.get('entity')}|{outcome.get('type')}"
    if key in keys and not force:
        return False

    from notify_channels import alert_all

    subject, body = format_outcome_email(outcome)
    html = format_outcome_html(outcome)
    alert_all(subject, body, html_body=html, priority="high", tags="calendar,outcome")
    keys.append(key)
    _save_sent(state)

    item = {k: outcome.get(k) for k in ("date", "entity", "type", "event", "hypothesis", "context")}
    log_event("date_outcome", item, {
        "grade": outcome.get("grade"),
        "summary": outcome.get("summary"),
        "metrics": outcome.get("metrics"),
    })

    all_outcomes = []
    if os.path.isfile(OUTCOMES_PATH):
        try:
            all_outcomes = json.load(open(OUTCOMES_PATH, encoding="utf-8"))
        except Exception:
            pass
    all_outcomes = [o for o in all_outcomes if o.get("date") != outcome.get("date") or o.get("event") != outcome.get("event")]
    all_outcomes.append(outcome)
    json.dump(all_outcomes, open(OUTCOMES_PATH, "w"), indent=2)
    print(f"outcome sent: {key} [{outcome.get('grade')}]")
    return True


def check_outcomes(today=None, force=False, test_date=None):
    items = sync_material_dates(today)
    sent = 0
    today = today or datetime.utcnow().strftime("%Y-%m-%d")

    for item in items:
        if not is_major_date(item):
            continue
        days = item.get("days_until", 999)
        if test_date:
            if item.get("date") != test_date:
                continue
            days = -1
        elif days not in (-1, -2):
            continue

        outcome = build_outcome(item, today)
        if send_outcome(outcome, force=force or bool(test_date)):
            sent += 1

    return sent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--test-date", help="Simulate outcome for this date")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        items = sync_material_dates()
        for item in items:
            if not is_major_date(item):
                continue
            if item.get("days_until", 0) not in (-1, -2, -3):
                continue
            o = build_outcome(item)
            print(f"\n{o['date']} [{o['grade']}] {o['event'][:60]}")
            print(f"  {o['summary']}")
        return 0

    n = check_outcomes(force=args.force, test_date=args.test_date)
    print(f"outcomes sent: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
