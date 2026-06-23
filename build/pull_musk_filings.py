#!/usr/bin/env python3
"""
Pull Elon Musk's complete Section 16 filing trail from SEC EDGAR and parse
every Form 3/4/5 into a structured transaction ledger.

Outputs (written to ../data/):
  - musk_submissions.json   raw EDGAR submissions index (cache)
  - filings_index.csv       one row per filing (form, date, accession, url)
  - transactions.csv        one row per non-derivative/derivative transaction

No third-party deps. SEC requires a descriptive User-Agent and < 10 req/s.
"""
import json
import os
import time
import csv
import urllib.request
import xml.etree.ElementTree as ET

CIK = "0001494730"            # Musk Elon (reporting person)
CIK_INT = str(int(CIK))
UA = "Watts Advisor research kiran@conformingcredit.org"
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA, exist_ok=True)

OWNERSHIP_FORMS = {"3", "4", "5", "3/A", "4/A", "5/A"}

# Transaction code -> plain-English label
CODE_LABEL = {
    "P": "open-market/private purchase",
    "S": "open-market/private sale",
    "A": "grant/award/acquisition",
    "M": "exercise/conversion of derivative",
    "F": "shares withheld for tax",
    "G": "gift",
    "C": "conversion of derivative",
    "X": "exercise of in-the-money derivative",
    "D": "disposition to issuer",
    "J": "other acquisition/disposition",
    "W": "acquisition/disposition by will",
}


def fetch(url, raw=False, retries=4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            time.sleep(0.18)  # stay well under SEC's 10 req/s
            return data if raw else data.decode("utf-8", "replace")
        except Exception as e:
            if attempt == retries - 1:
                print(f"  ! failed {url}: {e}")
                return None
            time.sleep(1.5 * (attempt + 1))


def get_submissions():
    path = os.path.join(DATA, "musk_submissions.json")
    txt = fetch(f"https://data.sec.gov/submissions/CIK{CIK}.json")
    if txt:
        with open(path, "w") as f:
            f.write(txt)
    return json.loads(open(path).read())


def localname(tag):
    return tag.split("}")[-1]


def text(el, *path):
    """Walk child elements by local name; return inner 'value' text if present."""
    cur = el
    for name in path:
        nxt = None
        for c in list(cur):
            if localname(c.tag) == name:
                nxt = c
                break
        if nxt is None:
            return None
        cur = nxt
    # ownership XML wraps scalars in a <value> child
    for c in list(cur):
        if localname(c.tag) == "value":
            return (c.text or "").strip()
    return (cur.text or "").strip() if cur.text else None


def parse_ownership_xml(xml_bytes, meta):
    rows = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        print(f"  ! XML parse error {meta['accession']}: {e}")
        return rows

    issuer_name = text(root, "issuer", "issuerName")
    issuer_cik = text(root, "issuer", "issuerCik")
    ticker = text(root, "issuer", "issuerTradingSymbol")

    # collect footnotes for 10b5-1 detection
    footnote_text = ""
    for fn in root.iter():
        if localname(fn.tag) == "footnote":
            footnote_text += " " + "".join(fn.itertext())
    flat = footnote_text.lower().replace(" ", "").replace("\n", "")
    rule_10b5_1 = "10b5-1" in flat or "rule10b5" in flat

    def emit(t, table):
        code = text(t, "transactionCoding", "transactionCode")
        shares = text(t, "transactionAmounts", "transactionShares")
        price = text(t, "transactionAmounts", "transactionPricePerShare")
        ad = text(t, "transactionAmounts", "transactionAcquiredDisposedCode")
        date = text(t, "transactionDate")
        sec_title = text(t, "securityTitle")
        owned_after = text(t, "postTransactionAmounts", "sharesOwnedFollowingTransaction")
        direct = text(t, "ownershipNature", "directOrIndirectOwnership")
        underlying = text(t, "underlyingSecurity", "underlyingSecurityShares")
        exercise_price = text(t, "conversionOrExercisePrice")

        def fnum(x):
            try:
                return float(x)
            except (TypeError, ValueError):
                return None

        sh, pr = fnum(shares), fnum(price)
        value = round(sh * pr, 2) if (sh is not None and pr is not None) else None
        rows.append({
            "filing_date": meta["filing_date"],
            "transaction_date": date,
            "form": meta["form"],
            "issuer": issuer_name,
            "ticker": ticker,
            "issuer_cik": issuer_cik,
            "table": table,
            "security": sec_title,
            "code": code,
            "code_label": CODE_LABEL.get(code, code),
            "acquired_disposed": ad,
            "shares": shares,
            "price_per_share": price,
            "value_usd": value,
            "shares_owned_after": owned_after,
            "direct_indirect": direct,
            "deriv_exercise_price": exercise_price,
            "deriv_underlying_shares": underlying,
            "rule_10b5_1": "Y" if rule_10b5_1 else "",
            "accession": meta["accession"],
            "url": meta["url"],
        })

    for tbl_name, t_name, lbl in [
        ("nonDerivativeTable", "nonDerivativeTransaction", "nonderiv"),
        ("derivativeTable", "derivativeTransaction", "deriv"),
    ]:
        for tbl in root.iter():
            if localname(tbl.tag) == tbl_name:
                for t in list(tbl):
                    if localname(t.tag) == t_name:
                        emit(t, lbl)
    return rows


def find_ownership_xml_url(acc_nodash):
    base = f"https://www.sec.gov/Archives/edgar/data/{CIK_INT}/{acc_nodash}"
    idx = fetch(f"{base}/index.json")
    if not idx:
        return None
    try:
        items = json.loads(idx)["directory"]["item"]
    except Exception:
        return None
    candidates = [it["name"] for it in items if it["name"].lower().endswith(".xml")
                  and not it["name"].lower().startswith("xsl")]
    # prefer the ownership form xml (usually only one)
    if not candidates:
        return None
    return f"{base}/{candidates[0]}"


def main():
    sub = get_submissions()
    print("Reporting person:", sub.get("name"))
    rec = sub["filings"]["recent"]
    n = len(rec["form"])

    index_rows, all_tx = [], []
    for i in range(n):
        form = rec["form"][i]
        acc = rec["accessionNumber"][i]
        acc_nodash = acc.replace("-", "")
        filing_date = rec["filingDate"][i]
        primary = rec["primaryDocument"][i]
        url = f"https://www.sec.gov/Archives/edgar/data/{CIK_INT}/{acc_nodash}/{primary}"
        index_rows.append({
            "filing_date": filing_date, "form": form, "accession": acc,
            "primary_document": primary, "url": url,
        })

        if form in OWNERSHIP_FORMS:
            xml_url = find_ownership_xml_url(acc_nodash)
            if not xml_url:
                print(f"  ? no ownership xml for {form} {acc}")
                continue
            xb = fetch(xml_url, raw=True)
            if not xb:
                continue
            meta = {"form": form, "accession": acc, "filing_date": filing_date, "url": xml_url}
            tx = parse_ownership_xml(xb, meta)
            all_tx.extend(tx)
            print(f"  [{i+1}/{n}] {form} {filing_date} -> {len(tx)} tx")

    # write filings index
    with open(os.path.join(DATA, "filings_index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(index_rows[0].keys()))
        w.writeheader()
        w.writerows(index_rows)

    # write transactions
    if all_tx:
        cols = list(all_tx[0].keys())
        all_tx.sort(key=lambda r: (r["transaction_date"] or r["filing_date"] or ""))
        with open(os.path.join(DATA, "transactions.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(all_tx)

    print(f"\nDONE. {len(index_rows)} filings indexed, {len(all_tx)} transactions parsed.")


if __name__ == "__main__":
    main()
