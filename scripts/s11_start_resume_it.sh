#!/usr/bin/env bash
set -euo pipefail
ROOT=/mnt/c/projects/llm-semantic-afterlife
sed -i 's/\r$//' "$ROOT/scripts/s11_resume_it.sh" "$ROOT/scripts/s11_run_one.sh" || true
mkdir -p /home/adam/s11
nohup bash "$ROOT/scripts/s11_resume_it.sh" > /home/adam/s11/resume_it.nohup 2>&1 &
echo "PID=$!"
echo "$!" > /home/adam/s11/resume_it.pid
sleep 2
tail -n 8 /home/adam/s11/matrix.log
