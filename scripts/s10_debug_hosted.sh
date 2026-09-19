#!/usr/bin/env bash
set -u
echo "==== PS ===="
ps -o pid,stat,etime,wchan:24,cmd -p 3292
echo "==== NET ===="
ls -l /proc/3292/fd 2>/dev/null | head
echo "==== STACK ===="
# lightweight: see if it's in futex
cat /proc/3292/wchan 2>/dev/null; echo
echo "==== EVENTS ===="
wc -l /mnt/c/projects/llm-semantic-afterlife/runs/s10/s10-embed-paperb-olmo-embed-qwen-hosted-20260918T181024Z-56bec26e/events.jsonl
echo "==== LOG SIZE ===="
ls -l /home/adam/s10/embed-qwen-s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3.log
tail -n 15 /home/adam/s10/embed-qwen-s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3.log
