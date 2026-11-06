#!/usr/bin/env bash
set -u
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
echo "==== COMPUTE ===="
nvidia-smi --query-compute-apps=pid --format=csv,noheader
echo "==== PROCS ===="
ps -ef | grep -E 's12_rotate|afterlife generate' | grep -v grep || echo none
echo "==== MAP ===="
cat /home/adam/s12/runs.map
echo "==== STATUS ===="
python3 - <<'PY'
import json
from pathlib import Path
root = Path("runs/s12")
for run in sorted(p for p in root.iterdir() if p.is_dir()):
    status = (run/"STATUS").read_text().strip() if (run/"STATUS").is_file() else "NOSTATUS"
    steps = list((run/"data"/"trajectories").glob("*.steps.jsonl")) if (run/"data"/"trajectories").is_dir() else []
    print(status, len(steps), run.name)
PY
