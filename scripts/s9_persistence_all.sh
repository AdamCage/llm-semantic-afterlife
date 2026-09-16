#!/usr/bin/env bash
# Persistence G_t + prefix lock on every S9 embed run (one space each).
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
cd /mnt/c/projects/llm-semantic-afterlife

LOGDIR=/home/adam/s9
mkdir -p "$LOGDIR"
MASTER="$LOGDIR/persistence.log"

RUNS=(
  s9-embed-paperb-qwen-embed-bge-20260915T052756Z-67e34519
  s9-embed-paperb-qwen-embed-bge-20260915T053111Z-f39fda7b
  s9-embed-paperb-qwen-embed-bge-20260915T053243Z-5dab69c8
  s9-embed-paperb-qwen-embed-bge-20260915T053326Z-5b7d1cb9
  s9-embed-paperb-qwen-embed-qwen-hosted-20260915T061135Z-f7e02b57
  s9-embed-paperb-qwen-embed-qwen-hosted-20260915T063412Z-4d5ac57f
  s9-embed-paperb-qwen-embed-qwen-hosted-20260915T064725Z-55778666
  s9-embed-paperb-qwen-embed-qwen-hosted-20260915T065143Z-05c4d516
)

say() { echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) $* ===" | tee -a "$MASTER"; }

say "persistence start"
for RUN in "${RUNS[@]}"; do
  say "persistence $RUN"
  set +e
  uv run afterlife analyze persistence --run "$RUN" >>"$LOGDIR/persistence-${RUN}.log" 2>&1
  rc=$?
  set -e
  say "persistence $RUN rc=$rc"
  if [ "$rc" -ne 0 ]; then
    say "BLOCKED persistence $RUN"
    exit "$rc"
  fi
done
say "PERSISTENCE QUEUE DONE"
