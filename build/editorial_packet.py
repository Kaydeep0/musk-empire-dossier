#!/usr/bin/env python3
"""Single editorial email per material filing: brief + LinkedIn + calendar + follow-up.

Public content still requires human approval (copy-paste from email).
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
QUEUE_PATH = os.path.join(DATA, "ship_queue.json")
SITE = os.environ.get("MUSK_DOSSIER_URL", "https://kaydeep0.github.io/musk-empire-dossier/")

sys.path.insert(0, HERE)
from dossier_constants import LINKEDIN_FORMS, SITE as DOSSIER_SITE  # noqa: E402


def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ascii(s):
    return (s or "").encode("ascii", "replace").decode("ascii")


def _next_material_date():
    try:
        from material_dates import sync_material_dates, is_major_date
        items = sync_material_dates()
        for item in items:
            if is_major_date(item) and item.get("days_until", -1) >= 0:
                ctx = item.get("context") or {}
                return item, ctx.get("why_it_matters", "")[:220]
    except Exception:
        pass
    return None, ""


def _linkedin_post(brief, form):
    from linkedin_alert import compose_post

    reason = "8-K material event"
    if form.startswith("4"):
        reason = "Form 4 insider filing"
    elif "DEF" in form:
        reason = "proxy filing"
    post = compose_post(reason)
    os.makedirs(DATA, exist_ok=True)
    open(os.path.join(DATA, "linkedin_post_latest.txt"), "w", encoding="utf-8").write(post)
    return post


def _brief_sections_plain(brief):
    from filing_analysis import _section_plain, DISCLAIMER

    sections = [
        ("WHAT HAPPENED", brief["summary"]),
        ("TRADER (price / positioning)", brief["trader"]),
        ("DEMAND & SUPPLY", brief["supply_demand"]),
        ("ELON (personal / control)", brief["elon"]),
    ]
    parts = []
    for title, body in sections:
        parts.append(_section_plain(title, body))
    parts.append(DISCLAIMER)
    return "\n".join(parts)


def _queue_item(brief, linkedin_post, form):
    acc = brief.get("accession") or "unknown"
    item_id = re.sub(r"[^\w-]", "_", acc)
    item = {
        "id": item_id,
        "status": "draft",
        "accession": brief.get("accession"),
        "entity": brief.get("entity"),
        "form": form,
        "filing_date": brief.get("filing_date"),
        "created_utc": _utc_now(),
        "linkedin_post": linkedin_post,
        "brief_headline": (brief.get("summary") or "").split("\n")[0][:120],
        "public_actions": ["linkedin"] if linkedin_post else [],
        "approve_hint": "Copy LinkedIn block to post if approved. Reply SKIP to discard.",
    }
    state = {"updated": _utc_now(), "items": []}
    if os.path.isfile(QUEUE_PATH):
        try:
            state = json.load(open(QUEUE_PATH, encoding="utf-8"))
        except Exception:
            pass
    items = [i for i in state.get("items", []) if i.get("id") != item_id]
    items.insert(0, item)
    state["items"] = items[:20]
    state["updated"] = _utc_now()
    os.makedirs(DATA, exist_ok=True)
    json.dump(state, open(QUEUE_PATH, "w"), indent=2)
    return item


def build_packet(brief, form_desc, include_linkedin=True):
    form = brief.get("form") or ""
    linkedin = None
    if include_linkedin and form in LINKEDIN_FORMS:
        linkedin = _linkedin_post(brief, form)

    next_ev, next_why = _next_material_date()
    try:
        from filing_followups import followup_watch_lines
        watch = followup_watch_lines(brief.get("accession"))
    except Exception:
        watch = []

    subject = f"EDITORIAL PACKET: {brief.get('entity')} {form} ({brief.get('filing_date')})"

    lines = [
        "EDITORIAL PACKET · read before anything goes public",
        "",
        f"{brief.get('entity')} | {form} | {brief.get('filing_date')}",
        form_desc,
        "",
        "=" * 50,
        "NEEDS YOU (public)",
        "=" * 50,
        "",
    ]

    if linkedin:
        lines += [
            "Copy-paste to LinkedIn if you approve:",
            "",
            linkedin,
            "",
            "(Skip posting if you reply SKIP or ignore this block.)",
            "",
        ]
    else:
        lines += ["No LinkedIn draft for this form type.", ""]

    lines += [
        "=" * 50,
        "FILING BRIEF",
        "=" * 50,
        "",
        _brief_sections_plain(brief),
        "",
    ]

    if next_ev:
        lines += [
            "=" * 50,
            "NEXT DATED TEST",
            "=" * 50,
            "",
            f"{next_ev.get('date')} ({next_ev.get('days_until')}d): {next_ev.get('event')}",
            next_why,
            "",
        ]

    if watch:
        lines += [
            "=" * 50,
            "FOLLOW-UP WATCH (24h eyes)",
            "=" * 50,
            "",
        ]
        lines.extend(watch)
        lines.append("")

    lines += [
        "=" * 50,
        "SOURCES",
        "=" * 50,
        "",
        f"EDGAR: {brief.get('url')}",
        f"Dossier: {brief.get('dossier_url', DOSSIER_SITE)}",
        f"Ship queue: {QUEUE_PATH}",
        "",
        "Educational only. Not investment advice.",
    ]

    plain = "\n".join(lines)
    html = _packet_html(brief, form_desc, linkedin, next_ev, next_why, watch)
    return subject, plain, html, linkedin


def _packet_html(brief, form_desc, linkedin, next_ev, next_why, watch):
    def esc(s):
        return _ascii(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>\n")

    li_block = ""
    if linkedin:
        li_block = f"""
<h2 style="font-size:14px;color:#2563eb;margin-top:24px;">Needs you: LinkedIn (copy if approved)</h2>
<pre style="white-space:pre-wrap;font-family:inherit;font-size:14px;line-height:1.5;background:#f8fafc;padding:12px;border-radius:8px;">{esc(linkedin)}</pre>"""

    next_block = ""
    if next_ev:
        next_block = f"""
<h2 style="font-size:14px;margin-top:20px;">Next dated test</h2>
<p><strong>{esc(next_ev.get('date'))}</strong> ({esc(str(next_ev.get('days_until')))}d): {esc(next_ev.get('event'))}</p>
<p style="color:#555;">{esc(next_why)}</p>"""

    watch_block = ""
    if watch:
        watch_block = "<h2 style=\"font-size:14px;margin-top:20px;\">Follow-up watch</h2><ul>"
        for w in watch:
            watch_block += f"<li>{esc(w)}</li>"
        watch_block += "</ul>"

    trader = esc(brief.get("trader", ""))
    supply = esc(brief.get("supply_demand", ""))
    summary = esc(brief.get("summary", ""))

    return f"""<!DOCTYPE html>
<html><body style="font-family:-apple-system,sans-serif;max-width:600px;margin:0 auto;padding:16px;">
<p style="color:#2563eb;font-weight:700;letter-spacing:.04em;">EDITORIAL PACKET</p>
<h1 style="font-size:20px;">{esc(brief.get('entity'))} · {esc(brief.get('form'))}</h1>
<p style="color:#666;">{esc(brief.get('filing_date'))} · {esc(form_desc)}</p>
{li_block}
<h2 style="font-size:14px;margin-top:24px;">What happened</h2>
<p style="line-height:1.55;">{summary}</p>
<h2 style="font-size:14px;">Trader</h2>
<p style="line-height:1.55;">{trader}</p>
<h2 style="font-size:14px;">Demand &amp; supply</h2>
<p style="line-height:1.55;">{supply}</p>
{next_block}
{watch_block}
<p style="margin-top:24px;"><a href="{esc(brief.get('url'))}">EDGAR filing</a> · <a href="{DOSSIER_SITE}">Live dossier</a></p>
<p style="font-size:12px;color:#888;">Educational only. Not investment advice.</p>
</body></html>"""


def send_editorial_packet(brief, form_desc, filing=None, sms_teaser_fn=None):
    """Send unified editorial email and update ship queue."""
    if not brief:
        return False
    form = brief.get("form") or (filing or {}).get("form", "")
    subject, plain, html, linkedin = build_packet(brief, form_desc)
    _queue_item(brief, linkedin, form)

    sms = None
    if sms_teaser_fn:
        sms = sms_teaser_fn(brief)
    elif linkedin:
        hook = linkedin.split("\n")[0].replace("🔴 ", "")[:90]
        sms = f"EDITORIAL: {hook}\nDossier: {DOSSIER_SITE}"

    from notify_channels import alert_all

    alert_all(subject, plain, html_body=html, priority="high", tags="editorial,memo", sms_body=sms)
    print(f"editorial packet sent: {subject[:60]}")
    return True


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-spcx", action="store_true")
    args = ap.parse_args()
    if args.test_spcx:
        from filing_analysis import build_brief, sms_teaser
        filing = {
            "url": "https://www.sec.gov/Archives/edgar/data/1181412/000162828026044955/spcx-pricing8xk.htm",
            "form": "8-K",
            "filingDate": "2026-06-23",
            "accession": "0001628280-26-044955",
        }
        brief = build_brief("Space Exploration Technologies (SPCX)", filing)
        from filing_analysis import save_brief
        save_brief(brief)
        send_editorial_packet(brief, "Material event report", filing, sms_teaser)
