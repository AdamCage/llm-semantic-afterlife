#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export AFTERLIFE_BUDGET_USD_TOTAL=200
cd /mnt/c/projects/llm-semantic-afterlife

supersede() {
  local run_id="$1"
  local reason="$2"
  local by="${3:-}"
  if [ -f "runs/s10/${run_id}/SUPERSEDED" ]; then
    echo "already SUPERSEDED  ${run_id}"
    return 0
  fi
  if [ -n "$by" ]; then
    uv run afterlife supersede "$run_id" --reason "$reason" --by "$by"
  else
    uv run afterlife supersede "$run_id" --reason "$reason"
  fi
}

# Older BGE persist duplicates from analysis-resume; keep the later COMPLETED sibling.
supersede s10-persistence-local-bge-m3-20260918T181215Z-ae5ce920 \
  "duplicate BGE persist; analysis-resume re-ran the same embed" \
  s10-persistence-local-bge-m3-20260918T183606Z-ae5ce920
supersede s10-persistence-local-bge-m3-20260918T181540Z-a488eb25 \
  "duplicate BGE persist; analysis-resume re-ran the same embed" \
  s10-persistence-local-bge-m3-20260918T183928Z-a488eb25
supersede s10-persistence-local-bge-m3-20260918T181744Z-8281a4d8 \
  "duplicate BGE persist; analysis-resume re-ran the same embed" \
  s10-persistence-local-bge-m3-20260918T184127Z-8281a4d8
supersede s10-persistence-local-bge-m3-20260918T182127Z-43802c37 \
  "duplicate BGE persist; analysis-resume re-ran the same embed" \
  s10-persistence-local-bge-m3-20260918T184158Z-43802c37
supersede s10-persistence-local-bge-m3-20260918T181845Z-6401324e \
  "duplicate BGE persist; analysis-resume re-ran the same embed" \
  s10-persistence-local-bge-m3-20260918T184229Z-6401324e

# RLVR INT8 persist: 0 completers, min_chunks=8. Recorded skip, not a silent drop.
supersede s10-persistence-local-bge-m3-20260918T184303Z-e1089709 \
  "RLVR INT8 has 0 completers; persistence refused min_chunks=8. Kept as recorded skip, not an E5 cell."
supersede s10-persistence-qwen3-embed-8b-20260918T185656Z-bf8e0779 \
  "RLVR INT8 has 0 completers; persistence refused min_chunks=8. Kept as recorded skip, not an E5 cell."

echo "==== REMAINING INCOMPLETE NON-SUPERSEDED ===="
for d in runs/s10/*/; do
  [ -d "$d" ] || continue
  [ -f "${d}SUPERSEDED" ] && continue
  st=NOSTATUS
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  [ "$st" = "COMPLETED" ] && continue
  echo "$st  $(basename "$d")"
done
