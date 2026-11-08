#!/usr/bin/env bash
set -u
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
echo "==== PROCS ===="
ps -ef | grep -E 's11_resume_it|afterlife generate|s11_watch' | grep -v grep || echo none
echo "==== LOG ===="
tail -n 30 /home/adam/s11/pb-gemma4-12b-it.log | sed 's/\r$//'
echo "==== STATUS ===="
tr -d '\r\n' < runs/s11/s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427/STATUS
echo
