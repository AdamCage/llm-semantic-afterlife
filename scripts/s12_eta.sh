#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== TIME ===="
date -u +%Y-%m-%dT%H:%M:%SZ
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
echo "==== PROC ===="
ps -ef | grep 'afterlife generate' | grep -v grep || echo none
echo "==== TAIL ===="
tail -n 4 /home/adam/s12/rotate.log
echo "==== ETA ===="
uv run python scripts/s12_eta.py
