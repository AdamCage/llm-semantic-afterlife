#!/usr/bin/env bash
# After every S12 cell is COMPLETED or a terminal empty-completion death:
# degeneracy once, then stop. Does not start S13, does not run G_t.
set -u
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
export HF_HOME=/home/adam/hf-paperb
export TOKENIZERS_PARALLELISM=false
export AFTERLIFE_BUDGET_USD_TOTAL=200
ROOT=/mnt/c/projects/llm-semantic-afterlife
cd "$ROOT"
LOGDIR=/home/adam/s12
LOG="$LOGDIR/after_cohort.log"
mkdir -p "$LOGDIR"

exec 8>"$LOGDIR/after_cohort.lock"
if ! flock -n 8; then
  echo "AFTER_COHORT_LOCKED $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG"
  exit 0
fi

if [ -f "$LOGDIR/DEGENERACY_DONE" ] || [ -f "$LOGDIR/DEGENERACY_FAILED" ]; then
  exit 0
fi

echo "AFTER_COHORT_BEGIN $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG"
fail=0
while read -r tag run; do
  [ -n "${run:-}" ] || continue
  echo "DEGENERACY $tag $run $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG"
  if ! uv run afterlife analyze degeneracy --run "$run" >> "$LOG" 2>&1; then
    echo "DEGENERACY_FAIL $tag $run" | tee -a "$LOG"
    fail=1
  fi
done < "$LOGDIR/runs.map"

if [ "$fail" -eq 0 ]; then
  date -u +%Y-%m-%dT%H:%M:%SZ > "$LOGDIR/DEGENERACY_DONE"
  echo "WATCHDOG_DEGENERACY_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG"
else
  date -u +%Y-%m-%dT%H:%M:%SZ > "$LOGDIR/DEGENERACY_FAILED"
  echo "WATCHDOG_DEGENERACY_FAILED $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG"
fi

cat > "$LOGDIR/AFTER_GENERATE.txt" <<'EOF'
Generation settled. Degeneracy was attempted (see DEGENERACY_DONE or DEGENERACY_FAILED).
Next, still on stage-12, not S13:
- tau_escape table only. Clock origin is the L0 lock at 0.75W, plus the L0 49152 tokens.
  A cell still locked at the stop is censored at T_min. Do not call the lock absorbing.
- Do not publish a last-band G_t as the S12 headline.
- Score PLAN predictions. afterlife review --stage s12 until exit 0.
- Do not merge. Do not retune. Do not start a second generate.
EOF
