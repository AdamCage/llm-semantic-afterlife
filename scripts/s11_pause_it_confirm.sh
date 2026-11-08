#!/usr/bin/env bash
set -u
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== GPU ===="
nvidia-smi --query-compute-apps=pid --format=csv,noheader
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
echo "==== PROCS ===="
ps -ef | grep -E 'afterlife generate|s11_resume|s11_watch' | grep -v grep || echo none
python3 - <<'PY'
import json
from pathlib import Path
run = Path("runs/s11/s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427")
print("STATUS", (run/"STATUS").read_text().strip())
events = [json.loads(l) for l in (run/"events.jsonl").read_text().splitlines() if l.strip()]
steps = [e for e in events if e.get("event")=="generation.step.completed"]
failed = {e.get("trajectory_id") for e in events if e.get("event")=="generation.trajectory.failed"}
finished = {e.get("trajectory_id") for e in events if e.get("event")=="generation.trajectory.finished"}
last = steps[-1]
print(f"steps={len(steps)} finished={len(finished)} failed={len(failed)}")
print("last", last.get("trajectory_id"), "step", last.get("step"), "tok", last.get("generated_tokens"), "ts", last.get("ts"))
PY
