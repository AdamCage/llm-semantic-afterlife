#!/usr/bin/env bash
# Resume paused Gemma Base, then start Gemma IT. Do not rerun Ministral.
set -u
ROOT=/mnt/c/projects/llm-semantic-afterlife
cd "$ROOT"
sed -i 's/\r$//' "$ROOT/scripts/s11_run_one.sh" || true
LOGDIR=/home/adam/s11
mkdir -p "$LOGDIR"
MASTER="$LOGDIR/matrix.log"
RUN=s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981

say() { echo "$* $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"; }

say "RESUME BEGIN $RUN"
set +e
bash "$ROOT/scripts/s11_run_one.sh" \
  configs/stages/stage11_ministral_gemma/pb-gemma4-12b-base.yaml \
  --resume-run "$RUN"
rc=$?
set -e
say "END gemma-base rc=$rc"
if [ -f "$LOGDIR/pb-gemma4-12b-base.oom" ]; then
  say "STOP Gemma family after OOM on base"
  say "MATRIX PARTIAL OOM"
  exit 0
fi
if [ "$rc" -ne 0 ]; then
  say "RESUME FAILED rc=$rc"
  exit "$rc"
fi

say "BEGIN gemma-it"
set +e
bash "$ROOT/scripts/s11_run_one.sh" \
  configs/stages/stage11_ministral_gemma/pb-gemma4-12b-it.yaml
rc=$?
set -e
say "END gemma-it rc=$rc"
if [ -f "$LOGDIR/pb-gemma4-12b-it.oom" ]; then
  say "STOP Gemma family after OOM on it"
  say "MATRIX PARTIAL OOM"
  exit 0
fi
if [ "$rc" -ne 0 ]; then
  say "GEMMA IT FAILED rc=$rc"
  exit "$rc"
fi
say "MATRIX DONE"
