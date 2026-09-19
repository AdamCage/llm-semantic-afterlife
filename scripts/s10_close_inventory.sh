#!/usr/bin/env bash
set -u
export PATH="/home/adam/.local/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export AFTERLIFE_BUDGET_USD_TOTAL=200
cd /mnt/c/projects/llm-semantic-afterlife
echo "==== TIME ===="
date -u +%Y-%m-%dT%H:%M:%SZ
echo "==== BRANCH ===="
git rev-parse --abbrev-ref HEAD
git rev-parse --short HEAD
echo "==== GPU ===="
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader || true
echo "==== GENERATE STATUS ===="
for d in \
  s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3 \
  s10-paperb-olmo-sft-nf4-20260917T142201Z-2b7b5b6e \
  s10-paperb-olmo-dpo-nf4-20260918T000412Z-64ad9f9f \
  s10-paperb-olmo-rlvr-nf4-20260918T022536Z-30b5b3fc \
  s10-paperb-olmo-base-int8-20260918T050048Z-2b2cdfd8 \
  s10-paperb-olmo-rlvr-int8-20260918T142301Z-7125ccca
do
  st=NOSTATUS
  [ -f "runs/s10/$d/STATUS" ] && st=$(tr -d '\r\n' < "runs/s10/$d/STATUS")
  echo "$st  $d"
done
echo "==== EMBED ===="
for d in runs/s10/s10-embed-*/; do
  [ -d "$d" ] || continue
  st=NOSTATUS
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  sup=""
  [ -f "${d}SUPERSEDED" ] && sup=" SUPERSEDED"
  echo "$st$sup  $(basename "$d")"
done
echo "==== PERSIST ===="
for d in runs/s10/s10-persistence-*/; do
  [ -d "$d" ] || continue
  st=NOSTATUS
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  sup=""
  [ -f "${d}SUPERSEDED" ] && sup=" SUPERSEDED"
  echo "$st$sup  $(basename "$d")"
done
echo "==== DEGEN ===="
for d in runs/s10/s10-degeneracy-*/; do
  [ -d "$d" ] || continue
  st=NOSTATUS
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  sup=""
  [ -f "${d}SUPERSEDED" ] && sup=" SUPERSEDED"
  echo "$st$sup  $(basename "$d")"
done
echo "==== INCOMPLETE NON-SUPERSEDED ===="
for d in runs/s10/*/; do
  [ -d "$d" ] || continue
  [ -f "${d}SUPERSEDED" ] && continue
  st=NOSTATUS
  [ -f "${d}STATUS" ] && st=$(tr -d '\r\n' < "${d}STATUS")
  [ "$st" = "COMPLETED" ] && continue
  echo "$st  $(basename "$d")"
done
echo "==== GT ===="
uv run python scripts/s10_print_gt.py
echo "==== LEDGER TAIL ===="
tail -n 15 runs/_ledger/spend.jsonl
