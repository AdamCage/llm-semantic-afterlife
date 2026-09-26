#!/usr/bin/env bash
set -u
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== TIME ===="
date -u +%Y-%m-%dT%H:%M:%SZ
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
echo "==== PS ===="
pgrep -af 's11_run_matrix|s11_run_one|afterlife generate|afterlife embed|afterlife analyze' || true
echo "==== MASTER TAIL ===="
tail -n 30 /home/adam/s11/matrix.log 2>/dev/null || echo none
echo "==== GENERATE ===="
for d in runs/s11/s11-paperb-*/; do
  [ -d "$d" ] || continue
  st=NOSTATUS
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  echo "$st  $(basename "$d")"
done
echo "==== EMBED/PERSIST ===="
for d in runs/s11/s11-embed-*/ runs/s11/s11-persistence-*/ runs/s11/s11-degeneracy-*/; do
  [ -d "$d" ] || continue
  st=NOSTATUS
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  sup=""
  [ -f "${d}SUPERSEDED" ] && sup=" SUPERSEDED"
  echo "$st$sup  $(basename "$d")"
done
