#!/usr/bin/env bash
# After generate: summarise → degeneracy → BGE → hosted Qwen-embed → persistence.
# Degeneracy before any G_t. One CUDA process (BGE). Hosted is API (ADR-0028).
# Do not start S11. Do not pool with Qwen. Do not load a generator.
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

say() { echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) $* ===" | tee -a "$MASTER"; }

refuse_if_busy() {
  local n
  n="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -c '[0-9]' || true)"
  if [ "${n:-0}" -gt 0 ]; then
    say "REFUSE: GPU already has compute apps"
    nvidia-smi | tee -a "$MASTER"
    exit 2
  fi
}

say "analysis queue start"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$MASTER" || true

say "summarise"
set +e
/mnt/c/projects/llm-semantic-afterlife/scripts/s10_summarise_all.sh
rc=$?
set -e
say "summarise rc=$rc"
if [ "$rc" -ne 0 ]; then
  say "summarise failed; continuing (diagnostics, not a hard stop)"
fi

for RUN in "${S10_GEN_RUNS[@]}"; do
  say "degeneracy $RUN"
  set +e
  /mnt/c/projects/llm-semantic-afterlife/scripts/s10_degeneracy.sh "$RUN"
  rc=$?
  set -e
  say "degeneracy $RUN rc=$rc"
  if [ "$rc" -ne 0 ]; then
    say "BLOCKED degeneracy $RUN"
    exit "$rc"
  fi
done

refuse_if_busy
for RUN in "${S10_GEN_RUNS[@]}"; do
  say "embed-bge $RUN"
  nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$MASTER" || true
  set +e
  /mnt/c/projects/llm-semantic-afterlife/scripts/s10_embed_bge.sh "$RUN"
  rc=$?
  set -e
  say "embed-bge $RUN rc=$rc"
  if [ "$rc" -ne 0 ]; then
    say "BLOCKED embed-bge $RUN"
    exit "$rc"
  fi
done

say "hosted qwen-embed estimate"
set +e
uv run python scripts/s10_estimate_hosted_qwen_embed.py | tee -a "$MASTER"
rc=$?
set -e
if [ "$rc" -eq 3 ]; then
  say "BLOCKED hosted embed over ADR-0028 $5 cap — stop and ask"
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
    # RLVR INT8 can have too few min_chunks=8 trajectories for G_t.
    say "persistence $RUN failed; continuing remaining embeds"
  fi
done

say "ANALYSIS QUEUE DONE"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$MASTER" || true
