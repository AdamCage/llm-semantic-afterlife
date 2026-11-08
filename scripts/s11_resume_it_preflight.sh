#!/usr/bin/env bash
set -u
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
echo "==== COMPUTE ===="
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
echo "==== PROCS ===="
ps -ef | grep -E 's11_resume|s11_run|afterlife generate' | grep -v grep || echo none
RUN=runs/s11/s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427
echo -n "STATUS "
tr -d '\r\n' < "$RUN/STATUS"
echo
python3 - <<'PY'
import json
from pathlib import Path
run = Path("runs/s11/s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427")
events = [json.loads(l) for l in (run/"events.jsonl").read_text().splitlines() if l.strip()]
steps = [e for e in events if e.get("event")=="generation.step.completed"]
last = steps[-1]
print("last", last.get("trajectory_id"), "step", last.get("step"), "tok", last.get("generated_tokens"))
PY
