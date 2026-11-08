#!/usr/bin/env bash
# Stop the live S11 generate and free the GPU. Do not mint a new run.
set -u
ROOT=/mnt/c/projects/llm-semantic-afterlife
cd "$ROOT"
LOGDIR=/home/adam/s11
mkdir -p "$LOGDIR"
RUN=s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981

echo "PAUSE $(date -u +%Y-%m-%dT%H:%M:%SZ) target=$RUN" | tee -a "$LOGDIR/matrix.log"

# Matrix parent first so a child exit cannot advance to Gemma IT.
kill -TERM 843 7199 7217 7221 2>/dev/null || true
sleep 3
if kill -0 7221 2>/dev/null; then
  echo "still alive after TERM; waiting for in-flight step" | tee -a "$LOGDIR/matrix.log"
  for _ in 1 2 3 4 5 6 7 8 9 10 11 12; do
    kill -0 7221 2>/dev/null || break
    sleep 5
  done
fi
if kill -0 7221 2>/dev/null; then
  echo "KILL python 7221" | tee -a "$LOGDIR/matrix.log"
  kill -KILL 7221 7217 7199 843 2>/dev/null || true
  sleep 2
fi
# Watcher is a timer, not generate.
kill -TERM 1131 2>/dev/null || true

echo "==== AFTER ===="
ps -ef | grep -E 's11_run|afterlife generate' | grep -v grep || echo "no s11 generate procs"
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
if [ -f "runs/s11/$RUN/STATUS" ]; then
  echo -n "STATUS "
  tr -d '\r\n' < "runs/s11/$RUN/STATUS"
  echo
fi
cat > "$LOGDIR/PAUSED.txt" <<EOF
paused $(date -u +%Y-%m-%dT%H:%M:%SZ)
run_id $RUN
resume:
  bash $ROOT/scripts/s11_run_one.sh configs/stages/stage11_ministral_gemma/pb-gemma4-12b-base.yaml --resume-run $RUN
do not restart scripts/s11_run_matrix.sh from the top
EOF
echo "wrote $LOGDIR/PAUSED.txt"
