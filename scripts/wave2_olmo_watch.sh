#!/usr/bin/env bash
set -eu
echo ---smi---
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv
echo ---ps---
ps aux | grep -E 'afterlife|olmo' | grep -v grep | head
echo ---run---
ls -la /mnt/c/projects/llm-semantic-afterlife/runs/s8/s8-paperb-micro-olmo3-7b-base-20260910T222217Z-e3cc4b7f/ | head
echo ---steps---
wc -l /mnt/c/projects/llm-semantic-afterlife/runs/s8/s8-paperb-micro-olmo3-7b-base-20260910T222217Z-e3cc4b7f/requests/*.jsonl 2>/dev/null || true
tail -c 400 /mnt/c/projects/llm-semantic-afterlife/runs/s8/s8-paperb-micro-olmo3-7b-base-20260910T222217Z-e3cc4b7f/events.jsonl
echo
echo ---status---
cat /mnt/c/projects/llm-semantic-afterlife/runs/s8/s8-paperb-micro-olmo3-7b-base-20260910T222217Z-e3cc4b7f/STATUS
