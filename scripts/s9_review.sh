#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
export AFTERLIFE_BUDGET_USD_TOTAL=200
export AFTERLIFE_BUDGET_USD_PER_RUN=7
cd /mnt/c/projects/llm-semantic-afterlife
uv run afterlife review --stage s9
uv run pytest tests/test_wave1_paper_b_harness.py tests/test_persistence.py -q --tb=line
