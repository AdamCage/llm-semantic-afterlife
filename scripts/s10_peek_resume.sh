#!/usr/bin/env bash
set -u
echo "==== TIME ===="
date -u +%Y-%m-%dT%H:%M:%SZ
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
echo "==== PS ===="
pgrep -af 's10_analysis_resume|afterlife embed|afterlife analyze' || true
echo "==== ANALYSIS TAIL ===="
tail -n 25 /home/adam/s10/analysis.log
echo "==== HOSTED MASTER ===="
tail -n 15 /home/adam/s10/embed_qwen_hosted.log 2>/dev/null || echo none
echo "==== EMBED STATUS ===="
for d in /mnt/c/projects/llm-semantic-afterlife/runs/s10/s10-embed-*/; do
  name=$(basename "$d")
  st=NOSTATUS
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  sup=""
  [ -f "${d}SUPERSEDED" ] && sup=" SUPERSEDED"
  echo "$st$sup  $name"
done
