#!/usr/bin/env bash
# One-shot S12 research finish. Refuses to run twice.
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
export HF_HOME=/home/adam/hf-paperb
export TOKENIZERS_PARALLELISM=false
export AFTERLIFE_BUDGET_USD_TOTAL=200
ROOT=/mnt/c/projects/llm-semantic-afterlife
cd "$ROOT"
sed -i 's/\r$//' "$ROOT/scripts/s12_research.py" "$ROOT/scripts/s12_tau.py" || true
exec uv run python "$ROOT/scripts/s12_research.py"
