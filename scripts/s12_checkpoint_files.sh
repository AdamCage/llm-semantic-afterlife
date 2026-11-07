#!/usr/bin/env bash
set -u
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== GPU ===="
nvidia-smi --query-compute-apps=pid --format=csv,noheader
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
echo "==== PROCS ===="
ps -ef | grep -E 's12_rotate|afterlife generate' | grep -v grep || echo none
echo "==== STEP FILES ===="
find runs/s12 -name '*.steps.jsonl' -printf '%s %p\n' | sort
echo "==== WATCH ===="
pgrep -af s12_watch || echo no-watch
