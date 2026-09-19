#!/usr/bin/env bash
# Resume after hung RLVR INT8 BGE: timeout-retry that cell, then hosted + G_t.
# Do not re-run summarise / degeneracy / completed BGE. Do not start S11.
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
export HF_HOME=/home/adam/hf-paperb
export HUGGINGFACE_HUB_CACHE=/home/adam/hf-paperb/hub
export TRANSFORMERS_CACHE=/home/adam/hf-paperb/hub
export HF_HUB_CACHE=/home/adam/hf-paperb/hub
export AFTERLIFE_BUDGET_USD_TOTAL=200
export TOKENIZERS_PARALLELISM=false
export PYTHONWARNINGS=ignore
export TRANSFORMERS_VERBOSITY=error
cd /mnt/c/projects/llm-semantic-afterlife
# shellcheck source=s10_runs.sh
source /mnt/c/projects/llm-semantic-afterlife/scripts/s10_runs.sh

LOGDIR=/home/adam/s10
mkdir -p "$LOGDIR"
MASTER="$LOGDIR/analysis.log"
RLVR_INT8=s10-paperb-olmo-rlvr-int8-20260918T142301Z-7125ccca

say() { echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) $* ===" | tee -a "$MASTER"; }

say "analysis resume start (skip completed BGE/degeneracy)"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$MASTER" || true

say "retry embed-bge $RLVR_INT8 timeout=180s"
set +e
timeout 180 /mnt/c/projects/llm-semantic-afterlife/scripts/s10_embed_bge.sh "$RLVR_INT8"
rc=$?
set -e
say "embed-bge $RLVR_INT8 rc=$rc"
if [ "$rc" -ne 0 ]; then
  say "SKIP embed-bge $RLVR_INT8 (timeout or fail); E5 is NF4-only; 0 completers"
  latest=$(ls -td /mnt/c/projects/llm-semantic-afterlife/runs/s10/s10-embed-paperb-olmo-embed-bge-* 2>/dev/null | head -n 1 || true)
  if [ -n "${latest:-}" ] && [ ! -f "$latest/SUPERSEDED" ]; then
    st=$(tr -d '\r\n' <"$latest/STATUS" 2>/dev/null || true)
    if [ "$st" != "COMPLETED" ]; then
      echo 'ABORTED' >"$latest/STATUS"
      echo "timeout/fail retry of RLVR INT8 BGE; not an E5 cell" >"$latest/SUPERSEDED"
      say "superseded $(basename "$latest")"
    fi
  fi
fi

say "hosted qwen-embed estimate"
set +e
uv run python scripts/s10_estimate_hosted_qwen_embed.py | tee -a "$MASTER"
rc=$?
set -e
if [ "$rc" -eq 3 ]; then
  say "BLOCKED hosted embed over ADR-0028 \$5 cap — stop and ask"
  exit 3
fi
if [ "$rc" -ne 0 ]; then
  say "BLOCKED hosted estimate rc=$rc"
  exit "$rc"
fi

say "hosted qwen-embed keys"
uv run python scripts/s9_check_hosted_keys.py | tee -a "$MASTER"

set +e
/mnt/c/projects/llm-semantic-afterlife/scripts/s10_embed_qwen_hosted.sh "${S10_GEN_RUNS[@]}"
rc=$?
set -e
say "hosted qwen-embed rc=$rc"
if [ "$rc" -ne 0 ]; then
  say "BLOCKED hosted qwen-embed"
  exit "$rc"
fi

say "persistence on completed embed runs"
mapfile -t EMBEDS < <(uv run python scripts/s10_discover_embeds.py | awk '$1=="COMPLETED"{print $4}')
if [ "${#EMBEDS[@]}" -eq 0 ]; then
  say "BLOCKED no COMPLETED embed runs"
  exit 2
fi
for RUN in "${EMBEDS[@]}"; do
  say "persistence $RUN"
  set +e
  uv run afterlife analyze persistence --run "$RUN" >>"$LOGDIR/persistence-${RUN}.log" 2>&1
  rc=$?
  set -e
  say "persistence $RUN rc=$rc"
  if [ "$rc" -ne 0 ]; then
    say "persistence $RUN failed; continuing remaining embeds"
  fi
done

say "ANALYSIS QUEUE DONE"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$MASTER" || true
