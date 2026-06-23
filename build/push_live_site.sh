#!/bin/bash
# Commit and push live site + data updates to GitHub (triggers Pages redeploy).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
git add public/ data/filings_index.csv data/transactions.csv data/filing_alerts.log charts/ 2>/dev/null || true
if git diff --staged --quiet; then
  echo "nothing to push"
  exit 0
fi
git commit -m "Live update: EDGAR sync $(date -u +%Y-%m-%dT%H:%M:%SZ)"
git push origin main
