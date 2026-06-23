#!/usr/bin/env python3
"""
Run when the SEC watcher detects new Musk filings.
Re-pulls EDGAR, regenerates charts on material forms, publishes public feed.

Usage:
  python3 on_new_filing.py              # rebuild everything
  python3 on_new_filing.py --forms 4,4/A  # only if these forms in latest batch
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
LOG = os.path.join(DATA, "pipeline.log")

# Forms that trigger full data + chart rebuild
MATERIAL_FORMS = {
    "4", "4/A", "3", "5",
    "SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A", "SCHEDULE 13G/A",
    "8-K", "DEF 14A", "DEFA14A", "DEFM14A", "S-1", "S-4", "424B4", "424B5",
}


def log(msg):
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\t{msg}\n"
    os.makedirs(DATA, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line)
    print(msg)


def run(cmd, cwd=ROOT):
    log(f"RUN {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.returncode != 0:
        log(f"FAIL ({r.returncode}): {r.stderr.strip()}")
        return False
    return True


def recent_alert_forms(limit=5):
    """Forms from the most recent filing_alerts.log entries."""
    path = os.path.join(DATA, "filing_alerts.log")
    if not os.path.exists(path):
        return set()
    forms = set()
    for line in open(path, encoding="utf-8").read().strip().splitlines()[-limit:]:
        parts = line.split("\t")
        if len(parts) >= 3:
            forms.add(parts[2])
    return forms


def needs_full_rebuild(forms_filter=None):
    forms = forms_filter or recent_alert_forms()
    if not forms:
        return True  # conservative default
    return bool(forms & MATERIAL_FORMS)


def main():
    forms_arg = None
    entities_arg = set()
    if "--forms" in sys.argv:
        i = sys.argv.index("--forms")
        if i + 1 < len(sys.argv):
            forms_arg = set(sys.argv[i + 1].split(","))
    if "--entities" in sys.argv:
        i = sys.argv.index("--entities")
        if i + 1 < len(sys.argv):
            entities_arg = set(sys.argv[i + 1].split(","))

    # Always refresh issuer EDGAR + market on any pipeline run
    run([sys.executable, os.path.join(HERE, "pull_spacex_edgar.py")])
    run([sys.executable, os.path.join(HERE, "pull_tesla_edgar.py")])

    if forms_arg and not needs_full_rebuild(forms_arg):
        log("Non-material forms only: publishing feed without full rebuild")
        run([sys.executable, os.path.join(HERE, "pull_spcx_market.py")])
        os.environ["MUSK_LINKEDIN_ALERT"] = "0"
        run([sys.executable, os.path.join(HERE, "publish_live_feed.py")])
        _finish(entities_arg, forms_arg)
        return

    log("=== pipeline start (material filing) ===")
    if "musk" in entities_arg or not entities_arg:
        ok = run([sys.executable, os.path.join(HERE, "pull_musk_filings.py")])
        if ok:
            run([sys.executable, os.path.join(HERE, "phase3_analyze.py")])
            run([sys.executable, os.path.join(HERE, "networth_timeline.py")])
            run([sys.executable, os.path.join(HERE, "debt_chain_chart.py")])
            run([sys.executable, os.path.join(HERE, "empire_mechanics_chart.py")])
    run([sys.executable, os.path.join(HERE, "pull_spcx_market.py")])
    os.environ["MUSK_LINKEDIN_ALERT"] = "0"
    run([sys.executable, os.path.join(HERE, "publish_live_feed.py")])
    _finish(entities_arg, forms_arg)
    log("=== pipeline done ===")


def _finish(entities_arg, forms_arg):
    if os.environ.get("MUSK_WATCH_GIT_PUSH", "1") != "0":
        push = os.path.join(HERE, "push_live_site.sh")
        if os.path.isfile(push):
            run(["bash", push])
    if os.environ.get("MUSK_LINKEDIN_ALERT", "1") != "0":
        reason = "site published"
        if "spacex" in entities_arg:
            reason = "SpaceX issuer filing detected"
        elif forms_arg and forms_arg & {"8-K", "8-K/A"}:
            reason = "8-K material event"
        run([sys.executable, os.path.join(HERE, "linkedin_alert.py"), reason])


if __name__ == "__main__":
    main()
