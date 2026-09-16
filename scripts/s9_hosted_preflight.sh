#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== keys ===="
uv run python scripts/s9_check_hosted_keys.py
echo "==== tokens ===="
uv run python scripts/s9_estimate_hosted_qwen_embed.py
echo "==== config ===="
uv run python -c "from pathlib import Path; from semantic_afterlife.config import load_experiment_config; e,_,_=load_experiment_config(Path('configs/stages/stage9_qwen/embed_qwen.yaml')); print([(x.slug,x.api,x.model_id,e.budget_usd) for x in e.embeddings])"
