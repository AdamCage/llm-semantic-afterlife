#!/usr/bin/env bash
set -u
ROOT=/mnt/c/projects/llm-semantic-afterlife
sed -i 's/\r$//' \
  "$ROOT/scripts/s12_watchdog_once.sh" \
  "$ROOT/scripts/s12_watchdog_daemon.sh" \
  "$ROOT/scripts/s12_after_cohort.sh" \
  "$ROOT/scripts/s12_rotate.sh"
bash -n "$ROOT/scripts/s12_watchdog_once.sh"
bash -n "$ROOT/scripts/s12_watchdog_daemon.sh"
mkdir -p /home/adam/s12
if [ -f /home/adam/s12/watchdog.pid ]; then
  old="$(tr -d '\r\n' < /home/adam/s12/watchdog.pid)"
  if [ -n "$old" ] && kill -0 "$old" 2>/dev/null; then
    echo "ALREADY $old"
    exit 0
  fi
fi
setsid nohup bash "$ROOT/scripts/s12_watchdog_daemon.sh" >> /home/adam/s12/watchdog.nohup 2>&1 &
echo "STARTED $!"
sleep 2
echo "==== LOG ===="
tail -n 5 /home/adam/s12/watchdog.log || true
echo "==== PIDFILE ===="
cat /home/adam/s12/watchdog.pid || true
