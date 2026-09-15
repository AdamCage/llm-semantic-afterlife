#!/usr/bin/env bash
# One Paper B local generate on WSL. Usage: wave2_run_one.sh <yaml>
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
# Default ~/.cache/huggingface is root-owned on this box (PermissionError).
export HF_HOME=/home/adam/hf-paperb
export HUGGINGFACE_HUB_CACHE=/home/adam/hf-paperb/hub
export TRANSFORMERS_CACHE=/home/adam/hf-paperb/hub
export HF_HUB_CACHE=/home/adam/hf-paperb/hub
export TOKENIZERS_PARALLELISM=false
cd /mnt/c/projects/llm-semantic-afterlife

CFG="${1:?config yaml required}"
TAG="$(basename "$CFG" .yaml)"
LOGDIR=/home/adam/wave2
mkdir -p "$LOGDIR"
LOG="$LOGDIR/${TAG}.log"

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) start $TAG ===" | tee -a "$LOG"
echo "free_wsl=$(df -B1 / | awk 'NR==2{print $4}')" | tee -a "$LOG"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$LOG"

set +e
uv run afterlife generate --config "$CFG" --yes 2>&1 | tee -a "$LOG"
RC=${PIPESTATUS[0]}
set -e
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) exit=$RC $TAG ===" | tee -a "$LOG"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$LOG"
exit "$RC"
