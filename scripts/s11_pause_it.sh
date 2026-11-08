#!/usr/bin/env bash
# Pause the live Gemma IT generate and free the GPU. Same run_id.
set -u
ROOT=/mnt/c/projects/llm-semantic-afterlife
cd "$ROOT"
LOGDIR=/home/adam/s11
mkdir -p "$LOGDIR"
RUN=s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427

echo "PAUSE $(date -u +%Y-%m-%dT%H:%M:%SZ) target=$RUN" | tee -a "$LOGDIR/matrix.log"

mapfile -t PIDS < <(ps -ef | awk '/s11_resume_gemma|s11_run_one|afterlife generate|s11_watch_matrix/ && !/awk/ {print $2}')
echo "pids ${PIDS[*]}"
if [ "${#PIDS[@]}" -gt 0 ]; then
  kill -TERM "${PIDS[@]}" 2>/dev/null || true
fi
sleep 3
if pgrep -f "afterlife generate" >/dev/null 2>&1; then
  echo "still alive after TERM; waiting" | tee -a "$LOGDIR/matrix.log"
  for _ in 1 2 3 4 5 6 7 8 9 10 11 12; do
    pgrep -f "afterlife generate" >/dev/null 2>&1 || break
    sleep 5
  done
fi
if pgrep -f "afterlife generate" >/dev/null 2>&1; then
  echo "KILL generate" | tee -a "$LOGDIR/matrix.log"
  pkill -KILL -f "afterlife generate" 2>/dev/null || true
  sleep 2
fi
pkill -TERM -f "s11_resume_gemma|s11_run_one|s11_watch_matrix" 2>/dev/null || true

echo "==== AFTER ===="
ps -ef | grep -E 's11_resume|s11_run_one|afterlife generate|s11_watch' | grep -v grep || echo "no s11 generate procs"
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
Gemma Base is COMPLETED. Do not rerun it.
resume IT only:
  bash $ROOT/scripts/s11_run_one.sh configs/stages/stage11_ministral_gemma/pb-gemma4-12b-it.yaml --resume-run $RUN
do not restart scripts/s11_run_matrix.sh or scripts/s11_resume_gemma.sh
EOF
echo "wrote $LOGDIR/PAUSED.txt"
