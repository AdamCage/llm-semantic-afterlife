#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export AFTERLIFE_BUDGET_USD_TOTAL=200
export HF_HOME=/home/adam/hf-paperb
cd /mnt/c/projects/llm-semantic-afterlife
echo "=== git ==="
git branch --show-current
git rev-parse --short HEAD
echo "=== gpu ==="
nvidia-smi --query-gpu=name,memory.used,memory.free,memory.total --format=csv
echo "=== compute apps ==="
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv || true
echo "=== disk ==="
df -h / /mnt/c
echo "=== olmo cache ==="
ls -d /home/adam/hf-paperb/hub/models--allenai--Olmo-3-* 2>/dev/null || echo "NO_OLMO_CACHE"
du -sh /home/adam/hf-paperb/hub/models--allenai--Olmo-3-* 2>/dev/null || true
echo "=== existing s10 runs ==="
ls -la runs/s10 2>/dev/null || echo "NO_S10_RUNS"
echo "=== doctor ==="
uv run afterlife doctor || true
