"""Median decode tok/s from local.generate.completed, skipping zeros."""

from __future__ import annotations

import json
import statistics
from pathlib import Path

RUNS = [
    "runs/s8/s8-paperb-micro-qwen3-8b-instruct-20260910T221623Z-61c9ad74",
    "runs/s8/s8-paperb-micro-olmo3-7b-base-20260910T232755Z-e3cc4b7f",
    "runs/s8/s8-paperb-micro-ministral-8b-instruct-20260910T222222Z-e528749b",
    "runs/s8/s8-paperb-micro-gemma4-12b-it-20260910T233125Z-f89a95a4",
]


def main() -> None:
    for path in RUNS:
        run = Path(path)
        vals = []
        for raw in (run / "events.jsonl").read_text(encoding="utf-8").splitlines():
            obj = json.loads(raw)
            if obj.get("event") == "local.generate.completed":
                tok_s = obj.get("tok_s")
                n_out = obj.get("n_output_ids") or 0
                if tok_s and n_out:
                    vals.append(float(tok_s))
        print(run.name)
        if vals:
            print("  n", len(vals), "median", round(statistics.median(vals), 3), "min", round(min(vals), 3), "max", round(max(vals), 3), vals)
        else:
            print("  no nonzero decode events")


if __name__ == "__main__":
    main()
