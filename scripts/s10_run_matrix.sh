#!/usr/bin/env bash
# Sequential S10 generate: Base → SFT → DPO → RLVR NF4, then Base/RLVR INT8.
# Native-chat is not in this list (PLAN E3). Do not invoke until human yes.
set -euo pipefail
ROOT=/mnt/c/projects/llm-semantic-afterlife
cd "$ROOT"
sed -i 's/\r$//' "$ROOT/scripts/s10_run_one.sh" || true

LOGDIR=/home/adam/s10
mkdir -p "$LOGDIR"
MASTER="$LOGDIR/matrix.log"

run_one() {
  local cfg="$1"
  echo "BEGIN $cfg $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"
  bash "$ROOT/scripts/s10_run_one.sh" "$cfg"
  local rc=$?
  echo "END $cfg rc=$rc $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"
  return "$rc"
}

run_one configs/stages/stage10_olmo/pb-olmo3-7b-base.yaml
run_one configs/stages/stage10_olmo/pb-olmo3-7b-sft.yaml
run_one configs/stages/stage10_olmo/pb-olmo3-7b-dpo.yaml
run_one configs/stages/stage10_olmo/pb-olmo3-7b-rlvr.yaml
run_one configs/stages/stage10_olmo/pb-olmo3-7b-base-int8.yaml
run_one configs/stages/stage10_olmo/pb-olmo3-7b-rlvr-int8.yaml
echo "MATRIX DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"
