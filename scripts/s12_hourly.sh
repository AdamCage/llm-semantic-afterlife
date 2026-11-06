#!/usr/bin/env bash
# Fired every hour by Task Scheduler. Does not depend on Cursor.
# Keeps generation alive, and when the cohort has settled runs the research finish once.
set -u
ROOT=/mnt/c/projects/llm-semantic-afterlife
cd "$ROOT"
sed -i 's/\r$//' \
  "$ROOT/scripts/s12_keepalive.sh" \
  "$ROOT/scripts/s12_research.sh" || true
LOGDIR=/home/adam/s12
mkdir -p "$LOGDIR"
WINLOG="$ROOT/runs/_ledger/s12_hourly.log"
mkdir -p "$ROOT/runs/_ledger"
now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "HOURLY_TICK $now" | tee -a "$LOGDIR/hourly.log" >> "$WINLOG"

bash "$ROOT/scripts/s12_keepalive.sh" || true

if [ -f "$LOGDIR/DEGENERACY_DONE" ] && [ ! -f "$LOGDIR/RESEARCH_DONE" ] && [ ! -f "$LOGDIR/RESEARCH_FAILED" ]; then
  echo "HOURLY_RESEARCH_BEGIN $now" | tee -a "$LOGDIR/hourly.log" >> "$WINLOG"
  if bash "$ROOT/scripts/s12_research.sh" >> "$LOGDIR/research.log" 2>&1; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$LOGDIR/RESEARCH_DONE"
    echo "HOURLY_RESEARCH_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOGDIR/hourly.log" >> "$WINLOG"
  else
    echo "$now" >> "$LOGDIR/research_attempts.log"
    n="$(wc -l < "$LOGDIR/research_attempts.log" | tr -d ' ')"
    echo "HOURLY_RESEARCH_FAIL $now attempt=$n" | tee -a "$LOGDIR/hourly.log" >> "$WINLOG"
    if [ "${n:-0}" -ge 5 ]; then
      date -u +%Y-%m-%dT%H:%M:%SZ > "$LOGDIR/RESEARCH_FAILED"
    fi
  fi
fi

if [ -f "$LOGDIR/RESEARCH_DONE" ] && [ ! -f "$LOGDIR/GATE_PASS" ] && [ ! -f "$LOGDIR/GATE_FAILED" ]; then
  export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
  export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
  export UV_LINK_MODE=copy
  export AFTERLIFE_BUDGET_USD_TOTAL=200
  if uv run afterlife review --stage s12 >> "$LOGDIR/review.log" 2>&1; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$LOGDIR/GATE_PASS"
    echo "HOURLY_GATE_PASS $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOGDIR/hourly.log" >> "$WINLOG"
  else
    echo "$now" >> "$LOGDIR/gate_attempts.log"
    n="$(wc -l < "$LOGDIR/gate_attempts.log" | tr -d ' ')"
    echo "HOURLY_GATE_FAIL $now attempt=$n" | tee -a "$LOGDIR/hourly.log" >> "$WINLOG"
    if [ "${n:-0}" -ge 5 ]; then
      date -u +%Y-%m-%dT%H:%M:%SZ > "$LOGDIR/GATE_FAILED"
    fi
  fi
fi
