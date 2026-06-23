#!/usr/bin/env python3
"""Validate public site artifacts after sync (links, JSON, exhibits)."""
import json
import os
import re
import sys

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
PUBLIC = os.path.join(ROOT, "public")
DATA = os.path.join(ROOT, "data")


def fail(msg):
    print(f"FAIL: {msg}")
    return False


def ok(msg):
    print(f"OK: {msg}")
    return True


def check_status_json():
    path = os.path.join(PUBLIC, "status.json")
    if not os.path.isfile(path):
        return fail("status.json missing")
    st = json.load(open(path, encoding="utf-8"))
    required = (
        "updated_at", "latest_musk_filing", "latest_spacex_filing",
        "latest_tesla_filing", "portfolio", "spcx", "catalysts",
    )
    for key in required:
        if key not in st:
            return fail(f"status.json missing key: {key}")
    for label, filing in (
        ("musk", st.get("latest_musk_filing")),
        ("spacex", st.get("latest_spacex_filing")),
        ("tesla", st.get("latest_tesla_filing")),
    ):
        if not filing or not filing.get("url", "").startswith("https://www.sec.gov/"):
            return fail(f"latest_{label}_filing has no SEC url")
    pf = st.get("portfolio") or {}
    if not pf.get("net_worth_proxy_usd_b"):
        return fail("portfolio.net_worth_proxy_usd_b missing")
    if len(pf.get("holdings") or []) < 4:
        return fail("portfolio.holdings too short")
    return ok("status.json structure + filing URLs + portfolio")


def check_index_html():
    path = os.path.join(PUBLIC, "index.html")
    if not os.path.isfile(path):
        return fail("index.html missing")
    html = open(path, encoding="utf-8").read()
    checks = [
        ('id="portfolio"', "portfolio section"),
        ('id="spcx"', "spcx section"),
        ("sec.gov/Archives/edgar", "SEC filing links"),
        ("exhibits/V5_lockup_calendar.svg", "lock-up exhibit"),
        ("exhibits/V4_value_flow_loop.svg", "value-flow exhibit"),
        ("exhibits/V3_three_leg_refinancing.svg", "refinance exhibit"),
        ("Form 4 code S filings on EDGAR", "sales ledger EDGAR link"),
        ("Latest issuer filings", "issuer filings block"),
    ]
    for needle, label in checks:
        if needle not in html:
            return fail(f"index.html missing: {label}")
    # No bare latest filings without sec.gov link in issuer block
    issuer = re.search(r"Latest issuer filings.*?</section>", html, re.S)
    if issuer and "sec.gov" not in issuer.group(0):
        return fail("issuer filings section has no SEC links")
    musk = re.search(r"Latest Musk filing.*?</section>", html, re.S)
    if musk and "sec.gov" not in musk.group(0):
        return fail("Musk filing section has no SEC link")
    bad = re.findall(r'href="#"(?!>)', html)
    if bad:
        return fail(f"index.html has {len(bad)} empty href=# links")
    return ok("index.html sections + SEC links + exhibits")


def check_exhibits():
    for name in (
        "V3_three_leg_refinancing.svg",
        "V4_value_flow_loop.svg",
        "V5_lockup_calendar.svg",
    ):
        path = os.path.join(PUBLIC, "exhibits", name)
        if not os.path.isfile(path):
            return fail(f"missing exhibit {name}")
        text = open(path, encoding="utf-8").read()
        if 'viewBox="0 0 1600 900"' in text:
            return fail(f"{name} still has full-canvas viewBox (whitespace bug)")
        if "0 186 1600 558" in text and "80 300" not in text and "60 230" not in text:
            return fail(f"{name} still has uncropped PDF embed viewBox")
    return ok("exhibit SVGs present with tight viewBox")


def check_portfolio_data():
    path = os.path.join(DATA, "portfolio_live.json")
    if not os.path.isfile(path):
        return fail("portfolio_live.json missing")
    pf = json.load(open(path, encoding="utf-8"))
    priced = [h for h in pf.get("holdings", []) if h.get("price")]
    if len(priced) < 2:
        return fail("portfolio_live.json missing TSLA/SPCX prices")
    return ok(f"portfolio_live.json ({len(priced)} priced holdings)")


def check_feed():
    path = os.path.join(PUBLIC, "feed.xml")
    if not os.path.isfile(path):
        return fail("feed.xml missing")
    text = open(path, encoding="utf-8").read()
    if "<rss" not in text or "<channel>" not in text:
        return fail("feed.xml not valid RSS skeleton")
    return ok("feed.xml present")


def main():
    results = [
        check_portfolio_data(),
        check_status_json(),
        check_index_html(),
        check_exhibits(),
        check_feed(),
    ]
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\n{passed}/{total} checks passed")
    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
