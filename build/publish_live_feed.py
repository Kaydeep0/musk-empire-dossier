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
*,*::before,*::after{box-sizing:border-box}
body{font-family:system-ui,-apple-system,sans-serif;max-width:920px;margin:0 auto;padding:1rem 1.25rem 3rem;line-height:1.6;color:#111;background:#fff}
header{border-bottom:2px solid #7a2230;padding-bottom:1.25rem;margin-bottom:1.25rem}
h1{font-size:1.55rem;margin:.35rem 0 .5rem;line-height:1.25}
h2{font-size:1.12rem;margin:0 0 .6rem;color:#7a2230;line-height:1.3}
h3{font-size:.95rem;margin:1.1rem 0 .4rem;color:#333}
p{margin:.55rem 0}
.muted{color:#555;font-size:.9rem}
.badge{display:inline-block;background:#7a2230;color:#fff;padding:.18rem .5rem;border-radius:4px;font-size:.7rem;font-weight:600;letter-spacing:.04em;margin-left:.35rem;vertical-align:middle}
.badge-auto{background:#1a5c42}.badge-soon{background:#b8860b}.badge-past{background:#888}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem;margin:1rem 0}
.box{background:#fafafa;border:1px solid #ddd;border-radius:8px;padding:1.1rem 1.25rem;margin:1.25rem 0}
.box-intro{background:#fff;border-color:#7a2230;border-width:1px 1px 1px 4px}
.box-warn{border-color:#c9a227;background:#fffbf0}
.table-wrap{overflow-x:auto;margin:.6rem 0;-webkit-overflow-scrolling:touch}
table{width:100%;min-width:520px;border-collapse:collapse;font-size:.86rem}
th,td{border:1px solid #ddd;padding:.5rem .6rem;text-align:left;vertical-align:top}
th{background:#eee;font-weight:600;white-space:nowrap}
td code{font-size:.82em}
ul,ol{padding-left:1.35rem;margin:.5rem 0 .75rem}
li{margin:.35rem 0}
li+li{margin-top:.4rem}
figure{margin:1.5rem 0 0;padding:0}
figure img{display:block;width:100%;max-width:100%;height:auto;border:1px solid #ddd;border-radius:6px;background:#fff}
.exhibits-grid{display:grid;gap:1.75rem;margin-top:1rem}
.exhibit-card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:1rem 1.1rem 1.15rem}
.exhibit-card h4{margin:0 0 .35rem;font-size:1rem;color:#7a2230}
.exhibit-card .exhibit-desc{margin:0 0 .85rem;font-size:.88rem;color:#555;line-height:1.45}
.exhibit-card img{width:100%;height:auto;border:1px solid #e0e0e0;border-radius:4px}
.exhibit-card .exhibit-link{font-size:.8rem;margin-top:.5rem;display:inline-block}
figcaption{font-size:.84rem;color:#555;margin-top:.45rem;line-height:1.45}
nav.toc{display:flex;flex-wrap:wrap;gap:.35rem .65rem;font-size:.88rem;margin-top:.85rem;padding-top:.75rem;border-top:1px solid #eee}
nav.toc a{text-decoration:none;padding:.2rem 0;border-bottom:1px solid transparent}
nav.toc a:hover{border-bottom-color:#7a2230}
.entity-tag{font-size:.74rem;background:#e8e8e8;padding:.12rem .4rem;border-radius:3px;margin-right:.35rem}
.upcoming td:first-child{font-weight:600;color:#7a2230}
a{color:#7a2230}
code{font-size:.84em;background:#eee;padding:.12rem .35rem;border-radius:3px}
.intro-lead{font-size:1.02rem;line-height:1.65;margin:.75rem 0 1rem}
.pillars{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:.65rem;margin:1rem 0}
.pillar{background:#fff;border:1px solid #e0e0e0;border-radius:6px;padding:.7rem .85rem;font-size:.86rem;line-height:1.45}
.pillar strong{display:block;color:#7a2230;margin-bottom:.25rem;font-size:.78rem;text-transform:uppercase;letter-spacing:.03em}
.loop{font-family:ui-monospace,monospace;font-size:.72rem;line-height:1.45;background:#f5f5f5;border:1px solid #ddd;border-radius:6px;padding:.85rem 1rem;overflow-x:auto;white-space:pre;margin:1rem 0}
.section-note{font-size:.88rem;color:#555;margin-bottom:.75rem}
@media(max-width:640px){body{padding:.85rem} h1{font-size:1.35rem} .box{padding:.9rem}}
"""

CHART_CAPTIONS = {
    "H3_sells_into_strength.png": "H3: Tesla sales vs share price. Do Form 4 sales cluster into strength?",
    "H12_debt_chain.png": "H12: Debt that started at Twitter now sits on SpaceX. Bridge cliff 2027-09-02.",
    "EMPIRE_actors.png": "Recurring cast wearing multiple hats (board, lender, seller, counterparty).",
    "CLIMB_networth.png": "Net-worth proxy over time (Tesla stake + SpaceX marks + cash from sales).",
    "H2_cumulative_cash.png": "H2: Cumulative cash from open-market sales (~$40B), not salary or dividends.",
    "JOURNEY_companies.png": "Career arc: Zip2 to PayPal to Tesla to Twitter/X to SpaceX IPO.",
}
EXHIBIT_CAPTIONS = {
    "V5_lockup_calendar.png": "Lock-up calendar: when insider supply hits the market.",
    "V4_value_flow_loop.png": "Value flows between Tesla, SpaceX, Valor, and public shareholders.",
    "V3_three_leg_refinancing.png": "Three-leg refinance: bridge loan, IPO, senior notes.",
}
EXHIBIT_TITLES = {
    "V5_lockup_calendar.png": "Lock-up calendar",
    "V4_value_flow_loop.png": "Value-flow loop",
    "V3_three_leg_refinancing.png": "Three-leg refinance",
}
EXHIBIT_DESCS = {
    "V5_lockup_calendar.png": "Pre-registered supply steps from the SPCX prospectus. Aug 20 is the first clean test of the scarcity premium.",
    "V4_value_flow_loop.png": "Related-party routes: Tesla Megapacks, Valor leases, IPO proceeds, affiliate billings.",
    "V3_three_leg_refinancing.png": "How ~$13B Twitter debt became a Goldman bridge, then IPO cash, then senior notes.",
}


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
            "exhibits/V5_lockup_calendar.png",
            "exhibits/V4_value_flow_loop.png",
            "exhibits/V3_three_leg_refinancing.png",
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


def _capitalize_first(s):
    s = (s or "").strip()
    if not s:
        return ""
    return s[0].upper() + s[1:]


def _catalyst_badge(c, today):
    if c["date"] < today:
        return '<span class="badge badge-past">past</span>'
    days = c.get("days_until")
    if days is None:
        return ""
    if days <= 30:
        return f'<span class="badge badge-soon">{days}d</span>'
    return f'<span class="muted"> ({days}d)</span>'


def _intro_html(sales_total):
    return f"""
<section id="start" class="box box-intro">
<h2>What you are looking at</h2>
<p class="intro-lead">This page is a <strong>live research dossier</strong>, not a news feed or a trading signal.
An automated bot polls the SEC every 30 minutes for filings tied to Elon Musk and the public companies he
has founded, acquired, or controlled. When something new lands, the site rebuilds itself from primary
records. Every dollar figure here is meant to trace back to a filing, proxy, or market snapshot labeled
by basis (<strong>b</strong> = filing, <strong>m</strong> = market data).</p>

<h3>The hypothesis we are testing</h3>
<p>Across a chain of companies, Musk may run a <strong>repeatable loop</strong>: build real-economy hype,
own the channel that broadcasts it, list or absorb into a vehicle he controls, let belief inflate the
stock, then <strong>sell his stake into the demand that loop created</strong> and roll proceeds into the
next venture. We are not claiming fraud or intent. We are testing whether the same structural moves
recur and whether dated public events confirm or falsify each piece.</p>

<div class="loop">Frontier (Tesla, SpaceX, Twitter/X)
  → Megaphone (X, Grok, owned disclosure channels)
  → Public vehicle (IPO or absorption)
  → Control wedge (vote ≫ economics)
  → Belief premium (high multiple funds the gap)
  → Exit (Form 4 sales, lock-up releases)
  → Roll (debt + cash into next vehicle)</div>

<h3>Why the SpaceX IPO (SPCX) matters now</h3>
<p>SpaceX listed as <strong>SPCX on June 16, 2026</strong> at $135/share. It is the latest turn of the loop:
xAI and X were folded in, ~$13B of Twitter LBO debt traveled with them, a $20B Goldman bridge was added,
and IPO proceeds repaid ~$19B of that stack. Only ~5% of shares trade; the rest unlock on a public calendar.
The first big test is <strong>August 20, 2026</strong>, when tradable float roughly doubles. The debt cliff
is <strong>September 2, 2027</strong>, when the remaining bridge matures.</p>

<h3>Four pillars (each graded separately)</h3>
<div class="pillars">
<div class="pillar"><strong>P1 · Megaphone</strong>He produces, broadcasts, and helps price the belief later sold into.</div>
<div class="pillar"><strong>P2 · Control</strong>Voting power far exceeds economic ownership; public funds, limited steer.</div>
<div class="pillar"><strong>P3 · Transfer</strong>Cash exits to insiders via sales; junior risk migrates to retail/index.</div>
<div class="pillar"><strong>P4 · Engineering</strong>Debt and related-party flows travel vehicle to vehicle.</div>
</div>

<h3>What is already supported from filings</h3>
<ul>
<li><strong>H2 (payday is the sale):</strong> ~${sales_total}B cumulative Tesla open-market sales parsed from Form 4s, not salary or dividends.</li>
<li><strong>H11 (absorb + restate):</strong> SolarCity 2016 prototype; xAI/X into SpaceX 2025–26 at larger scale.</li>
<li><strong>H12 (debt travels):</strong> Twitter $13B → X → xAI → SpaceX bridge → IPO repay → notes offering (see debt chain below).</li>
<li><strong>H13 (related parties):</strong> Tesla↔SpaceX↔Valor loops (~$235M/yr proxy; ~$20B Valor leases in SPCX filings).</li>
</ul>

<p class="section-note"><strong>How to read the rest of the page:</strong> SPCX box = live price + latest issuer 8-K.
Catalyst calendar = pre-registered dates that stress-test the thesis. Debt chain = how leverage moved between entities.
Related parties = channels he can act through without a headline "Musk sold." Charts = evidence, not opinion.
<strong>{UA_NOTE}</strong></p>
</section>
"""


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
        proceeds = _capitalize_first(b.get("use_of_proceeds") or "")
        proc = f" {proceeds}." if proceeds else ""
        spcx_html += (
            f'<p><strong>{_esc(b.get("event"))}</strong> '
            f'(<time>{_esc(b.get("date"))}</time>, basis b). '
            f'Disclosed ~${_esc(b.get("cash_disclosed_b"))}B cash as of {_esc(b.get("cash_as_of"))}.{proc} '
            f'<a href="{_esc(b.get("url","#"))}">Read SpaceX 8-K on EDGAR</a></p>\n'
        )
    if m:
        spcx_html += (
            f'<p>SPCX last <strong>${_esc(m.get("price"))}</strong> '
            f'({m.get("change_pct_1d",0):+.1f}% 1d, basis m, as of {_esc(m.get("as_of_utc"))}). '
            f'Vs IPO ${_esc(m.get("ipo_price"))}: {m.get("pct_vs_ipo",0):+.1f}%. '
            f'Vs all-time high ${_esc(m.get("ath_price"))} ({_esc(m.get("ath_date"))}): '
            f'{m.get("pct_vs_ath",0):+.1f}%.</p>\n'
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
        badge = _catalyst_badge(c, today)
        cat_rows += (
            f'<tr class="{cls}"><td>{_esc(c["date"])}{badge}</td>'
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
        base = os.path.basename(rel)
        pub = os.path.join(PUBLIC, rel)
        root = os.path.join(ROOT, rel)
        if not (os.path.isfile(pub) or os.path.isfile(root)):
            continue
        cap = CHART_CAPTIONS.get(base, base)
        charts_html += (
            f'<figure><img src="{rel}" alt="{_esc(cap)}" loading="lazy"/>'
            f'<figcaption>{_esc(cap)}</figcaption></figure>\n'
        )
    exhibits_html = ""
    exhibit_files = [
        "V5_lockup_calendar.png",
        "V4_value_flow_loop.png",
        "V3_three_leg_refinancing.png",
    ]
    cards = []
    for fname in exhibit_files:
        rel = f"exhibits/{fname}"
        pub_path = os.path.join(PUBLIC, rel)
        if not os.path.isfile(pub_path):
            svg_rel = rel.replace(".png", ".svg")
            if os.path.isfile(os.path.join(PUBLIC, svg_rel)):
                rel = svg_rel
                fname = fname.replace(".png", ".svg")
            else:
                continue
        title = EXHIBIT_TITLES.get(fname, fname)
        desc = EXHIBIT_DESCS.get(fname, EXHIBIT_CAPTIONS.get(fname, ""))
        cap = EXHIBIT_CAPTIONS.get(fname, title)
        cards.append(
            f'<article class="exhibit-card">'
            f'<h4>{_esc(title)}</h4>'
            f'<p class="exhibit-desc">{_esc(desc)}</p>'
            f'<a href="{rel}"><img src="{rel}" alt="{_esc(cap)}" loading="lazy"/></a>'
            f'<p class="exhibit-link"><a href="{rel}">Open full size</a></p>'
            f'</article>'
        )
    if cards:
        exhibits_html = f'<div class="exhibits-grid">{"".join(cards)}</div>'

    intro = _intro_html(sales.get("total_usd_b", 0))

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
<p class="muted">Live SEC dossier testing a falsifiable thesis about how narrative converts to cash across Musk vehicles.
Updated automatically from EDGAR every 30 minutes.</p>
<nav class="toc">
<a href="#start">Start here</a>
<a href="#spcx">SPCX / IPO</a>
<a href="#catalysts">Catalysts</a>
<a href="#debt">Debt chain</a>
<a href="#parties">Related parties</a>
<a href="#watch">Watch list</a>
<a href="#alerts">Alerts</a>
<a href="#charts">Charts</a>
<a href="feed.xml">RSS</a>
<a href="status.json">JSON</a>
</nav>
</header>

{intro}

<section id="spcx" class="box">
<h2>SPCX live: SpaceX IPO + latest issuer filing</h2>
<p class="section-note">Space Exploration Technologies listed as SPCX on June 16, 2026. This box pulls the live stock price (basis m) and the latest material 8-K from issuer CIK 1181412 (basis b).</p>
{spcx_html or '<p class="muted">Market and bond data refresh on each sync.</p>'}
</section>

<section id="catalysts" class="box box-warn">
<h2>Dated catalyst calendar</h2>
<p class="section-note">Pre-registered dates from prospectuses and debt docs. These confirm or break the thesis (lock-ups, refi cliffs), not price targets.</p>
<div class="table-wrap"><table>
<thead><tr><th>Date</th><th>Entity</th><th>Event</th><th>Tests</th></tr></thead>
<tbody>{cat_rows}</tbody>
</table></div>
</section>

<section id="debt" class="box">
<h2>Debt chain: Twitter → X → xAI → SpaceX</h2>
<p class="section-note">The ~$13B Twitter LBO debt was recast through common-control mergers until SpaceX IPO proceeds repaid part of it. The bridge maturing in 2027 is the next infrastructure cliff.</p>
<div class="table-wrap"><table>
<thead><tr><th>Date</th><th>Entity</th><th>Event</th><th>Debt out</th></tr></thead>
<tbody>{debt_rows}</tbody>
</table></div>
</section>

<section id="parties" class="box">
<h2>Related parties and channels</h2>
<p class="section-note">Musk rarely acts alone on a Form 4. Value also moves through directors, trusts, lenders, and affiliates listed here.</p>
<div class="table-wrap"><table>
<thead><tr><th>Party</th><th>Role</th><th>Flow</th><th>Source</th></tr></thead>
<tbody>{party_rows}</tbody>
</table></div>
</section>

<section id="watch" class="box">
<h2>What the bot watches (technical)</h2>
<p class="section-note">Five SEC identities polled on a schedule. Form 4s come from Musk CIK 1494730; issuer filings come from company CIKs.</p>
<div class="table-wrap"><table>
<thead><tr><th>Entity key</th><th>Filings tracked</th><th>Last poll</th></tr></thead>
<tbody>{watch_rows or '<tr><td colspan="3">Watcher not run yet</td></tr>'}</tbody>
</table></div>
<h3>Registered parties (v1 scope)</h3>
<div class="table-wrap"><table>
<thead><tr><th>Entity</th><th>Ticker</th><th>CIK</th><th>Kind</th></tr></thead>
<tbody>{reg_rows}</tbody>
</table></div>
</section>

<div class="grid">
<section class="box">
<h2>Latest Musk filing</h2>
<p class="section-note">Personal CIK 1494730: every buy, sell, option exercise.</p>
<p><strong>{_esc(lf.get('form','n/a'))}</strong> · {_esc(lf.get('filing_date','n/a'))}<br/>
<a href="{_esc(lf.get('url','#'))}">View on EDGAR</a></p>
<h3>Sales ledger (H2)</h3>
<p><strong>~${sales.get('total_usd_b',0)}B</strong> cumulative open-market sales parsed from Form 4 code S.</p>
</section>
<section class="box">
<h2>Latest issuer filings</h2>
<p><strong>SpaceX:</strong> {_esc((status.get('latest_spacex_filing') or {}).get('form'))} · {_esc((status.get('latest_spacex_filing') or {}).get('filing_date'))}</p>
<p><strong>Tesla:</strong> {_esc((status.get('latest_tesla_filing') or {}).get('form'))} · {_esc((status.get('latest_tesla_filing') or {}).get('filing_date'))}</p>
</section>
</div>

<section id="alerts" class="box">
<h2>Recent SEC alerts</h2>
<ul>{alerts_html or '<li class="muted">No new filings detected since watcher seeded. Next alert appears here, by email, and by SMS.</li>'}</ul>
</section>

<section id="charts" class="box">
<h2>Evidence charts</h2>
<p class="section-note">Generated from parsed Form 4 data and filing-backed debt / actor maps. Not price predictions.</p>
{charts_html or '<p class="muted">Charts regenerate on each full sync.</p>'}
<h3>SPCX structural exhibits</h3>
{exhibits_html or '<p class="muted">Lock-up calendar and value-flow maps from the SpaceX dossier.</p>'}
</section>

<footer class="muted" style="margin-top:2rem;border-top:1px solid #ddd;padding-top:1rem">
<p>{UA_NOTE}</p>
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
