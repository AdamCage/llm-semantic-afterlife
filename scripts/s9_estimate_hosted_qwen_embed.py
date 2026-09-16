"""Token + ceiling estimate for hosted S9 Qwen3-Embedding-8B."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("runs/s9")
RUNS = [
    "s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6",
    "s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc",
    "s9-paperb-qwen-instruct-int8-20260912T180435Z-e9c7d498",
    "s9-paperb-qwen-base-int8-20260914T091655Z-11069a87",
]
# Conservative ceiling if the provider starts charging (S0/S5 recorded $0).
USD_PER_M = 0.15


def main() -> None:
    rows = []
    for run_id in RUNS:
        chunks = pd.read_parquet(ROOT / run_id / "data" / "chunks.parquet")
        n = int(len(chunks))
        tokens = int(chunks["n_tokens"].sum())
        rows.append({"run_id": run_id, "n_chunks": n, "n_tokens": tokens})
        print(f"{run_id}  chunks={n}  tokens={tokens}")
    frame = pd.DataFrame(rows)
    total_chunks = int(frame["n_chunks"].sum())
    total_tokens = int(frame["n_tokens"].sum())
    ceiling = USD_PER_M / 1e6 * total_tokens
    print(f"TOTAL chunks={total_chunks} tokens={total_tokens}")
    print(f"historical RouterAI embed unit cost: $0.00 (S0/S5)")
    print(f"conservative ceiling @{USD_PER_M}/M tokens: ${ceiling:.4f}")


if __name__ == "__main__":
    main()
