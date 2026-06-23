#!/usr/bin/env python3
"""Single entry point for GitHub Actions and manual full sync."""
import os
import subprocess
import sys

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")


def run(cmd):
    print("RUN", " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print(f"WARN exit {r.returncode}: {' '.join(cmd)}")


def main():
    py = sys.executable
    os.environ.setdefault("MUSK_WATCH_PIPELINE", "0")
    run([py, os.path.join(HERE, "watch_entities.py")])
    run([py, os.path.join(HERE, "pull_musk_filings.py")])
    run([py, os.path.join(HERE, "pull_spacex_edgar.py")])
    run([py, os.path.join(HERE, "pull_tesla_edgar.py")])
    run([py, os.path.join(HERE, "pull_spcx_market.py")])
    run([py, os.path.join(HERE, "pull_portfolio_live.py")])
    # Charts (best effort)
    for script in ("phase3_analyze.py", "networth_timeline.py", "debt_chain_chart.py",
                   "empire_mechanics_chart.py"):
        p = os.path.join(HERE, script)
        if os.path.isfile(p):
            run([py, p])
    run([py, os.path.join(HERE, "sync_public_assets.py")])
    run([py, os.path.join(HERE, "empire_memory.py"), "--sync"])
    os.environ["MUSK_LINKEDIN_ALERT"] = "0"
    run([py, os.path.join(HERE, "publish_live_feed.py")])
    run([py, os.path.join(HERE, "filing_followups.py")])
    run([py, os.path.join(HERE, "date_reminders.py")])
    run([py, os.path.join(HERE, "date_outcomes.py")])
    run([py, os.path.join(HERE, "daily_digest.py")])


if __name__ == "__main__":
    main()
