#!/bin/bash
# Load local notification secrets then run the entity watcher.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/data/.notify.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi
exec /opt/homebrew/bin/python3 "$ROOT/build/watch_entities.py" "$@"
