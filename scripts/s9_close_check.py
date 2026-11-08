#!/usr/bin/env python3
"""Unique generate outcomes + degeneracy rates + incomplete runs."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd

from semantic_afterlife.config import get_settings

GENERATE = {
    "instruct-nf4": "s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6",
    "base-nf4": "s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc",
    "instruct-int8": "s9-paperb-qwen-instruct-int8-20260912T180435Z-e9c7d498",
    "base-int8": "s9-paperb-qwen-base-int8-20260914T091655Z-11069a87",
}


def events(path: Path) -> list[dict]:
    out = []
    with path.open("rb") as handle:
        for raw in handle:
            raw = raw.strip()
            if raw:
                try:
                    out.append(json.loads(raw))
                except json.JSONDecodeError:
                    continue
    return out


def main() -> None:
    settings = get_settings()
    runs = settings.paths.runs / "s9"
    for cell, run_id in GENERATE.items():
        evs = events(runs / run_id / "events.jsonl")
        finished = [e for e in evs if e.get("event") == "generation.trajectory.finished"]
        by_id: dict[str, str] = {}
        for e in finished:
            by_id[str(e.get("trajectory_id"))] = str(e.get("status"))
        c = Counter(by_id.values())
        print(f"{cell} unique={len(by_id)} {dict(c)} finished_events={len(finished)}")

    degen = pd.read_csv(
        settings.paths.stage_artifacts("9") / "degeneracy" / "degeneracy_verdicts.csv"
    )
    print("\nDEGEN")
    print(
        degen.groupby("cell")
        .agg(n=("trajectory_id", "nunique"), n_deg=("degenerate", "sum"))
        .to_string()
    )

    status = pd.read_csv(settings.paths.stage_artifacts("9") / "run_status" / "run_status.csv")
    bad = status[(status["manifest_status"] != "COMPLETED") & (~status["superseded"])]
    print("\nINCOMPLETE")
    print(bad.to_string(index=False) if not bad.empty else "none")

    loo = pd.read_csv(settings.paths.stage_artifacts("9") / "loo" / "persistence_loo_all.csv")
    print("\nLOO sign flips (G<=0)")
    print(
        loo.loc[loo["G"] <= 0, ["cell", "embedding", "held_out_seed", "G"]].to_string(index=False)
    )

    ledger = settings.paths.ledger
    if ledger.is_file():
        frame = pd.read_json(ledger, lines=True)
        s9 = frame[frame["run_id"].astype(str).str.startswith("s9")]
        print(
            f"\nLEDGER project={frame['cost_usd'].sum():.6f} s9={s9['cost_usd'].sum():.6f} n={len(frame)}"
        )
        hosted = s9[s9["run_id"].astype(str).str.contains("qwen-hosted|embed-qwen|qwen3-embed")]
        print(f"s9 embed-ish {hosted['cost_usd'].sum():.6f}")


if __name__ == "__main__":
    main()
