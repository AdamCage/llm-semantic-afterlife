#!/usr/bin/env bash
set -u
date -u +%Y-%m-%dT%H:%M:%SZ
echo "==== PS ===="
pgrep -af 's9_persistence|analyze persistence' || echo none
echo "==== RUNS ===="
for d in /mnt/c/projects/llm-semantic-afterlife/runs/s9/s9-persistence-*/; do
  [ -d "$d" ] || continue
  name=$(basename "$d")
  st="NOSTATUS"
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  echo "$st  $name"
done
echo "==== LAST G ===="
for f in /home/adam/s9/persistence-s9-embed-*.log; do
  [ -f "$f" ] || continue
  echo "-- $(basename "$f") --"
  grep -E 'last-band|confirmed lock|run_id:|Error|Traceback|BLOCKED' "$f" | tail -n 8
done
