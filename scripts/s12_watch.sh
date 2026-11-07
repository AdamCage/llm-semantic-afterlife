#!/usr/bin/env bash
set -u
LOG=/home/adam/s12/rotate.log
while true; do
  if [ -f "$LOG" ] && grep -Eq 'S12 COHORT DONE|REFUSE:' "$LOG"; then
    printf '%s\n' 'AGENT_LOOP_WAKE_s12 {"prompt":"S12 rotate finished or refused. Read /home/adam/s12/rotate.log and runs/s12. If COHORT DONE, degeneracy then tau_escape table, REPORT, afterlife review --stage s12 until exit 0. Do not start S13. Do not call a lock absorbing. Do not retune."}'
    exit 0
  fi
  sleep 120
done
