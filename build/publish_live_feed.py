#!/usr/bin/env python3
"""Build public live feed artifacts from local data/ — JSON, RSS, changelog markdown."""
import csv
import json
import os
import shutil
import sys
import xml.sax.saxutils as xml
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
PUBLIC = os.path.join(ROOT, "public")
REGISTRY = os.path.join(ROOT, "registry", "entities.csv")

SITE_TITLE = "Elon Musk: Empire & Exit (Live EDGAR dossier)"
SITE_URL = os.environ.get("MUSK_DOSSIER_URL", "https://example.com/musk-dossier")
UA_NOTE = "Educational only. Not investment advice."


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_json(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def latest_filing():
    rows = read_csv(os.path.join(DATA, "filings_index.csv"))
    if not rows:
        return None
    rows.sort(key=lambda r: (r.get("filing_date", ""), r.get("accession", "")), reverse=True)
    return rows[0]


def sale_stats():
    rows = read_csv(os.path.join(DATA, "transactions.csv"))
    total = 0.0
    by_year = {}
    for r in rows:
        if r.get("code") != "S":
            continue
        try:
            v = float(r.get("value_usd") or 0)
        except ValueError:
            continue
        if v <= 0:
            continue
        total += v
        y = (r.get("transaction_date") or "")[:4]
        if y:
            by_year[y] = by_year.get(y, 0) + v
    return {"total_usd_b": round(total / 1e9, 2), "by_year_usd_b": {k: round(v / 1e9, 2) for k, v in sorted(by_year.items())}}


def alerts(limit=30):
    log = os.path.join(DATA, "filing_alerts.log")
    if not os.path.exists(log):
        return []
    lines = open(log, encoding="utf-8").read().strip().splitlines()
    out = []
    for line in reversed(lines[-limit:]):
        parts = line.split("\t")
        if len(parts) >= 5:
            out.append({
                "seen_at": parts[0],
                "filing_date": parts[1],
                "form": parts[2],
                "description": parts[3],
                "url": parts[4],
            })
    return out


def spcx_snapshot():
    return load_json(os.path.join(DATA, "spcx_market.json"), {})


def watch_state():
    st = load_json(os.path.join(DATA, ".watch_state.json"), {})
    return {"last_poll": st.get("updated"), "filings_tracked": len(st.get("seen", []))}


def build_status():
    lf = latest_filing()
    sales = sale_stats()
    spcx = spcx_snapshot()
    return {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "site_url": SITE_URL,
        "disclaimer": UA_NOTE,
        "latest_filing": lf,
        "sales": sales,
        "spcx": spcx,
        "watch": watch_state(),
        "recent_alerts": alerts(20),
        "charts": [
            "charts/H2_cumulative_cash.png",
            "charts/H3_sells_into_strength.png",
            "charts/CLIMB_networth.png",
            "charts/JOURNEY_companies.png",
            "charts/H12_debt_chain.png",
            "charts/EMPIRE_actors.png",
        ],
        "research": [
            "research/EMPIRE_MECHANICS.md",
            "research/STRUCTURE_BRIEF.md",
            "research/HYPOTHESIS.md",
        ],
    }


def write_json(status):
    os.makedirs(PUBLIC, exist_ok=True)
    path = os.path.join(PUBLIC, "status.json")
    json.dump(status, open(path, "w"), indent=2)
    return path


def write_changelog(status):
    path = os.path.join(PUBLIC, "CHANGELOG.md")
    lf = status.get("latest_filing") or {}
    sales = status.get("sales", {})
    lines = [
        "# Live changelog",
        "",
        f"**Last rebuilt:** {status['updated_at']} (UTC)",
        "",
        "## Latest SEC filing (Musk CIK)",
        "",
    ]
    if lf:
        lines += [
            f"- **{lf.get('form')}** filed **{lf.get('filing_date')}**",
            f"- [View on EDGAR]({lf.get('url')})",
            "",
        ]
    else:
        lines += ["- (no filings_index.csv yet — run `pull_musk_filings.py`)", ""]

    lines += [
        "## Cumulative Tesla sales (Form 4, parsed)",
        "",
        f"- **Total realized (sales): ~${sales.get('total_usd_b', 0)}B**",
        "",
    ]
    for y, v in (sales.get("by_year_usd_b") or {}).items():
        lines.append(f"- {y}: ~${v}B")
    lines += ["", "## Recent alerts", ""]
    for a in status.get("recent_alerts", [])[:10]:
        lines.append(f"- `{a['seen_at']}` **{a['form']}** ({a['filing_date']}) - [{a['description']}]({a['url']})")
    lines += ["", "---", UA_NOTE, ""]
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    return path


def write_rss(status):
    path = os.path.join(PUBLIC, "feed.xml")
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = []
    for a in status.get("recent_alerts", [])[:25]:
        title = xml.escape(f"{a['form']}: {a['description']} ({a['filing_date']})")
        link = xml.escape(a["url"])
        desc = xml.escape(f"Detected {a['seen_at']}. {a['description']}")
        items.append(
            f"<item><title>{title}</title><link>{link}</link>"
            f"<guid isPermaLink=\"true\">{link}</guid>"
            f"<pubDate>{now}</pubDate><description>{desc}</description></item>"
        )
    if not items and status.get("latest_filing"):
        lf = status["latest_filing"]
        link = xml.escape(lf.get("url", SITE_URL))
        title = xml.escape(f"Latest: {lf.get('form')} {lf.get('filing_date')}")
        items.append(
            f"<item><title>{title}</title><link>{link}</link>"
            f"<guid isPermaLink=\"true\">{link}</guid><pubDate>{now}</pubDate></item>"
        )
    xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>{xml.escape(SITE_TITLE)}</title>
<link>{xml.escape(SITE_URL)}</link>
<description>{xml.escape(UA_NOTE)}</description>
<lastBuildDate>{now}</lastBuildDate>
{''.join(items)}
</channel>
</rss>
"""
    open(path, "w", encoding="utf-8").write(xml_body)
    return path


def write_index(status):
    path = os.path.join(PUBLIC, "index.html")
    lf = status.get("latest_filing") or {}
    sales = status.get("sales", {})
    spcx = status.get("spcx") or {}
    m = spcx.get("market") or {}
    b = spcx.get("bond") or {}
    alerts_html = ""
    for a in status.get("recent_alerts", [])[:8]:
        alerts_html += (
            f'<li><a href="{a["url"]}"><strong>{a["form"]}</strong></a> '
            f'{a["filing_date"]}: {a["description"]}</li>\n'
        )
    spcx_html = ""
    if b:
        spcx_html += (
            f'<p><strong>{b.get("event")}</strong> ({b.get("date")}, basis {b.get("basis","b")}). '
            f'Disclosed ~${b.get("cash_disclosed_b")}B cash as of {b.get("cash_as_of")}. '
            f'{b.get("use_of_proceeds")}.</p>\n'
        )
    if m:
        spcx_html += (
            f'<p>SPCX <strong>${m.get("price")}</strong> '
            f'({m.get("change_pct_1d"):+.1f}% 1d, basis {m.get("basis","m")}, '
            f'as of {m.get("as_of_utc")}). '
            f'Vs IPO ${m.get("ipo_price")}: {m.get("pct_vs_ipo"):+.1f}%. '
            f'Vs ATH ${m.get("ath_price")} ({m.get("ath_date")}): {m.get("pct_vs_ath"):+.1f}%.</p>'
        )
    if not spcx_html:
        spcx_html = '<p class="muted">Run pull_spcx_market.py to refresh SPCX price and bond snapshot.</p>'
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{SITE_TITLE}</title>
<meta name="description" content="Live SEC-grounded dossier: Musk filings, sales ledger, empire mechanics. Updated from EDGAR."/>
<link rel="alternate" type="application/rss+xml" title="Musk SEC alerts" href="feed.xml"/>
<style>
body{{font-family:system-ui,sans-serif;max-width:820px;margin:2rem auto;padding:0 1rem;line-height:1.5;color:#111}}
h1{{font-size:1.4rem}} .muted{{color:#666;font-size:.9rem}}
.badge{{display:inline-block;background:#7a2230;color:#fff;padding:.2rem .5rem;border-radius:4px;font-size:.75rem}}
ul{{padding-left:1.2rem}} img{{max-width:100%;height:auto;border:1px solid #ddd}}
.box{{background:#fafafa;border:1px solid #ddd;padding:1rem;margin:1rem 0}}
</style>
</head>
<body>
<p><span class="badge">LIVE</span> <span class="muted">Updated {status['updated_at']}</span></p>
<h1>Empire &amp; Exit: live from EDGAR</h1>
<p>Every load-bearing number traces to a primary SEC filing. Strongest counter-argument stated first.
Dated calls graded on the calendar. <strong>{UA_NOTE}</strong></p>

<div class="box">
<h2>SPCX snapshot (market + bond)</h2>
{spcx_html}
<p class="muted">Market cap wipeout figures from social posts are not on this page unless we can source them.
Re-pull before citing. Bond/cash from SpaceX 8-K (June 22, 2026).</p>
</div>

<h2>Latest Musk filing</h2>
<p><strong>{lf.get('form','n/a')}</strong> · {lf.get('filing_date','n/a')}<br/>
<a href="{lf.get('url','#')}">View on SEC EDGAR</a></p>

<h2>Sales ledger (Form 4)</h2>
<p><strong>~${sales.get('total_usd_b',0)}B</strong> cumulative open-market sales parsed from Musk CIK filings.</p>

<h2>Recent SEC alerts</h2>
<ul>
{alerts_html or '<li>No alerts yet. Watcher will populate this.</li>'}
</ul>

<h2>Key charts</h2>
<p><img src="charts/H3_sells_into_strength.png" alt="Sales vs price"/><br/>
<img src="charts/EMPIRE_actors.png" alt="Empire actors matrix"/><br/>
<img src="charts/H12_debt_chain.png" alt="Debt chain"/></p>

<h2>Subscribe</h2>
<p>RSS: <a href="feed.xml">feed.xml</a> · JSON: <a href="status.json">status.json</a></p>

<p class="muted">Money in Motion · Eigenstate Research · IAR disclosure pending WSP</p>
</body>
</html>
"""
    open(path, "w", encoding="utf-8").write(html)
    return path


def copy_charts(status):
    """Copy chart PNGs into public/charts/ for self-contained GitHub Pages deploy."""
    src_dir = os.path.join(ROOT, "charts")
    dst_dir = os.path.join(PUBLIC, "charts")
    os.makedirs(dst_dir, exist_ok=True)
    copied = []
    for rel in status.get("charts", []):
        src = os.path.join(ROOT, rel)
        if os.path.isfile(src):
            dst = os.path.join(PUBLIC, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(rel)
    return copied


def main():
    status = build_status()
    paths = [write_json(status), write_changelog(status), write_rss(status), write_index(status)]
    copied = copy_charts(status)
    if copied:
        print(f"copied {len(copied)} charts to public/charts/")
    print("published:")
    for p in paths:
        print(" ", p)
    if os.environ.get("MUSK_LINKEDIN_ALERT", "1") != "0":
        try:
            import subprocess
            subprocess.run(
                [sys.executable, os.path.join(HERE, "linkedin_alert.py"), "site published"],
                cwd=ROOT, check=False, timeout=30,
            )
        except Exception as e:
            print(f"linkedin alert skipped: {e}")


if __name__ == "__main__":
    main()
