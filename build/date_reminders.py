#!/usr/bin/env python3
"""Context-rich reminders for major material dates (1 day before, 7 days for supply).

Logs every alert to data/material_dates_log.jsonl so the dossier builds a
longitudinal record of how catalysts evolved.
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
SENT_PATH = os.path.join(DATA, "material_dates_reminders.json")
SITE = os.environ.get("MUSK_DOSSIER_URL", "https://kaydeep0.github.io/musk-empire-dossier/")

sys.path.insert(0, HERE)
from dossier_constants import INSTANT_REMIND_DAYS  # noqa: E402
from material_dates import sync_material_dates, explain_date, is_major_date  # noqa: E402


def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_sent():
    if os.path.isfile(SENT_PATH):
        try:
            return json.load(open(SENT_PATH, encoding="utf-8"))
        except Exception:
            pass
    return {"sent": []}


def _save_sent(state):
    os.makedirs(DATA, exist_ok=True)
    json.dump(state, open(SENT_PATH, "w"), indent=2)


def _reminder_key(item, days_before):
    return f"{item['date']}|{days_before}|{item.get('entity')}|{item.get('type')}|{(item.get('event') or '')[:48]}"


def log_event(kind, item, extra=None):
    os.makedirs(DATA, exist_ok=True)
    row = {
        "ts": _utc_now(),
        "kind": kind,
        "date": item.get("date"),
        "entity": item.get("entity"),
        "type": item.get("type"),
        "event": item.get("event"),
        "hypothesis": item.get("hypothesis"),
        "days_until": item.get("days_until"),
        "context": item.get("context"),
    }
    if extra:
        row.update(extra)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def format_reminder_email(item, days_before):
    ctx = item.get("context") or explain_date(item)
    when = "TOMORROW" if days_before == 1 else f"IN {days_before} DAYS"
    title = f"{when}: {item.get('entity')} — {(item.get('event') or '')[:70]}"

    lines = [
        f"Material date reminder ({item.get('date')})",
        "",
        f"WHAT THIS IS",
        ctx.get("what_it_is", ""),
        "",
        f"WHY IT MATTERS",
        ctx.get("why_it_matters", ""),
        "",
        f"WHAT TO WATCH",
        ctx.get("what_to_watch", ""),
        "",
        f"THESIS LINK",
        f"{item.get('hypothesis', 'n/a')}: {ctx.get('thesis_note', '')}",
        "",
    ]
    if item.get("url"):
        lines += ["SEC filing:", item["url"], ""]
    if item.get("source"):
        lines += ["Source doc:", item["source"], ""]
    lines += [
        f"Live dossier (calendar, charts, memory): {SITE}",
        "",
        "This alert is logged in the dossier timeline for longitudinal tracking.",
        "",
        "Educational only. Not investment advice.",
    ]
    return title, "\n".join(lines)


def format_reminder_html(item, days_before):
    ctx = item.get("context") or explain_date(item)
    when = "Tomorrow" if days_before == 1 else f"In {days_before} days"
    title = f"{when}: {item.get('entity')}"

    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:16px;">
  <p style="color:#2563eb;font-size:12px;font-weight:600;">MATERIAL DATE REMINDER</p>
  <h1 style="font-size:20px;line-height:1.3;">{esc(title)}</h1>
  <p style="color:#666;">{esc(item.get('date'))} · {esc(item.get('event'))}</p>
  <h2 style="font-size:14px;margin-top:20px;">What this is</h2>
  <p style="line-height:1.55;">{esc(ctx.get('what_it_is'))}</p>
  <h2 style="font-size:14px;">Why it matters</h2>
  <p style="line-height:1.55;">{esc(ctx.get('why_it_matters'))}</p>
  <h2 style="font-size:14px;">What to watch</h2>
  <p style="line-height:1.55;">{esc(ctx.get('what_to_watch'))}</p>
  <h2 style="font-size:14px;">Thesis link</h2>
  <p style="line-height:1.55;">{esc(item.get('hypothesis'))}: {esc(ctx.get('thesis_note'))}</p>
  <p style="margin-top:20px;"><a href="{SITE}">Live dossier</a></p>
  <p style="font-size:12px;color:#888;">Educational only. Not investment advice.</p>
</body></html>"""


def send_reminder(item, days_before, force=False):
    state = _load_sent()
    key = _reminder_key(item, days_before)
    if key in state["sent"] and not force:
        return False

    from notify_channels import alert_all

    subject, body = format_reminder_email(item, days_before)
    html = format_reminder_html(item, days_before)
    sms = (
        f"{subject[:80]}\n"
        f"{(item.get('context') or explain_date(item)).get('why_it_matters', '')[:120]}\n"
        f"{SITE}"
    )
    alert_all(subject, body, html_body=html, sms_body=sms, priority="high", tags="calendar,memo")
    state["sent"].append(key)
    _save_sent(state)
    log_event("reminder_sent", item, {"days_before": days_before, "reminder_key": key})
    print(f"reminder sent: {key}")
    return True


def log_passed_dates(items, today=None):
    """After a major date passes, log once for the dossier timeline."""
    today = today or datetime.utcnow().strftime("%Y-%m-%d")
    state = _load_sent()
    passed_keys = state.setdefault("passed_logged", [])
    for item in items:
        if not is_major_date(item):
            continue
        if item.get("days_until", 0) != -1:
            continue
        key = f"passed|{item['date']}|{item.get('entity')}|{item.get('type')}"
        if key in passed_keys:
            continue
        log_event("date_passed", item, {"note": "Major date has passed; check filings and price action."})
        passed_keys.append(key)
    _save_sent(state)


def check_reminders(today=None, force=False, test_date=None):
    items = sync_material_dates(today)
    sent = 0

    if test_date:
        for item in items:
            if item.get("date") == test_date and is_major_date(item):
                fake = dict(item)
                fake["days_until"] = 1
                if send_reminder(fake, 1, force=True):
                    sent += 1
        return sent

    for item in items:
        if not is_major_date(item):
            continue
        days = item.get("days_until", 999)
        remind_at = item.get("remind_instant") or sorted(
            set(item.get("remind_days") or [1, 3]) & INSTANT_REMIND_DAYS
        ) or [1, 3]
        for offset in remind_at:
            if days == offset:
                if send_reminder(item, offset, force=force):
                    sent += 1

    log_passed_dates(items, today)
    return sent


def main():
    ap = argparse.ArgumentParser(description="Send contextual material-date reminders")
    ap.add_argument("--force", action="store_true", help="Resend even if already sent")
    ap.add_argument("--test-date", help="Simulate 1-day reminder for this ISO date (e.g. 2026-08-20)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        items = sync_material_dates()
        for item in items:
            if not is_major_date(item):
                continue
            ctx = item.get("context") or explain_date(item)
            print(f"\n{item['date']} ({item.get('days_until')}d) {item.get('type')} remind={item.get('remind_days')}")
            print(f"  {item['event'][:70]}")
            print(f"  -> {ctx.get('why_it_matters', '')[:100]}...")
        return 0

    n = check_reminders(force=args.force, test_date=args.test_date)
    print(f"reminders sent: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
