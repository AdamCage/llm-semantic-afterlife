#!/usr/bin/env bash
set -euo pipefail
{ exec 7>&- 8>&- 9>&-; } 2>/dev/null || true
ROOT=/mnt/c/projects/llm-semantic-afterlife
sed -i 's/\r$//' "$ROOT/scripts/s12_rotate.sh" "$ROOT/scripts/s12_run_one.sh" || true
mkdir -p /home/adam/s12
nohup bash "$ROOT/scripts/s12_rotate.sh" > /home/adam/s12/rotate.nohup 2>&1 &
echo "PID=$!"
echo "$!" > /home/adam/s12/rotate.pid
sleep 3
tail -n 15 /home/adam/s12/rotate.log || true
