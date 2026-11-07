#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
cd /mnt/c/projects/llm-semantic-afterlife
sed -i 's/\r$//' scripts/s12_hourly.sh scripts/s12_keepalive.sh scripts/s12_research.sh scripts/s12_tau.py scripts/s12_research.py || true
bash -n scripts/s12_hourly.sh
bash -n scripts/s12_keepalive.sh
bash -n scripts/s12_research.sh
uv run pytest tests/test_s12_tau_clock.py -q
