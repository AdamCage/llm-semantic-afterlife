#!/usr/bin/env bash
# Kill the hung RLVR INT8 BGE embed and the blocked analysis queue.
set -u
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) kill stuck BGE ==="
pgrep -af 's10_analysis_queue|afterlife embed --run s10-paperb-olmo-rlvr-int8|s10_embed_bge.sh' || true
pkill -f 's10_analysis_queue.sh' || true
pkill -f 'afterlife embed --run s10-paperb-olmo-rlvr-int8' || true
pkill -f 's10_embed_bge.sh' || true
sleep 2
pgrep -af 's10_analysis_queue|afterlife embed --run s10-paperb-olmo-rlvr-int8' && echo STILL_ALIVE || echo KILLED
HUNG=/mnt/c/projects/llm-semantic-afterlife/runs/s10/s10-embed-paperb-olmo-embed-bge-20260918T172254Z-60d02d30
if [ -d "$HUNG" ]; then
  echo 'ABORTED' >"$HUNG/STATUS"
  cat >"$HUNG/SUPERSEDED" <<'EOF'
Hung after SentenceTransformer weight load (~44 min, 14 chunks, GPU idle,
process wait_woken, only run.started). Not an E5 cell (RLVR INT8, 0
completers). Retry with timeout; keep this dir as the hang record.
EOF
  echo "superseded $HUNG"
fi
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
