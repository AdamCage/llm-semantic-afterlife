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
ps -ef | grep -E 's12_rotate|afterlife generate' | grep -v grep || echo none
echo "==== ROTATE TAIL ===="
tail -n 12 /home/adam/s12/rotate.log 2>/dev/null || echo none
echo "==== MAP ===="
cat /home/adam/s12/runs.map 2>/dev/null || echo none
echo "==== RUNS ===="
python3 - <<'PY'
import json
from pathlib import Path
root = Path("runs/s12")
rows = []
if not root.is_dir():
    print("no runs/s12")
    raise SystemExit
for run in sorted(p for p in root.iterdir() if p.is_dir()):
    status = (run/"STATUS").read_text().strip() if (run/"STATUS").is_file() else "NOSTATUS"
    steps = 0
    last = None
    failed = 0
    events = run/"events.jsonl"
    if events.is_file():
        for line in events.read_text(encoding="utf-8", errors="replace").splitlines():
            if "generation.trajectory.failed" in line:
                failed += 1
            if "generation.step.completed" not in line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("event") == "generation.step.completed":
                steps += 1
                last = ev
    tok = last.get("generated_tokens") if last else 0
    reason = last.get("finish_reason") if last else ""
    think = last.get("reasoning_tokens") if last else ""
    prov = last.get("served_provider") if last else ""
    ts = last.get("ts") if last else ""
    print(f"{status} steps={steps} tok={tok} failed={failed} reason={reason} think={think} prov={prov} ts={ts} {run.name}")
PY
