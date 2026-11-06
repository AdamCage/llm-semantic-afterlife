#!/usr/bin/env bash
# One S12 health check. Safe to run every few minutes from WSL or Task Scheduler.
# Restarts the rotator only when generate is actually down. Does not start a
# second GPU process. After the cohort is finished, runs degeneracy once.
set -u
ROOT=/mnt/c/projects/llm-semantic-afterlife
cd "$ROOT"
LOGDIR=/home/adam/s12
LOG="$LOGDIR/watchdog.log"
mkdir -p "$LOGDIR"
now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# fd 9 on the old lock was inherited by the rotator and held for the whole
# generate, so every later check exited LOCKED. Use a new lock and close it
# before starting any child.
{ exec 9>&-; } 2>/dev/null || true
exec 7>"$LOGDIR/watchdog.flock"
if ! flock -n 7; then
  echo "WATCHDOG_LOCKED $now" | tee -a "$LOG"
  exit 0
fi
drop_lock() { exec 7>&-; }

status_of() {
  local f="runs/s12/${1}/STATUS"
  if [ -f "$f" ]; then tr -d '\r\n' < "$f"; else echo NONE; fi
}

terminal_empty() {
  local run="$1" f
  [ "$(status_of "$run")" = "FAILED" ] || return 1
  f="runs/s12/${run}/events.jsonl"
  [ -f "$f" ] || return 1
  tail -c 500000 "$f" | grep -q 'consecutive empty completions'
}

cohort_settled() {
  local n=0 tag run
  [ -f "$LOGDIR/runs.map" ] || return 1
  while read -r tag run; do
    [ -n "${run:-}" ] || continue
    n=$((n + 1))
    if [ "$(status_of "$run")" = "COMPLETED" ]; then
      continue
    fi
    if terminal_empty "$run"; then
      continue
    fi
    return 1
  done < "$LOGDIR/runs.map"
  [ "$n" -eq 8 ]
}

kill_s12() {
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
  sleep 2
}

if cohort_settled; then
  echo "WATCHDOG_COHORT_DONE $now" | tee -a "$LOG"
  drop_lock
  bash "$ROOT/scripts/s12_after_cohort.sh" || true
  exit 0
fi

rot="$(pgrep -fc 'scripts/s12_rotate.sh' || true)"
gen="$(pgrep -fc 'afterlife generate --config configs/stages/stage12_horizon' || true)"

if [ "${gen:-0}" -gt 0 ]; then
  newest=0
  for f in runs/s12/s12-paperb-l2-*/data/trajectories/*.steps.jsonl; do
    [ -f "$f" ] || continue
    mt="$(stat -c %Y "$f" 2>/dev/null || echo 0)"
    if [ "$mt" -gt "$newest" ]; then newest="$mt"; fi
  done
  now_s="$(date +%s)"
  age=$((now_s - newest))
  max_et=0
  for p in $(pgrep -f 'afterlife generate --config configs/stages/stage12_horizon' || true); do
    et="$(ps -o etimes= -p "$p" 2>/dev/null | tr -d ' ' || true)"
    if [ -n "${et:-}" ] && [ "$et" -gt "$max_et" ]; then max_et="$et"; fi
  done
  # A healthy slice is ~30 min. The rotator kills a stuck slice at 60 min.
  # This is the backup if that rotator is wedged too.
  if [ "$max_et" -gt 4200 ] && [ "$age" -gt 2400 ]; then
    echo "WATCHDOG_HUNG $now etimes=$max_et step_age_s=$age" | tee -a "$LOG"
    kill_s12
    rot=0
    gen=0
  fi
fi

# setsid leaves generate running if the rotator dies. Nothing then
# enforces the 48-step slice, so stop that process and resume the cohort.
if [ "${gen:-0}" -gt 0 ] && [ "${rot:-0}" -eq 0 ]; then
  echo "WATCHDOG_ORPHAN $now" | tee -a "$LOG"
  if [ -f "$LOGDIR/current.pid" ]; then
    gpid="$(tr -d '\r\n' < "$LOGDIR/current.pid")"
    kill -TERM -- "-${gpid}" 2>/dev/null || kill -TERM "$gpid" 2>/dev/null || true
  fi
  pkill -TERM -f 'afterlife generate --config configs/stages/stage12_horizon' 2>/dev/null || true
  sleep 4
  pkill -KILL -f 'afterlife generate --config configs/stages/stage12_horizon' 2>/dev/null || true
  sleep 2
  gen=0
fi

if [ "${rot:-0}" -gt 0 ] || [ "${gen:-0}" -gt 0 ]; then
  echo "WATCHDOG_OK $now rotate=$rot generate=$gen" | tee -a "$LOG"
  exit 0
fi

free_kb="$(df -Pk /mnt/c | awk 'NR==2 {print $4}')"
if [ "${free_kb:-0}" -lt 20971520 ]; then
  echo "WATCHDOG_DISK $now free_kb=$free_kb" | tee -a "$LOG"
  exit 0
fi

ncomp="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -c '[0-9]' || true)"
if [ "${ncomp:-0}" -gt 0 ]; then
  echo "WATCHDOG_BUSY $now gpu_compute=$ncomp" | tee -a "$LOG"
  exit 0
fi

echo "WATCHDOG_RESTART $now" | tee -a "$LOG"
drop_lock
bash "$ROOT/scripts/s12_start_rotate.sh" >> "$LOG" 2>&1 || true
echo "WATCHDOG_RESTARTED $now" | tee -a "$LOG"
