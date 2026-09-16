#!/usr/bin/env bash
# Hosted Qwen3-Embedding-8B for the four S9 generate runs (ADR-0027).
# RouterAI primary. Logs under /home/adam/s9 only.
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
export TOKENIZERS_PARALLELISM=false
cd /mnt/c/projects/llm-semantic-afterlife

LOGDIR=/home/adam/s9
mkdir -p "$LOGDIR"
MASTER="$LOGDIR/embed_qwen_hosted.log"
CFG=configs/stages/stage9_qwen/embed_qwen.yaml

RUNS=(
  s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6
  s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc
  s9-paperb-qwen-instruct-int8-20260912T180435Z-e9c7d498
  s9-paperb-qwen-base-int8-20260914T091655Z-11069a87
)

say() { echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) $* ===" | tee -a "$MASTER"; }

say "hosted qwen-embed start cfg=$CFG"
for RUN in "${RUNS[@]}"; do
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
