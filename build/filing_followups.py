#!/usr/bin/env python3
"""Track follow-ups for SpaceX issuer filings and Musk personal CIK filings.

Checks run on sync; notes surface in daily digest and editorial packets.
"""
import json
import os
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
STORE = os.path.join(DATA, "filing_followups.json")
LOG = os.path.join(DATA, "filing_followups_log.jsonl")
ALERTS = os.path.join(DATA, "filing_alerts.log")
MUSK_CIK = "1494730"


def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load():
    if os.path.isfile(STORE):
        try:
            return json.load(open(STORE, encoding="utf-8"))
        except Exception:
            pass
    return {"active": [], "closed": []}


def _save(state):
    os.makedirs(DATA, exist_ok=True)
    json.dump(state, open(STORE, "w"), indent=2)


def _log(kind, card, note):
    os.makedirs(DATA, exist_ok=True)
    row = {
        "ts": _utc_now(),
        "kind": kind,
        "lane": card.get("lane"),
        "accession": card.get("accession"),
        "filed": card.get("filed"),
        "headline": card.get("headline"),
        "note": note,
    }
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _is_spacex_brief(brief):
    entity = (brief.get("entity") or "").upper()
    return "SPCX" in entity or "SPACE" in entity


def _is_musk_brief(brief):
    entity = brief.get("entity") or ""
    url = brief.get("url") or ""
    if "Musk" in entity or "1494730" in url.replace("-", ""):
        return True
    return False


def _parse_date(s):
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _parse_us_date(text):
    if not text:
        return None
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(text.strip()[:20], fmt).date()
        except ValueError:
            continue
    return None


def _filings_after(since_date, lane, exclude_accession=None):
    found = []
    if not os.path.isfile(ALERTS):
        return found
    for line in open(ALERTS, encoding="utf-8"):
        parts = line.strip().split("\t")
        if len(parts) < 5:
            continue
        fdate = parts[1][:10]
        if fdate < since_date:
            continue
        url = parts[4]
        acc = url.split("/")[-2] if "/" in url else ""
        if exclude_accession and acc and exclude_accession.replace("-", "") in acc.replace("-", ""):
            continue
        ent = (parts[5] if len(parts) > 5 else "").lower()
        form = parts[2]
        if lane == "spacex":
            if "space" not in ent and "spcx" not in ent:
                continue
        elif lane == "musk":
            if MUSK_CIK not in url and "musk" not in ent:
                continue
        found.append({
            "date": fdate,
            "form": form,
            "desc": parts[3],
            "url": url,
            "entity": parts[5] if len(parts) > 5 else "",
        })
    return found[-5:]


def _add_checks(base_date, offsets):
    checks = []
    base = _parse_date(base_date)
    if not base:
        return checks
    for offset, label in offsets:
        checks.append({
            "kind": label,
            "due": (base + timedelta(days=offset)).strftime("%Y-%m-%d"),
            "sent": False,
        })
    return checks


def _register_spacex(brief, state):
    form = brief.get("form") or ""
    if form not in ("8-K", "8-K/A", "424B4", "424B5", "S-1", "S-4", "DEF 14A", "DEFA14A"):
        return None

    acc = brief.get("accession")
    if not acc or any(c.get("accession") == acc for c in state["active"]):
        return None

    filed = brief.get("filing_date") or _utc_now()[:10]
    facts = brief.get("facts") or {}
    settlement = _parse_us_date(facts.get("settlement"))
    headline = facts.get("headline") or (brief.get("summary") or "").split("\n")[0]

    checks = _add_checks(filed, ((1, "d+1"), (3, "d+3"), (7, "d+7")))
    if settlement:
        checks.append({"kind": "settlement", "due": settlement.strftime("%Y-%m-%d"), "sent": False})

    expect = []
    if facts.get("settlement") or facts.get("has_bridge_repay"):
        expect.append("Confirm settlement or bridge payoff in a follow-on 8-K")
    if facts.get("tranches"):
        expect.append("Watch SPCX price and credit reception after bond pricing")
    expect.append("Next supply step on material dates calendar (Aug 20 unlock)")

    card = {
        "lane": "spacex",
        "accession": acc,
        "entity": brief.get("entity"),
        "form": form,
        "filed": filed[:10],
        "headline": headline,
        "url": brief.get("url"),
        "settlement": facts.get("settlement"),
        "expect": expect,
        "checks": checks,
        "status": "watching",
        "created": _utc_now(),
    }
    state["active"].append(card)
    _log("registered", card, f"SpaceX follow-up opened for {form} {filed[:10]}")
    return card


def _register_musk(brief, state):
    """All Musk CIK filings get a follow-up card (not just material forms)."""
    acc = brief.get("accession")
    if not acc or any(c.get("accession") == acc for c in state["active"]):
        return None

    form = brief.get("form") or "Filing"
    filed = brief.get("filing_date") or _utc_now()[:10]
    headline = (brief.get("summary") or "").split("\n")[0] or f"Musk {form}"

    offsets = ((1, "d+1"), (3, "d+3"))
    if form.startswith("4"):
        offsets = ((1, "d+1"), (3, "d+3"), (7, "d+7"))
    checks = _add_checks(filed, offsets)

    expect = []
    if form.startswith("4"):
        expect.append("Personal ledger: sale vs exercise vs gift; 10b5-1 footnote if present")
        expect.append("Cross-check TSLA price/volume vs dossier H2 sell-into-demand thesis")
        expect.append("Separate from SPCX issuer filings (company vs person)")
    elif form in ("3", "5"):
        expect.append("Baseline ownership snapshot; compare to prior Form 4 cluster")
    else:
        expect.append("Map to control, related-party, or personal liquidity channel")

    card = {
        "lane": "musk",
        "accession": acc,
        "entity": brief.get("entity"),
        "form": form,
        "filed": filed[:10],
        "headline": headline,
        "url": brief.get("url"),
        "expect": expect,
        "checks": checks,
        "status": "watching",
        "created": _utc_now(),
    }
    state["active"].append(card)
    _log("registered", card, f"Musk personal follow-up opened for {form} {filed[:10]}")
    return card


def register_from_brief(brief):
    if not brief:
        return None
    state = _load()
    card = None
    if _is_musk_brief(brief):
        card = _register_musk(brief, state)
    elif _is_spacex_brief(brief):
        card = _register_spacex(brief, state)
    _save(state)
    return card


def card_for_accession(accession):
    if not accession:
        return None
    for c in _load().get("active", []):
        if c.get("accession") == accession:
            return c
    return None


def followup_watch_lines(accession=None):
    state = _load()
    card = card_for_accession(accession) if accession else None
    if not card and state.get("active"):
        card = state["active"][-1]
    if not card:
        return []

    lane = "Musk personal" if card.get("lane") == "musk" else "SpaceX public"
    lines = [f"[{lane}] Opened {card.get('filed')}: {card.get('headline', '')[:70]}"]
    for ex in card.get("expect") or []:
        lines.append(f"  Watch: {ex}")
    pending = [c for c in card.get("checks") or [] if not c.get("sent")]
    if pending:
        lines.append(f"  Next check: {pending[0].get('kind')} on {pending[0].get('due')}")
    return lines


def check_followups(today=None):
    today = today or datetime.utcnow().strftime("%Y-%m-%d")
    state = _load()
    notes = []

    for card in state.get("active", []):
        lane = card.get("lane") or "spacex"
        label = "Musk" if lane == "musk" else "SpaceX"
        new_filings = _filings_after(card.get("filed"), lane, exclude_accession=card.get("accession"))
        updated = False
        for chk in card.get("checks") or []:
            if chk.get("sent"):
                continue
            due = chk.get("due")
            if not due or due > today:
                continue
            if new_filings:
                nf = new_filings[-1]
                note = (
                    f"[{label}] Follow-up ({chk.get('kind')}): new {nf.get('form')} "
                    f"{nf.get('date')} after {card.get('headline', '')[:45]}. "
                    f"{nf.get('desc', '')[:70]}"
                )
            else:
                note = (
                    f"[{label}] Follow-up ({chk.get('kind')}): no new filing yet since "
                    f"{card.get('filed')} ({card.get('headline', '')[:45]})."
                )
                if card.get("settlement") and chk.get("kind") == "settlement":
                    note += f" Expected settlement: {card.get('settlement')}."
            chk["sent"] = True
            chk["note"] = note
            chk["checked_at"] = _utc_now()
            notes.append(note)
            _log("check", card, note)
            updated = True

        if updated and all(c.get("sent") for c in card.get("checks") or []):
            card["status"] = "complete"
            state["closed"].append(card)
            state["active"] = [c for c in state["active"] if c.get("accession") != card.get("accession")]

    _save(state)
    return notes


def digest_lines(limit=8):
    state = _load()
    lines = []
    musk_cards = [c for c in state.get("active", []) if c.get("lane") == "musk"][:2]
    spacex_cards = [c for c in state.get("active", []) if c.get("lane") != "musk"][:2]
    for card in musk_cards + spacex_cards:
        tag = "Musk" if card.get("lane") == "musk" else "SpaceX"
        lines.append(f"[{tag}] {card.get('filed')} {card.get('form')}: {card.get('headline', '')[:55]}")
        pending = [c for c in card.get("checks") or [] if not c.get("sent")]
        if pending:
            lines.append(f"  Next check {pending[0].get('kind')} due {pending[0].get('due')}")
    if os.path.isfile(LOG):
        for line in reversed(open(LOG, encoding="utf-8").readlines()[-limit:]):
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("kind") == "check" and row.get("note"):
                lines.append(row["note"][:140])
    return lines[:limit]


if __name__ == "__main__":
    notes = check_followups()
    print(f"follow-up checks: {len(notes)}")
    for n in notes:
        print(" ", n[:100])
