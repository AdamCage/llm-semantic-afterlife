#!/usr/bin/env bash
# BGE-M3 embed of one S10 generate run. Logs under /home/adam/s10.
# Usage: s10_embed_bge.sh <generate_run_id>
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

RUN="${1:?generate run_id required}"
LOGDIR=/home/adam/s10
mkdir -p "$LOGDIR"
LOG="$LOGDIR/embed-bge-${RUN}.log"

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) embed-bge $RUN ===" >>"$LOG"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader >>"$LOG" || true
set +e
uv run afterlife embed --run "$RUN" --config configs/stages/stage10_olmo/embed_bge.yaml >>"$LOG" 2>&1
RC=$?
set -e
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) exit=$RC embed-bge $RUN ===" >>"$LOG"
exit "$RC"
