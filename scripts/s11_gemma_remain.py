"""Remaining Gemma Base time from checkpoints. Read-only."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

RUN = Path("runs/s11/s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981")
STEPS = 48


def main() -> None:
    events = [
        json.loads(line)
        for line in (RUN / "events.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    steps_by: dict[str, int] = defaultdict(int)
    lats: list[float] = []
    finished: set[str] = set()
    failed: dict[str, str] = {}
    for event in events:
        name = event.get("event")
        tid = str(event.get("trajectory_id") or "")
        if name == "generation.step.completed" and tid:
            step = event.get("step")
            if isinstance(step, int):
                steps_by[tid] = max(steps_by[tid], step)
            lat = event.get("latency_s")
            if isinstance(lat, (int, float)) and lat > 5:
                lats.append(float(lat))
        elif name == "generation.trajectory.finished" and tid:
            finished.add(tid)
        elif name == "generation.trajectory.failed" and tid:
            failed[tid] = str(event.get("error") or event.get("reason") or "")[:180]
    print(f"finished {len(finished)} failed {len(failed)} with_steps {len(steps_by)}")
    for tid, reason in failed.items():
        print(f"FAIL {tid} steps={steps_by.get(tid)} {reason}")
    current = max(steps_by, key=lambda tid: (tid not in finished and tid not in failed, steps_by[tid]))
    # current = not finished and not failed, highest step
    open_ids = [tid for tid in steps_by if tid not in finished and tid not in failed]
    print(f"open {len(open_ids)}")
    for tid in open_ids:
        print(f"OPEN {tid} step {steps_by[tid]}")
    done = len(finished) + len(failed)
    # planned 40; remaining full after open ones
    remain_full = 40 - done - len(open_ids)
    mean = sum(lats) / len(lats) if lats else 72.0
    remain_steps = 0
    for tid in open_ids:
        remain_steps += max(0, STEPS - steps_by[tid])
    remain_steps += max(0, remain_full) * STEPS
    print(f"mean_decode_s {mean:.2f} n={len(lats)}")
    print(f"remain_full_after_open {remain_full}")
    print(f"remain_steps {remain_steps}")
    print(f"remain_h {remain_steps * mean / 3600:.1f}")


if __name__ == "__main__":
    main()
