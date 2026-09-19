#!/usr/bin/env bash
set -u
echo "==== TIME ===="
date -u +%Y-%m-%dT%H:%M:%SZ
echo "==== GIT ===="
git -C /mnt/c/projects/llm-semantic-afterlife branch --show-current 2>/dev/null || true
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader 2>/dev/null || true
echo "==== COMPUTE ===="
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv 2>/dev/null || true
echo "==== PS ===="
pgrep -af 's10_run_|afterlife generate|afterlife embed' || true
echo "==== DISK ===="
df -h / /mnt/c | awk 'NR==1||/\/$|\/mnt\/c/'
echo "==== MASTER ===="
tail -n 20 /home/adam/s10/matrix.log 2>/dev/null || echo 'no matrix.log'
echo "==== SUPERVISOR ===="
tail -n 20 /home/adam/s10/supervisor.log 2>/dev/null || echo 'no supervisor.log'
echo "==== GENERATE LOGS ===="
ls -lt /home/adam/s10/*.log 2>/dev/null | head
echo "==== LAST GENERATE TAIL ===="
latest=$(ls -t /home/adam/s10/pb-olmo3-7b-*.log 2>/dev/null | head -n 1)
if [ -n "${latest:-}" ]; then
  echo "file=$latest"
  tail -n 30 "$latest"
fi
echo "==== RUNS S10 ===="
if [ -d /mnt/c/projects/llm-semantic-afterlife/runs/s10 ]; then
  for d in /mnt/c/projects/llm-semantic-afterlife/runs/s10/*/; do
    name=$(basename "$d")
    st="NOSTATUS"
    [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
    njson=0
    [ -d "${d}requests" ] && njson=$(find "${d}requests" -name '*.jsonl' 2>/dev/null | wc -l)
    echo "$st  $name  request_files=$njson"
  done
else
  echo "NO_S10_RUNS"
fi
