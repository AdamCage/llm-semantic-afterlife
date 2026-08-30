"""Per-model operational summary of a generation run.

Reports the protocol diagnostics that Stage 0 established as load-bearing and
that every later stage report has to include: realised block fill, stop-event
rate, tokenizer round-trip integrity, reasoning leaks, retry pressure, served
provider, and the local-versus-API prompt-token delta.

Also estimates the wall-clock cost of a full-size trajectory from the observed
per-step latency, because under protocol P1 that is what decides whether a stage
is feasible, not the price per token.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

import pandas as pd

from semantic_afterlife.config import get_settings


def load_events(run_dir: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with run_dir.joinpath("events.jsonl").open("rb") as handle:
        for raw in handle:
            raw = raw.strip()
            if raw:
                try:
                    events.append(json.loads(raw))
                except json.JSONDecodeError:
                    continue
    return events


def summarise(run_dir: Path, *, target_steps: int) -> pd.DataFrame:
    events = load_events(run_dir)
    steps = [e for e in events if e["event"] == "generation.step.completed"]
    retries = [e for e in events if e["event"] == "provider.retry"]
    leaks = [e for e in events if e["event"] == "generation.step.reasoning_leak"]
    finished = {
        e["trajectory_id"]: e for e in events if e["event"] == "generation.trajectory.finished"
    }

    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in steps:
        grouped.setdefault(str(event["trajectory_id"]), []).append(event)

    rows: list[dict[str, Any]] = []
    for trajectory_id, block in grouped.items():
        fresh = [e for e in block if not e.get("from_cache")]
        latencies = [e["latency_s"] for e in fresh] or [0.0]
        fills = [e["block_fill_ratio"] for e in block]
        outcome = finished.get(trajectory_id, {})
        # Wall-clock forecast uses the median of *fresh* calls: cache hits are
        # free and instant, so including them would flatter the estimate.
        median_latency = statistics.median(latencies)
        rows.append(
            {
                "model": trajectory_id.split("__")[0],
                "status": outcome.get("status", "?"),
                "steps": len(block),
                "fresh_calls": len(fresh),
                "generated_tokens": max((e["generated_tokens"] for e in block), default=0),
                "block_fill_mean": round(statistics.mean(fills), 3),
                "block_fill_min": round(min(fills), 3),
                "stop_rate": round(
                    sum(1 for e in block if e["finish_reason"] != "length") / len(block), 3
                ),
                "median_latency_s": round(median_latency, 2),
                "max_latency_s": round(max(latencies), 2),
                "prompt_token_delta": int(
                    statistics.median(e["prompt_token_delta"] for e in block)
                ),
                "roundtrip_failures": sum(1 for e in block if not e["tokenizer_roundtrip_ok"]),
                "reasoning_tokens": sum(e.get("reasoning_tokens", 0) for e in block),
                "served_provider": ",".join(
                    sorted({str(e["served_provider"]) for e in block if e.get("served_provider")})
                ),
                "cost_usd": round(sum(e["cost_usd"] for e in block), 6),
                "forecast_hours_full_trajectory": round(median_latency * target_steps / 3600.0, 2),
            }
        )
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame.attrs["retries"] = len(retries)
        frame.attrs["reasoning_leaks"] = len(leaks)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id", nargs="+", help="one or more run ids to summarise")
    parser.add_argument(
        "--target-steps",
        type=int,
        default=256,
        help="steps in a full-size Stage 1 trajectory (W=8192, T=262144, B=1024)",
    )
    args = parser.parse_args()

    settings = get_settings()
    pd.set_option("display.width", 220)
    frames = []
    for run_id in args.run_id:
        run_dir = settings.paths.find_run(run_id).root
        frame = summarise(run_dir, target_steps=args.target_steps)
        if frame.empty:
            print(f"{run_id}: no completed steps")
            continue
        frame.insert(0, "run", run_id.split("-2026")[0])
        print(
            f"\n{run_id}  (retries {frame.attrs['retries']}, "
            f"reasoning leaks {frame.attrs['reasoning_leaks']})"
        )
        frames.append(frame)

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        print()
        print(combined.to_string(index=False))
        print(
            "\nforecast_hours_full_trajectory = median fresh-call latency x "
            f"{args.target_steps} steps. Multiply by the trajectory count and divide by "
            "concurrency for a stage estimate; throttling makes that optimistic."
        )


if __name__ == "__main__":
    main()
