#!/usr/bin/env bash
set -u
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader
echo "==== PS ===="
ps -ef | grep -E 's11_analysis|afterlife analyze|afterlife embed|summarise' | grep -v grep || echo none
echo "==== LOG MARKERS ===="
grep -E '=== ' /home/adam/s11/analysis.log | tail -n 20
