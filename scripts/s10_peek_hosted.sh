#!/usr/bin/env bash
set -u
echo "==== TIME ===="
date -u +%Y-%m-%dT%H:%M:%SZ
echo "==== ANALYSIS TAIL ===="
tail -n 12 /home/adam/s10/analysis.log
echo "==== HOSTED ===="
tail -n 8 /home/adam/s10/embed_qwen_hosted.log 2>/dev/null
RUN=$(ls -td /mnt/c/projects/llm-semantic-afterlife/runs/s10/s10-embed-paperb-olmo-embed-qwen-hosted-* 2>/dev/null | head -n 1)
echo "run=$RUN"
if [ -n "${RUN:-}" ]; then
  echo -n "STATUS="; tr -d '\r\n' <"$RUN/STATUS"; echo
  echo -n "events="; wc -l <"$RUN/events.jsonl"
  tail -n 3 "$RUN/events.jsonl"
fi
echo "==== PS ===="
pgrep -af 'afterlife embed|afterlife analyze' || true
