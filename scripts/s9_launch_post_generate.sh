#!/usr/bin/env bash
set -euo pipefail
mkdir -p /home/adam/s9
nohup /mnt/c/projects/llm-semantic-afterlife/scripts/s9_post_generate.sh \
  >/home/adam/s9/post_generate.nohup 2>&1 &
echo "PIPELINE_PID=$!"
nohup /mnt/c/projects/llm-semantic-afterlife/scripts/s9_hourly_embed_watch.sh \
  >/home/adam/s9/hourly_watch.log 2>&1 &
echo "WATCH_PID=$!"
sleep 1
head -n 20 /home/adam/s9/post_generate.log || true
