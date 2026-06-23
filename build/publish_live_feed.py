#!/usr/bin/env python3
"""Build public live feed artifacts from local data/ — JSON, RSS, changelog, dashboard HTML."""
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
SPCX_PDF = "https://github.com/Kaydeep0/musk-empire-dossier/raw/main/../Spacexsec/SPCX_The_Anatomy_of_a_Premium.pdf"

SITE_TITLE = "Musk Infrastructure Watch (Live EDGAR)"
SITE_URL = os.environ.get("MUSK_DOSSIER_URL", "https://kaydeep0.github.io/musk-empire-dossier/")
LINKEDIN_PROFILE = "https://www.linkedin.com/in/ksekhon44"
LINKEDIN_NEWSLETTER = "https://www.linkedin.com/newsletters/money-in-motion-7054180694628995073"
UA_NOTE = "Educational only. Not investment advice."

CSS = """
body{font-family:system-ui,-apple-system,sans-serif;max-width:960px;margin:0 auto;padding:1rem 1.25rem 3rem;line-height:1.55;color:#111;background:#fff}
header{border-bottom:2px solid #7a2230;padding-bottom:1rem;margin-bottom:1.5rem}
h1{font-size:1.5rem;margin:.25rem 0} h2{font-size:1.1rem;margin:0 0 .5rem;color:#7a2230}
h3{font-size:.95rem;margin:1rem 0 .35rem}
.muted{color:#555;font-size:.88rem}
.badge{display:inline-block;background:#7a2230;color:#fff;padding:.15rem .45rem;border-radius:4px;font-size:.72rem;font-weight:600;letter-spacing:.03em}
.badge-auto{background:#1a5c42}.badge-soon{background:#b8860b}.badge-past{background:#666}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem;margin:1rem 0}
.box{background:#fafafa;border:1px solid #ddd;border-radius:6px;padding:1rem;margin:1rem 0}
.box-warn{border-color:#b8860b;background:#fffbf0}
table{width:100%;border-collapse:collapse;font-size:.88rem;margin:.5rem 0}
th,td{border:1px solid #ddd;padding:.4rem .5rem;text-align:left;vertical-align:top}
th{background:#f0f0f0}
ul{padding-left:1.2rem;margin:.4rem 0}
img,svg.img{max-width:100%;height:auto;border:1px solid #ddd;border-radius:4px}
nav.toc{font-size:.9rem;margin:.75rem 0}
nav.toc a{margin-right:.75rem}
.entity-tag{font-size:.75rem;background:#eee;padding:.1rem .35rem;border-radius:3px;white-space:nowrap}
.upcoming{font-weight:600;color:#7a2230}
a{color:#7a2230}
"""


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


def latest_from_index(name):
    rows = read_csv(os.path.join(DATA, name))
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


def alerts(limit=40):
    log = os.path.join(DATA, "filing_alerts.log")
    if not os.path.exists(log):
        return []
    lines = open(log, encoding="utf-8").read().strip().splitlines()
    out = []
    for line in reversed(lines[-limit:]):
        parts = line.split("\t")
        if len(parts) >= 5:
            out.append({
                "seen_at": parts[0], "filing_date": parts[1], "form": parts[2],
                "description": parts[3], "url": parts[4],
                "entity": parts[5] if len(parts) >= 6 else "Elon Musk",
            })
    return out


def watch_entities_status():
    out = []
    for fname in sorted(os.listdir(DATA) if os.path.isdir(DATA) else []):
        if not fname.startswith(".watch_state_") or not fname.endswith(".json"):
            continue
        key = fname.replace(".watch_state_", "").replace(".json", "")
        st = load_json(os.path.join(DATA, fname), {})
        out.append({"key": key, "tracked": len(st.get("seen", [])), "updated": st.get("updated")})
    return sorted(out, key=lambda x: x["key"])


def registry_entities():
    return read_csv(REGISTRY)


def catalysts():
    items = load_json(os.path.join(DATA, "catalyst_calendar.json"), [])
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for c in items:
        c["status"] = "past" if c["date"] < today else ("soon" if c["date"] <= today[:8] + "31" else "future")
        if c["date"] >= today and (c.get("status") != "past"):
            delta = (datetime.strptime(c["date"], "%Y-%m-%d") - datetime.strptime(today, "%Y-%m-%d")).days
            c["days_until"] = delta
    return sorted(items, key=lambda x: x["date"])


def parties_summary():
    return [
        {"party": "Valor / Antonio Gracias", "role": "Director + #2 owner + AI compute lessor",
         "flow": "~$20B life-of-lease; ~$885M paid FY25", "vehicle": "SpaceX (SPCX)"},
        {"party": "Tesla Inc", "role": "Megapacks, vehicles, services to SpaceX",
         "flow": "~$778M/yr net to Tesla (2025 proxy)", "vehicle": "TSLA DEF 14A"},
        {"party": "Tesla → xAI", "role": "Capital rotation", "flow": "$2.0B Series E", "vehicle": "Tesla / xAI"},
        {"party": "Goldman Sachs", "role": "Bridge lender + IPO underwriter",
         "flow": "$20B bridge; matures 2027-09-02", "vehicle": "SpaceX debt chain"},
        {"party": "Musk revocable trust + GRATs", "role": "Control + economic extraction",
         "flow": "Form 4 sales ~$40B (TSLA); SPCX lock-ups", "vehicle": "CIK 1494730"},
    ]


def build_status():
    return {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "site_url": SITE_URL,
        "disclaimer": UA_NOTE,
        "latest_musk_filing": latest_from_index("filings_index.csv"),
        "latest_spacex_filing": latest_from_index("spacex_filings_index.csv"),
        "latest_tesla_filing": latest_from_index("tesla_filings_index.csv"),
        "sales": sale_stats(),
        "spcx": load_json(os.path.join(DATA, "spcx_market.json"), {}),
        "spacex_events": load_json(os.path.join(DATA, "spacex_events.json"), {}),
        "tesla_events": load_json(os.path.join(DATA, "tesla_events.json"), {}),
        "debt_chain": read_csv(os.path.join(DATA, "debt_chain.csv")),
        "catalysts": catalysts(),
        "watch": watch_entities_status(),
        "registry": registry_entities(),
        "parties": parties_summary(),
        "recent_alerts": alerts(30),
        "charts": [
            "charts/H3_sells_into_strength.png", "charts/H12_debt_chain.png",
            "charts/EMPIRE_actors.png", "charts/CLIMB_networth.png",
            "charts/H2_cumulative_cash.png", "charts/JOURNEY_companies.png",
        ],
        "exhibits": [
            "exhibits/V5_lockup_calendar.svg", "exhibits/V4_value_flow_loop.svg",
            "exhibits/V3_three_leg_refinancing.svg",
        ],
    }


def write_json(status):
    os.makedirs(PUBLIC, exist_ok=True)
    path = os.path.join(PUBLIC, "status.json")
    json.dump(status, open(path, "w"), indent=2)
    return path


def write_changelog(status):
    path = os.path.join(PUBLIC, "CHANGELOG.md")
    lines = [f"# Live changelog\n", f"**Last rebuilt:** {status['updated_at']} (UTC)\n"]
    lf = status.get("latest_musk_filing") or {}
    if lf:
        lines.append(f"- Latest Musk filing: **{lf.get('form')}** {lf.get('filing_date')} [{lf.get('url')}]\n")
    for a in status.get("recent_alerts", [])[:12]:
        lines.append(f"- `{a['seen_at']}` **{a.get('entity')}** {a['form']} ({a['filing_date']})")
    lines += ["\n---\n", UA_NOTE, ""]
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    return path


def write_rss(status):
    path = os.path.join(PUBLIC, "feed.xml")
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = []
    for a in status.get("recent_alerts", [])[:30]:
        title = xml.escape(f"[{a.get('entity','?')}] {a['form']}: {a['description']}")
        link = xml.escape(a["url"])
        desc = xml.escape(f"{a['seen_at']} · {a['filing_date']}")
        items.append(
            f"<item><title>{title}</title><link>{link}</link>"
            f"<guid isPermaLink=\"true\">{link}</guid><pubDate>{now}</pubDate>"
            f"<description>{desc}</description></item>"
        )
    for c in status.get("catalysts", []):
        if c.get("days_until", 999) <= 45 and c.get("days_until", -1) >= 0:
            link = xml.escape(SITE_URL)
            title = xml.escape(f"Catalyst in {c['days_until']}d: {c['event']}")
            items.append(
                f"<item><title>{title}</title><link>{link}</link>"
                f"<guid>{xml.escape(c['date']+c['event'])}</guid><pubDate>{now}</pubDate></item>"
            )
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>{xml.escape(SITE_TITLE)}</title>
<link>{xml.escape(SITE_URL)}</link>
<description>{xml.escape(UA_NOTE)}</description>
<lastBuildDate>{now}</lastBuildDate>
{''.join(items)}
</channel></rss>"""
    open(path, "w", encoding="utf-8").write(body)
    return path


def _esc(s):
    return xml.escape(str(s or ""))


def write_index(status):
    path = os.path.join(PUBLIC, "index.html")
    spcx = status.get("spcx") or {}
    m = spcx.get("market") or {}
    b = spcx.get("bond") or {}
    sales = status.get("sales") or {}
    lf = status.get("latest_musk_filing") or {}

    # SPCX box
    spcx_html = ""
    if b:
        spcx_html += (
            f'<p><strong>{_esc(b.get("event"))}</strong> ({_esc(b.get("date"))}, basis b). '
            f'Cash ~${_esc(b.get("cash_disclosed_b"))}B as of {_esc(b.get("cash_as_of"))}. '
            f'<a href="{_esc(b.get("url","#"))}">SpaceX 8-K</a></p>'
        )
    if m:
        spcx_html += (
            f'<p>SPCX <strong>${_esc(m.get("price"))}</strong> ({m.get("change_pct_1d",0):+.1f}% 1d, basis m). '
            f'Vs IPO ${_esc(m.get("ipo_price"))}: {m.get("pct_vs_ipo",0):+.1f}%. '
            f'Vs ATH ${_esc(m.get("ath_price"))} ({_esc(m.get("ath_date"))}): {m.get("pct_vs_ath",0):+.1f}%.</p>'
        )

    # Watch table
    watch_rows = ""
    for w in status.get("watch", []):
        watch_rows += f'<tr><td>{_esc(w["key"])}</td><td>{w["tracked"]}</td><td class="muted">{_esc(w.get("updated"))}</td></tr>\n'
    reg_rows = ""
    for r in status.get("registry", []):
        if r.get("v1_scope") != "yes" or not r.get("cik"):
            continue
        reg_rows += (
            f'<tr><td>{_esc(r.get("entity"))}</td><td>{_esc(r.get("ticker"))}</td>'
            f'<td><code>{_esc(r.get("cik"))}</code></td><td>{_esc(r.get("kind"))}</td></tr>\n'
        )

    # Catalysts
    cat_rows = ""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for c in status.get("catalysts", []):
        cls = "upcoming" if c["date"] >= today else "muted"
        badge = "badge-soon" if c.get("days_until", 999) <= 30 and c["date"] >= today else ("badge-past" if c["date"] < today else "")
        du = f' · {c["days_until"]}d' if c.get("days_until") is not None and c["date"] >= today else ""
        cat_rows += (
            f'<tr class="{cls}"><td>{_esc(c["date"])}<span class="badge {badge}">{du}</span></td>'
            f'<td>{_esc(c["entity"])}</td><td>{_esc(c["event"])}</td>'
            f'<td class="muted">{_esc(c.get("hypothesis"))}</td></tr>\n'
        )

    # Debt chain
    debt_rows = ""
    for r in status.get("debt_chain", []):
        debt_rows += (
            f'<tr><td>{_esc(r.get("date"))}</td><td>{_esc(r.get("entity"))}</td>'
            f'<td>{_esc(r.get("event"))}</td><td>${_esc(r.get("debt_outstanding_b"))}B</td></tr>\n'
        )

    # Parties
    party_rows = ""
    for p in status.get("parties", []):
        party_rows += (
            f'<tr><td><strong>{_esc(p["party"])}</strong></td><td>{_esc(p["role"])}</td>'
            f'<td>{_esc(p["flow"])}</td><td>{_esc(p["vehicle"])}</td></tr>\n'
        )

    # Alerts
    alerts_html = ""
    for a in status.get("recent_alerts", [])[:15]:
        alerts_html += (
            f'<li><span class="entity-tag">{_esc(a.get("entity"))}</span> '
            f'<a href="{_esc(a["url"])}"><strong>{_esc(a["form"])}</strong></a> '
            f'{_esc(a["filing_date"])}: {_esc(a["description"])}</li>\n'
        )

    # Charts
    charts_html = ""
    for rel in status.get("charts", []):
        if os.path.isfile(os.path.join(PUBLIC, rel)) or os.path.isfile(os.path.join(ROOT, rel)):
            charts_html += f'<figure><img src="{rel}" alt="{_esc(os.path.basename(rel))}"/></figure>\n'
    exhibits_html = ""
    for rel in status.get("exhibits", []):
        if os.path.isfile(os.path.join(PUBLIC, rel)):
            exhibits_html += f'<figure><img class="img" src="{rel}" alt="{_esc(os.path.basename(rel))}"/></figure>\n'

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{_esc(SITE_TITLE)}</title>
<meta name="description" content="Live bot watching Musk, SpaceX, Tesla and related-party SEC filings. Infrastructure moves, debt chain, catalyst calendar."/>
<link rel="alternate" type="application/rss+xml" title="Musk infrastructure alerts" href="feed.xml"/>
<style>{CSS}</style>
</head><body>
<header>
<p><span class="badge">LIVE</span> <span class="badge badge-auto">AUTO</span>
<span class="muted">Updated {_esc(status['updated_at'])} · GitHub Actions every 30 min</span></p>
<h1>Musk infrastructure watch</h1>
<p class="muted">A bot that polls SEC EDGAR for Musk and every public vehicle he acts through.
Every number links to a primary filing. Dated calls graded on the calendar.
<strong>{UA_NOTE}</strong></p>
<nav class="toc">
<a href="#watch">Watch list</a><a href="#spcx">SPCX</a><a href="#catalysts">Catalysts</a>
<a href="#debt">Debt chain</a><a href="#parties">Related parties</a><a href="#alerts">Alerts</a>
<a href="#charts">Charts</a><a href="feed.xml">RSS</a><a href="status.json">JSON</a>
</nav>
</header>

<section id="watch" class="box">
<h2>What the bot watches</h2>
<p class="muted">Registry-driven CIKs from <code>registry/entities.csv</code>. New filings trigger email, SMS, ntfy, site rebuild, and git push.</p>
<table><tr><th>Entity key</th><th>Filings tracked</th><th>Last poll</th></tr>{watch_rows or '<tr><td colspan="3">Run watch_entities.py</td></tr>'}</table>
<h3>Registered parties (v1 scope)</h3>
<table><tr><th>Entity</th><th>Ticker</th><th>CIK</th><th>Kind</th></tr>{reg_rows}</table>
</section>

<section id="spcx" class="box">
<h2>SPCX live (market + issuer 8-K)</h2>
{spcx_html or '<p class="muted">Run pull_spcx_market.py</p>'}
<p class="muted">Full structural dossier: <a href="https://github.com/Kaydeep0/musk-empire-dossier">repo</a> · Spacexsec research in sibling folder.</p>
</section>

<section id="catalysts" class="box box-warn">
<h2>Dated catalyst calendar</h2>
<p class="muted">Pre-registered tests from filings. The bot surfaces these before they hit.</p>
<table><tr><th>Date</th><th>Entity</th><th>Event</th><th>Hypothesis</th></tr>{cat_rows}</table>
</section>

<section id="debt" class="box">
<h2>Debt chain (Twitter → X → xAI → SpaceX)</h2>
<p class="muted">Traveling debt buys time between vehicles. Next cliff: <strong>2027-09-02</strong> bridge maturity.</p>
<table><tr><th>Date</th><th>Entity</th><th>Event</th><th>Debt out</th></tr>{debt_rows}</table>
</section>

<section id="parties" class="box">
<h2>Related parties &amp; channels Musk acts through</h2>
<table><tr><th>Party</th><th>Role</th><th>Flow</th><th>Source</th></tr>{party_rows}</table>
</section>

<div class="grid">
<section class="box">
<h2>Latest Musk filing (CIK 1494730)</h2>
<p><strong>{_esc(lf.get('form','n/a'))}</strong> · {_esc(lf.get('filing_date','n/a'))}<br/>
<a href="{_esc(lf.get('url','#'))}">EDGAR</a></p>
<h3>Sales ledger</h3>
<p><strong>~${sales.get('total_usd_b',0)}B</strong> cumulative open-market sales (Form 4).</p>
</section>
<section class="box">
<h2>Latest issuer filings</h2>
<p><strong>SpaceX:</strong> {_esc((status.get('latest_spacex_filing') or {}).get('form'))} · {_esc((status.get('latest_spacex_filing') or {}).get('filing_date'))}</p>
<p><strong>Tesla:</strong> {_esc((status.get('latest_tesla_filing') or {}).get('form'))} · {_esc((status.get('latest_tesla_filing') or {}).get('filing_date'))}</p>
</section>
</div>

<section id="alerts" class="box">
<h2>Recent SEC alerts</h2>
<ul>{alerts_html or '<li class="muted">No alerts logged yet. First detection will email + SMS + appear here.</li>'}</ul>
</section>

<section id="charts">
<h2>Charts &amp; exhibits</h2>
{charts_html or '<p class="muted">Charts generate on sync (phase3, debt_chain, empire_mechanics).</p>'}
<h3>From SPCX structural dossier</h3>
{exhibits_html}
</section>

<footer class="muted" style="margin-top:2rem;border-top:1px solid #ddd;padding-top:1rem">
<p><a href="{LINKEDIN_NEWSLETTER}">Money in Motion</a> · <a href="{LINKEDIN_PROFILE}">Kiran Sekhon</a> · Watts Advisor</p>
</footer>
</body></html>"""
    open(path, "w", encoding="utf-8").write(html)
    return path


def copy_assets(status):
    copied = []
    for rel in status.get("charts", []) + status.get("exhibits", []):
        src = os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            src = os.path.join(PUBLIC, rel)
        if os.path.isfile(os.path.join(ROOT, rel)):
            src = os.path.join(ROOT, rel)
        elif os.path.isfile(os.path.join(PUBLIC, rel)):
            continue
        else:
            continue
        dst = os.path.join(PUBLIC, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(rel)
    return copied


def main():
    status = build_status()
    paths = [write_json(status), write_changelog(status), write_rss(status), write_index(status)]
    # Run asset sync if available
    sync = os.path.join(HERE, "sync_public_assets.py")
    if os.path.isfile(sync):
        import subprocess
        subprocess.run([sys.executable, sync], cwd=ROOT, check=False)
    copied = copy_assets(status)
    if copied:
        print(f"assets: {len(copied)}")
    print("published:")
    for p in paths:
        print(" ", p)
    if os.environ.get("MUSK_LINKEDIN_ALERT", "1") != "0":
        import subprocess
        subprocess.run(
            [sys.executable, os.path.join(HERE, "linkedin_alert.py"), "site published"],
            cwd=ROOT, check=False, timeout=30,
        )


if __name__ == "__main__":
    main()
