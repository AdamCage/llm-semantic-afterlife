#!/usr/bin/env bash
set -euo pipefail
cd /mnt/c/projects/llm-semantic-afterlife
echo "=== CWD ==="
pwd
echo "=== RUNS TOP ==="
ls -1 runs 2>/dev/null | head -40 || echo "no runs/"
echo "=== HOME S9 ==="
ls -1 /home/adam/s9 2>/dev/null | head -40 || true
echo "=== FIND GENERATE ==="
find /mnt/c/projects/llm-semantic-afterlife/runs /home/adam -maxdepth 3 -type d -name 's9-paperb-qwen-*' 2>/dev/null | head -40
echo "=== FIND PERSIST ==="
find /mnt/c/projects/llm-semantic-afterlife/runs /home/adam -maxdepth 3 -type d -name 's9-persistence-*' 2>/dev/null | head -40
echo "=== FIND EMBED ==="
find /mnt/c/projects/llm-semantic-afterlife/runs /home/adam -maxdepth 3 -type d -name 's9-embed-*' 2>/dev/null | head -40
echo "=== FIND DEGEN ==="
find /mnt/c/projects/llm-semantic-afterlife/runs /home/adam -maxdepth 3 -type d -name 's9-degeneracy-*' 2>/dev/null | head -40
