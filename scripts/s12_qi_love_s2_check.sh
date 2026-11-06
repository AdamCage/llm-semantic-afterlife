#!/usr/bin/env bash
set -u
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader
echo "==== PROC ===="
ps -ef | grep 'afterlife generate' | grep -v grep || echo none
echo "==== RESUME ===="
grep -E 'resuming |start pb-' /home/adam/s12/qi-love-s2.log | tail -n 4
python3 - <<'PY'
import json
from pathlib import Path
p = Path("runs/s12/s12-paperb-l2-qi-love-s2-20260926T140850Z-dd90cb82/events.jsonl")
n = 0
last = None
for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
    if "generation.step.completed" not in line:
        continue
    try:
        ev = json.loads(line)
    except json.JSONDecodeError:
        continue
    if ev.get("event") == "generation.step.completed":
        n += 1
        last = ev
print("steps", n, "last", None if not last else (last.get("step"), last.get("generated_tokens"), last.get("ts"), last.get("served_provider")))
PY
