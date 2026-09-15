#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
export HF_HOME=/home/adam/hf-paperb
export HUGGINGFACE_HUB_CACHE=/home/adam/hf-paperb/hub
export TRANSFORMERS_CACHE=/home/adam/hf-paperb/hub
export HF_HUB_CACHE=/home/adam/hf-paperb/hub
export TOKENIZERS_PARALLELISM=false
cd /mnt/c/projects/llm-semantic-afterlife
CFG="${1:?config}"
RUN="${2:?run_id}"
LOGDIR=/home/adam/wave2
mkdir -p "$LOGDIR"
LOG="$LOGDIR/resume-$(basename "$CFG" .yaml).log"
echo "=== resume $RUN ===" | tee -a "$LOG"
uv run afterlife generate --config "$CFG" --yes --resume-run "$RUN" 2>&1 | tee -a "$LOG"
echo "=== resume exit ${PIPESTATUS[0]} ===" | tee -a "$LOG"
