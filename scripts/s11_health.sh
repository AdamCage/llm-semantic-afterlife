#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== TIME ===="
date -u +%Y-%m-%dT%H:%M:%SZ
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
echo "==== MASTER ===="
cat /home/adam/s11/matrix.log 2>/dev/null || echo none
echo "==== HEALTH ===="
uv run python scripts/s11_health.py
echo "==== LOG TAIL ===="
tail -n 15 /home/adam/s11/pb-ministral-8b-base.log | sed 's/\r$//'
