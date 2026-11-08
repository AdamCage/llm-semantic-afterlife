#!/usr/bin/env bash
set -u
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== GPU ===="
nvidia-smi --query-compute-apps=pid --format=csv,noheader
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
echo "==== PROCS ===="
ps -ef | grep -E 's11_run|afterlife generate|s11_watch' | grep -v grep || echo none
python3 - <<'PY'
import json
from pathlib import Path
run = Path("runs/s11/s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981")
print("STATUS", (run/"STATUS").read_text().strip())
events = [json.loads(l) for l in (run/"events.jsonl").read_text().splitlines() if l.strip()]
steps = [e for e in events if e.get("event")=="generation.step.completed"]
fin = {e.get("trajectory_id") for e in events if e.get("event")=="generation.trajectory.finished"}
last = steps[-1]
print(f"steps={len(steps)} finished_traj={len(fin)}")
print("last", last.get("trajectory_id"), "step", last.get("step"), "ts", last.get("ts"))
PY
