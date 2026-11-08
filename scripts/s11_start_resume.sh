#!/usr/bin/env bash
set -euo pipefail
ROOT=/mnt/c/projects/llm-semantic-afterlife
sed -i 's/\r$//' "$ROOT/scripts/s11_resume_gemma.sh" "$ROOT/scripts/s11_run_one.sh" || true
mkdir -p /home/adam/s11
nohup bash "$ROOT/scripts/s11_resume_gemma.sh" > /home/adam/s11/resume.nohup 2>&1 &
echo "PID=$!"
echo "$!" > /home/adam/s11/resume.pid
sleep 3
tail -n 30 /home/adam/s11/matrix.log || true
