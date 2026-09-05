#!/usr/bin/env bash
# S4.2 post-generate analysis. Does not mint a generate run_id.
# Degeneracy and protocol do not need embeddings; geometry/separation wait
# for the embed STATUS file.
set -euo pipefail
cd /workspace
export AFTERLIFE_BUDGET_USD_TOTAL=200
export AFTERLIFE_BUDGET_USD_PER_RUN=7.0
export AFTERLIFE_EXECUTION_MODE=live

GEN=s4-w8192-20260904T120057Z-ce82ce55
EMBED=${S42_EMBED_RUN:-s4-embed-w8192-20260905T090901Z-15172d14}

echo "=== degeneracy $GEN ==="
uv run afterlife analyze degeneracy --run "$GEN"

echo "=== protocol $GEN ==="
uv run afterlife analyze protocol --run "$GEN"

echo "=== wait for embed $EMBED ==="
status_file="runs/s4/${EMBED}/STATUS"
if [[ ! -f "$status_file" ]]; then
  echo "missing $status_file" >&2
  exit 1
fi
while true; do
  status=$(tr -d '[:space:]' < "$status_file")
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) embed STATUS=$status"
  if [[ "$status" == "COMPLETED" ]]; then
    break
  fi
  if [[ "$status" == "FAILED" || "$status" == "ABORTED" ]]; then
    echo "embed $EMBED ended $status" >&2
    exit 1
  fi
  sleep 30
done

for space in bge-m3 qwen3-embed-8b; do
  echo "=== geometry $space ==="
  uv run afterlife analyze geometry --run "$EMBED" --embedding "$space"
  echo "=== separation $space ==="
  uv run afterlife analyze separation --run "$EMBED" --embedding "$space"
done

echo "=== assemble grid ==="
uv run python scripts/assemble_stage4_grid.py --s42-embed "$EMBED"
echo "S4.2 analysis pipeline finished"
