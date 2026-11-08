#!/usr/bin/env bash
set -u
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== TIME ===="
date -u +%Y-%m-%dT%H:%M:%SZ
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
echo "==== COMPUTE ===="
nvidia-smi --query-compute-apps=pid --format=csv,noheader
echo "==== PROCS ===="
ps -ef | grep -E 's11_resume|s11_watch|afterlife generate' | grep -v grep || echo none
echo "==== IT STATUS ===="
st=runs/s11/s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427/STATUS
if [ -f "$st" ]; then tr -d '\r\n' < "$st"; echo; else echo MISSING; fi
echo "==== LAST STEP ===="
python3 - <<'PY'
import json
from pathlib import Path
p = Path("runs/s11/s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427/events.jsonl")
last = None
for line in p.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    ev = json.loads(line)
    if ev.get("event") == "generation.step.completed":
        last = ev
if not last:
    print("no steps")
else:
    print(last.get("ts"), last.get("trajectory_id"), "step", last.get("step"), "lat", last.get("latency_s"))
PY
