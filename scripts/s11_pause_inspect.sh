#!/usr/bin/env bash
set -u
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
echo "==== COMPUTE ===="
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
echo "==== PROCS ===="
ps -ef | grep -E 's11_run|afterlife generate|s11_watch' | grep -v grep || true
echo "==== STATUS ===="
st=runs/s11/s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981/STATUS
if [ -f "$st" ]; then tr -d '\r\n' < "$st"; echo; else echo MISSING; fi
