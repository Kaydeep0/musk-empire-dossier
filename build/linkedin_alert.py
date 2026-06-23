#!/usr/bin/env python3
"""Send ntfy alert + save LinkedIn draft when the live site is updated."""
import json
import os
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
DRAFT = os.path.join(DATA, "linkedin_draft_latest.txt")
SITE = os.environ.get("MUSK_DOSSIER_URL", "https://kaydeep0.github.io/musk-empire-dossier/")
NTFY = os.environ.get("MUSK_WATCH_NTFY", "https://ntfy.sh/musk-sec-9053334806")
UA = "Watts Advisor research kiran@conformingcredit.org"


def load_json(path):
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return {}


def build_draft(reason, details=None):
    spcx = load_json(os.path.join(DATA, "spcx_market.json"))
    m = (spcx.get("market") or {}) if spcx else {}
    b = (spcx.get("bond") or {}) if spcx else {}
    lines = [
        f"LIVE DOSSIER UPDATE ({reason})",
        f"Site: {SITE}",
        "",
        "Suggested LinkedIn post (edit before posting):",
        "",
        "Update on the live EDGAR dossier. Every load-bearing number still traces to a primary filing.",
        "",
    ]
    if details:
        lines.append(details)
        lines.append("")
    if b:
        lines += [
            f"SPCX ({b.get('basis','b')}): {b.get('event')} on {b.get('date')}.",
            f"Disclosed ~${b.get('cash_disclosed_b')}B cash as of {b.get('cash_as_of')}.",
            f"Proceeds: {b.get('use_of_proceeds')}.",
            "",
        ]
    if m:
        lines += [
            f"SPCX price ({m.get('basis','m')}): ${m.get('price')} as of {m.get('as_of_utc','')}.",
            f"Vs IPO (${m.get('ipo_price')}): {m.get('pct_vs_ipo'):+.1f}%. Vs ATH (${m.get('ath_price')} on {m.get('ath_date')}): {m.get('pct_vs_ath'):+.1f}%.",
            "",
        ]
    lines += [
        f"Full dossier: {SITE}",
        f"RSS: {SITE}feed.xml",
        "",
        "Educational only. Not investment advice.",
        "Money in Motion: https://www.linkedin.com/newsletters/money-in-motion-7054180694628995073",
    ]
    return "\n".join(lines)


def notify(title, body, priority="high", tags="warning,memo"):
    if not NTFY:
        return
    req = urllib.request.Request(
        NTFY,
        data=body.encode("utf-8"),
        headers={
            "User-Agent": UA,
            "Title": title[:250],
            "Priority": priority,
            "Tags": tags,
        },
    )
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print(f"ntfy failed: {e}")


def alert_linkedin_post(reason="site published", details=None):
    draft = build_draft(reason, details)
    os.makedirs(DATA, exist_ok=True)
    open(DRAFT, "w", encoding="utf-8").write(draft)
    summary = draft.split("\n\n")[0:4]
    notify(
        "POST TO LINKEDIN: dossier updated",
        "\n".join(summary) + f"\n\nFull draft saved locally:\n{DRAFT}",
    )
    print("linkedin draft:", DRAFT)
    return DRAFT


if __name__ == "__main__":
    import sys
    reason = sys.argv[1] if len(sys.argv) > 1 else "manual publish"
    details = sys.argv[2] if len(sys.argv) > 2 else None
    alert_linkedin_post(reason, details)
