#!/usr/bin/env bash
set -u
echo "==== TIME ===="
date -u +%Y-%m-%dT%H:%M:%SZ
echo "==== PS ===="
pgrep -af 's9_embed_qwen|afterlife embed|s9_post_generate|s9_embed_qwen_hosted' || true
echo "==== MASTER HOSTED ===="
tail -n 40 /home/adam/s9/embed_qwen_hosted.log 2>/dev/null || echo 'no hosted master'
echo "==== HOSTED LOGS ===="
ls -lt /home/adam/s9/embed-qwen-*.log 2>/dev/null | head
echo "==== LAST HOSTED TAIL ===="
latestq=$(ls -t /home/adam/s9/embed-qwen-*.log 2>/dev/null | head -n 1)
if [ -n "${latestq:-}" ]; then
  echo "file=$latestq"
  tail -n 40 "$latestq"
fi
echo "==== RUNS S9 ===="
for d in /mnt/c/projects/llm-semantic-afterlife/runs/s9/*/; do
  name=$(basename "$d")
  st="NOSTATUS"
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  echo "$st  $name"
done
echo "==== ARTIFACTS S9 ===="
find /mnt/c/projects/llm-semantic-afterlife/artifacts/stage-9 -maxdepth 3 -type f 2>/dev/null | head -80
