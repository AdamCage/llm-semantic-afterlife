#!/usr/bin/env bash
# Round-robin the eight S12 continuations, 48 new steps per slice.
# One GPU process. Resume the same run_id. Do not start a fresh id
# for a cell that already has a run.
set -u
ROOT=/mnt/c/projects/llm-semantic-afterlife
cd "$ROOT"
sed -i 's/\r$//' "$ROOT/scripts/s12_run_one.sh" || true
LOGDIR=/home/adam/s12
mkdir -p "$LOGDIR"
MASTER="$LOGDIR/rotate.log"
MAP="$LOGDIR/runs.map"
SLICE=48
touch "$MAP"

say() { echo "$* $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$MASTER"; }

CELLS=(
  configs/stages/stage12_horizon/mb-physics-s1.yaml
  configs/stages/stage12_horizon/mb-physics-s2.yaml
  configs/stages/stage12_horizon/mb-love-s1.yaml
  configs/stages/stage12_horizon/mb-love-s2.yaml
  configs/stages/stage12_horizon/qi-physics-s1.yaml
  configs/stages/stage12_horizon/qi-physics-s2.yaml
  configs/stages/stage12_horizon/qi-love-s1.yaml
  configs/stages/stage12_horizon/qi-love-s2.yaml
)

lookup() {
  local tag="$1"
  awk -v t="$tag" '$1==t {print $2}' "$MAP" | tail -n 1
}

remember() {
  local tag="$1" run="$2"
  grep -q "^${tag} ${run}$" "$MAP" 2>/dev/null || echo "$tag $run" >> "$MAP"
}

status_of() {
  local run="$1"
  local f="runs/s12/${run}/STATUS"
  if [ -f "$f" ]; then tr -d '\r\n' < "$f"; else echo NONE; fi
}

steps_of() {
  local run="$1"
  local f="runs/s12/${run}/events.jsonl"
  if [ ! -f "$f" ]; then echo 0; return; fi
  grep -c '"event": "generation.step.completed"' "$f" || true
}

say "ROTATE START slice=$SLICE"
while true; do
  progress=0
  for cfg in "${CELLS[@]}"; do
    tag="$(basename "$cfg" .yaml)"
    run="$(lookup "$tag")"
    if [ -n "$run" ]; then
      st="$(status_of "$run")"
      if [ "$st" = "COMPLETED" ]; then
        continue
      fi
    fi
    progress=1
    before=0
    if [ -n "$run" ]; then before="$(steps_of "$run")"; fi
    say "SLICE $tag run=${run:-new} steps_before=$before"
    if [ -n "$run" ]; then
      bash "$ROOT/scripts/s12_run_one.sh" "$cfg" --resume-run "$run" &
    else
      bash "$ROOT/scripts/s12_run_one.sh" "$cfg" &
    fi
    pid=$!
    echo "$pid" > "$LOGDIR/current.pid"
    # Wait until SLICE new steps, or the process exits.
    for _ in $(seq 1 240); do
      if ! kill -0 "$pid" 2>/dev/null; then
        wait "$pid" || true
        break
      fi
      if [ -z "$run" ]; then
        found="$(ls -1dt runs/s12/s12-paperb-l2-${tag}-* 2>/dev/null | head -n 1 || true)"
        if [ -n "$found" ]; then
          run="$(basename "$found")"
          remember "$tag" "$run"
        fi
      fi
      if [ -n "$run" ]; then
        now="$(steps_of "$run")"
        if [ "$((now - before))" -ge "$SLICE" ]; then
          say "SLICE CAP $tag steps=$now"
          kill -TERM "$pid" 2>/dev/null || true
          sleep 2
          kill -KILL "$pid" 2>/dev/null || true
          wait "$pid" 2>/dev/null || true
          break
        fi
      fi
      sleep 15
    done
    if kill -0 "$pid" 2>/dev/null; then
      say "SLICE TIMEOUT $tag"
      kill -TERM "$pid" 2>/dev/null || true
      sleep 2
      kill -KILL "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
    fi
    nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$MASTER" || true
  done
  if [ "$progress" -eq 0 ]; then
    say "S12 COHORT DONE"
    exit 0
  fi
done
