#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
cd /mnt/c/projects/llm-semantic-afterlife
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader
uv run python scripts/s11_first_step.py
tail -n 8 /home/adam/s11/pb-ministral-8b-base.log | sed 's/\r$//'
