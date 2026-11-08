"""Dump one S11 generation.step.completed event. No generate."""

from __future__ import annotations

import json
from pathlib import Path

run = Path(
    "/mnt/c/projects/llm-semantic-afterlife/runs/s11/"
    "s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b/events.jsonl"
)
for raw in run.read_text(encoding="utf-8").splitlines():
    ev = json.loads(raw)
    if ev.get("event") == "generation.step.completed":
        keep = {
            k: ev.get(k)
            for k in (
                "event",
                "step_index",
                "trajectory_id",
                "generated_tokens",
                "completion_tokens",
                "prompt_tokens",
                "finish_reason",
                "tokens_per_second",
                "tok_s",
                "latency_s",
                "block_fill",
                "fill",
                "served_provider",
                "reasoning_tokens",
                "tokenizer_roundtrip_ok",
            )
            if k in ev
        }
        print(json.dumps(keep, indent=2, default=str)[:2000])
        print("keys", sorted(ev.keys()))
        break
