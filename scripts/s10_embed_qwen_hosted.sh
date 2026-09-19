#!/usr/bin/env bash
# Hosted Qwen3-Embedding-8B for S10 generate runs (ADR-0028).
# Usage: s10_embed_qwen_hosted.sh <run_id> [<run_id> ...]
# RouterAI primary. Logs under /home/adam/s10 only. Cap $5.
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
export AFTERLIFE_BUDGET_USD_TOTAL=200
export TOKENIZERS_PARALLELISM=false
cd /mnt/c/projects/llm-semantic-afterlife

if [ "$#" -lt 1 ]; then
  echo "usage: s10_embed_qwen_hosted.sh <run_id> [<run_id> ...]" >&2
  exit 2
fi

LOGDIR=/home/adam/s10
mkdir -p "$LOGDIR"
MASTER="$LOGDIR/embed_qwen_hosted.log"
CFG=configs/stages/stage10_olmo/embed_qwen.yaml

say() { echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) $* ===" | tee -a "$MASTER"; }

say "hosted qwen-embed start cfg=$CFG"
for RUN in "$@"; do
  say "embed-qwen $RUN"
  set +e
  uv run afterlife embed --run "$RUN" --config "$CFG" \
    >>"$LOGDIR/embed-qwen-${RUN}.log" 2>&1
  rc=$?
  set -e
  say "embed-qwen $RUN rc=$rc"
  if [ "$rc" -ne 0 ]; then
    say "BLOCKED embed-qwen $RUN"
    exit "$rc"
  fi
done
say "HOSTED QWEN-EMBED QUEUE DONE"
