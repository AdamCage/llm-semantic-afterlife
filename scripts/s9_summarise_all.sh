#!/usr/bin/env bash
# Protocol diagnostics for the four closed S9 generate runs.
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
cd /mnt/c/projects/llm-semantic-afterlife

LOGDIR=/home/adam/s9
mkdir -p "$LOGDIR"
LOG="$LOGDIR/summarise.log"

RUNS=(
  s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6
  s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc
  s9-paperb-qwen-instruct-int8-20260912T180435Z-e9c7d498
  s9-paperb-qwen-base-int8-20260914T091655Z-11069a87
)

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) summarise start ===" >>"$LOG"
for RUN in "${RUNS[@]}"; do
  echo "=== $RUN ===" >>"$LOG"
  uv run python scripts/summarise_run.py "$RUN" >>"$LOG" 2>&1 || echo "FAILED $RUN" >>"$LOG"
done
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) summarise done ===" >>"$LOG"
