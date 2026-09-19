#!/usr/bin/env bash
set -euo pipefail
mkdir -p /home/adam/s10
nohup /mnt/c/projects/llm-semantic-afterlife/scripts/s10_analysis_queue.sh \
  >/home/adam/s10/analysis.nohup 2>&1 &
echo "PIPELINE_PID=$!"
echo $! >/home/adam/s10/analysis.pid
nohup /mnt/c/projects/llm-semantic-afterlife/scripts/s10_hourly_watch.sh \
  >/home/adam/s10/hourly_watch.log 2>&1 &
echo "WATCH_PID=$!"
echo $! >/home/adam/s10/hourly_watch.pid
sleep 2
head -n 30 /home/adam/s10/analysis.log || true
