"""Shared EDGAR fetch, state, and alert helpers for entity watchers."""
import json
import os
import re
import subprocess
import time
import urllib.request

UA = "Watts Advisor research kiran@conformingcredit.org"
HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
LOG = os.path.join(DATA, "filing_alerts.log")

FORM_DESC = {
    "4": "Insider transaction (buy/sell/exercise)",
    "4/A": "Insider transaction amended",
    "3": "Initial insider ownership",
    "5": "Annual insider ownership",
    "8-K": "Material event report",
    "8-K/A": "Material event amended",
    "424B4": "Prospectus supplement",
    "424B5": "Prospectus supplement",
    "DEF 14A": "Proxy statement",
    "DEFA14A": "Proxy additional materials",
    "SC 13D": "Activist/>5% ownership",
    "SC 13D/A": ">5% ownership amended",
    "SC 13G": "Passive >5% ownership",
    "SC 13G/A": ">5% ownership amended",
    "10-K": "Annual report",
    "10-Q": "Quarterly report",
}


def fetch(url, raw=False, retries=4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                data = r.read()
            return data if raw else data.decode("utf-8", "replace")
        except Exception as e:
            if attempt == retries - 1:
                print(f"fetch failed {url}: {e}")
                return None
            time.sleep(1.5 * (attempt + 1))


def state_path(entity_key):
    return os.path.join(DATA, f".watch_state_{entity_key}.json")


def load_state(entity_key):
    p = state_path(entity_key)
    if os.path.exists(p):
        try:
            return set(json.load(open(p)).get("seen", []))
        except Exception:
            return set()
    return set()


def save_state(entity_key, seen):
    os.makedirs(DATA, exist_ok=True)
    keep = sorted(seen)[-800:]
    json.dump({"seen": keep, "updated": time.strftime("%Y-%m-%dT%H:%M:%S")}, open(state_path(entity_key), "w"))


def filing_url(cik, accession, primary):
    cik_int = str(int(cik))
    acc_nodash = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{primary}"


def get_recent_filings(cik, limit=120):
    txt = fetch(f"https://data.sec.gov/submissions/CIK{cik}.json")
    if not txt:
        return []
    rec = json.loads(txt)["filings"]["recent"]
    out = []
    for i in range(min(len(rec["form"]), limit)):
        out.append({
            "accession": rec["accessionNumber"][i],
            "form": rec["form"][i],
            "filingDate": rec["filingDate"][i],
            "primaryDocument": rec["primaryDocument"][i],
            "url": filing_url(cik, rec["accessionNumber"][i], rec["primaryDocument"][i]),
        })
    return out


def notify_mac(title, subtitle, text):
    if os.environ.get("MUSK_WATCH_NO_MAC", "0") == "1":
        return
    def clean(s):
        return (s or "").replace('"', "'").replace("\\", "")
    script = (f'display notification "{clean(text)}" '
              f'with title "{clean(title)}" subtitle "{clean(subtitle)}" '
              f'sound name "Submarine"')
    try:
        subprocess.run(["osascript", "-e", script], check=False, capture_output=True, timeout=10)
    except Exception:
        pass


def post_json(url, payload):
    try:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "User-Agent": UA})
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print(f"webhook failed: {e}")


def post_ntfy(title, body, priority="default", tags=""):
    ntfy = os.environ.get("MUSK_WATCH_NTFY")
    if not ntfy:
        return
    headers = {"User-Agent": UA, "Title": title[:250], "Priority": priority}
    if tags:
        headers["Tags"] = tags
    try:
        req = urllib.request.Request(ntfy, data=body.encode(), headers=headers)
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print(f"ntfy failed: {e}")


def log_alert(entity_label, filing, desc):
    line = (f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\t{filing['filingDate']}\t{filing['form']}\t"
            f"{desc}\t{filing['url']}\t{entity_label}\n")
    os.makedirs(DATA, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line)


def alert_filing(entity_label, filing, trigger_linkedin=False):
    form = filing["form"]
    desc = FORM_DESC.get(form, form)
    title = f"New {entity_label} SEC filing"
    subtitle = f"{form} · {filing['filingDate']}"
    notify_mac(title, subtitle, f"{desc} ({filing['filingDate']})")
    log_alert(entity_label, filing, desc)
    print(f"ALERT [{entity_label}] {subtitle}  {desc}\n       {filing['url']}")
    hook = os.environ.get("MUSK_WATCH_WEBHOOK")
    if hook:
        post_json(hook, {"text": f"*{title}*\n{subtitle}: {desc}\n{filing['url']}"})
    priority = "high" if trigger_linkedin else "default"
    tags = "memo" if trigger_linkedin else "sec"
    post_ntfy(
        f"{entity_label}: {form} filed",
        f"{desc}\n{filing['filingDate']}\n{filing['url']}",
        priority=priority,
        tags=tags,
    )


def html_to_text(html):
    html = html.replace("&#160;", " ").replace("&nbsp;", " ")
    html = html.replace("&#8217;", "'").replace("&#8220;", '"').replace("&#8221;", '"')
    html = html.replace("&#58;", ":")
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<[^>]+>", " ", html)
    html = re.sub(r"\s+", " ", html)
    return html.strip()
