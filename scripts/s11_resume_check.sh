#!/usr/bin/env bash
set -u
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
echo "==== PROCS ===="
ps -ef | grep -E 's11_resume|afterlife generate' | grep -v grep || echo none
echo "==== LOG ===="
tail -n 40 /home/adam/s11/pb-gemma4-12b-base.log | sed 's/\r$//'
echo "==== RUNS ===="
for d in runs/s11/s11-paperb-gemma4-*/; do
  [ -d "$d" ] || continue
  st=NOSTATUS
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  echo "$st $(basename "$d")"
done
