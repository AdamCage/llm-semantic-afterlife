"""Token + ceiling estimate for hosted S11 Qwen3-Embedding-8B (ADR-0029)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("runs/s11")
USD_PER_M = 0.15
CAP_USD = 5.0


def main() -> None:
    rows = []
    if not ROOT.is_dir():
        raise SystemExit("no runs/s11")
    for run_dir in sorted(ROOT.glob("s11-paperb-*")):
        if (run_dir / "SUPERSEDED").is_file():
            continue
        path = run_dir / "data" / "chunks.parquet"
        if not path.is_file():
            print(f"{run_dir.name}  MISSING chunks.parquet")
            continue
        chunks = pd.read_parquet(path)
        n = int(len(chunks))
        tokens = int(chunks["n_tokens"].sum())
        rows.append({"run_id": run_dir.name, "n_chunks": n, "n_tokens": tokens})
        print(f"{run_dir.name}  chunks={n}  tokens={tokens}")
    if not rows:
        raise SystemExit("no chunks.parquet found")
    frame = pd.DataFrame(rows)
    total_chunks = int(frame["n_chunks"].sum())
    total_tokens = int(frame["n_tokens"].sum())
    ceiling = USD_PER_M / 1e6 * total_tokens
    print(f"TOTAL chunks={total_chunks} tokens={total_tokens}")
    print("historical RouterAI embed unit cost: $0.00 (S0/S5/S9/S10)")
    print(f"conservative ceiling @{USD_PER_M}/M tokens: ${ceiling:.4f}")
    print(f"ADR-0029 cap: ${CAP_USD:.2f}")
    if ceiling > CAP_USD:
        print("OVER_CAP")
        raise SystemExit(3)


if __name__ == "__main__":
    main()
