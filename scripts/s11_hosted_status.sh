#!/usr/bin/env bash
set -u
echo "==== ESTIMATE / HOSTED MARKERS ===="
grep -E 'TOTAL|OVER_CAP|cap|embed-qwen|HOSTED|BLOCKED|ANALYSIS' /home/adam/s11/analysis.log | tail -n 40
echo "==== HOSTED LOG TAIL ===="
tail -n 15 /home/adam/s11/embed_qwen_hosted.log 2>/dev/null || echo none
echo "==== EMBED RUNS ===="
cd /mnt/c/projects/llm-semantic-afterlife
for d in runs/s11/s11-embed-*/; do
  [ -d "$d" ] || continue
  st=NOSTATUS
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  echo "$st $(basename "$d")"
done
