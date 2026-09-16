#!/usr/bin/env bash
set -euo pipefail
mkdir -p /home/adam/s9
chmod +x /mnt/c/projects/llm-semantic-afterlife/scripts/s9_embed_qwen_hosted.sh
nohup /mnt/c/projects/llm-semantic-afterlife/scripts/s9_embed_qwen_hosted.sh \
  >/home/adam/s9/embed_qwen_hosted.nohup 2>&1 &
echo "HOSTED_EMBED_PID=$!"
sleep 2
tail -n 20 /home/adam/s9/embed_qwen_hosted.log || true
