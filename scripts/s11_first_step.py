"""Print latest S11 generate step events. No generate."""

from __future__ import annotations

import json
from pathlib import Path

runs = Path("/mnt/c/projects/llm-semantic-afterlife/runs/s11")
if not runs.is_dir():
    print("no runs/s11")
    raise SystemExit(0)
for run_dir in sorted(runs.glob("s11-paperb-*")):
    status = (run_dir / "STATUS").read_text(encoding="utf-8").strip() if (run_dir / "STATUS").is_file() else "NOSTATUS"
    events_path = run_dir / "events.jsonl"
    print(f"{status} {run_dir.name}")
    if not events_path.is_file():
        continue
    n = 0
    last_step = None
    finished = 0
    failed = 0
    for raw in events_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            ev = json.loads(raw)
        except json.JSONDecodeError:
            continue
        n += 1
        name = ev.get("event", "")
        if name.endswith("generation.step.completed") or name == "generation.step.completed":
            last_step = ev
        if name == "generation.trajectory.finished":
            finished += 1
        if name == "generation.trajectory.failed":
            failed += 1
    print(f"  events={n} finished={finished} failed={failed}")
    if last_step:
        print(
            "  last_step",
            last_step.get("trajectory_id", "")[:72],
            "idx",
            last_step.get("step_index"),
            "tok/s",
            last_step.get("tokens_per_second") or last_step.get("tok_s"),
            "fill",
            last_step.get("block_fill") or last_step.get("fill"),
            "reason",
            last_step.get("finish_reason"),
        )
