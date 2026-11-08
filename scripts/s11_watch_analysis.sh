#!/usr/bin/env bash
set -u
LOG=/home/adam/s11/analysis.log
while true; do
  if [ -f "$LOG" ] && grep -Eq 'ANALYSIS QUEUE DONE|BLOCKED' "$LOG"; then
    printf '%s\n' 'AGENT_LOOP_WAKE_s11ana {"prompt":"S11 analysis queue finished or blocked. Read /home/adam/s11/analysis.log. If ANALYSIS QUEUE DONE, assemble artifacts, write REPORT, afterlife review --stage s11 until exit 0, hand off for scientific review. Do not start S12. Do not retune. Do not pool with Qwen or OLMo. Keep FAILED empty cells."}'
    exit 0
  fi
  sleep 60
done
