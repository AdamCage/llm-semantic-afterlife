#!/usr/bin/env bash
# Hourly heartbeat while S9 post-generate is running. Logs only.
set -euo pipefail
LOG=/home/adam/s9/hourly_watch.log
mkdir -p /home/adam/s9
while true; do
  sleep 3600
  {
    echo "HOUR $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    tail -n 12 /home/adam/s9/post_generate.log || true
    nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader || true
    pgrep -af s9_post_generate || echo "pipeline not in pgrep"
  } >>"$LOG"
done
