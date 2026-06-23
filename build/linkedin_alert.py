#!/usr/bin/env python3
"""Send ntfy alert + save LinkedIn draft when the live site is updated.

Post style (all filing alerts):
  1. Just in: [actual filing headline]
  2. Short cascading paragraphs (Marjunal-style)
  3. Source: SEC EDGAR link + dossier
  No em-dashes or en-dashes in post text.
"""
import json
import os
import re
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
DRAFT = os.path.join(DATA, "linkedin_draft_latest.txt")
POST_ONLY = os.path.join(DATA, "linkedin_post_latest.txt")
SITE = os.environ.get("MUSK_DOSSIER_URL", "https://kaydeep0.github.io/musk-empire-dossier/")
NEWSLETTER = "https://www.linkedin.com/newsletters/money-in-motion-7054180694628995073"

from notify_channels import alert_all  # noqa: E402


def load_json(path, default=None):
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception:
            pass
    return default if default is not None else {}


def latest_filing_brief():
    d = os.path.join(DATA, "filing_analyses")
    if not os.path.isdir(d):
        return None
    files = sorted(
        [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".json")],
        key=os.path.getmtime,
        reverse=True,
    )
    return load_json(files[0]) if files else None


def next_catalyst(within_days=120):
    today = datetime.now(timezone.utc).date()
    best = None
    for ev in load_json(os.path.join(DATA, "catalyst_calendar.json"), []):
        try:
            d = datetime.strptime(ev["date"][:10], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            continue
        delta = (d - today).days
        if 0 <= delta <= within_days:
            if best is None or delta < best[0]:
                best = (delta, ev)
    return best[1] if best else None


def top_pattern():
    mem = load_json(os.path.join(ROOT, "public", "empire_memory.json"))
    if not mem:
        mem = load_json(os.path.join(DATA, "empire_memory", "patterns.json"), [])
    patterns = mem.get("patterns") if isinstance(mem, dict) else mem
    if not patterns:
        return None
    for strength in ("emerging", "confirmed", "watch"):
        for p in patterns:
            if p.get("strength") == strength:
                return p
    return patterns[0] if patterns else None


def _sanitize(text):
    """Strip em-dashes, en-dashes, and arrow glyphs from post copy."""
    if not text:
        return ""
    t = text.replace("\u2014", ", ")  # em dash
    t = t.replace("\u2013", " to ")   # en dash
    t = t.replace("\u2192", " to ")   # right arrow
    t = re.sub(r",\s*,", ",", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _clean_proceeds(text):
    if not text:
        return ""
    t = _sanitize(text.strip().rstrip("."))
    if len(t) > 180:
        t = t[:177] + "..."
    return t


def _headline(brief):
    facts = brief.get("facts") or {}
    headline = facts.get("headline") or ""
    if not headline and brief.get("summary"):
        headline = brief["summary"].split("\n")[0]
    return _sanitize(headline)


def _short_entity(entity):
    e = entity or ""
    if "Space" in e or "SPCX" in e:
        return "SpaceX"
    if "Tesla" in e:
        return "Tesla"
    if "Musk" in e:
        return "Elon Musk"
    short = _sanitize(e.split("(")[0].strip())
    return short or "Musk entity"


def _money_hook(text):
    """Pull the biggest dollar figure from brief text for a punchy hook."""
    if not text:
        return None
    best = None
    for m in re.finditer(r"~\$\s*([\d,.]+)\s*([BbMm])", text):
        val = float(m.group(1).replace(",", ""))
        mult = 1e9 if m.group(2).upper() == "B" else 1e6
        amt = val * mult
        if best is None or amt > best[0]:
            best = (amt, val, m.group(2).upper())
    if not best:
        return None
    val, unit = best[1], best[2]
    if unit == "B":
        label = f"~${val:.0f}B" if val >= 10 else f"~${val:.1f}B"
    else:
        label = f"~${val:.0f}M"
    return label


def _scroll_hook(brief):
    """Line 1: scroll-stop news. Stakes first, not filing metadata."""
    if not brief:
        return "Just in: new SEC filing on the Musk empire."

    form = brief.get("form") or "SEC filing"
    facts = brief.get("facts") or {}
    name = _short_entity(brief.get("entity"))
    summary = brief.get("summary") or ""
    headline = _headline(brief)

    if facts.get("tranches") or facts.get("has_bridge_repay"):
        total = facts.get("total_offering_b") or 25
        return f"Just in: {name} priced ~${total:.0f}B of inaugural bonds."

    if str(form).startswith("4"):
        hl = headline.lower()
        if "sale" in hl or "sold" in hl:
            money = _money_hook(summary)
            if money:
                return f"Just in: Elon Musk sold {money} of stock."
            return "Just in: Elon Musk sold stock again."
        if "purchase" in hl or "bought" in hl:
            return "Just in: Elon Musk bought stock on the open market."
        return "Just in: Elon Musk just filed a Form 4."

    money = _money_hook(summary) or _money_hook(headline)
    if money and form in ("8-K", "8-K/A"):
        return f"Just in: {name} disclosed a {money} move."

    if "lock" in headline.lower():
        return f"Just in: {name} lock-up terms just changed."

    if "proxy" in form.lower() or "DEF" in form:
        return f"Just in: {name} dropped a new proxy. Read the dates."

    if headline and len(headline) < 72 and not headline.lower().startswith("material event"):
        return f"Just in: {name} {headline[0].lower() + headline[1:]}."

    return f"Just in: {name} just filed a new {form}."


def _hook_subline(brief):
    """Line 2: payoff or why you should keep reading."""
    if not brief:
        return "Fresh from EDGAR. Full breakdown below."

    form = brief.get("form") or ""
    facts = brief.get("facts") or {}
    date = brief.get("filing_date") or ""
    headline = _headline(brief)

    if facts.get("tranches") or facts.get("has_bridge_repay"):
        return "No new shares. This is a debt print, not an equity unlock."

    if str(form).startswith("4"):
        summary = _sanitize((brief.get("summary") or "").split("\n")[0])
        if summary:
            return summary + "."
        return "Form 4 is the personal ledger. 8-K is the company ledger."

    trader = _sanitize((brief.get("trader") or "").split("\n")[0])
    if trader.lower().startswith("tradeable read:"):
        trader = trader.split(":", 1)[1].strip()
    if trader and len(trader) < 120:
        return trader[0].upper() + trader[1:] + ("" if trader.endswith(".") else ".")

    if headline:
        return headline + "."

    cite = f"SEC {form} filed {date}." if date else f"SEC {form} just hit EDGAR."
    return cite


def _filing_cite(brief):
    """Compact filing attribution for the source block."""
    if not brief:
        return None
    entity = _sanitize(brief.get("entity") or "")
    form = brief.get("form") or "Filing"
    date = brief.get("filing_date") or ""
    if date:
        return f"{entity} | {form} | {date}"
    return f"{entity} | {form}"


def _opening_block(brief):
    """Two-beat hook: attention, then payoff."""
    return [
        f"🔴 {_scroll_hook(brief)}",
        "",
        _hook_subline(brief),
        "",
    ]


def _source_footer(brief):
    lines = ["Source:"]
    cite = _filing_cite(brief)
    if cite:
        lines.append(cite)
    url = brief.get("url") if brief else None
    if url:
        lines.append(url)
    lines += ["", f"Dossier: {SITE}", "", "Educational only. Not investment advice."]
    return lines


def _is_filing_trigger(reason, brief):
    if brief and brief.get("form"):
        return True
    r = (reason or "").lower()
    return any(k in r for k in ("filing", "8-k", "form 4", "form4", "issuer", "material event"))


def compose_form4(brief, catalyst, pattern):
    if brief:
        lines = _opening_block(brief)
    else:
        lines = [
            "🔴 Just in: Elon Musk just filed a Form 4.",
            "",
            "The personal ledger moved again.",
            "",
        ]

    lines += [
        "Company 8-Ks tell you what the vehicle did.",
        "",
        "Form 4 tells you what the person did.",
        "",
        "Those are not the same trade.",
        "",
    ]

    if brief:
        elon = _sanitize((brief.get("elon") or "").split("\n")[0])
        if elon:
            lines += [elon + ".", ""]

    lines += [
        "The dossier thesis is simple.",
        "",
        "Hype builds a vehicle.",
        "",
        "Control stays concentrated.",
        "",
        "Cash exits when shares sell into demand.",
        "",
        "TSLA Form 4 sales are the active personal liquidity channel (~$40B cumulative in our ledger).",
        "",
        "SPCX economic stake is still gated by lock-ups.",
        "",
    ]

    if catalyst:
        lines += [
            f"Next dated supply step: {catalyst['date'][:10]}.",
            "",
            f"{_sanitize(catalyst.get('event', ''))}.",
            "",
        ]

    lines += _source_footer(brief)
    return "\n".join(lines)


def compose_spcx_bond(brief, m, b, catalyst, pattern):
    facts = brief.get("facts") if brief else {}
    tranches = facts.get("tranches") or []
    total = facts.get("total_offering_b") or 25

    if brief:
        lines = _opening_block(brief)
    else:
        lines = [
            f"🔴 Just in: SpaceX priced ~${total:.0f}B of inaugural bonds.",
            "",
            "No new shares. This is a debt print, not an equity unlock.",
            "",
        ]

    if tranches:
        lines += [
            "The filing prices senior unsecured notes.",
            "",
            f"Five tranches. Roughly ${total:.0f}B total.",
            "",
            "Coupons run 5.35% to 6.65%.",
            "",
            "Maturities run 2031 to 2056.",
            "",
        ]
        settlement = facts.get("settlement")
        if settlement:
            lines += [f"Expected settlement: {settlement}.", ""]
    elif b:
        cash = b.get("cash_disclosed_b")
        if cash:
            lines += [f"Issuer disclosed ~${cash}B cash on the balance sheet.", ""]

    proceeds = _clean_proceeds(facts.get("use_of_proceeds") or (b or {}).get("use_of_proceeds"))
    if proceeds:
        p = proceeds.rstrip(".")
        lines += [f"Use of proceeds: {p}.", ""]

    lines += [
        "The June IPO gave SpaceX public-market cash.",
        "",
        "But the Goldman bridge from the Twitter to X to xAI debt relay was still on the balance sheet.",
        "",
        "So the company did not need to sell new shares to fix the cap table.",
        "",
        "It issued bonds instead.",
        "",
        "That means no new insider shares hit the tape from this filing.",
        "",
        "Markets may read it as refi relief.",
        "",
        "One overhang cleared before the supply calendar wakes up.",
        "",
    ]

    if catalyst:
        lines += [
            f"But the prospectus still has a date circled: {catalyst['date'][:10]}.",
            "",
            f"{_sanitize(catalyst.get('event', 'Lock-up step'))}.",
            "",
            "Infrastructure filings and supply filings are different animals.",
            "",
            "One fixes the balance sheet.",
            "",
            "The other changes who can sell.",
            "",
        ]

    if pattern and pattern.get("name"):
        summary = _sanitize(pattern.get("summary") or "")
        if len(summary) > 220:
            summary = summary[:217] + "..."
        lines += [
            f"The pattern our dossier tracks: {pattern['name'].lower()}.",
            "",
            summary,
            "",
        ]

    if m and m.get("price"):
        lines += [
            (
                f"SPCX last ${m['price']}. "
                f"{m.get('pct_vs_ipo', 0):+.0f}% vs the $135 IPO. "
                f"{m.get('pct_vs_ath', 0):+.0f}% vs the day-one high."
            ),
            "",
        ]

    lines += _source_footer(brief)
    return "\n".join(lines)


def compose_generic_filing(brief, m, catalyst, pattern):
    lines = _opening_block(brief)

    summary_lines = [_sanitize(ln) for ln in (brief.get("summary") or "").split("\n") if ln.strip()]
    for ln in summary_lines[1:3]:
        if ln and not ln.startswith("•"):
            lines += [ln + ".", ""]

    supply = _sanitize((brief.get("supply_demand") or "").split("\n")[0])
    if supply:
        lines += [supply + ".", ""]

    if catalyst:
        lines += [
            f"Next dated catalyst: {catalyst['date'][:10]}.",
            "",
            f"{_sanitize(catalyst.get('event', ''))}.",
            "",
        ]

    if pattern and pattern.get("name"):
        lines += [f"Pattern flagged: {pattern['name'].lower()}.", ""]

    if m and m.get("price"):
        lines += [f"SPCX ${m['price']} ({m.get('pct_vs_ipo', 0):+.0f}% vs IPO).", ""]

    lines += _source_footer(brief)
    return "\n".join(lines)


def compose_site_update(m, b, catalyst, pattern, brief):
    """Dossier rebuild post when no filing brief is available."""
    if brief:
        return compose_from_brief(brief, m, b, catalyst, pattern)

    lines = [
        "🔴 Just in: the Musk empire dossier rebuilt from fresh SEC filings.",
        "",
        "Most Musk coverage chases the headline.",
        "",
        "We chase the filing.",
        "",
        "That is where the dates and dollar amounts actually live.",
        "",
        "You see Tesla, SpaceX, Twitter debt, lock-ups, related parties.",
        "",
        "Behind that story is a repeatable loop.",
        "",
        "Build hype.",
        "",
        "List or absorb.",
        "",
        "Retain control.",
        "",
        "Sell into demand.",
        "",
        "Roll into the next vehicle.",
        "",
    ]

    if b:
        lines += [
            f"Latest issuer signal: {b.get('event')} ({b.get('date')}).",
            "",
        ]
        proceeds = _clean_proceeds(b.get("use_of_proceeds"))
        if proceeds:
            lines += [f"Proceeds: {proceeds}.", ""]

    if catalyst:
        lines += [
            f"Next dated test: {catalyst['date'][:10]}.",
            "",
            f"{_sanitize(catalyst.get('event', ''))}.",
            "",
        ]

    if pattern:
        lines += [f"Pattern flagged: {pattern.get('name')}.", ""]

    if m and m.get("price"):
        lines += [f"SPCX ${m['price']} ({m.get('pct_vs_ipo', 0):+.0f}% vs IPO).", ""]

    lines += [
        f"Dossier: {SITE}",
        "",
        f"Newsletter: {NEWSLETTER}",
        "",
        "Educational only. Not investment advice.",
    ]
    return "\n".join(lines)


def compose_from_brief(brief, m, b, catalyst, pattern):
    form = str(brief.get("form") or "")
    facts = brief.get("facts") or {}

    if form.startswith("4"):
        return compose_form4(brief, catalyst, pattern)
    if facts.get("tranches") or facts.get("has_bridge_repay"):
        return compose_spcx_bond(brief, m, b, catalyst, pattern)
    if b and "note" in (b.get("event") or "").lower() and not brief:
        return compose_spcx_bond(brief, m, b, catalyst, pattern)
    return compose_generic_filing(brief, m, catalyst, pattern)


def compose_post(reason="site published", details=None):
    spcx = load_json(os.path.join(DATA, "spcx_market.json"))
    m = (spcx.get("market") or {}) if spcx else {}
    b = (spcx.get("bond") or {}) if spcx else {}
    brief = latest_filing_brief()
    catalyst = next_catalyst()
    pattern = top_pattern()

    if details and "🔴" in details:
        post = _sanitize(details)
    elif _is_filing_trigger(reason, brief) and brief:
        post = compose_from_brief(brief, m, b, catalyst, pattern)
    elif brief and (reason or "").lower() != "site published":
        post = compose_from_brief(brief, m, b, catalyst, pattern)
    else:
        post = compose_site_update(m, b, catalyst, pattern, brief)

    return _finalize(post)


def _finalize(text):
    """Ensure no dash glyphs slip through and blank lines stay clean."""
    out = []
    for line in text.split("\n"):
        clean = line.replace("\u2014", ", ").replace("\u2013", " to ").replace("\u2192", " to ")
        out.append(clean.rstrip())
    return "\n".join(out).strip()


def build_draft(reason, details=None):
    post = compose_post(reason, details)
    hook_line = next((ln for ln in post.split("\n") if ln.strip()), "Dossier update")
    hook_line = hook_line.replace("🔴 ", "")[:80]
    internal = [
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Trigger: {reason}",
        f"Site: {SITE}",
        "",
        "--- COPY BELOW TO LINKEDIN ---",
        "",
        post,
        "",
        "--- END POST ---",
    ]
    return post, "\n".join(internal), hook_line


def notify(title, body, priority="high", tags="warning,memo"):
    alert_all(title, body, priority=priority, tags=tags)


def alert_linkedin_post(reason="site published", details=None):
    post, full_draft, hook = build_draft(reason, details)
    os.makedirs(DATA, exist_ok=True)
    open(DRAFT, "w", encoding="utf-8").write(full_draft)
    open(POST_ONLY, "w", encoding="utf-8").write(post)

    email_body = f"Copy-paste this to LinkedIn:\n\n{post}"
    notify(f"POST TO LINKEDIN: {hook[:55]}", email_body)
    print("linkedin post:", POST_ONLY)
    print("full draft:", DRAFT)
    return POST_ONLY


if __name__ == "__main__":
    import sys
    reason = sys.argv[1] if len(sys.argv) > 1 else "8-K material event"
    details = sys.argv[2] if len(sys.argv) > 2 else None
    alert_linkedin_post(reason, details)
