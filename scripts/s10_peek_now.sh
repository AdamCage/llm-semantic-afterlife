#!/usr/bin/env bash
set -u
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== GT ===="
uv run python scripts/s10_print_gt.py
echo "==== HOSTED ===="
wc -l runs/s10/s10-embed-paperb-olmo-embed-qwen-hosted-20260918T181024Z-56bec26e/events.jsonl
pgrep -af 'afterlife embed --run s10-paperb-olmo' || echo hosted_gone
echo "==== ANALYSIS ===="
tail -n 8 /home/adam/s10/analysis.log
echo "==== RETRY ===="
tail -n 8 /home/adam/s10/retry_rlvr_persist.nohup
