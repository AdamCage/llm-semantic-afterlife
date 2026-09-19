#!/usr/bin/env bash
# Protocol diagnostics for the six closed S10 generate runs.
# target-steps=48 = T/B at W=4096 / B=1024 / T=49152.
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
cd /mnt/c/projects/llm-semantic-afterlife
# shellcheck source=s10_runs.sh
source /mnt/c/projects/llm-semantic-afterlife/scripts/s10_runs.sh

LOGDIR=/home/adam/s10
mkdir -p "$LOGDIR"
LOG="$LOGDIR/summarise.log"

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) summarise start ===" >>"$LOG"
for RUN in "${S10_GEN_RUNS[@]}"; do
  echo "=== $RUN ===" >>"$LOG"
  uv run python scripts/summarise_run.py --target-steps 48 "$RUN" >>"$LOG" 2>&1 \
    || echo "FAILED $RUN" >>"$LOG"
done
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) summarise done ===" >>"$LOG"
