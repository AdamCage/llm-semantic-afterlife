#!/usr/bin/env bash
# Detached S10 matrix. Logs only under /home/adam/s10 — not Cursor stdout.
set -euo pipefail
ROOT=/mnt/c/projects/llm-semantic-afterlife
LOGDIR=/home/adam/s10
mkdir -p "$LOGDIR"
sed -i 's/\r$//' "$ROOT/scripts/s10_run_one.sh" "$ROOT/scripts/s10_run_matrix.sh" || true

if pgrep -f 's10_run_matrix.sh|afterlife generate' >/dev/null; then
  echo "REFUSE: generate already running"
  pgrep -af 's10_run_matrix.sh|afterlife generate' || true
  exit 2
fi

ncomp="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -c '[0-9]' || true)"
if [ "${ncomp:-0}" -gt 0 ]; then
  echo "REFUSE: GPU already has compute apps"
  nvidia-smi
  exit 2
fi

echo "=== launch $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" >>"$LOGDIR/supervisor.log"
nohup bash "$ROOT/scripts/s10_run_matrix.sh" >>"$LOGDIR/supervisor.log" 2>&1 &
echo "$!" | tee "$LOGDIR/matrix.pid"
echo "launched matrix pid=$(cat "$LOGDIR/matrix.pid") $(date -u +%Y-%m-%dT%H:%M:%SZ)"
