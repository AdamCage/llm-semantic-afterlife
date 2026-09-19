#!/usr/bin/env bash
# BGE persistence while hosted Qwen-embed runs (CPU). Degeneracy already done.
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
export AFTERLIFE_BUDGET_USD_TOTAL=200
cd /mnt/c/projects/llm-semantic-afterlife
LOGDIR=/home/adam/s10
MASTER="$LOGDIR/persist_bge.log"
say() { echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) $* ===" | tee -a "$MASTER"; }
mapfile -t EMBEDS < <(uv run python scripts/s10_discover_embeds.py | awk '$1=="COMPLETED" && $2=="local-bge-m3"{print $4}')
say "bge persistence n=${#EMBEDS[@]}"
for RUN in "${EMBEDS[@]}"; do
  say "persistence $RUN"
  set +e
  uv run afterlife analyze persistence --run "$RUN" >>"$LOGDIR/persistence-${RUN}.log" 2>&1
  rc=$?
  set -e
  say "persistence $RUN rc=$rc"
done
say "BGE PERSISTENCE DONE"
