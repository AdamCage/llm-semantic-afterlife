#!/usr/bin/env bash
# Emit a wake line when the S11 generate matrix finishes or blocks.
set -u
LOG=/home/adam/s11/matrix.log
while true; do
  if [ -f "$LOG" ] && grep -Eq 'MATRIX DONE|MATRIX PARTIAL|OOM_DETECTED|REFUSE:' "$LOG"; then
    printf '%s\n' 'AGENT_LOOP_WAKE_s11 {"prompt":"S11 generate matrix finished or blocked. Read /home/adam/s11/matrix.log and runs/s11. If MATRIX DONE or PARTIAL, run scripts/s11_analysis_queue.sh then assemble artifacts, write REPORT, afterlife review --stage s11 to exit 0, hand off. Do not start S12. Do not retune sampling. Do not launch a second generate. Keep FAILED empty cells."}'
    exit 0
  fi
  sleep 60
done
