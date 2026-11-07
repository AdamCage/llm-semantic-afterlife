#!/usr/bin/env bash
set -u
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== ROTATE TAIL ===="
tail -n 40 /home/adam/s12/rotate.log
echo "==== NOHUP TAIL ===="
tail -n 30 /home/adam/s12/rotate.nohup 2>/dev/null || echo none
echo "==== LOVE LOG TAIL ===="
tail -n 25 /home/adam/s12/mb-love-s1.log | sed 's/\r$//'
echo "==== ROTATE PID ===="
if [ -f /home/adam/s12/rotate.pid ]; then
  pid=$(tr -d '\r\n' < /home/adam/s12/rotate.pid)
  echo "pidfile=$pid"
  ps -p "$pid" -o pid,cmd || echo dead
fi
pgrep -af 's12_rotate|s12_watch' || echo no-watchers
