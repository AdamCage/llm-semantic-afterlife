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
pgrep -af 's10_analysis_resume|s10_analysis_queue|afterlife embed|afterlife analyze' || true
echo "==== ANALYSIS TAIL ===="
tail -n 20 /home/adam/s10/analysis.log
echo "==== HOSTED MASTER ===="
tail -n 20 /home/adam/s10/embed_qwen_hosted.log 2>/dev/null || echo none
echo "==== EMBED/PERSIST ===="
for d in runs/s10/s10-embed-*/ runs/s10/s10-persistence-*/; do
  [ -d "$d" ] || continue
  st=NOSTATUS
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  sup=""
  [ -f "${d}SUPERSEDED" ] && sup=" SUPERSEDED"
  echo "$st$sup  $(basename "$d")"
done
echo "==== GT ===="
uv run python scripts/s10_print_gt.py
