#!/usr/bin/env bash
# Degeneracy on one S11 generate run. CPU. Before any G_t / geometry.
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
cd /mnt/c/projects/llm-semantic-afterlife

RUN="${1:?generate run_id required}"
LOGDIR=/home/adam/s11
mkdir -p "$LOGDIR"
LOG="$LOGDIR/degeneracy-${RUN}.log"

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) degeneracy $RUN ===" >>"$LOG"
set +e
uv run afterlife analyze degeneracy --run "$RUN" >>"$LOG" 2>&1
RC=$?
set -e
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) exit=$RC degeneracy $RUN ===" >>"$LOG"
exit "$RC"
