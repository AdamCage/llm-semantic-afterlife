#!/usr/bin/env bash
# Doctor + GPU check before S11 generate. No generate.
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
export HF_HOME=/home/adam/hf-paperb
export AFTERLIFE_BUDGET_USD_TOTAL=200
cd /mnt/c/projects/llm-semantic-afterlife

echo "==== TIME ===="
date -u +%Y-%m-%dT%H:%M:%SZ
echo "==== GIT ===="
git rev-parse --abbrev-ref HEAD
git log -1 --oneline
echo "==== GPU ===="
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv
echo "==== COMPUTE ===="
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
echo "==== DOCTOR ===="
uv run afterlife doctor
echo "==== WEIGHTS ===="
ls -d /home/adam/hf-paperb/hub/models--mistralai--Ministral-3-8B-Base-2512 2>/dev/null || echo "MISSING Ministral Base"
ls -d /home/adam/hf-paperb/hub/models--mistralai--Ministral-3-8B-Instruct-2512-BF16 2>/dev/null || echo "MISSING Ministral Instruct"
ls -d /home/adam/hf-paperb/hub/models--google--gemma-4-12B 2>/dev/null || echo "MISSING Gemma Base"
ls -d /home/adam/hf-paperb/hub/models--google--gemma-4-12B-it 2>/dev/null || echo "MISSING Gemma IT"
