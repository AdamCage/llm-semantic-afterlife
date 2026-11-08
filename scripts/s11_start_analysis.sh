#!/usr/bin/env bash
set -euo pipefail
ROOT=/mnt/c/projects/llm-semantic-afterlife
sed -i 's/\r$//' "$ROOT/scripts/s11_analysis_queue.sh" \
  "$ROOT/scripts/s11_degeneracy.sh" \
  "$ROOT/scripts/s11_embed_bge.sh" \
  "$ROOT/scripts/s11_embed_qwen_hosted.sh" || true
mkdir -p /home/adam/s11
nohup bash "$ROOT/scripts/s11_analysis_queue.sh" > /home/adam/s11/analysis.nohup 2>&1 &
echo "PID=$!"
echo "$!" > /home/adam/s11/analysis.pid
sleep 2
tail -n 20 /home/adam/s11/analysis.log || true
