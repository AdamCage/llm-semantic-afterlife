#!/usr/bin/env bash
# Round-robin eight S12 continuations. Each slice adds 48 steps to the
# trajectory that currently has the fewest, so a cell that ran ahead
# waits. One GPU process. Resume the mapped run_id only.
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
  awk -v t="$1" '$1==t {print $2}' "$MAP" | tail -n 1
}

remember() {
  grep -q "^${1} ${2}$" "$MAP" 2>/dev/null || echo "$1 $2" >> "$MAP"
}

status_of() {
  local f="runs/s12/${1}/STATUS"
  if [ -f "$f" ]; then tr -d '\r\n' < "$f"; else echo NONE; fi
}

steps_of() {
  local f="runs/s12/${1}/events.jsonl"
  if [ ! -f "$f" ]; then echo 0; return; fi
  grep -o 'generation.step.completed' "$f" | wc -l
}

stop_group() {
  local pid="$1"
  kill -TERM -- "-${pid}" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
  sleep 3
  kill -KILL -- "-${pid}" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
  if pgrep -f 'afterlife generate --config configs/stages/stage12_horizon' >/dev/null 2>&1; then
    pkill -TERM -f 'afterlife generate --config configs/stages/stage12_horizon' 2>/dev/null || true
    sleep 2
    pkill -KILL -f 'afterlife generate --config configs/stages/stage12_horizon' 2>/dev/null || true
  fi
}

say "ROTATE RESTART slice=$SLICE fewest-first"
while true; do
  best_cfg=""
  best_tag=""
  best_run=""
  best_steps=999999999
  pending=0
  for cfg in "${CELLS[@]}"; do
    tag="$(basename "$cfg" .yaml)"
    run="$(lookup "$tag")"
    if [ -n "$run" ] && [ "$(status_of "$run")" = "COMPLETED" ]; then
      continue
    fi
    pending=1
    steps=0
    if [ -n "$run" ]; then steps="$(steps_of "$run")"; fi
    if [ "$steps" -lt "$best_steps" ]; then
      best_steps="$steps"
      best_cfg="$cfg"
      best_tag="$tag"
      best_run="$run"
    fi
  done
  if [ "$pending" -eq 0 ]; then
    say "S12 COHORT DONE"
    exit 0
  fi
  say "SLICE $best_tag run=${best_run:-new} steps_before=$best_steps"
  if [ -n "$best_run" ]; then
    setsid bash "$ROOT/scripts/s12_run_one.sh" "$best_cfg" --resume-run "$best_run" &
  else
    setsid bash "$ROOT/scripts/s12_run_one.sh" "$best_cfg" &
  fi
  pid=$!
  echo "$pid" > "$LOGDIR/current.pid"
  before="$best_steps"
  for _ in $(seq 1 240); do
    if ! kill -0 "$pid" 2>/dev/null; then
      wait "$pid" || true
      break
    fi
    if [ -z "$best_run" ]; then
      found="$(ls -1dt runs/s12/s12-paperb-l2-${best_tag}-* 2>/dev/null | head -n 1 || true)"
      if [ -n "$found" ]; then
        best_run="$(basename "$found")"
        remember "$best_tag" "$best_run"
      fi
    fi
    if [ -n "$best_run" ]; then
      now="$(steps_of "$best_run")"
      if [ "$((now - before))" -ge "$SLICE" ]; then
        say "SLICE CAP $best_tag steps=$now"
        stop_group "$pid"
        break
      fi
    fi
    sleep 15
  done
  if kill -0 "$pid" 2>/dev/null; then
    say "SLICE TIMEOUT $best_tag"
    stop_group "$pid"
  fi
  nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | tee -a "$MASTER" || true
done
