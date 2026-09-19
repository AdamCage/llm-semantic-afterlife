#!/usr/bin/env bash
# Expand and estimate every S11 generate YAML. No network, no generate.
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
export AFTERLIFE_BUDGET_USD_TOTAL=200
cd /mnt/c/projects/llm-semantic-afterlife

for f in \
  configs/stages/stage11_ministral_gemma/pb-ministral-8b-base.yaml \
  configs/stages/stage11_ministral_gemma/pb-ministral-8b-instruct.yaml \
  configs/stages/stage11_ministral_gemma/pb-gemma4-12b-base.yaml \
  configs/stages/stage11_ministral_gemma/pb-gemma4-12b-it.yaml
do
  echo "======== PLAN $f ========"
  uv run afterlife plan --config "$f"
  echo "======== EST $f ========"
  uv run afterlife estimate --config "$f"
done
