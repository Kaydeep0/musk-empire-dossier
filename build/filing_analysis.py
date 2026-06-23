#!/usr/bin/env python3
"""
Read an SEC filing and produce a personal brief: engineer, trader, CFA, supply/demand.

  python3 build/filing_analysis.py --url 'https://www.sec.gov/Archives/edgar/...'
  python3 build/filing_analysis.py --test-spcx-pricing
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
ANALYSIS_DIR = os.path.join(DATA, "filing_analyses")

sys.path.insert(0, HERE)
from edgar_common import fetch, html_to_text  # noqa: E402

DISCLAIMER = "Educational research only. Not investment advice."
DOSSIER_URL = os.environ.get("MUSK_DOSSIER_URL", "https://kaydeep0.github.io/musk-empire-dossier/")
GITHUB_URL = os.environ.get("MUSK_GITHUB_URL", "https://github.com/kaydeep0/musk-empire-dossier")


def _ascii(s):
    """Strip chars that break SMS/ntfy headers."""
    return s.replace("\u2014", "-").replace("\u2013", "-").replace("\u00b7", " | ")


def load_catalysts():
    path = os.path.join(DATA, "catalyst_calendar.json")
    if os.path.isfile(path):
        return json.load(open(path, encoding="utf-8"))
    return []


def load_debt_chain():
    path = os.path.join(DATA, "debt_chain.csv")
    if not os.path.isfile(path):
        return []
    import csv
    return list(csv.DictReader(open(path, encoding="utf-8")))


def extract_money(text):
    """Return list of (label, billions) from dollar phrases."""
    out = []
    for m in re.finditer(
        r"\$?\s*([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)\b[^.]{0,80}",
        text,
        re.I,
    ):
        val = float(m.group(1).replace(",", ""))
        unit = m.group(2).lower()
        if unit in ("billion", "b"):
            val_b = val
        else:
            val_b = val / 1000.0
        snippet = text[max(0, m.start() - 20) : m.end() + 40].strip()
        out.append((snippet[:120], val_b))
    return out


def extract_note_tranches(text):
    tranches = []
    pat = re.compile(
        r"\$?\s*([\d,.]+)\s*billion\s+of\s+([\d.]+%)\s+Senior Notes due\s+(\d{4})",
        re.I,
    )
    for m in pat.finditer(text):
        tranches.append(
            {
                "amount_b": float(m.group(1).replace(",", "")),
                "coupon": m.group(2),
                "maturity": m.group(3),
            }
        )
    return tranches


def extract_items(text):
    items = []
    for m in re.finditer(r"Item\s+([\d.]+)\.\s*([^.\n]{5,120})", text, re.I):
        items.append(f"Item {m.group(1)}: {m.group(2).strip()}")
    return items[:6]


def extract_use_of_proceeds(text):
    for phrase in (
        r"intends? to use the net proceeds[^.]+\.",
        r"use of proceeds[^.]+\.",
        r"repay[^.]+\bbridge[^.]+\.",
        r"repay[^.]+\boutstanding borrowings[^.]+\.",
    ):
        m = re.search(phrase, text, re.I)
        if m:
            return m.group(0).strip()
    return ""


def extract_settlement(text):
    m = re.search(
        r"(?:expected to )?settle(?:ment)?(?: on| date)?\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        text,
        re.I,
    )
    return m.group(1) if m else ""


def extract_headline(text, form):
    lower = text.lower()
    if "priced" in lower and "senior notes" in lower:
        return "Bond offering priced (coupon and maturity set)"
    if "commenced an offering" in lower or "commenced a offering" in lower:
        return "New debt or securities offering commenced"
    if form.startswith("4"):
        return "Insider transaction reported (Form 4)"
    if "lock-up" in lower or "lockup" in lower:
        return "Lock-up or transfer restriction disclosure"
    if "earnings" in lower or "results of operations" in lower:
        return "Operating results or guidance"
    return f"Material event ({form})"


def upcoming_catalysts(entity_label, limit=3):
    today = datetime.now().date()
    label = entity_label.split("(")[0].strip()
    hits = []
    for ev in load_catalysts():
        ent = ev.get("entity", "")
        if ent not in (label, entity_label, "SpaceX", "SPCX") and "SpaceX" not in entity_label:
            if ent not in entity_label:
                continue
        try:
            d = datetime.strptime(ev["date"][:10], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            continue
        if d >= today:
            hits.append((d, ev))
    hits.sort(key=lambda x: x[0])
    return [ev for _, ev in hits[:limit]]


def parse_filing(text, form):
    tranches = extract_note_tranches(text)
    total_b = sum(t["amount_b"] for t in tranches) if tranches else None
    if total_b is None:
        amounts = extract_money(text)
        big = [a for a in amounts if a[1] >= 0.5]
        if big:
            total_b = max(a[1] for a in big)
    return {
        "headline": extract_headline(text, form),
        "items": extract_items(text),
        "tranches": tranches,
        "total_offering_b": total_b,
        "use_of_proceeds": extract_use_of_proceeds(text),
        "settlement": extract_settlement(text),
        "has_bridge_repay": bool(re.search(r"bridge loan", text, re.I)),
        "has_cash_disclosure": bool(re.search(r"\$[\d,.]+\s*billion.*cash", text, re.I)),
        "text_sample": text[:4000],
    }


def summarize(facts):
    lines = [facts["headline"]]
    if facts["tranches"]:
        lines.append(f"Total priced: ~${facts['total_offering_b']:.1f}B across {len(facts['tranches'])} tranches:")
        for t in facts["tranches"]:
            lines.append(f"  • ${t['amount_b']:.1f}B @ {t['coupon']} due {t['maturity']}")
    elif facts["total_offering_b"]:
        lines.append(f"Key size disclosed: ~${facts['total_offering_b']:.1f}B")
    if facts["use_of_proceeds"]:
        lines.append(f"Use of proceeds: {facts['use_of_proceeds']}")
    if facts["settlement"]:
        lines.append(f"Expected settlement: {facts['settlement']}")
    if facts["items"]:
        lines.append("Items filed: " + "; ".join(facts["items"][:3]))
    return "\n".join(lines)


def perspective_engineer(facts, entity_label):
    lines = []
    if facts["tranches"] and facts["has_bridge_repay"]:
        lines.append(
            "Capital stack move: unsecured notes replace short-dated bridge bank debt. "
            "Operationally this buys runway to fund Starlink, Starship, and xAI compute "
            "without issuing new equity today."
        )
        lines.append(
            "Engineering implication: proceeds retire the bridge facility that was funding "
            "the post-IPO debt overhang from the Twitter/X/xAI chain. Fixed-rate tranches "
            "lock in cost of capital out to 2031–2056 instead of floating bank exposure."
        )
    elif facts["has_bridge_repay"]:
        lines.append(
            "Debt refi event: filing confirms bridge repayment intent. "
            "Reduces near-term bank covenant / maturity engineering risk on the ops side."
        )
    elif facts["headline"].startswith("Insider"):
        lines.append(
            "Insider ledger update: mechanical SEC reporting of ownership changes. "
            "Check whether sale is 10b5-1, tax, or discretionary."
        )
    else:
        lines.append(
            "Read the exhibit for operational detail (contracts, launches, compute). "
            "8-K body is often legal wrapper; Exhibit 99.1 carries the substance."
        )
    if "SpaceX" in entity_label or "SPCX" in entity_label:
        lines.append(
            "Infrastructure lens: this issuer runs launch, satellite, and AI compute "
            "capex cycles measured in billions. Debt taps public markets; equity supply "
            "is still gated by lock-ups in the prospectus."
        )
    return "\n".join(lines)


def perspective_trader(facts, entity_label):
    lines = []
    if facts["tranches"]:
        lines.append(
            "Tradeable read: this is a DEBT print, not new equity float. "
            "Near-term SPCX supply impact is indirect (sentiment / overhang), not shares hitting the tape."
        )
        if facts["has_bridge_repay"]:
            lines.append(
                "Bridge paydown removes a known overhang from the June IPO narrative. "
                "Short-term: can support price if market was discounting refi risk. "
                "Medium-term: adds ~$25B fixed coupons to the capital structure."
            )
        lines.append(
            "Watch: bond pricing reception (order book), credit spreads vs Mag7, "
            "and whether SPCX equity trades as a levered growth proxy after settlement."
        )
    elif facts["headline"].startswith("Insider"):
        lines.append(
            "Form 4: check size vs 20-day volume, cluster with other insiders, "
            "and whether price is into strength (dossier H2/H6)."
        )
    else:
        lines.append(
            "Map filing to next dated catalyst on the calendar before sizing risk."
        )

    cats = upcoming_catalysts(entity_label)
    if cats:
        lines.append("Next dated supply/demand events on our calendar:")
        for ev in cats:
            lines.append(f"  • {ev['date']}: {ev['event']}")
    return "\n".join(lines)


def perspective_cfa(facts, entity_label):
    lines = []
    if facts["tranches"]:
        wavg = None
        if facts["total_offering_b"]:
            num = sum(t["amount_b"] * float(t["coupon"].rstrip("%")) for t in facts["tranches"])
            wavg = num / facts["total_offering_b"]
        lines.append(
            "Credit / structure: senior unsecured notes rank pari passu with existing "
            "unsubordinated debt. This extends duration and fixes coupons."
        )
        if wavg:
            lines.append(f"Blended coupon on priced tranches: ~{wavg:.2f}% (simple size-weighted).")
        lines.append(
            "Use of proceeds (bridge repayment + fees + general corporate) implies "
            "IPO cash and note proceeds are closing the Goldman bridge chapter, not "
            "returning capital to shareholders."
        )
        lines.append(
            "Equity holder lens: no dilution from this filing, but higher financial "
            "leverage and future interest burden. Monitor coverage once 10-Q debt footnotes update."
        )
    else:
        lines.append(
            "Treat as corporate finance or governance signal until quantified in financials."
        )

    chain = load_debt_chain()
    if chain and ("SpaceX" in entity_label or "SPCX" in entity_label):
        last = chain[-1]
        lines.append(
            f"Debt chain context: {last['date']} {last['event']} "
            f"(~${last['debt_outstanding_b']}B outstanding per dossier model)."
        )
    return "\n".join(lines)


def perspective_elon(facts, entity_label, filing):
    """What this filing means for Musk personally (control, liquidity, loop)."""
    lines = []
    form = filing.get("form", "")

    if facts["tranches"] and ("SpaceX" in entity_label or "SPCX" in entity_label):
        lines.append(
            "This is a company-level bond print, not a Musk Form 4. He does not receive "
            "cash from it personally today. His ~36% economic SPCX stake still cannot "
            "be sold until lock-up releases (largest block unlock: Jun 16, 2027 per prospectus)."
        )
        lines.append(
            "Personally, the win is balance-sheet cleanup: the Goldman bridge tied to the "
            "Twitter -> X -> xAI -> SpaceX debt relay gets retired with public-market notes. "
            "That removes a near-term refi sword over the vehicle he controls."
        )
        lines.append(
            "Loop read (H2/H12): Musk builds hype, takes the empire public, retains control, "
            "then realizes personal cash by selling existing stake into retail demand at "
            "dated unlock steps. This filing is infrastructure (debt refi), not the exit step."
        )
        lines.append(
            "Watch his personal ledger separately: TSLA Form 4 sales (~$40B cumulative in "
            "our dossier) remain the active personal liquidity channel while SPCX is gated."
        )
    elif form.startswith("4") or "Musk" in entity_label:
        lines.append(
            "Form 4 is direct personal ledger: shares sold, exercised, or gifted change "
            "his cash and control. Size and timing vs price strength test H2 (sell into demand)."
        )
        lines.append(
            "Cluster with other insiders and catalyst calendar before inferring intent "
            "(10b5-1 plan vs discretionary)."
        )
    elif "Tesla" in entity_label or "TSLA" in entity_label:
        lines.append(
            "Issuer filing: affects TSLA capital structure and governance, not necessarily "
            "Musk's personal sales today. Cross-check CIK 1494730 Form 4 stream for his moves."
        )
    else:
        lines.append(
            "Map to Musk only if he is reporting person, related party, or control person "
            "named in the exhibit."
        )
    return "\n".join(lines)


def supply_demand(facts, entity_label):
    lines = ["Demand vs supply (what actually moves the stock):"]
    if facts["tranches"]:
        lines.append(
            "• EQUITY SUPPLY: unchanged by this filing. Lock-up calendar still drives "
            "tradable float (next step Aug 20, 2026 ~7% pool per prospectus)."
        )
        lines.append(
            "• EQUITY DEMAND: debt deal can attract institutional credit buyers, not "
            "retail share buyers. Indirect bid possible if refi overhang clears."
        )
        lines.append(
            "• DEBT SUPPLY: +~${:.1f}B new notes to market (institutional allocation).".format(
                facts["total_offering_b"] or 0
            )
        )
        lines.append(
            "• FLOAT PSYCHOLOGY: removing bridge uncertainty may reduce forced-sale "
            "risk premium; does not add insider shares."
        )
    elif facts["headline"].startswith("Insider"):
        lines.append(
            "• SUPPLY: insider sale increases free float available at the margin; "
            "clustered Form 4s are the dossier's primary supply signal (H2/H5)."
        )
        lines.append(
            "• DEMAND: depends on retail/institutional absorption that day; "
            "cross-check vs unlock windows and hype cycle."
        )
    else:
        lines.append(
            "• Re-read for explicit share count, ATM, secondary, or lock-up language."
        )
    return "\n".join(lines)


def build_brief(entity_label, filing, text=None):
    if text is None:
        html = fetch(filing["url"])
        if not html:
            return None
        text = html_to_text(html)
    facts = parse_filing(text, filing["form"])
    brief = {
        "entity": entity_label,
        "form": filing["form"],
        "filing_date": filing["filingDate"],
        "url": filing["url"],
        "accession": filing.get("accession"),
        "dossier_url": DOSSIER_URL.rstrip("/"),
        "github_url": GITHUB_URL.rstrip("/"),
        "generated_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summarize(facts),
        "engineer": perspective_engineer(facts, entity_label),
        "trader": perspective_trader(facts, entity_label),
        "cfa": perspective_cfa(facts, entity_label),
        "elon": perspective_elon(facts, entity_label, filing),
        "supply_demand": supply_demand(facts, entity_label),
        "facts": {k: v for k, v in facts.items() if k != "text_sample"},
    }
    return brief


def _section_plain(title, body):
    body = _ascii(body.strip())
    return f"{title}\n{'-' * len(title)}\n{body}\n"


def format_email(brief, form_desc):
    """Return (plain_text, html) for multipart email."""
    sections = [
        ("WHAT HAPPENED", brief["summary"]),
        ("ENGINEER (ops / infrastructure)", brief["engineer"]),
        ("TRADER (price / positioning)", brief["trader"]),
        ("CFA (capital structure)", brief["cfa"]),
        ("ELON (personal / control / liquidity)", brief["elon"]),
        ("DEMAND & SUPPLY", brief["supply_demand"]),
    ]

    plain_parts = [
        "PERSONAL SEC BRIEF - read before reacting\n",
        f"{brief['entity']} | {brief['form']} | {brief['filing_date']}",
        form_desc,
        "",
        f"EDGAR filing:\n{brief['url']}",
        "",
        f"Live dossier (charts, catalysts, debt chain):\n{brief['dossier_url']}",
        "",
        f"GitHub repo (data + source):\n{brief['github_url']}",
        "",
    ]
    for title, body in sections:
        plain_parts.append(_section_plain(title, body))
    plain_parts.append(DISCLAIMER)
    plain = "\n".join(plain_parts)

    def esc(s):
        return (
            _ascii(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>\n")
        )

    html_sections = ""
    for title, body in sections:
        html_sections += f"""
<div style="margin: 20px 0 16px;">
  <div style="font-size: 13px; font-weight: 700; letter-spacing: 0.04em; color: #1a1a1a; border-bottom: 2px solid #2563eb; padding-bottom: 6px; margin-bottom: 10px;">{esc(title)}</div>
  <div style="font-size: 15px; line-height: 1.55; color: #333;">{esc(body)}</div>
</div>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:16px;background:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:8px;padding:20px 18px;box-shadow:0 1px 3px rgba(0,0,0,.08);">
  <div style="font-size:11px;font-weight:600;color:#2563eb;letter-spacing:.06em;text-transform:uppercase;">Personal SEC Brief</div>
  <h1 style="font-size:20px;line-height:1.3;margin:8px 0 4px;color:#111;">{_ascii(brief['entity'])}</h1>
  <p style="margin:0 0 14px;font-size:14px;color:#666;">{_ascii(brief['form'])} &middot; {_ascii(brief['filing_date'])} &middot; {_ascii(form_desc)}</p>
  <p style="margin:0 0 8px;font-size:14px;line-height:1.5;">
    <a href="{brief['url']}" style="color:#2563eb;word-break:break-all;">Read filing on EDGAR</a>
  </p>
  <p style="margin:0 0 16px;font-size:14px;line-height:1.5;">
    <a href="{brief['dossier_url']}" style="color:#2563eb;">Live dossier dashboard</a>
    &nbsp;&middot;&nbsp;
    <a href="{brief['github_url']}" style="color:#2563eb;">GitHub repo</a>
  </p>
  {html_sections}
  <p style="margin:20px 0 0;font-size:12px;color:#888;border-top:1px solid #eee;padding-top:12px;">{DISCLAIMER}</p>
</div>
</body></html>"""
    return plain, html


def save_brief(brief):
    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    acc = brief.get("accession") or "unknown"
    acc_safe = re.sub(r"[^\w-]", "_", acc)
    path = os.path.join(ANALYSIS_DIR, f"{acc_safe}.json")
    json.dump(brief, open(path, "w"), indent=2)
    try:
        from material_dates import sync_material_dates
        sync_material_dates()
    except Exception as e:
        print(f"material dates sync skipped: {e}")
    try:
        from filing_followups import register_from_brief
        register_from_brief(brief)
    except Exception as e:
        print(f"filing follow-up register skipped: {e}")
    return path


def sms_teaser(brief):
    first = _ascii(brief["summary"].split("\n")[0][:90])
    return (
        f"{brief['entity']} {brief['form']}: {first}\n"
        f"Dossier: {brief.get('dossier_url', DOSSIER_URL)}\n"
        f"EDGAR: {brief['url']}"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="EDGAR filing URL")
    ap.add_argument("--entity", default="Space Exploration Technologies (SPCX)")
    ap.add_argument("--form", default="8-K")
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    ap.add_argument("--test-spcx-pricing", action="store_true")
    ap.add_argument("--send", action="store_true", help="Email/SMS the brief (uses notify_channels)")
    args = ap.parse_args()

    if args.test_spcx_pricing:
        filing = {
            "url": "https://www.sec.gov/Archives/edgar/data/1181412/000162828026044955/spcx-pricing8xk.htm",
            "form": "8-K",
            "filingDate": "2026-06-23",
            "accession": "0001628280-26-044955",
        }
        entity = "Space Exploration Technologies (SPCX)"
    elif args.url:
        filing = {
            "url": args.url,
            "form": args.form,
            "filingDate": args.date,
            "accession": args.url.split("/")[-2] if "/" in args.url else None,
        }
        entity = args.entity
    else:
        ap.print_help()
        return 1

    brief = build_brief(entity, filing)
    if not brief:
        print("Could not fetch filing", file=sys.stderr)
        return 1
    body_plain, body_html = format_email(brief, "Material event report")
    print(body_plain)
    path = save_brief(brief)
    print(f"\nSaved {path}")
    if args.send:
        from editorial_packet import send_editorial_packet
        send_editorial_packet(brief, "Material event report", filing, sms_teaser)
        print("Editorial packet sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
