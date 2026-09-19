#!/usr/bin/env bash
# Hourly heartbeat while S10 analysis is running. Logs only.
set -euo pipefail
LOG=/home/adam/s10/hourly_watch.log
mkdir -p /home/adam/s10
while true; do
  sleep 3600
  {
    echo "HOUR $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    tail -n 16 /home/adam/s10/analysis.log || true
    nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader || true
    pgrep -af 's10_analysis_queue|afterlife embed|afterlife analyze' || echo "pipeline not in pgrep"
  } >>"$LOG"
done
