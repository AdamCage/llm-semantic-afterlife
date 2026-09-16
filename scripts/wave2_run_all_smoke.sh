#!/usr/bin/env bash
# Remaining Wave 2 smokes, one checkpoint at a time. Gemma last.
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
ROOT=/mnt/c/projects/llm-semantic-afterlife
SCRIPT="$ROOT/scripts/wave2_run_one.sh"
LOGDIR=/home/adam/wave2
mkdir -p "$LOGDIR"
RESULT="$LOGDIR/smoke_results.jsonl"

# Already completed: pb-qwen3-8b-base
MODELS=(
  pb-qwen3-8b-instruct
  pb-olmo3-7b-base
  pb-olmo3-7b-sft
  pb-olmo3-7b-dpo
  pb-olmo3-7b-rlv
  pb-ministral-8b-base
  pb-ministral-8b-instruct
  pb-gemma4-12b-base
  pb-gemma4-12b-it
)

for slug in "${MODELS[@]}"; do
  echo "======== $(date -u +%Y-%m-%dT%H:%M:%SZ) $slug ========"
  df -h / | tail -1
  nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheade
  free_bytes="$(df -B1 / | awk 'NR==2{print $4}')"
  if [ "$free_bytes" -lt 40000000000 ]; then
    echo "REFUSE download: only ${free_bytes} bytes free on /" | tee -a "$LOGDIR/blocker.txt"
    exit 2
  fi
  set +e
  bash "$SCRIPT" "configs/stages/stage8_smoke/${slug}.yaml"
  rc=$?
  set -e
  echo "{\"slug\":\"$slug\",\"utc\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"exit\":$rc}" >> "$RESULT"
  # Do not stop the loop on gated auth; stop on unexpected OOM for non-Gemma.
  if grep -Eiq "out of memory|CUDA out of memory" "$LOGDIR/${slug}.log"; then
    echo "OOM on $slug" | tee -a "$LOGDIR/blocker.txt"
    if [[ "$slug" == pb-gemma4-* ]]; then
      echo "Gemma OOM recorded; no substitute. Stopping remaining Gemma cells."
      break
    fi
    echo "Unexpected OOM; stopping remaining smokes."
    break
  fi
  if grep -Eiq "ReasoningLeakError|thinking tokens leaked" "$LOGDIR/${slug}.log"; then
    echo "thinking-storm on $slug; stopping." | tee -a "$LOGDIR/blocker.txt"
    break
  fi
done
echo "======== smoke loop done $(date -u +%Y-%m-%dT%H:%M:%SZ) ========"
