#!/usr/bin/env bash
# Pause S12 and free the GPU. Keep runs.map and every run directory.
set -u
cd /mnt/c/projects/llm-semantic-afterlife
LOGDIR=/home/adam/s12
mkdir -p "$LOGDIR"
echo "PAUSE KEEP $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOGDIR/rotate.log"

if [ -f "$LOGDIR/rotate.pid" ]; then
  rpid="$(tr -d '\r\n' < "$LOGDIR/rotate.pid")"
  kill -TERM "$rpid" 2>/dev/null || true
fi
pkill -TERM -f 'scripts/s12_rotate.sh' 2>/dev/null || true
sleep 1

if [ -f "$LOGDIR/current.pid" ]; then
  gpid="$(tr -d '\r\n' < "$LOGDIR/current.pid")"
  kill -TERM -- "-${gpid}" 2>/dev/null || kill -TERM "$gpid" 2>/dev/null || true
fi
pkill -TERM -f 'afterlife generate --config configs/stages/stage12_horizon' 2>/dev/null || true
sleep 4
pkill -KILL -f 'scripts/s12_rotate.sh' 2>/dev/null || true
pkill -KILL -f 'afterlife generate --config configs/stages/stage12_horizon' 2>/dev/null || true
sleep 1

echo "==== PROCS ===="
ps -ef | grep -E 's12_rotate|afterlife generate' | grep -v grep || echo none
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
nvidia-smi --query-compute-apps=pid --format=csv,noheader
echo "==== MAP ===="
cat "$LOGDIR/runs.map"
python3 - <<'PY'
import json
from pathlib import Path
root = Path("runs/s12")
print("==== CHECKPOINTS ====")
for run in sorted(p for p in root.iterdir() if p.is_dir()):
    status = (run/"STATUS").read_text().strip() if (run/"STATUS").is_file() else "NOSTATUS"
    steps = 0
    last_tok = None
    events = run/"events.jsonl"
    if events.is_file():
        for line in events.read_text(encoding="utf-8", errors="replace").splitlines():
            if "generation.step.completed" not in line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("event") == "generation.step.completed":
                steps += 1
                last_tok = ev.get("generated_tokens")
    stepfiles = list((run/"data"/"trajectories").glob("*.steps.jsonl")) if (run/"data"/"trajectories").is_dir() else []
    print(f"{status} steps={steps} tok={last_tok} stepfiles={len(stepfiles)} {run.name}")
PY
cat > "$LOGDIR/PAUSED.txt" <<'EOF'
paused
resume with the same run_ids:
  bash /mnt/c/projects/llm-semantic-afterlife/scripts/s12_rotate.sh
It reads /home/adam/s12/runs.map and continues each cell with --resume-run.
Do not delete runs/s12 or runs.map. Do not start the eight YAMLs as new runs.
The hourly watchdog must stay stopped until resume, or it will start generate again.
EOF
echo "wrote $LOGDIR/PAUSED.txt"
