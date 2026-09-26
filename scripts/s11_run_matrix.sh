#!/usr/bin/env bash
# Sequential S11 generate: Ministral Base → Instruct, then Gemma Base → IT.
# Native-chat is not in this list (PLAN E3). Gemma OOM stops that family.
set -euo pipefail
ROOT=/mnt/c/projects/llm-semantic-afterlife
cd "$ROOT"
sed -i 's/\r$//' "$ROOT/scripts/s11_run_one.sh" || true

LOGDIR=/home/adam/s11
mkdir -p "$LOGDIR"
MASTER="$LOGDIR/matrix.log"

run_one() {
  local cfg="$1"
  shift
  echo "BEGIN $cfg $* $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"
  bash "$ROOT/scripts/s11_run_one.sh" "$cfg" "$@"
  local rc=$?
  echo "END $cfg rc=$rc $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"
  return "$rc"
}

maybe_stop_gemma() {
  local tag="$1"
  if [ -f "$LOGDIR/${tag}.oom" ]; then
    echo "STOP Gemma family after OOM on $tag $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"
    echo "MATRIX PARTIAL OOM $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"
    exit 0
  fi
}

run_one configs/stages/stage11_ministral_gemma/pb-ministral-8b-base.yaml
run_one configs/stages/stage11_ministral_gemma/pb-ministral-8b-instruct.yaml
run_one configs/stages/stage11_ministral_gemma/pb-gemma4-12b-base.yaml
maybe_stop_gemma pb-gemma4-12b-base
run_one configs/stages/stage11_ministral_gemma/pb-gemma4-12b-it.yaml
maybe_stop_gemma pb-gemma4-12b-it
echo "MATRIX DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"
