#!/usr/bin/env bash
set -u
echo "==== LAST OK ===="
grep 'WATCHDOG_OK' /home/adam/s12/watchdog.log | tail -n 3
echo "==== LOCK HOLDERS ===="
if command -v fuser >/dev/null 2>&1; then
  fuser -v /home/adam/s12/watchdog.lock 2>&1 || true
else
  echo no-fuser
fi
echo "==== PROC LOCKS ===="
# show processes whose fd points at the lock
for d in /proc/[0-9]*; do
  pid="${d#/proc/}"
  if ls -l "$d/fd" 2>/dev/null | grep -q 'watchdog.lock'; then
    echo "pid=$pid"
    tr '\0' ' ' < "$d/cmdline"; echo
  fi
done
echo "==== WATCHDOG PROCS ===="
pgrep -af 's12_watchdog|s12_hourly|s12_keepalive|s12_after' || echo none
