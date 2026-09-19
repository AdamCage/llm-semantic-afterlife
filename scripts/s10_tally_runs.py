"""Tally COMPLETED vs FAILED per S10 generate run."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path("/mnt/c/projects/llm-semantic-afterlife/runs/s10")


def tally(run_dir: Path) -> None:
    events = run_dir / "events.jsonl"
    last: dict[str, dict] = {}
    if not events.is_file():
        print(run_dir.name, "NO_EVENTS")
        return
    for line in events.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("event") != "generation.trajectory.finished":
            continue
        tid = rec.get("trajectory_id")
        if tid:
            last[tid] = rec
    by = Counter(r.get("status") for r in last.values())
    print(run_dir.name, "n=", len(last), dict(by))
    for tid, rec in sorted(last.items()):
        if rec.get("status") != "COMPLETED":
            print(
                " ",
                rec.get("status"),
                tid.split("__")[-2] + " " + tid.split("__")[-1],
                "tok=" + str(rec.get("generated_tokens")),
            )


def main() -> None:
    for d in sorted(ROOT.iterdir()):
        if d.is_dir():
            tally(d)


if __name__ == "__main__":
    main()
