#!/usr/bin/env bash
set -u
if [ -f /home/adam/s12/watchdog.pid ]; then
  pid="$(tr -d '\r\n' < /home/adam/s12/watchdog.pid)"
  if [ -n "$pid" ]; then
    kill -TERM "$pid" 2>/dev/null || true
  fi
fi
pkill -TERM -f 'scripts/s12_watchdog_daemon.sh' 2>/dev/null || true
sleep 1
pkill -KILL -f 'scripts/s12_watchdog_daemon.sh' 2>/dev/null || true
if pgrep -f 'scripts/s12_watchdog_daemon.sh' >/dev/null 2>&1; then
  echo DAEMON_STILL_ALIVE
else
  echo DAEMON_STOPPED
fi
