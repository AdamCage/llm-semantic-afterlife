#!/usr/bin/env bash
# Sequential S9 generate: Instruct NF4 → Base NF4 → Instruct INT8 → Base INT8.
# Native-chat is not in this list (PLAN E3).
set -euo pipefail
ROOT=/mnt/c/projects/llm-semantic-afterlife
cd "$ROOT"
sed -i 's/\r$//' "$ROOT/scripts/s9_run_one.sh" || true

LOGDIR=/home/adam/s9
mkdir -p "$LOGDIR"
MASTER="$LOGDIR/matrix.log"

run_one() {
  local cfg="$1"
  echo "BEGIN $cfg $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"
  bash "$ROOT/scripts/s9_run_one.sh" "$cfg"
  local rc=$?
  echo "END $cfg rc=$rc $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"
  return "$rc"
}

run_one configs/stages/stage9_qwen/pb-qwen3-8b-instruct.yaml
run_one configs/stages/stage9_qwen/pb-qwen3-8b-base.yaml
run_one configs/stages/stage9_qwen/pb-qwen3-8b-instruct-int8.yaml
run_one configs/stages/stage9_qwen/pb-qwen3-8b-base-int8.yaml
echo "MATRIX DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"
