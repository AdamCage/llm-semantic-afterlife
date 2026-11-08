#!/usr/bin/env bash
set -u
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== TIME ===="
date -u +%Y-%m-%dT%H:%M:%SZ
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
echo "==== MASTER ===="
tail -n 15 /home/adam/s11/matrix.log 2>/dev/null || echo none
echo "==== ONE LOG TAIL ===="
tail -n 25 /home/adam/s11/pb-ministral-8b-base.log 2>/dev/null || echo none
echo "==== RUNS ===="
for d in runs/s11/s11-paperb-*/; do
  [ -d "$d" ] || continue
  st=NOSTATUS
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  echo "$st  $(basename "$d")"
  if [ -f "${d}events.jsonl" ]; then
    echo "  events=$(wc -l < "${d}events.jsonl")"
    tail -n 2 "${d}events.jsonl" | python3 -c 'import sys,json
for line in sys.stdin:
  try:
    o=json.loads(line)
  except Exception:
    continue
  print(" ", o.get("event"), o.get("trajectory_id","")[:60], o.get("step_index",""), o.get("status",""))'
  fi
done
