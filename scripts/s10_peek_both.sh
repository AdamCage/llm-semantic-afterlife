#!/usr/bin/env bash
set -u
bash /mnt/c/projects/llm-semantic-afterlife/scripts/s10_peek_hosted.sh
echo "==== PERSIST BGE ===="
cat /home/adam/s10/persist_bge.log
echo "==== PERSIST RUNS ===="
for d in /mnt/c/projects/llm-semantic-afterlife/runs/s10/s10-persistence-*/; do
  [ -d "$d" ] || continue
  st=NOSTATUS
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  echo "$st  $(basename "$d")"
done
