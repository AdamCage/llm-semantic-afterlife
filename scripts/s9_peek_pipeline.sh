#!/usr/bin/env bash
set -u
echo "==== PS ===="
pgrep -af 's9_post_generate|afterlife embed|s9_launch' || true
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader || true
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv || true
echo "==== MASTER ===="
tail -n 30 /home/adam/s9/post_generate.log 2>/dev/null || echo 'no master'
echo "==== EMBED LOGS ===="
ls -lt /home/adam/s9/embed-bge-*.log 2>/dev/null | head
echo "==== EMBED TAIL ===="
latest=$(ls -t /home/adam/s9/embed-bge-*.log 2>/dev/null | head -n 1)
if [ -n "${latest:-}" ]; then
  echo "file=$latest"
  tail -n 50 "$latest"
else
  echo "no embed logs"
fi
echo "==== HOSTED QWEN ===="
tail -n 20 /home/adam/s9/embed_qwen_hosted.log 2>/dev/null || echo 'no hosted master'
latestq=$(ls -t /home/adam/s9/embed-qwen-*.log 2>/dev/null | head -n 1)
if [ -n "${latestq:-}" ]; then
  echo "file=$latestq"
  tail -n 30 "$latestq"
fi
echo "==== RUNS EMBED ===="
ls -1 /mnt/c/projects/llm-semantic-afterlife/runs/s9 | grep -E 'embed|degeneracy' || true
