#!/usr/bin/env bash
# Resume paused Gemma IT only. Base is already COMPLETED.
set -u
ROOT=/mnt/c/projects/llm-semantic-afterlife
cd "$ROOT"
sed -i 's/\r$//' "$ROOT/scripts/s11_run_one.sh" || true
LOGDIR=/home/adam/s11
mkdir -p "$LOGDIR"
MASTER="$LOGDIR/matrix.log"
RUN=s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427

say() { echo "$* $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"; }

say "RESUME BEGIN $RUN"
set +e
bash "$ROOT/scripts/s11_run_one.sh" \
  configs/stages/stage11_ministral_gemma/pb-gemma4-12b-it.yaml \
  --resume-run "$RUN"
rc=$?
set -e
say "END gemma-it rc=$rc"
if [ -f "$LOGDIR/pb-gemma4-12b-it.oom" ]; then
  say "STOP Gemma family after OOM on it"
  say "MATRIX PARTIAL OOM"
  exit 0
fi
if [ "$rc" -ne 0 ]; then
  say "RESUME FAILED rc=$rc"
  exit "$rc"
fi
say "MATRIX DONE"
