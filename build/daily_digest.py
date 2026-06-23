#!/usr/bin/env python3
"""Once-daily dossier digest: upcoming dates, memory, changelog, 7-day heads-up.

Instant alerts remain for new 8-K/Form 4 briefs and 1/3-day date reminders.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
STATE_PATH = os.path.join(DATA, ".daily_digest.json")
CHANGELOG = os.path.join(ROOT, "public", "CHANGELOG.md")
SITE = os.environ.get("MUSK_DOSSIER_URL", "https://kaydeep0.github.io/musk-empire-dossier/")

sys.path.insert(0, HERE)
from dossier_constants import DIGEST_REMIND_DAYS, SITE as DOSSIER_SITE  # noqa: E402
from material_dates import sync_material_dates, is_major_date, explain_date  # noqa: E402


def _utc_now():
    return datetime.now(timezone.utc)


def _load_state():
    if os.path.isfile(STATE_PATH):
        try:
            return json.load(open(STATE_PATH, encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_state(state):
    os.makedirs(DATA, exist_ok=True)
    json.dump(state, open(STATE_PATH, "w"), indent=2)


def should_send_digest(force=False):
    if os.environ.get("MUSK_DIGEST_DISABLED", "0") == "1":
        return False
    if force or os.environ.get("MUSK_DIGEST_FORCE", "0") == "1":
        return True
    today = _utc_now().strftime("%Y-%m-%d")
    if _load_state().get("last_sent") == today:
        return False
    hour = int(os.environ.get("MUSK_DIGEST_HOUR_UTC", "12"))
    return _utc_now().hour >= hour


def _recent_alerts(hours=24):
    path = os.path.join(DATA, "filing_alerts.log")
    if not os.path.isfile(path):
        return []
    cutoff = _utc_now().timestamp() - hours * 3600
    out = []
    for line in open(path, encoding="utf-8"):
        parts = line.strip().split("\t")
        if len(parts) < 5:
            continue
        try:
            ts = datetime.strptime(parts[0][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if ts.timestamp() >= cutoff:
            out.append({
                "ts": parts[0],
                "date": parts[1],
                "form": parts[2],
                "desc": parts[3],
                "url": parts[4],
                "entity": parts[5] if len(parts) > 5 else "",
            })
    return out[-10:]


def _memory_blurb():
    path = os.path.join(ROOT, "public", "empire_memory.json")
    if not os.path.isfile(path):
        return None
    mem = json.load(open(path, encoding="utf-8"))
    syn = mem.get("synthesis") or {}
    patterns = mem.get("patterns") or []
    emerging = [p for p in patterns if p.get("strength") == "emerging"]
    confirmed = [p for p in patterns if p.get("strength") == "confirmed"]
    top = (emerging or confirmed or patterns[:1])
    pat = top[0] if top else None
    return {
        "narrative": (syn.get("narrative") or "")[:400],
        "pattern": pat,
    }


def _changelog_lines(limit=5):
    if not os.path.isfile(CHANGELOG):
        return []
    lines = [ln.strip() for ln in open(CHANGELOG, encoding="utf-8").readlines() if ln.strip().startswith("- ")]
    return lines[:limit]


def _upcoming_dates(items):
    digest = []
    for item in items:
        if not is_major_date(item):
            continue
        d = item.get("days_until", 999)
        if d < 0:
            continue
        if d in DIGEST_REMIND_DAYS:
            digest.append(item)
    return digest, []


def build_digest_body(items):
    digest_dates, horizon = _upcoming_dates(items)
    alerts = _recent_alerts()
    mem = _memory_blurb()
    changes = _changelog_lines()

    lines = [
        f"MUSK DOSSIER DAILY DIGEST · {_utc_now().strftime('%Y-%m-%d')}",
        "",
        f"Live dossier: {DOSSIER_SITE}",
        "",
    ]

    if digest_dates:
        lines += ["UPCOMING MAJOR DATES (7-day heads-up)", ""]
        for item in digest_dates:
            ctx = item.get("context") or explain_date(item)
            lines += [
                f"• {item['date']} ({item.get('days_until')}d) — {item.get('entity')}",
                f"  {item.get('event')}",
                f"  Why: {ctx.get('why_it_matters', '')[:200]}",
                "",
            ]

    soon = [i for i in items if is_major_date(i) and 0 < i.get("days_until", 999) <= 14]
    if soon:
        lines += ["NEXT 14 DAYS (calendar)", ""]
        for item in soon[:6]:
            lines.append(f"• {item['date']} ({item.get('days_until')}d): {item.get('event')[:70]}")
        lines.append("")

    if alerts:
        lines += ["RECENT SEC FILINGS (24h)", ""]
        for a in alerts[-5:]:
            lines.append(f"• {a.get('form')} {a.get('date')}: {a.get('desc', '')[:70]}")
            lines.append(f"  {a.get('url', '')}")
        lines.append("")

    if mem and mem.get("pattern"):
        p = mem["pattern"]
        lines += [
            "MEMORY AGENT",
            "",
            f"Pattern: {p.get('name')} ({p.get('strength')})",
            (p.get("summary") or "")[:250],
            "",
        ]

    if changes:
        lines += ["SITE UPDATES", ""]
        for c in changes[:4]:
            lines.append(c if c.startswith("-") else f"- {c}")
        lines.append("")

    try:
        from filing_followups import digest_lines, check_followups
        check_followups()
        fu = digest_lines(5)
        if fu:
            lines += ["FOLLOW-UP QUEUE (SpaceX public + Musk personal)", ""]
            for row in fu:
                lines.append(f"• {row}")
            lines.append("")
    except Exception:
        pass

    lines += [
        "Instant alerts still fire for new 8-K/Form 4 briefs and 1/3-day date reminders.",
        "",
        "Educational only. Not investment advice.",
    ]
    return "\n".join(lines)


def build_digest_html(body, items):
    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    sections = ""
    digest_dates, _ = _upcoming_dates(items)
    for item in digest_dates:
        ctx = item.get("context") or explain_date(item)
        sections += f"""
<div style="margin:16px 0;padding:12px;background:#f8fafc;border-radius:8px;">
  <div style="font-weight:700;">{esc(item.get('date'))} · {esc(item.get('entity'))}</div>
  <div style="margin:6px 0;">{esc(item.get('event'))}</div>
  <div style="font-size:14px;color:#555;line-height:1.5;">{esc(ctx.get('why_it_matters', ''))}</div>
</div>"""

    return f"""<!DOCTYPE html>
<html><body style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:16px;">
<p style="color:#2563eb;font-weight:600;">DAILY DOSSIER DIGEST</p>
<p>{esc(_utc_now().strftime('%A %B %d, %Y'))}</p>
{sections or '<p>No 7-day heads-up dates today. See live calendar on site.</p>'}
<p style="margin-top:20px;"><a href="{DOSSIER_SITE}">Open live dossier</a></p>
<p style="font-size:12px;color:#888;">Educational only. Not investment advice.</p>
</body></html>"""


def send_digest(force=False):
    if not should_send_digest(force=force):
        print("digest skipped (already sent today or before digest hour)")
        return False

    items = sync_material_dates()
    body = build_digest_body(items)
    html = build_digest_html(body, items)
    subject = f"Musk dossier daily · {_utc_now().strftime('%Y-%m-%d')}"

    from notify_channels import alert_all

    alert_all(subject, body, html_body=html, priority="default", tags="digest,memo")
    _save_state({"last_sent": _utc_now().strftime("%Y-%m-%d"), "sent_at": _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")})
    print(f"digest sent: {subject}")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="Send even if already sent today")
    ap.add_argument("--preview", action="store_true", help="Print digest without sending")
    args = ap.parse_args()

    items = sync_material_dates()
    if args.preview:
        print(build_digest_body(items))
        return 0

    ok = send_digest(force=args.force)
    return 0 if ok or not should_send_digest(force=args.force) else 0


if __name__ == "__main__":
    sys.exit(main())
