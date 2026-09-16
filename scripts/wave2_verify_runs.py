"""Verify Wave 2 official run_ids exist and STATUS matches SMOKE.md."""

from __future__ import annotations

from pathlib import Path

ROOT = Path("runs")
IDS = [
    "s8-paperb-smoke-qwen3-8b-base-20260910T200925Z-28827fb7",
    "s8-paperb-smoke-qwen3-8b-instruct-20260910T202114Z-c1a44453",
    "s8-paperb-smoke-olmo3-7b-base-20260910T203216Z-a08dbea4",
    "s8-paperb-smoke-olmo3-7b-sft-20260910T204127Z-e446abc8",
    "s8-paperb-smoke-olmo3-7b-dpo-20260910T205044Z-1d237e73",
    "s8-paperb-smoke-olmo3-7b-rlvr-20260910T205941Z-2fc2def8",
    "s8-paperb-smoke-ministral-8b-base-20260910T215308Z-42f29e6e",
    "s8-paperb-smoke-ministral-8b-instruct-20260910T220441Z-1c1fd482",
    "s8-paperb-smoke-gemma4-12b-base-20260910T210919Z-2cf3ff6d",
    "s8-paperb-smoke-gemma4-12b-it-20260910T213805Z-58e90177",
    "s8-paperb-micro-qwen3-8b-instruct-20260910T221623Z-61c9ad74",
    "s8-paperb-micro-olmo3-7b-base-20260910T232755Z-e3cc4b7f",
    "s8-paperb-micro-ministral-8b-instruct-20260910T222222Z-e528749b",
    "s8-paperb-micro-gemma4-12b-it-20260910T233125Z-f89a95a4",
]


def main() -> None:
    parquet = Path("artifacts/stage-8/smoke/smoke_microbench.data.parquet")
    print("parquet", parquet.exists(), parquet.stat().st_size if parquet.exists() else 0)
    for run_id in IDS:
        matches = list(ROOT.glob(f"*/{run_id}")) + list(ROOT.glob(run_id))
        if not matches:
            print(f"MISSING {run_id}")
            continue
        status_path = matches[0] / "STATUS"
        status = status_path.read_text(encoding="utf-8").strip() if status_path.exists() else "NO_STATUS"
        print(f"{status:10} {matches[0]}")


if __name__ == "__main__":
    main()
