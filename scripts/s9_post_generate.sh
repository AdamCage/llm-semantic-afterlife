#!/usr/bin/env bash
# After generate: summarise → degeneracy → BGE-M3 embed for all four S9 runs.
# Logs under /home/adam/s9 only. Do not start S10. Do not load a generator.
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
export HF_HOME=/home/adam/hf-paperb
export HUGGINGFACE_HUB_CACHE=/home/adam/hf-paperb/hub
export TRANSFORMERS_CACHE=/home/adam/hf-paperb/hub
export HF_HUB_CACHE=/home/adam/hf-paperb/hub
export TOKENIZERS_PARALLELISM=false
export PYTHONWARNINGS=ignore
export TRANSFORMERS_VERBOSITY=error
cd /mnt/c/projects/llm-semantic-afterlife

LOGDIR=/home/adam/s9
mkdir -p "$LOGDIR"
MASTER="$LOGDIR/post_generate.log"

RUNS=(
  s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6
  s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc
  s9-paperb-qwen-instruct-int8-20260912T180435Z-e9c7d498
  s9-paperb-qwen-base-int8-20260914T091655Z-11069a87
)

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

say "post-generate start"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$MASTER" || true

for RUN in "${RUNS[@]}"; do
  say "summarise $RUN"
  set +e
  uv run python scripts/summarise_run.py "$RUN" >>"$LOGDIR/summarise.log" 2>&1
  rc=$?
  set -e
  say "summarise $RUN rc=$rc"
  if [ "$rc" -ne 0 ]; then
    say "summarise failed; continuing remaining runs"
  fi
done

for RUN in "${RUNS[@]}"; do
  say "degeneracy $RUN"
  set +e
  uv run afterlife analyze degeneracy --run "$RUN" >>"$LOGDIR/degeneracy-${RUN}.log" 2>&1
  rc=$?
  set -e
  say "degeneracy $RUN rc=$rc"
  if [ "$rc" -ne 0 ]; then
    say "BLOCKED degeneracy $RUN"
    exit "$rc"
  fi
done

refuse_if_busy
for RUN in "${RUNS[@]}"; do
  say "embed-bge $RUN"
  nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$MASTER" || true
  set +e
  uv run afterlife embed --run "$RUN" --config configs/stages/stage9_qwen/embed_bge.yaml \
    >>"$LOGDIR/embed-bge-${RUN}.log" 2>&1
  rc=$?
  set -e
  say "embed-bge $RUN rc=$rc"
  if [ "$rc" -ne 0 ]; then
    say "BLOCKED embed-bge $RUN"
    exit "$rc"
  fi
done

say "POST-GENERATE QUEUE DONE"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$MASTER" || true
