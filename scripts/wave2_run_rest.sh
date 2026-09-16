#!/usr/bin/env bash
set -uo pipefail
export PATH="/home/adam/.local/bin:/usr/bin:/bin:$PATH"
ROOT=/mnt/c/projects/llm-semantic-afterlife
cd "$ROOT"
for slug in \
  pb-olmo3-7b-base \
  pb-olmo3-7b-sft \
  pb-olmo3-7b-dpo \
  pb-olmo3-7b-rlvr \
  pb-ministral-8b-base \
  pb-ministral-8b-instruct \
  pb-gemma4-12b-base \
  pb-gemma4-12b-it
do
  echo "BEGIN $slug"
  /usr/bin/df -h /
  bash "$ROOT/scripts/wave2_run_one.sh" "configs/stages/stage8_smoke/${slug}.yaml"
  echo "END $slug rc=$?"
done
echo ALL_SMOKE_DONE
