#!/usr/bin/env bash
set -euo pipefail
sed -i 's/\r$//' /mnt/c/projects/llm-semantic-afterlife/scripts/s10_retry_rlvr_persist.sh
chmod +x /mnt/c/projects/llm-semantic-afterlife/scripts/s10_retry_rlvr_persist.sh
nohup /mnt/c/projects/llm-semantic-afterlife/scripts/s10_retry_rlvr_persist.sh \
  >/home/adam/s10/retry_rlvr_persist.nohup 2>&1 &
echo "RETRY_PID=$!"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
cd /mnt/c/projects/llm-semantic-afterlife
uv run python scripts/s10_print_dpo_gt.py
