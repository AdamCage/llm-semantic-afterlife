#!/usr/bin/env bash
set -u
RUN=s10-embed-paperb-olmo-embed-bge-20260918T172254Z-60d02d30
ROOT=/mnt/c/projects/llm-semantic-afterlife/runs/s10/$RUN
echo "==== STATUS ===="
cat "$ROOT/STATUS" 2>/dev/null
echo
echo "==== EVENTS TAIL ===="
tail -n 20 "$ROOT/events.jsonl" 2>/dev/null
echo
echo "==== EVENT COUNT ===="
wc -l "$ROOT/events.jsonl" 2>/dev/null
echo "==== PS STATE ===="
ps -o pid,stat,etime,wchan:20,cmd -p 2718 2>/dev/null || ps -o pid,stat,etime,cmd -C python3 | head
echo "==== BGE LOGS ===="
ls -lt /home/adam/s10/embed-bge-*.log
