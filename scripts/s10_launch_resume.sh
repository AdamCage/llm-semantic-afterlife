#!/usr/bin/env bash
set -euo pipefail
mkdir -p /home/adam/s10
sed -i 's/\r$//' /mnt/c/projects/llm-semantic-afterlife/scripts/s10_kill_stuck_bge.sh \
  /mnt/c/projects/llm-semantic-afterlife/scripts/s10_analysis_resume.sh \
  /mnt/c/projects/llm-semantic-afterlife/scripts/s10_discover_embeds.py
chmod +x /mnt/c/projects/llm-semantic-afterlife/scripts/s10_kill_stuck_bge.sh \
  /mnt/c/projects/llm-semantic-afterlife/scripts/s10_analysis_resume.sh
/mnt/c/projects/llm-semantic-afterlife/scripts/s10_kill_stuck_bge.sh
nohup /mnt/c/projects/llm-semantic-afterlife/scripts/s10_analysis_resume.sh \
  >/home/adam/s10/analysis_resume.nohup 2>&1 &
echo "RESUME_PID=$!"
echo $! >/home/adam/s10/analysis.pid
sleep 2
tail -n 20 /home/adam/s10/analysis.log || true
