#!/usr/bin/env bash
set -u
echo "==== RLVR NF4 persist log tail ===="
tail -n 40 /home/adam/s10/persistence-s10-embed-paperb-olmo-embed-bge-20260918T172025Z-ed8ca4aa.log
echo "==== RLVR INT8 persist log tail ===="
tail -n 20 /home/adam/s10/persistence-s10-embed-paperb-olmo-embed-bge-20260918T180938Z-60d02d30.log
echo "==== DPO GT ===="
python3 - <<'PY'
import pandas as pd
p="runs/s10/s10-persistence-local-bge-m3-20260918T181744Z-8281a4d8/data/persistence_gt.parquet"
print(pd.read_parquet(p).to_string())
PY
echo "==== HOSTED RUN LOG ===="
tail -n 30 /mnt/c/projects/llm-semantic-afterlife/runs/s10/s10-embed-paperb-olmo-embed-qwen-hosted-20260918T181024Z-56bec26e/logs/run.log
