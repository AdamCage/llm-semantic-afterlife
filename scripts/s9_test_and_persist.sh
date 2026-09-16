#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
cd /mnt/c/projects/llm-semantic-afterlife
uv run pytest tests/test_wave1_paper_b_harness.py -q --tb=short
chmod +x /mnt/c/projects/llm-semantic-afterlife/scripts/s9_persistence_all.sh
nohup /mnt/c/projects/llm-semantic-afterlife/scripts/s9_persistence_all.sh \
  >/home/adam/s9/persistence.nohup 2>&1 &
echo "PERSIST_PID=$!"
sleep 2
tail -n 15 /home/adam/s9/persistence.log || true
