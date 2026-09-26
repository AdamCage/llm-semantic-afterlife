#!/usr/bin/env bash
# After generate: summarise → degeneracy → BGE → hosted Qwen-embed → persistence.
# Degeneracy before any G_t. One CUDA process (BGE). Hosted is API (ADR-0029).
# Do not start S12. Do not pool with Qwen or OLMo. Do not load a generator.
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

LOGDIR=/home/adam/s11
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

mapfile -t GEN_RUNS < <(uv run python scripts/s11_discover_generate.py | awk '$1!="SUPERSEDED" && $2!="SUPERSEDED"{print $NF}')
if [ "${#GEN_RUNS[@]}" -eq 0 ]; then
  say "BLOCKED no S11 generate runs"
  exit 2
fi

say "analysis queue start runs=${GEN_RUNS[*]}"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$MASTER" || true

for RUN in "${GEN_RUNS[@]}"; do
  say "summarise $RUN"
  set +e
  uv run python scripts/summarise_run.py "$RUN" | tee -a "$MASTER"
  rc=$?
  set -e
  say "summarise $RUN rc=$rc"
done

for RUN in "${GEN_RUNS[@]}"; do
  say "degeneracy $RUN"
  set +e
  /mnt/c/projects/llm-semantic-afterlife/scripts/s11_degeneracy.sh "$RUN"
  rc=$?
  set -e
  say "degeneracy $RUN rc=$rc"
  if [ "$rc" -ne 0 ]; then
    say "BLOCKED degeneracy $RUN"
    exit "$rc"
  fi
done

refuse_if_busy
for RUN in "${GEN_RUNS[@]}"; do
  say "embed-bge $RUN"
  nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$MASTER" || true
  set +e
  /mnt/c/projects/llm-semantic-afterlife/scripts/s11_embed_bge.sh "$RUN"
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
uv run python scripts/s11_estimate_hosted_qwen_embed.py | tee -a "$MASTER"
rc=$?
set -e
if [ "$rc" -eq 3 ]; then
  say "BLOCKED hosted embed over ADR-0029 $5 cap — stop and ask"
  exit 3
fi
if [ "$rc" -ne 0 ]; then
  say "BLOCKED hosted estimate rc=$rc"
  exit "$rc"
fi

set +e
/mnt/c/projects/llm-semantic-afterlife/scripts/s11_embed_qwen_hosted.sh "${GEN_RUNS[@]}"
rc=$?
set -e
say "hosted qwen-embed rc=$rc"
if [ "$rc" -ne 0 ]; then
  say "BLOCKED hosted qwen-embed"
  exit "$rc"
fi

say "persistence on completed embed runs"
mapfile -t EMBEDS < <(
  for d in runs/s11/s11-embed-*/; do
    [ -d "$d" ] || continue
    [ -f "${d}SUPERSEDED" ] && continue
    st=NOSTATUS
    [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
    [ "$st" = "COMPLETED" ] && echo "$(basename "$d")"
  done
)
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
