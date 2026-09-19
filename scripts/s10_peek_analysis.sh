#!/usr/bin/env bash
set -u
echo "==== TIME ===="
date -u +%Y-%m-%dT%H:%M:%SZ
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu,temperature.gpu --format=csv,noheader
echo "==== PS ===="
pgrep -af 's10_analysis_queue|afterlife embed|afterlife analyze' || true
echo "==== ANALYSIS ===="
cat /home/adam/s10/analysis.log
echo "==== EMBED/DEGEN/PERSIST ===="
for d in /mnt/c/projects/llm-semantic-afterlife/runs/s10/s10-embed-*/ /mnt/c/projects/llm-semantic-afterlife/runs/s10/s10-degeneracy-*/ /mnt/c/projects/llm-semantic-afterlife/runs/s10/s10-persistence-*/; do
  [ -d "$d" ] || continue
  name=$(basename "$d")
  st=NOSTATUS
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  echo "$st  $name"
done
echo "==== LAST BGE ===="
latest=$(ls -t /home/adam/s10/embed-bge-*.log 2>/dev/null | head -n 1)
echo "file=$latest"
tail -n 30 "$latest" 2>/dev/null
