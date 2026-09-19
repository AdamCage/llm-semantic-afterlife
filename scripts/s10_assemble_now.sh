#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export AFTERLIFE_BUDGET_USD_TOTAL=200
export MPLBACKEND=Agg
cd /mnt/c/projects/llm-semantic-afterlife
uv run python scripts/s10_assemble.py
echo "==== LOCKS BY SEED ===="
uv run python -c "import pandas as pd; p='artifacts/stage-10/locks_by_seed/locks_by_seed.csv'; print(pd.read_csv(p).to_string()) if __import__('pathlib').Path(p).is_file() else print('missing')"
echo "==== LAST BAND ===="
uv run python -c "import pandas as pd; p='artifacts/stage-10/gt_last_band/gt_last_band.csv'; print(pd.read_csv(p).to_string()) if __import__('pathlib').Path(p).is_file() else print('missing')"
echo "==== EDGES ===="
uv run python -c "import pandas as pd; p='artifacts/stage-10/adjacent_edges/adjacent_edges.csv'; print(pd.read_csv(p).to_string()) if __import__('pathlib').Path(p).is_file() else print('missing')"
