#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
cd /mnt/c/projects/llm-semantic-afterlife
uv run python scripts/s12_write_continuation.py
uv run python scripts/s12_write_yamls.py
uv run afterlife plan --config configs/stages/stage12_horizon/mb-physics-s1.yaml
uv run afterlife estimate --config configs/stages/stage12_horizon/mb-physics-s1.yaml
