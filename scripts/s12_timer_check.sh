#!/usr/bin/env bash
set -u
echo "==== DAEMON ===="
if [ -f /home/adam/s12/watchdog.pid ]; then
  pid="$(tr -d '\r\n' < /home/adam/s12/watchdog.pid)"
  echo "pidfile=$pid"
  if kill -0 "$pid" 2>/dev/null; then
    ps -p "$pid" -o pid,etime,cmd
  else
    echo DEAD
  fi
else
  echo NO_PIDFILE
fi
echo "==== WATCHDOG TAIL ===="
tail -n 4 /home/adam/s12/watchdog.log
echo "==== ROTATE ===="
pgrep -af 'scripts/s12_rotate.sh' || echo none
echo "==== GENERATE COUNT ===="
pgrep -fc 'afterlife generate --config configs/stages/stage12_horizon' || true
