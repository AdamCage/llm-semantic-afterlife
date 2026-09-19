"""Token + ceiling estimate for hosted S10 Qwen3-Embedding-8B (ADR-0028)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("runs/s10")
RUNS = [
    "s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3",
    "s10-paperb-olmo-sft-nf4-20260917T142201Z-2b7b5b6e",
    "s10-paperb-olmo-dpo-nf4-20260918T000412Z-64ad9f9f",
    "s10-paperb-olmo-rlvr-nf4-20260918T022536Z-30b5b3fc",
    "s10-paperb-olmo-base-int8-20260918T050048Z-2b2cdfd8",
    "s10-paperb-olmo-rlvr-int8-20260918T142301Z-7125ccca",
]
# Conservative ceiling if the provider starts charging (S0/S5/S9 recorded $0).
USD_PER_M = 0.15
CAP_USD = 5.0


def main() -> None:
    rows = []
    for run_id in RUNS:
        path = ROOT / run_id / "data" / "chunks.parquet"
        if not path.is_file():
            print(f"{run_id}  MISSING chunks.parquet")
            continue
        chunks = pd.read_parquet(path)
        n = int(len(chunks))
        tokens = int(chunks["n_tokens"].sum())
        rows.append({"run_id": run_id, "n_chunks": n, "n_tokens": tokens})
        print(f"{run_id}  chunks={n}  tokens={tokens}")
    if not rows:
        raise SystemExit("no chunks.parquet found")
    frame = pd.DataFrame(rows)
    total_chunks = int(frame["n_chunks"].sum())
    total_tokens = int(frame["n_tokens"].sum())
    ceiling = USD_PER_M / 1e6 * total_tokens
    print(f"TOTAL chunks={total_chunks} tokens={total_tokens}")
    print("historical RouterAI embed unit cost: $0.00 (S0/S5/S9)")
    print(f"conservative ceiling @{USD_PER_M}/M tokens: ${ceiling:.4f}")
    print(f"ADR-0028 cap: ${CAP_USD:.2f}")
    if ceiling > CAP_USD:
        print("OVER_CAP")
        raise SystemExit(3)


if __name__ == "__main__":
    main()
