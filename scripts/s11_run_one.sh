#!/usr/bin/env bash
# One S11 local generate on WSL. Usage: s11_run_one.sh <yaml>
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
export HF_HOME=/home/adam/hf-paperb
export HUGGINGFACE_HUB_CACHE=/home/adam/hf-paperb/hub
export TRANSFORMERS_CACHE=/home/adam/hf-paperb/hub
export HF_HUB_CACHE=/home/adam/hf-paperb/hub
export AFTERLIFE_BUDGET_USD_TOTAL=200
export TOKENIZERS_PARALLELISM=false
cd /mnt/c/projects/llm-semantic-afterlife

CFG="${1:?config yaml required}"
shift
TAG="$(basename "$CFG" .yaml)"
LOGDIR=/home/adam/s11
mkdir -p "$LOGDIR"
LOG="$LOGDIR/${TAG}.log"

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) start $TAG $* ===" | tee -a "$LOG"
echo "free_wsl=$(df -B1 / | awk 'NR==2{print $4}')" | tee -a "$LOG"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$LOG"
ncomp="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -c '[0-9]' || true)"
if [ "${ncomp:-0}" -gt 0 ]; then
  echo "REFUSE: GPU already has compute apps" | tee -a "$LOG"
  nvidia-smi | tee -a "$LOG"
  exit 2
fi

set +e
uv run afterlife generate --config "$CFG" --yes "$@" 2>&1 | tee -a "$LOG"
RC=${PIPESTATUS[0]}
set -e
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) exit=$RC $TAG ===" | tee -a "$LOG"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$LOG"
if grep -Eqi 'out of memory|CUDA out of memory|torch.OutOfMemoryError' "$LOG"; then
  echo "OOM_DETECTED $TAG" | tee -a "$LOG"
  echo "OOM_DETECTED $TAG" > "$LOGDIR/${TAG}.oom"
fi
exit "$RC"
