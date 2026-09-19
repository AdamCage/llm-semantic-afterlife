#!/usr/bin/env bash
set -u
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
echo "=== TIME ==="
date -u +%Y-%m-%dT%H:%M:%SZ
echo "=== GIT ==="
git -C /mnt/c/projects/llm-semantic-afterlife branch --show-current
git -C /mnt/c/projects/llm-semantic-afterlife rev-parse --short HEAD
echo "=== GPU ==="
nvidia-smi --query-gpu=name,memory.used,memory.free --format=csv
echo "=== COMPUTE ==="
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv || true
echo "=== PS ==="
pgrep -af 's10_run_|afterlife generate|afterlife embed' || echo 'no generate'
echo "=== LOGS ==="
ls -lt /home/adam/s10 2>/dev/null | head
echo "=== MATRIX ==="
tail -n 20 /home/adam/s10/matrix.log 2>/dev/null || echo 'no matrix.log'
echo "=== RUNS ==="
ls -la /mnt/c/projects/llm-semantic-afterlife/runs/s10 2>/dev/null || echo 'NO_S10_RUNS'
