#!/usr/bin/env bash
# Resume S9.3 Instruct INT8, then S9.4 Base INT8.
# Logs go to /home/adam/s9 only — do not stream MatMul8bitLt to the console.
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
export BITSANDBYTES_NOWELCOME=1
export TRANSFORMERS_VERBOSITY=error
cd /mnt/c/projects/llm-semantic-afterlife

LOGDIR=/home/adam/s9
mkdir -p "$LOGDIR"
MASTER="$LOGDIR/int8_resume.log"

refuse_if_busy() {
  local n
  n="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -c '[0-9]' || true)"
  if [ "${n:-0}" -gt 0 ]; then
    echo "REFUSE: GPU already has compute apps" | tee -a "$MASTER"
    nvidia-smi | tee -a "$MASTER"
    exit 2
  fi
}

run_generate() {
  local cfg="$1"
  shift
  local tag
  tag="$(basename "$cfg" .yaml)"
  local log="$LOGDIR/${tag}.log"
  echo "BEGIN $cfg $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"
  nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$MASTER"
  refuse_if_busy
  set +e
  uv run afterlife generate --config "$cfg" --yes "$@" >>"$log" 2>&1
  local rc=$?
  set -e
  echo "END $cfg rc=$rc $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"
  return "$rc"
}

run_generate configs/stages/stage9_qwen/pb-qwen3-8b-instruct-int8.yaml \
  --resume-run s9-paperb-qwen-instruct-int8-20260912T180435Z-e9c7d498
run_generate configs/stages/stage9_qwen/pb-qwen3-8b-base-int8.yaml
echo "INT8 QUEUE DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"
