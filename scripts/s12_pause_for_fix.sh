#!/usr/bin/env bash
set -u
cd /mnt/c/projects/llm-semantic-afterlife
echo "PAUSE FOR ROTATE FIX $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /home/adam/s12/rotate.log
kill -TERM 488 527 532 2>/dev/null || true
sleep 3
kill -KILL 488 527 532 2>/dev/null || true
pkill -TERM -f 'afterlife generate --config configs/stages/stage12_horizon' 2>/dev/null || true
sleep 2
pkill -KILL -f 'afterlife generate --config configs/stages/stage12_horizon' 2>/dev/null || true
echo "==== AFTER ===="
ps -ef | grep -E 's12_rotate|afterlife generate' | grep -v grep || echo none
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
st=runs/s12/s12-paperb-l2-mb-physics-s1-20260926T000516Z-6c25fa59/STATUS
if [ -f "$st" ]; then echo -n "STATUS "; tr -d '\r\n' < "$st"; echo; fi
