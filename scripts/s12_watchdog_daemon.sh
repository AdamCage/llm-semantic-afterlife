#!/usr/bin/env bash
# Resident S12 watchdog. Survives Cursor closing. One instance.
set -u
ROOT=/mnt/c/projects/llm-semantic-afterlife
LOGDIR=/home/adam/s12
mkdir -p "$LOGDIR"
sed -i 's/\r$//' "$ROOT/scripts/s12_watchdog_once.sh" "$ROOT/scripts/s12_after_cohort.sh" || true

if [ -f "$LOGDIR/watchdog.pid" ]; then
  old="$(tr -d '\r\n' < "$LOGDIR/watchdog.pid")"
  if [ -n "$old" ] && [ "$old" != "$$" ] && kill -0 "$old" 2>/dev/null; then
    echo "WATCHDOG_DAEMON_ALREADY pid=$old"
    exit 0
  fi
fi
echo "$$" > "$LOGDIR/watchdog.pid"

echo "WATCHDOG_DAEMON_START $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOGDIR/watchdog.log"
while true; do
  bash "$ROOT/scripts/s12_watchdog_once.sh" || true
  sleep 600
done
