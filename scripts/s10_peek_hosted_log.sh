#!/usr/bin/env bash
set -u
ls -lt /home/adam/s10/embed-qwen-*.log 2>/dev/null | head
echo "==== TAIL ===="
tail -n 40 /home/adam/s10/embed-qwen-s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3.log 2>/dev/null
echo "==== EVENTS ===="
RUN=/mnt/c/projects/llm-semantic-afterlife/runs/s10/s10-embed-paperb-olmo-embed-qwen-hosted-20260918T181024Z-56bec26e
wc -l "$RUN/events.jsonl"
tail -n 5 "$RUN/events.jsonl"
