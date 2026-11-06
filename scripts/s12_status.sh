#!/usr/bin/env bash
set -u
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader
echo "==== ROTATE ===="
tail -n 8 /home/adam/s12/rotate.log
echo "==== MAP ===="
cat /home/adam/s12/runs.map 2>/dev/null || echo none
echo "==== ONE LOG ===="
tail -n 12 /home/adam/s12/mb-physics-s1.log | sed 's/\r$//'
