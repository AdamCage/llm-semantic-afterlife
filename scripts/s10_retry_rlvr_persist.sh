#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
export AFTERLIFE_BUDGET_USD_TOTAL=200
cd /mnt/c/projects/llm-semantic-afterlife

for d in \
  runs/s10/s10-persistence-local-bge-m3-20260918T181815Z-43802c37 \
  runs/s10/s10-persistence-local-bge-m3-20260918T181919Z-e1089709
do
  if [ -d "$d" ] && [ ! -f "$d/SUPERSEDED" ]; then
    echo "LOO <3 seeds or min_chunks; retried after CLI skip" >"$d/SUPERSEDED"
    echo SUPERSEDED "$(basename "$d")"
  fi
done

RUN=s10-embed-paperb-olmo-embed-bge-20260918T172025Z-ed8ca4aa
LOG=/home/adam/s10/persistence-${RUN}.retry.log
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) retry persistence $RUN ===" | tee -a "$LOG"
uv run afterlife analyze persistence --run "$RUN" >>"$LOG" 2>&1
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) rc=$? ===" | tee -a "$LOG"
uv run python scripts/s10_print_gt.py
