#!/usr/bin/env python3
"""Refresh SPCX market data and republish site (for cron/launchd, separate from SEC watcher)."""
import os
import subprocess
import sys

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")


def run(cmd):
    return subprocess.run(cmd, cwd=ROOT, check=False)


if __name__ == "__main__":
    run([sys.executable, os.path.join(HERE, "pull_spacex_edgar.py")])
    run([sys.executable, os.path.join(HERE, "pull_spcx_market.py")])
    os.environ["MUSK_LINKEDIN_ALERT"] = "0"
    run([sys.executable, os.path.join(HERE, "publish_live_feed.py")])
    if os.environ.get("MUSK_WATCH_GIT_PUSH", "1") != "0":
        run(["bash", os.path.join(HERE, "push_live_site.sh")])
