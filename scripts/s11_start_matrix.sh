#!/usr/bin/env bash
# Launch S11 generate matrix. One GPU. Logs: /home/adam/s11/matrix.log
set -euo pipefail
ROOT=/mnt/c/projects/llm-semantic-afterlife
sed -i 's/\r$//' "$ROOT/scripts/s11_run_one.sh" "$ROOT/scripts/s11_run_matrix.sh" || true
mkdir -p /home/adam/s11
nohup bash "$ROOT/scripts/s11_run_matrix.sh" > /home/adam/s11/matrix.nohup 2>&1 &
echo "PID=$!"
echo "$!" > /home/adam/s11/matrix.pid
sleep 2
head -n 20 /home/adam/s11/matrix.log || true
head -n 20 /home/adam/s11/matrix.nohup || true
