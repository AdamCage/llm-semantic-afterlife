#!/usr/bin/env bash
# Expand and estimate every S10 generate YAML. No network, no generate.
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
export AFTERLIFE_BUDGET_USD_TOTAL=200
cd /mnt/c/projects/llm-semantic-afterlife

for f in \
  configs/stages/stage10_olmo/pb-olmo3-7b-base.yaml \
  configs/stages/stage10_olmo/pb-olmo3-7b-sft.yaml \
  configs/stages/stage10_olmo/pb-olmo3-7b-dpo.yaml \
  configs/stages/stage10_olmo/pb-olmo3-7b-rlvr.yaml \
  configs/stages/stage10_olmo/pb-olmo3-7b-base-int8.yaml \
  configs/stages/stage10_olmo/pb-olmo3-7b-rlvr-int8.yaml
do
  echo "======== PLAN $f ========"
  uv run afterlife plan --config "$f"
  echo "======== EST $f ========"
  uv run afterlife estimate --config "$f"
done
