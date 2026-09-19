#!/usr/bin/env bash
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
cd /mnt/c/projects/llm-semantic-afterlife
uv run python scripts/s10_print_dpo_gt.py
echo "==== HOSTED ===="
wc -l /mnt/c/projects/llm-semantic-afterlife/runs/s10/s10-embed-paperb-olmo-embed-qwen-hosted-20260918T181024Z-56bec26e/events.jsonl
pgrep -af 'afterlife embed --run s10-paperb-olmo-base-nf4' || echo hosted_gone
echo "==== RETRY LOG ===="
tail -n 15 /home/adam/s10/retry_rlvr_persist.nohup
