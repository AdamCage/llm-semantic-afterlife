#!/usr/bin/env bash
set -u
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export AFTERLIFE_BUDGET_USD_TOTAL=200
export MPLBACKEND=Agg
cd /mnt/c/projects/llm-semantic-afterlife

echo "==== leftover dirs ===="
rm -rf artifacts/stage-10/persistence-local-bge-m3 artifacts/stage-10/persistence-qwen3-embed-8b
ls -d artifacts/stage-10/persistence-* 2>/dev/null || echo "no leftover space-level persist dirs"

echo "==== re-assemble (refresh INDEX) ===="
uv run python scripts/s10_assemble.py >/tmp/s10_assemble_gate.log
tail -n 20 /tmp/s10_assemble_gate.log

echo "==== leftover after assemble ===="
ls -d artifacts/stage-10/persistence-local-bge-m3 artifacts/stage-10/persistence-qwen3-embed-8b 2>/dev/null || echo "gone"

echo "==== bundle scan ===="
uv run python scripts/s10_check_bundles.py

echo "==== review gate ===="
uv run afterlife review --stage s10
echo "gate_exit=$?"
