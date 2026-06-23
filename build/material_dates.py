#!/usr/bin/env python3
"""Merge manual catalyst calendar + auto-extracted filing dates into one tracker.

Each date carries plain-English context (what it is, why it matters, what to watch).
Used by the live site, memory agent, and date_reminders.py alerts.
"""
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
CATALYST_PATH = os.path.join(DATA, "catalyst_calendar.json")
ANALYSIS_DIR = os.path.join(DATA, "filing_analyses")
OUT_PATH = os.path.join(DATA, "material_dates.json")
LOG_PATH = os.path.join(DATA, "material_dates_log.jsonl")
OUTCOMES_PATH = os.path.join(DATA, "material_date_outcomes.json")
PUBLIC_OUT = os.path.join(ROOT, "public", "material_dates.json")
SITE = os.environ.get("MUSK_DOSSIER_URL", "https://kaydeep0.github.io/musk-empire-dossier/")

sys.path.insert(0, HERE)
try:
    from dossier_constants import INSTANT_REMIND_DAYS, DIGEST_REMIND_DAYS
except ImportError:
    INSTANT_REMIND_DAYS = {1, 3}
    DIGEST_REMIND_DAYS = {7}


def _parse_us_date(text):
    if not text:
        return None
    text = text.strip()
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:20].strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    return m.group(1) if m else None


def _entity_key(entity):
    e = (entity or "").upper()
    if "SPCX" in e or "SPACE" in e:
        return "SPCX"
    if "TESLA" in e or "TSLA" in e:
        return "TSLA"
    if "MUSK" in e:
        return "Musk"
    return (entity or "Unknown").split("(")[0].strip()[:24]


def _dedupe_key(item):
    return (item.get("date"), item.get("entity"), (item.get("event") or "")[:60])


def load_brief_for_item(item):
    acc = item.get("accession")
    if not acc or not os.path.isdir(ANALYSIS_DIR):
        return None
    safe = re.sub(r"[^\w-]", "_", acc)
    path = os.path.join(ANALYSIS_DIR, f"{safe}.json")
    if os.path.isfile(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception:
            pass
    for name in os.listdir(ANALYSIS_DIR):
        if acc.replace("-", "") in name.replace("-", ""):
            try:
                return json.load(open(os.path.join(ANALYSIS_DIR, name), encoding="utf-8"))
            except Exception:
                pass
    return None


def enrich_context_from_brief(item, ctx):
    brief = load_brief_for_item(item)
    if not brief:
        return ctx
    out = dict(ctx)
    parts = []
    trader_lines = [ln.strip() for ln in (brief.get("trader") or "").split("\n") if ln.strip()]
    for ln in trader_lines[:2]:
        if ln.lower().startswith("tradeable read:"):
            ln = ln.split(":", 1)[1].strip()
        if len(ln) > 20:
            parts.append(ln.rstrip("."))
    supply_lines = [ln.strip() for ln in (brief.get("supply_demand") or "").split("\n") if ln.strip() and not ln.startswith("•")]
    if supply_lines:
        parts.append(supply_lines[0].rstrip("."))
    for ln in (brief.get("summary") or "").split("\n")[1:4]:
        ln = ln.strip()
        if ln and not ln.startswith("•") and any(k in ln.lower() for k in ("settlement", "proceeds", "unlock", "tranche")):
            parts.append(ln.rstrip("."))
    if parts:
        filing_bit = " ".join(parts[:2])
        if len(filing_bit) > 240:
            filing_bit = filing_bit[:237] + "..."
        out["why_it_matters"] = out.get("why_it_matters", "") + " Per the filing: " + filing_bit + "."
    for ln in trader_lines:
        if ln.lower().startswith("watch:"):
            out["what_to_watch"] = ln.split(":", 1)[1].strip()[:220]
            break
    return out


def explain_date(item):
    """Plain-English context for alerts and the live dossier."""
    typ = (item.get("type") or "catalyst").lower()
    ev = (item.get("event") or "").lower()
    entity = item.get("entity") or "Issuer"

    if typ == "settlement" or "settlement" in ev:
        return {
            "what_it_is": (
                "The bond trade settles. Cash moves from buyers to the company. "
                "The notes become live debt on the balance sheet."
            ),
            "why_it_matters": (
                "This is not new equity hitting the market. It closes the refi chapter: "
                "proceeds typically retire the Goldman bridge tied to the Twitter to X to xAI relay. "
                "After settlement, the story shifts from 'can they refinance?' to 'what supply date is next?'"
            ),
            "what_to_watch": (
                "Credit reception vs Mag7 peers, SPCX price vs IPO, any 8-K confirming bridge payoff, "
                "and whether equity trades as a levered growth proxy after the overhang clears."
            ),
            "thesis_note": "Infrastructure filing (H12) before tradable float expands (H5/H6).",
        }

    if "unlock" in ev and ("musk" in ev or "6.4" in ev or "largest" in ev):
        return {
            "what_it_is": (
                "The largest Musk-linked SPCX lock-up tranche becomes eligible to sell. "
                "This is the biggest single supply step on the calendar."
            ),
            "why_it_matters": (
                "Musk's economic stake is gated until these dates. When the block unlocks, "
                "the question is not whether he can sell, but whether retail demand absorbs supply "
                "without breaking the scarcity premium built at IPO."
            ),
            "what_to_watch": (
                "Form 4 filings (personal ledger), volume spikes, price vs $135 IPO and day-one high, "
                "10b5-1 plan disclosures, and whether selling clusters after strength."
            ),
            "thesis_note": "Core H2 exit channel + H5 supply step at empire scale.",
        }

    if "unlock" in ev or "lock-up" in ev or "lock up" in ev:
        return {
            "what_it_is": (
                "Shares that were restricted at IPO become free to trade. "
                "Tradable float expands; insiders and early holders may sell."
            ),
            "why_it_matters": (
                "Debt filings fix the balance sheet. Unlock dates change who can sell. "
                "This is a direct supply event: more shares can hit the tape even if the company "
                "does not issue new stock."
            ),
            "what_to_watch": (
                "Float change vs prospectus pool size, first-week volume, price reaction, "
                "and any Form 4 or 8-K confirming sales or transfers."
            ),
            "thesis_note": "Tests H5/H6: does scarcity premium survive when float roughly doubles?",
        }

    if "bridge" in ev and ("trigger" in ev or "175" in ev):
        return {
            "what_it_is": (
                "A contractual window tied to the Goldman bridge facility ends. "
                "Pricing or refi triggers tied to the stock price may no longer apply the same way."
            ),
            "why_it_matters": (
                "The bridge was the short-dated debt left from the Twitter acquisition chain. "
                "Missing this window can mean repricing, extension, or forced refi at worse terms."
            ),
            "what_to_watch": (
                "New debt 8-Ks, bridge balance in footnotes, credit spread moves, "
                "and whether bond proceeds already retired the facility."
            ),
            "thesis_note": "H12 debt buys time; this is a timing hinge on the traveling-debt chain (H7).",
        }

    if "maturity" in ev or "cliff" in ev:
        return {
            "what_it_is": (
                "A large debt facility comes due or must be refinanced. "
                "This is a balance-sheet cliff, not a share unlock."
            ),
            "why_it_matters": (
                "If cash and market access are insufficient, the issuer must refinance, renegotiate, "
                "or sell assets/equity. At ~$11B+ scale this is an infrastructure event for the whole empire loop."
            ),
            "what_to_watch": (
                "New bond prints, bridge extensions, covenant waivers, equity issuance rumors, "
                "and credit rating commentary."
            ),
            "thesis_note": "H12+H7: debt travels across vehicles until public markets absorb it.",
        }

    if "remainder lock" in ev or "180-day" in ev:
        return {
            "what_it_is": (
                "The customary 180-day IPO lock-up expires for the remaining restricted pool."
            ),
            "why_it_matters": (
                "After earlier partial unlocks, this is the broadest release of still-gated IPO shares. "
                "Supply pressure can compound if prior unlocks already softened the price."
            ),
            "what_to_watch": (
                "Total float vs prospectus, volume trend into the date, "
                "insider selling patterns, and whether the stock held premium into the event."
            ),
            "thesis_note": "H5 supply step; compare to SolarCity/Tesla unlock cadence in the dossier.",
        }

    return {
        "what_it_is": f"A pre-registered date for {entity} from SEC docs or the dossier calendar.",
        "why_it_matters": (
            "The Musk empire thesis is date-driven: hype, listing, lock-ups, refi, and personal sales "
            "each have filing-backed timestamps. This date is one of those tests."
        ),
        "what_to_watch": "New EDGAR filings around the date, price/volume, and memory-agent pattern flags.",
        "thesis_note": item.get("hypothesis") or "See dossier hypothesis map (H1-H14).",
    }


def is_major_date(item):
    """Major dates get email reminders; minor/historical anchors do not."""
    if item.get("major") is False:
        return False
    typ = (item.get("type") or "").lower()
    ev = (item.get("event") or "").lower()
    days = item.get("days_until", 0)
    if typ in ("settlement",):
        return True
    if "unlock" in ev or "lock-up" in ev or "lock up" in ev:
        return True
    if "bridge" in ev or "maturity" in ev or "cliff" in ev:
        return True
    if typ == "catalyst" and "offering" in ev:
        return False
    return typ == "catalyst" and days >= 0 and ("unlock" in ev or "bridge" in ev or "lock" in ev)


def _remind_schedule(item):
    ev = (item.get("event") or "").lower()
    instant = sorted(INSTANT_REMIND_DAYS)
    digest = sorted(DIGEST_REMIND_DAYS)
    if "unlock" in ev or "lock-up" in ev:
        return instant + digest
    if (item.get("type") or "") == "settlement":
        return instant + digest
    if "bridge" in ev or "maturity" in ev or "cliff" in ev:
        return instant + digest
    return instant or [1]


def dates_from_catalysts():
    items = []
    if not os.path.isfile(CATALYST_PATH):
        return items
    for c in json.load(open(CATALYST_PATH, encoding="utf-8")):
        items.append({
            "date": c.get("date"),
            "entity": c.get("entity"),
            "event": c.get("event"),
            "type": "catalyst",
            "hypothesis": c.get("hypothesis"),
            "basis": c.get("basis", "b"),
            "source_kind": "manual",
            "source": c.get("source"),
            "url": None,
            "accession": None,
        })
    return items


def dates_from_filing_briefs():
    items = []
    if not os.path.isdir(ANALYSIS_DIR):
        return items
    for name in os.listdir(ANALYSIS_DIR):
        if not name.endswith(".json"):
            continue
        path = os.path.join(ANALYSIS_DIR, name)
        try:
            brief = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        entity = _entity_key(brief.get("entity"))
        facts = brief.get("facts") or {}
        acc = brief.get("accession")
        url = brief.get("url")
        form = brief.get("form")

        settlement = facts.get("settlement")
        if settlement:
            iso = _parse_us_date(settlement)
            if iso:
                items.append({
                    "date": iso,
                    "entity": entity,
                    "event": f"Bond offering expected settlement ({settlement})",
                    "type": "settlement",
                    "hypothesis": "H12",
                    "basis": "b",
                    "source_kind": "filing",
                    "source": f"SEC {form} filed {brief.get('filing_date')}",
                    "url": url,
                    "accession": acc,
                })

    return items


def enrich(items, today=None):
    today = today or datetime.utcnow().strftime("%Y-%m-%d")
    out = []
    for c in items:
        if not c.get("date"):
            continue
        row = dict(c)
        delta = (datetime.strptime(c["date"], "%Y-%m-%d") - datetime.strptime(today, "%Y-%m-%d")).days
        row["days_until"] = delta
        if delta < 0:
            row["status"] = "past"
        elif delta <= 14:
            row["status"] = "soon"
        elif delta <= 60:
            row["status"] = "upcoming"
        else:
            row["status"] = "future"
        row["context"] = enrich_context_from_brief(row, explain_date(row))
        row["major"] = is_major_date(row) if "major" not in row else row["major"]
        row["remind_days"] = _remind_schedule(row)
        row["remind_instant"] = sorted(set(row["remind_days"]) & INSTANT_REMIND_DAYS)
        row["remind_digest"] = sorted(set(row["remind_days"]) & DIGEST_REMIND_DAYS)
        out.append(row)
    return sorted(out, key=lambda x: x["date"])


def sync_material_dates(today=None):
    merged = {}
    for item in dates_from_catalysts() + dates_from_filing_briefs():
        key = _dedupe_key(item)
        if key not in merged or item.get("source_kind") == "filing":
            merged[key] = item
    items = enrich(list(merged.values()), today)
    os.makedirs(DATA, exist_ok=True)
    json.dump(items, open(OUT_PATH, "w"), indent=2)
    os.makedirs(os.path.dirname(PUBLIC_OUT), exist_ok=True)
    json.dump({
        "updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "site": SITE,
        "dates": items,
        "timeline_log": "data/material_dates_log.jsonl",
        "outcomes": json.load(open(OUTCOMES_PATH, encoding="utf-8")) if os.path.isfile(OUTCOMES_PATH) else [],
    }, open(PUBLIC_OUT, "w"), indent=2)
    return items


def upcoming(limit=10, within_days=120, today=None):
    today = today or datetime.utcnow().strftime("%Y-%m-%d")
    items = sync_material_dates(today) if not os.path.isfile(OUT_PATH) else enrich(
        json.load(open(OUT_PATH, encoding="utf-8")), today
    )
    hits = [i for i in items if 0 <= i.get("days_until", -1) <= within_days]
    return hits[:limit]


def due_soon(within_days=3, today=None):
    today = today or datetime.utcnow().strftime("%Y-%m-%d")
    items = json.load(open(OUT_PATH, encoding="utf-8")) if os.path.isfile(OUT_PATH) else sync_material_dates(today)
    items = enrich(items, today)
    return [i for i in items if 0 <= i.get("days_until", 999) <= within_days and is_major_date(i)]


def load_timeline(limit=30):
    if not os.path.isfile(LOG_PATH):
        return []
    lines = open(LOG_PATH, encoding="utf-8").read().strip().splitlines()
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return list(reversed(out))


if __name__ == "__main__":
    items = sync_material_dates()
    print(f"Wrote {len(items)} material dates -> {OUT_PATH}")
    major = [i for i in items if i.get("major") and i.get("days_until", -1) >= 0]
    for i in major[:6]:
        ctx = i.get("context") or {}
        print(f"\n  {i['date']} ({i['days_until']}d) remind={i.get('remind_days')}")
        print(f"  {i['event'][:65]}")
        print(f"  -> {ctx.get('why_it_matters', '')[:90]}...")
