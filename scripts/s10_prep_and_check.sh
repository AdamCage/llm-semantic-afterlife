#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export UV_LINK_MODE=copy
export HF_HOME=/home/adam/hf-paperb
export AFTERLIFE_BUDGET_USD_TOTAL=200
cd /mnt/c/projects/llm-semantic-afterlife

for f in scripts/s10_runs.sh scripts/s10_summarise_all.sh scripts/s10_degeneracy.sh \
  scripts/s10_analysis_queue.sh scripts/s10_launch_analysis.sh scripts/s10_hourly_watch.sh \
  scripts/s10_hosted_preflight.sh scripts/s10_embed_bge.sh scripts/s10_embed_qwen_hosted.sh \
  scripts/s10_estimate_hosted_qwen_embed.py scripts/s10_discover_embeds.py; do
  sed -i 's/\r$//' "$f"
  chmod +x "$f"
done

echo "==== GIT ===="
git branch --show-current
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
echo "==== PS ===="
pgrep -af 's10_|afterlife generate|afterlife embed' || true
echo "==== CHUNKS ===="
for d in runs/s10/s10-paperb-olmo-*/data/chunks.parquet; do
  echo "$d $(ls -lh "$d" 2>/dev/null | awk '{print $5}')"
done
echo "==== DOCTOR ===="
uv run afterlife doctor
echo "==== HOSTED PREFLIGHT ===="
/mnt/c/projects/llm-semantic-afterlife/scripts/s10_hosted_preflight.sh
