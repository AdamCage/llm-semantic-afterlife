#!/usr/bin/env bash
set -u
cd /mnt/c/projects/llm-semantic-afterlife
python3 - <<'PY'
import json
from pathlib import Path
p = Path("runs/s11/s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427/events.jsonl")
last = None
resumed = None
for line in p.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    ev = json.loads(line)
    if ev.get("event") == "generation.trajectory.resumed" and "recipe__s4" in str(ev.get("trajectory_id")):
        resumed = ev
    if ev.get("event") == "generation.step.completed":
        last = ev
print("resumed", None if not resumed else (resumed.get("ts"), resumed.get("steps_replayed"), resumed.get("generated_tokens")))
print("last", last.get("ts"), last.get("trajectory_id"), "step", last.get("step"), "tok", last.get("generated_tokens"), "lat", last.get("latency_s"), "provider", last.get("served_provider"), "think", last.get("reasoning_tokens"))
PY
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader
