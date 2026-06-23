#!/usr/bin/env python3
"""
Watch Elon Musk's SEC EDGAR filings and alert on anything new.

Designed to run once per invocation (suited to launchd/cron). On each run it
pulls his submissions index, diffs against previously-seen accession numbers,
and for every NEW filing it:
  - posts a macOS desktop notification (osascript)
  - appends a line to data/filing_alerts.log
  - optionally hits a webhook and/or sends email (see env vars below)

State is kept in data/.watch_state.json (set of seen accession numbers).

Optional delivery (set as environment variables, all unset by default):
  MUSK_WATCH_WEBHOOK   Slack/Discord/generic incoming-webhook URL (POST JSON {"text": ...})
  MUSK_WATCH_NTFY      ntfy.sh topic URL for phone push (e.g. https://ntfy.sh/my-musk-topic)

Run modes:
  python3 watch_musk_filings.py           # one check-and-exit (for launchd/cron)
  python3 watch_musk_filings.py --daemon  # loop forever, checking every 15 min
  python3 watch_musk_filings.py --seed     # mark all current filings as seen, no alerts
"""
import json
import os
import sys
import time
import subprocess
import urllib.request

CIK = "0001494730"
CIK_INT = str(int(CIK))
UA = "Watts Advisor research kiran@conformingcredit.org"
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
STATE = os.path.join(DATA, ".watch_state.json")
LOG = os.path.join(DATA, "filing_alerts.log")
INTERVAL = 15 * 60  # daemon mode poll interval

# Friendly labels for common Musk form types
FORM_DESC = {
    "4": "Insider transaction (buy/sell/exercise)",
    "4/A": "Insider transaction — amended",
    "3": "Initial insider ownership",
    "5": "Annual insider ownership",
    "SC 13D": "Activist/>5% beneficial ownership",
    "SC 13D/A": ">5% ownership — amended",
    "SC 13G": "Passive >5% beneficial ownership",
    "SC 13G/A": ">5% ownership — amended",
    "SCHEDULE 13G/A": ">5% ownership — amended",
    "DFAN14A": "Proxy solicitation material",
    "CORRESP": "Correspondence with SEC",
}


def fetch(url, raw=False, retries=4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            return data if raw else data.decode("utf-8", "replace")
        except Exception as e:
            if attempt == retries - 1:
                print(f"fetch failed {url}: {e}", file=sys.stderr)
                return None
            time.sleep(1.5 * (attempt + 1))


def load_state():
    if os.path.exists(STATE):
        try:
            return set(json.load(open(STATE)).get("seen", []))
        except Exception:
            return set()
    return set()


def save_state(seen):
    keep = sorted(seen)[-500:]  # cap history
    json.dump({"seen": keep, "updated": time.strftime("%Y-%m-%dT%H:%M:%S")}, open(STATE, "w"))


def notify_mac(title, subtitle, text):
    def clean(s):
        return (s or "").replace('"', "'").replace("\\", "")
    script = (f'display notification "{clean(text)}" '
              f'with title "{clean(title)}" subtitle "{clean(subtitle)}" '
              f'sound name "Submarine"')
    try:
        subprocess.run(["osascript", "-e", script], check=False,
                       capture_output=True, timeout=10)
    except Exception as e:
        print(f"notify failed: {e}", file=sys.stderr)


def post_json(url, payload):
    try:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "User-Agent": UA})
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print(f"webhook failed: {e}", file=sys.stderr)


def post_text(url, text):
    try:
        req = urllib.request.Request(url, data=text.encode(),
                                     headers={"User-Agent": UA})
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print(f"ntfy failed: {e}", file=sys.stderr)


def alert(filing):
    form = filing["form"]
    desc = FORM_DESC.get(form, form)
    title = "New Musk SEC filing"
    subtitle = f"{form} · {filing['filingDate']}"
    body = f"{desc}\n{filing['url']}"

    notify_mac(title, subtitle, f"{desc} — {filing['filingDate']}")

    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\t{filing['filingDate']}\t{form}\t{desc}\t{filing['url']}\n"
    with open(LOG, "a") as f:
        f.write(line)
    print(f"ALERT  {subtitle}  {desc}\n       {filing['url']}")

    hook = os.environ.get("MUSK_WATCH_WEBHOOK")
    if hook:
        post_json(hook, {"text": f":rotating_light: *{title}*\n{subtitle} — {desc}\n{filing['url']}"})
    ntfy = os.environ.get("MUSK_WATCH_NTFY")
    if ntfy:
        post_text(ntfy, f"{form} ({desc}) {filing['filingDate']}\n{filing['url']}")


def get_recent_filings():
    txt = fetch(f"https://data.sec.gov/submissions/CIK{CIK}.json")
    if not txt:
        return []
    rec = json.loads(txt)["filings"]["recent"]
    out = []
    for i in range(len(rec["form"])):
        acc = rec["accessionNumber"][i]
        acc_nodash = acc.replace("-", "")
        primary = rec["primaryDocument"][i]
        out.append({
            "accession": acc,
            "form": rec["form"][i],
            "filingDate": rec["filingDate"][i],
            "url": f"https://www.sec.gov/Archives/edgar/data/{CIK_INT}/{acc_nodash}/{primary}",
        })
    return out


def check_once(seed=False):
    seen = load_state()
    filings = get_recent_filings()
    if not filings:
        return
    new = [f for f in filings if f["accession"] not in seen]
    if seed:
        save_state(seen | {f["accession"] for f in filings})
        print(f"Seeded {len(filings)} filings as already-seen. No alerts.")
        return
    if not seen:
        # first real run without seeding: avoid alert storm, just seed
        save_state({f["accession"] for f in filings})
        print(f"First run: seeded {len(filings)} filings. Future filings will alert.")
        return
    new.sort(key=lambda f: f["filingDate"])
    for f in new:
        alert(f)
    save_state(seen | {f["accession"] for f in filings})
    if new and os.environ.get("MUSK_WATCH_PIPELINE", "1") != "0":
        forms = ",".join(sorted({f["form"] for f in new}))
        pipeline = os.path.join(os.path.dirname(__file__), "on_new_filing.py")
        try:
            subprocess.run([sys.executable, pipeline, "--forms", forms],
                           cwd=os.path.join(os.path.dirname(__file__), ".."),
                           timeout=600, check=False)
        except Exception as e:
            print(f"pipeline failed: {e}", file=sys.stderr)
    if not new:
        print(f"{time.strftime('%H:%M:%S')}  no new filings ({len(filings)} known)")


def main():
    os.makedirs(DATA, exist_ok=True)
    if "--seed" in sys.argv:
        check_once(seed=True)
    elif "--daemon" in sys.argv:
        print(f"Daemon mode: checking every {INTERVAL//60} min. Ctrl-C to stop.")
        while True:
            check_once()
            time.sleep(INTERVAL)
    else:
        check_once()


if __name__ == "__main__":
    main()
