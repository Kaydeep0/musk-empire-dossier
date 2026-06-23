#!/usr/bin/env python3
"""Track SpaceX/SPCX filing follow-ups (D+1, D+3, D+7, settlement).

Checks run on sync; notes surface in daily digest and editorial packets.
"""
import json
import os
import re
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
STORE = os.path.join(DATA, "filing_followups.json")
LOG = os.path.join(DATA, "filing_followups_log.jsonl")
ALERTS = os.path.join(DATA, "filing_alerts.log")
SPACEX_INDEX = os.path.join(DATA, "spacex_filings_index.csv")


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


def _filings_after(since_date, exclude_accession=None):
    found = []
    if os.path.isfile(ALERTS):
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
            ent = parts[5] if len(parts) > 5 else ""
            if "space" not in ent.lower() and "spcx" not in ent.lower():
                continue
            found.append({
                "date": fdate,
                "form": parts[2],
                "desc": parts[3],
                "url": url,
            })
    return found[-5:]


def register_from_brief(brief):
    """Create a follow-up card when a SpaceX issuer brief is saved."""
    if not brief or not _is_spacex_brief(brief):
        return None
    form = brief.get("form") or ""
    if form not in ("8-K", "8-K/A", "424B4", "424B5", "S-1", "S-4", "DEF 14A", "DEFA14A"):
        return None

    acc = brief.get("accession")
    if not acc:
        return None

    state = _load()
    if any(c.get("accession") == acc for c in state["active"]):
        return None

    filed = brief.get("filing_date") or _utc_now()[:10]
    facts = brief.get("facts") or {}
    settlement = _parse_us_date(facts.get("settlement"))
    headline = facts.get("headline") or (brief.get("summary") or "").split("\n")[0]

    checks = []
    base = _parse_date(filed)
    if base:
        for offset, label in ((1, "d+1"), (3, "d+3"), (7, "d+7")):
            checks.append({
                "kind": label,
                "due": (base + timedelta(days=offset)).strftime("%Y-%m-%d"),
                "sent": False,
            })
    if settlement:
        checks.append({
            "kind": "settlement",
            "due": settlement.strftime("%Y-%m-%d"),
            "sent": False,
        })

    expect = []
    if facts.get("settlement") or facts.get("has_bridge_repay"):
        expect.append("Confirm settlement or bridge payoff in a follow-on 8-K")
    if facts.get("tranches"):
        expect.append("Watch SPCX price and credit reception after bond pricing")
    expect.append("Next supply step on material dates calendar (Aug 20 unlock)")

    card = {
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
    _save(state)
    _log("registered", card, f"Follow-up card opened for {form} {filed[:10]}")
    return card


def card_for_accession(accession):
    if not accession:
        return None
    for c in _load().get("active", []):
        if c.get("accession") == accession:
            return c
    return None


def followup_watch_lines(accession=None):
    """Short lines for editorial packet."""
    state = _load()
    card = None
    if accession:
        card = card_for_accession(accession)
    if not card and state.get("active"):
        card = state["active"][-1]
    if not card:
        return []
    lines = [f"Opened {card.get('filed')}: {card.get('headline', '')[:70]}"]
    for ex in card.get("expect") or []:
        lines.append(f"  Watch: {ex}")
    pending = [c for c in card.get("checks") or [] if not c.get("sent")]
    if pending:
        lines.append(f"  Next check: {pending[0].get('kind')} on {pending[0].get('due')}")
    return lines


def check_followups(today=None):
    """Run due checks; return new notes for digest (no separate email)."""
    today = today or datetime.utcnow().strftime("%Y-%m-%d")
    today_d = _parse_date(today)
    state = _load()
    notes = []

    for card in state.get("active", []):
        filed = card.get("filed")
        new_filings = _filings_after(filed, exclude_accession=card.get("accession"))
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
                    f"Follow-up ({chk.get('kind')}): new {nf.get('form')} filed {nf.get('date')} "
                    f"after {card.get('headline', '')[:50]}. {nf.get('desc', '')[:80]}"
                )
            else:
                note = (
                    f"Follow-up ({chk.get('kind')}): no new SpaceX EDGAR filing yet since "
                    f"{card.get('filed')} ({card.get('headline', '')[:50]})."
                )
                if card.get("settlement") and chk.get("kind") == "settlement":
                    note += f" Expected settlement: {card.get('settlement')}."
            chk["sent"] = True
            chk["note"] = note
            chk["checked_at"] = _utc_now()
            notes.append(note)
            _log("check", card, note)
            updated = True

        if updated:
            if all(c.get("sent") for c in card.get("checks") or []):
                card["status"] = "complete"
                state["closed"].append(card)
                state["active"] = [c for c in state["active"] if c.get("accession") != card.get("accession")]

    _save(state)
    return notes


def digest_lines(limit=5):
    """Lines for daily digest FOLLOW-UP QUEUE section."""
    state = _load()
    lines = []
    for card in state.get("active", [])[:3]:
        lines.append(f"{card.get('filed')} {card.get('form')}: {card.get('headline', '')[:60]}")
        pending = [c for c in card.get("checks") or [] if not c.get("sent")]
        if pending:
            lines.append(f"  Next check {pending[0].get('kind')} due {pending[0].get('due')}")
        for chk in card.get("checks") or []:
            if chk.get("sent") and chk.get("note") and chk.get("checked_at", "")[:10] == _utc_now()[:10]:
                lines.append(f"  {chk.get('note')[:120]}")
    recent = []
    if os.path.isfile(LOG):
        for line in open(LOG, encoding="utf-8").readlines()[-limit:]:
            try:
                recent.append(json.loads(line))
            except Exception:
                pass
    for row in reversed(recent):
        if row.get("kind") == "check" and row.get("note"):
            lines.append(row["note"][:140])
    return lines[:limit]


if __name__ == "__main__":
    notes = check_followups()
    print(f"follow-up checks: {len(notes)}")
    for n in notes:
        print(" ", n[:100])
