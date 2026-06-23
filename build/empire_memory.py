#!/usr/bin/env python3
"""
Empire Memory Agent — longitudinal memory across Musk ecosystem entities.

Ingests filing briefs, alerts, catalysts, debt chain, market syncs.
Detects emerging patterns. Publishes public/empire_memory.json for the site.

  python3 build/empire_memory.py --init          # seed entity canon + history
  python3 build/empire_memory.py --ingest        # ingest new sources (default)
  python3 build/empire_memory.py --synthesize    # rebuild patterns + narrative
  python3 build/empire_memory.py --digest      # email memory digest (if configured)
  python3 build/empire_memory.py --sync          # init + ingest + synthesize + publish
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from collections import defaultdict

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
MEM = os.path.join(DATA, "empire_memory")
EVENTS = os.path.join(MEM, "events.jsonl")
ENTITIES = os.path.join(MEM, "entities.json")
PATTERNS = os.path.join(MEM, "patterns.json")
SYNTHESIS = os.path.join(MEM, "synthesis.json")
STATE = os.path.join(MEM, "state.json")
PUBLIC = os.path.join(ROOT, "public", "empire_memory.json")

sys.path.insert(0, HERE)
from load_registry import load_watch_entities  # noqa: E402

DISCLAIMER = "Educational research memory. Not investment advice."
SITE_URL = os.environ.get("MUSK_DOSSIER_URL", "https://kaydeep0.github.io/musk-empire-dossier/")


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path, default=None):
    if not os.path.isfile(path):
        return default if default is not None else {}
    return json.load(open(path, encoding="utf-8"))


def save_json(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    json.dump(obj, open(path, "w"), indent=2)


def load_state():
    return load_json(STATE, {
        "initialized": False,
        "seen_event_ids": [],
        "last_ingest": None,
        "last_synthesis": None,
        "event_count": 0,
    })


def save_state(st):
    st["seen_event_ids"] = st["seen_event_ids"][-5000:]
    save_json(STATE, st)


def entity_canon():
    """Static + registry knowledge each entity 'knows by heart'."""
    registry = load_watch_entities()
    canon = {}
    seeds = {
        "musk": {
            "role": "Reporting insider CIK 1494730; spine of sell timeline",
            "loop_position": "Operator at center of hype -> vehicle -> exit loop",
            "liquidity": "TSLA Form 4 sales ~$40B cumulative; SPCX locked until 2027-06-16",
            "control": "Super-voting / trust structures across TSLA and SPCX",
            "watch": ["Form 4 clusters", "13D/G", "lock-up adjacent sales"],
        },
        "spacex": {
            "ticker": "SPCX",
            "role": "Latest public vehicle; absorbed X and xAI",
            "loop_position": "IPO Jun 2026 at $135; ~5% float initially",
            "debt": "Twitter $13B traveled here; $20B Goldman bridge; notes offering Jun 2026",
            "supply": "Lock-ups Aug 2026, Dec 2026, Musk block Jun 2027",
            "watch": ["8-K bond/refi", "unlock calendar", "Valor leases"],
        },
        "tesla": {
            "ticker": "TSLA",
            "role": "Primary public cash-extraction vehicle historically",
            "loop_position": "SolarCity absorption prototype 2016",
            "liquidity": "Form 4 sales into strength (H3)",
            "watch": ["Form 4", "DEF 14A comp", "Megapack sales to SpaceX"],
        },
        "twitter": {
            "ticker": "TWTR (defunct)",
            "role": "2022 LBO; debt carrier into X/xAI/SpaceX chain",
            "loop_position": "Going-private step in loop",
            "watch": ["Historical; debt now on SpaceX"],
        },
        "solarcity": {
            "ticker": "SCTY (acquired)",
            "role": "2016 Tesla absorption; related-party prototype",
            "loop_position": "Early loop iteration",
        },
    }
    for ent in registry:
        key = ent["key"]
        base = seeds.get(key, {})
        canon[key] = {
            "key": key,
            "label": ent["label"],
            "cik": ent["cik"],
            "kind": ent["kind"],
            "ticker": ent.get("ticker") or base.get("ticker", ""),
            "canon": base,
            "event_count": 0,
            "last_event_date": None,
            "last_event_summary": None,
            "themes": [],
            "updated": utcnow(),
        }
    return canon


def load_events():
    if not os.path.isfile(EVENTS):
        return []
    out = []
    for line in open(EVENTS, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def append_events(new_events, state):
    seen = set(state.get("seen_event_ids", []))
    added = []
    os.makedirs(MEM, exist_ok=True)
    with open(EVENTS, "a", encoding="utf-8") as f:
        for ev in new_events:
            eid = ev.get("id")
            if not eid or eid in seen:
                continue
            ev.setdefault("ingested_at", utcnow())
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
            seen.add(eid)
            added.append(ev)
    state["seen_event_ids"] = list(seen)
    state["event_count"] = len(seen)
    state["last_ingest"] = utcnow()
    return added


def map_entity_label(label):
    label = (label or "").lower()
    if "musk" in label and "reporting" in label:
        return "musk"
    if "spacex" in label or "spc" in label:
        return "spacex"
    if "tesla" in label:
        return "tesla"
    if "twitter" in label:
        return "twitter"
    if "solarcity" in label:
        return "solarcity"
    return None


def events_from_filing_analyses():
    d = os.path.join(DATA, "filing_analyses")
    if not os.path.isdir(d):
        return []
    out = []
    for fn in os.listdir(d):
        if not fn.endswith(".json"):
            continue
        b = load_json(os.path.join(d, fn))
        acc = b.get("accession") or fn.replace(".json", "")
        key = map_entity_label(b.get("entity", ""))
        headline = (b.get("summary") or "").split("\n")[0][:200]
        out.append({
            "id": f"filing-brief-{acc}",
            "date": b.get("filing_date"),
            "entity_key": key or "spacex",
            "entity_label": b.get("entity"),
            "type": "filing_brief",
            "form": b.get("form"),
            "headline": headline,
            "url": b.get("url"),
            "accession": acc,
            "lenses": {
                "engineer": (b.get("engineer") or "")[:400],
                "trader": (b.get("trader") or "")[:400],
                "cfa": (b.get("cfa") or "")[:400],
                "elon": (b.get("elon") or "")[:400],
            },
            "tags": _tags_from_brief(b),
        })
    return out


def _tags_from_brief(b):
    tags = []
    text = json.dumps(b).lower()
    if "bridge" in text:
        tags.append("debt_refi")
    if "bond" in text or "notes" in text:
        tags.append("bond_offering")
    if "form 4" in text or b.get("form", "").startswith("4"):
        tags.append("insider_trade")
    if "lock" in text:
        tags.append("supply")
    if "no dilution" in text or "unchanged" in text and "supply" in text:
        tags.append("no_equity_supply")
    return tags


def events_from_alerts_log():
    log = os.path.join(DATA, "filing_alerts.log")
    if not os.path.isfile(log):
        return []
    out = []
    for line in open(log, encoding="utf-8"):
        parts = line.strip().split("\t")
        if len(parts) < 5:
            continue
        seen_at, fdate, form, desc, url = parts[:5]
        entity = parts[5] if len(parts) > 5 else "Elon Musk"
        key = map_entity_label(entity)
        acc = url.split("/")[-2] if "/" in url else seen_at
        out.append({
            "id": f"alert-{acc}-{form}",
            "date": fdate,
            "entity_key": key or "musk",
            "entity_label": entity,
            "type": "sec_alert",
            "form": form,
            "headline": desc,
            "url": url,
            "seen_at": seen_at,
        })
    return out


def events_from_debt_chain():
    path = os.path.join(DATA, "debt_chain.csv")
    if not os.path.isfile(path):
        return []
    out = []
    for r in csv.DictReader(open(path, encoding="utf-8")):
        ent = (r.get("entity") or "").lower()
        key = "spacex" if "space" in ent else ("twitter" if "twitter" in ent or ent == "x" else "xai" if "xai" in ent else ent)
        if key in ("x", "xai"):
            key = "twitter"
        out.append({
            "id": f"debt-{r.get('date')}-{key}",
            "date": r.get("date"),
            "entity_key": key,
            "entity_label": r.get("entity"),
            "type": "debt_chain",
            "headline": r.get("event"),
            "debt_outstanding_b": float(r.get("debt_outstanding_b") or 0),
            "tags": ["debt_travel", "H12"],
        })
    return out


def events_from_catalysts():
    path = os.path.join(DATA, "material_dates.json")
    if not os.path.isfile(path):
        path = os.path.join(DATA, "catalyst_calendar.json")
    if not os.path.isfile(path):
        return []
    out = []
    for c in load_json(path, []):
        ent = (c.get("entity") or "").upper()
        key = "spacex" if ent in ("SPCX", "SPACEX", "SPACEX") else map_entity_label(ent) or "spacex"
        out.append({
            "id": f"catalyst-{c.get('date')}-{key}-{c.get('type', 'x')}",
            "date": c.get("date"),
            "entity_key": key,
            "entity_label": c.get("entity"),
            "type": c.get("type") or "catalyst",
            "headline": c.get("event"),
            "hypothesis": c.get("hypothesis"),
            "tags": ["supply", "catalyst", c.get("type", ""), c.get("hypothesis", "")[:20]],
        })
    return out


def events_from_spacex_edgar():
    path = os.path.join(DATA, "spacex_events.json")
    if not os.path.isfile(path):
        return []
    data = load_json(path)
    out = []
    for ev in data.get("events") or []:
        acc = ev.get("accession", "")
        out.append({
            "id": f"spacex-edgar-{acc}",
            "date": ev.get("filing_date"),
            "entity_key": "spacex",
            "entity_label": "Space Exploration Technologies (SPCX)",
            "type": "issuer_filing",
            "form": ev.get("form"),
            "headline": ev.get("event"),
            "url": ev.get("url"),
            "accession": acc,
            "tags": ["bond_offering"] if ev.get("bond_offering") else ["8-K"],
        })
    return out


def events_from_form4_summary():
    path = os.path.join(DATA, "transactions.csv")
    if not os.path.isfile(path):
        return []
    by_year = defaultdict(lambda: {"count": 0, "usd": 0.0})
    for r in csv.DictReader(open(path, encoding="utf-8")):
        if r.get("code") != "S":
            continue
        y = (r.get("transaction_date") or "")[:4]
        try:
            v = float(r.get("value_usd") or 0)
        except ValueError:
            continue
        if v > 0 and y:
            by_year[y]["count"] += 1
            by_year[y]["usd"] += v
    out = []
    for y in sorted(by_year.keys()):
        info = by_year[y]
        out.append({
            "id": f"form4-year-{y}",
            "date": f"{y}-12-31",
            "entity_key": "musk",
            "entity_label": "Elon Musk",
            "type": "form4_aggregate",
            "headline": f"TSLA open-market sales {y}: {info['count']} trades, ${info['usd']/1e9:.2f}B",
            "usd_b": round(info["usd"] / 1e9, 2),
            "trade_count": info["count"],
            "tags": ["H2", "insider_sale", "tesla"],
        })
    return out


def events_from_timeseries():
    path = os.path.join(DATA, "timeseries", "live.jsonl")
    if not os.path.isfile(path):
        return []
    lines = open(path, encoding="utf-8").read().strip().splitlines()
    if not lines:
        return []
    try:
        last = json.loads(lines[-1])
    except json.JSONDecodeError:
        return []
    ts = last.get("ts", utcnow())
    date = ts[:10]
    return [{
        "id": f"sync-daily-{date}",
        "date": ts[:10],
        "entity_key": "portfolio",
        "entity_label": "Portfolio proxy",
        "type": "market_sync",
        "headline": f"SPCX ${last.get('spcx')} TSLA ${last.get('tsla')} NW ${last.get('net_worth_b')}B",
        "metrics": last,
        "tags": ["market", "timeseries"],
    }]


def collect_all_sources():
    sources = []
    sources.extend(events_from_debt_chain())
    sources.extend(events_from_catalysts())
    sources.extend(events_from_form4_summary())
    sources.extend(events_from_spacex_edgar())
    sources.extend(events_from_alerts_log())
    sources.extend(events_from_filing_analyses())
    sources.extend(events_from_timeseries())
    return sources


def update_entity_profiles(canon, events):
    by_key = defaultdict(list)
    for ev in events:
        k = ev.get("entity_key")
        if k and k in canon:
            by_key[k].append(ev)
        elif k == "portfolio":
            pass
    for key, prof in canon.items():
        evs = sorted(by_key.get(key, []), key=lambda e: e.get("date") or "")
        prof["event_count"] = len(evs)
        if evs:
            last = evs[-1]
            prof["last_event_date"] = last.get("date")
            prof["last_event_summary"] = last.get("headline")
        themes = defaultdict(int)
        for ev in evs:
            for t in ev.get("tags") or []:
                if t:
                    themes[t] += 1
        prof["themes"] = [{"tag": t, "count": c} for t, c in sorted(themes.items(), key=lambda x: -x[1])[:8]]
        prof["updated"] = utcnow()
    return canon


def detect_patterns(events, canon):
    """Rule-based pattern detection across event memory."""
    today = datetime.now(timezone.utc).date()
    patterns = []
    by_date = sorted(events, key=lambda e: e.get("date") or "")

    debt_events = [e for e in events if e.get("type") == "debt_chain" or "debt_travel" in (e.get("tags") or [])]
    if len(debt_events) >= 4:
        patterns.append({
            "id": "H12_debt_relay",
            "name": "Debt travels across vehicles",
            "strength": "confirmed",
            "hypothesis": "H12",
            "summary": (
                f"{len(debt_events)} dated steps from Twitter LBO through X/xAI to SpaceX bridge and refi. "
                "Leverage migrates via common-control combinations, not clean paydown at each step."
            ),
            "entities": list({e.get("entity_key") for e in debt_events}),
            "evidence_ids": [e.get("id") for e in debt_events[-6:]],
        })

    bond_briefs = [e for e in events if e.get("type") == "filing_brief" and "bond_offering" in (e.get("tags") or [])]
    catalysts = [e for e in events if e.get("type") == "catalyst"]
    unlocks = [c for c in catalysts if "unlock" in (c.get("headline") or "").lower()]
    if bond_briefs and unlocks:
        patterns.append({
            "id": "refi_before_supply",
            "name": "Infrastructure before supply step",
            "strength": "emerging",
            "hypothesis": "H12 + H5",
            "summary": (
                "Bond/refi filings (bridge repayment) landed before the first major lock-up unlock (Aug 2026). "
                "Company clears bank overhang before tradable float expands — reduces forced-sale risk, "
                "does not reduce insider share count."
            ),
            "entities": ["spacex"],
            "evidence_ids": [bond_briefs[-1].get("id")] + [unlocks[0].get("id")],
        })

    form4_years = [e for e in events if e.get("type") == "form4_aggregate"]
    if form4_years:
        total_b = sum(e.get("usd_b", 0) for e in form4_years)
        patterns.append({
            "id": "H2_cumulative_extraction",
            "name": "Payday is the sale (TSLA)",
            "strength": "confirmed",
            "hypothesis": "H2",
            "summary": (
                f"Parsed Form 4 open-market sales total ~${total_b:.1f}B across {len(form4_years)} years. "
                "Primary personal liquidity channel while SPCX economic stake remains lock-up gated."
            ),
            "entities": ["musk", "tesla"],
            "evidence_ids": [e.get("id") for e in form4_years[-3:]],
        })

    upcoming = []
    for c in catalysts:
        try:
            d = datetime.strptime(c.get("date", "")[:10], "%Y-%m-%d").date()
            delta = (d - today).days
            if 0 <= delta <= 120:
                upcoming.append((delta, c))
        except ValueError:
            pass
    upcoming.sort(key=lambda x: (x[0], x[1].get("date") or "", x[1].get("id") or ""))
    if len(upcoming) >= 2:
        patterns.append({
            "id": "supply_staircase_2026",
            "name": "Supply staircase H1 2026-27",
            "strength": "watch",
            "hypothesis": "H5/H6",
            "summary": (
                f"{len(upcoming)} catalysts in next 120 days: "
                + "; ".join(f"{c.get('date')[:10]} {c.get('headline','')[:40]}" for _, c in upcoming[:4])
                + ". Pattern to watch: each step tests whether retail absorbs insider-adjacent supply."
            ),
            "entities": ["spacex", "musk"],
            "evidence_ids": [c.get("id") for _, c in upcoming[:4]],
        })

    no_supply = [e for e in bond_briefs if "no_equity_supply" in (e.get("tags") or [])]
    if no_supply:
        patterns.append({
            "id": "infrastructure_not_exit",
            "name": "Debt print ≠ equity exit",
            "strength": "confirmed",
            "hypothesis": "loop mechanics",
            "summary": (
                "Recent bond pricing 8-K adds ~$25B notes and retires bridge — classified as cap-structure "
                "infrastructure. Musk personal exit channel (Form 4 / unlock) not activated by this filing."
            ),
            "entities": ["spacex", "musk"],
            "evidence_ids": [no_supply[-1].get("id")],
        })

    loop_entities = ["solarcity", "twitter", "spacex"]
    loop_hits = [k for k in loop_entities if k in canon and canon[k].get("event_count", 0) > 0]
    if len(loop_hits) >= 2:
        patterns.append({
            "id": "loop_repetition",
            "name": "Repeatable empire loop",
            "strength": "emerging",
            "hypothesis": "master thesis",
            "summary": (
                "Same structural moves recur: SolarCity into Tesla (2016), Twitter debt into SpaceX IPO (2026). "
                "Hype -> vehicle -> control wedge -> belief premium -> exit -> roll. Testing whether SPCX "
                "follows the same supply calendar as prior vehicles."
            ),
            "entities": loop_hits,
            "evidence_ids": [],
        })

    return patterns


def build_synthesis(events, patterns, canon):
    today = utcnow()[:10]
    recent = sorted(events, key=lambda e: e.get("date") or "", reverse=True)[:12]

    narrative_parts = [
        f"As of {today}, the memory agent tracks {len(events)} events across "
        f"{len(canon)} entities (Musk, SPCX, Tesla, and related vehicles).",
    ]

    strong = [p for p in patterns if p.get("strength") == "confirmed"]
    emerging = [p for p in patterns if p.get("strength") == "emerging"]
    watch = [p for p in patterns if p.get("strength") == "watch"]

    if strong:
        narrative_parts.append(
            "Confirmed patterns: " + "; ".join(p["name"] for p in strong[:3]) + "."
        )
    if emerging:
        narrative_parts.append(
            "Emerging now: " + "; ".join(p["name"] for p in emerging[:2]) + "."
        )
    if watch:
        narrative_parts.append(
            "On watch: " + "; ".join(p["name"] for p in watch[:2]) + "."
        )

    sp = canon.get("spacex", {})
    musk = canon.get("musk", {})
    narrative_parts.append(
        f"SPCX last signal ({sp.get('last_event_date')}): {sp.get('last_event_summary', 'n/a')}. "
        f"Musk ledger focus: {musk.get('canon', {}).get('liquidity', 'Form 4 stream')}."
    )

    return {
        "updated_at": utcnow(),
        "disclaimer": DISCLAIMER,
        "narrative": " ".join(narrative_parts),
        "recent_events": [
            {"date": e.get("date"), "entity": e.get("entity_label"), "headline": e.get("headline"), "type": e.get("type")}
            for e in recent
        ],
        "pattern_count": len(patterns),
        "entity_count": len(canon),
        "event_count": len(events),
    }


def publish_public(canon, patterns, synthesis, events):
    payload = {
        "updated_at": utcnow(),
        "disclaimer": DISCLAIMER,
        "site_url": SITE_URL.rstrip("/"),
        "synthesis": synthesis,
        "patterns": patterns,
        "entities": {
            k: {
                "label": v.get("label"),
                "ticker": v.get("ticker"),
                "kind": v.get("kind"),
                "canon": v.get("canon"),
                "event_count": v.get("event_count"),
                "last_event_date": v.get("last_event_date"),
                "last_event_summary": v.get("last_event_summary"),
                "themes": v.get("themes"),
            }
            for k, v in canon.items()
        },
        "timeline": sorted(
            [
                {
                    "date": e.get("date"),
                    "entity_key": e.get("entity_key"),
                    "entity": e.get("entity_label"),
                    "type": e.get("type"),
                    "headline": e.get("headline"),
                    "url": e.get("url"),
                    "tags": e.get("tags"),
                }
                for e in events
            ],
            key=lambda x: x.get("date") or "",
            reverse=True,
        )[:80],
    }
    save_json(PUBLIC, payload)
    return PUBLIC


def format_digest_email(synthesis, patterns, added):
    lines = [
        "EMPIRE MEMORY DIGEST",
        "=" * 40,
        "",
        synthesis.get("narrative", ""),
        "",
        "PATTERNS TRACKED",
        "-" * 40,
    ]
    for p in patterns:
        lines.append(f"[{p.get('strength', '?').upper()}] {p.get('name')}")
        lines.append(f"  {p.get('summary', '')[:300]}")
        lines.append("")
    if added:
        lines.append("NEW EVENTS THIS RUN")
        lines.append("-" * 40)
        for e in added[:8]:
            lines.append(f"  {e.get('date')} | {e.get('entity_label')} | {e.get('headline', '')[:80]}")
    lines.extend(["", f"Full memory: {SITE_URL.rstrip('/')}/#memory", "", DISCLAIMER])
    return "\n".join(lines)


def cmd_init(state):
    os.makedirs(MEM, exist_ok=True)
    canon = entity_canon()
    save_json(ENTITIES, canon)
    state["initialized"] = True
    save_state(state)
    print(f"initialized entity canon: {len(canon)} entities")


def cmd_ingest(state):
    if not state.get("initialized"):
        cmd_init(state)
    sources = collect_all_sources()
    added = append_events(sources, state)
    events = load_events()
    canon = load_json(ENTITIES) or entity_canon()
    canon = update_entity_profiles(canon, events)
    save_json(ENTITIES, canon)
    save_state(state)
    print(f"ingested {len(added)} new events ({len(events)} total)")
    return added, events, canon


def cmd_synthesize(state):
    events = load_events()
    canon = load_json(ENTITIES) or entity_canon()
    canon = update_entity_profiles(canon, events)
    patterns = detect_patterns(events, canon)
    synthesis = build_synthesis(events, patterns, canon)
    save_json(ENTITIES, canon)
    save_json(PATTERNS, patterns)
    save_json(SYNTHESIS, synthesis)
    path = publish_public(canon, patterns, synthesis, events)
    state["last_synthesis"] = utcnow()
    save_state(state)
    print(f"synthesis: {len(patterns)} patterns, {len(events)} events")
    print(f"published {path}")
    return patterns, synthesis


def cmd_digest(state, added=None):
    synthesis = load_json(SYNTHESIS, {})
    patterns = load_json(PATTERNS, [])
    if not synthesis:
        cmd_synthesize(state)
        synthesis = load_json(SYNTHESIS, {})
        patterns = load_json(PATTERNS, [])
    body = format_digest_email(synthesis, patterns, added or [])
    try:
        from notify_channels import send_email
        send_email("Empire memory digest", body)
        print("digest email sent")
    except Exception as e:
        print(f"digest email skipped: {e}")
        print(body[:1500])


def main():
    ap = argparse.ArgumentParser(description="Empire memory agent")
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--ingest", action="store_true")
    ap.add_argument("--synthesize", action="store_true")
    ap.add_argument("--digest", action="store_true", help="Email memory digest")
    ap.add_argument("--sync", action="store_true", help="Full pipeline")
    args = ap.parse_args()

    state = load_state()
    if args.init:
        cmd_init(state)
    if args.sync or args.ingest or (not any(vars(args).values())):
        added, _, _ = cmd_ingest(state)
    else:
        added = []
    if args.sync or args.synthesize or (not any(vars(args).values())):
        cmd_synthesize(state)
    if args.digest:
        cmd_digest(state, added if (args.sync or args.ingest) else None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
