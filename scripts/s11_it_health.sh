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
ps -ef | grep -E 's11_resume_it|afterlife generate|s11_watch' | grep -v grep || echo none
echo "==== TAIL LOG ===="
tail -n 4 /home/adam/s11/matrix.log
python3 - <<'PY'
import json
from collections import Counter
from pathlib import Path
run = Path("runs/s11/s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427")
print("STATUS", (run/"STATUS").read_text().strip())
events = [json.loads(l) for l in (run/"events.jsonl").read_text().splitlines() if l.strip()]
steps = [e for e in events if e.get("event")=="generation.step.completed"]
failed = {e.get("trajectory_id") for e in events if e.get("event")=="generation.trajectory.failed"}
finished = {e.get("trajectory_id") for e in events if e.get("event")=="generation.trajectory.finished"}
errors = [e for e in events if str(e.get("level","")).upper() in {"ERROR","CRITICAL"} and e.get("event")!="generation.trajectory.failed"]
last = steps[-1]
providers = Counter(e.get("served_provider") for e in steps)
reasons = Counter(e.get("finish_reason") for e in steps)
think = Counter(e.get("reasoning_tokens") for e in steps)
rt = Counter(e.get("tokenizer_roundtrip_ok") for e in steps)
print(f"steps={len(steps)} finished={len(finished)} failed={len(failed)} other_errors={len(errors)}")
print("provider", dict(providers), "reason", dict(reasons), "think", dict(think), "roundtrip", dict(rt))
print("last", last.get("ts"), last.get("trajectory_id"), "step", last.get("step"), "tok", last.get("generated_tokens"), "lat", last.get("latency_s"))
open_ids = []
seen = {}
for e in events:
    tid = e.get("trajectory_id")
    if not tid:
        continue
    if e.get("event")=="generation.step.completed":
        seen[tid] = e.get("step")
for tid, step in seen.items():
    if tid not in finished and tid not in failed:
        open_ids.append((tid, step))
print("open", open_ids)
PY
