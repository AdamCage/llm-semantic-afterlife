"""Gemma IT progress. Read-only."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

RUN = Path("runs/s11/s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427")
STEPS = 48


def main() -> None:
    events = [
        json.loads(line)
        for line in (RUN / "events.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    steps_by: dict[str, int] = defaultdict(int)
    tokens_by: dict[str, int] = defaultdict(int)
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
            gen = event.get("generated_tokens")
            if isinstance(gen, int):
                tokens_by[tid] = max(tokens_by[tid], gen)
            lat = event.get("latency_s")
            if isinstance(lat, (int, float)) and lat > 5:
                lats.append(float(lat))
        elif name == "generation.trajectory.finished" and tid:
            finished.add(tid)
        elif name == "generation.trajectory.failed" and tid:
            failed[tid] = str(event.get("error") or event.get("reason") or "")[:160]
    print(f"steps_events {sum(1 for e in events if e.get('event') == 'generation.step.completed')}")
    print(f"finished {len(finished)} failed {len(failed)} touched {len(steps_by)}")
    for tid in sorted(finished | set(failed) | set(steps_by)):
        short = tid.split("__")[-2] + " " + tid.split("__")[-1]
        tag = "FAIL" if tid in failed else ("DONE" if tid in finished else "OPEN")
        print(f"{tag} {short} step={steps_by.get(tid)} tok={tokens_by.get(tid)}")
    mean = sum(lats) / len(lats) if lats else 75.0
    open_ids = [tid for tid in steps_by if tid not in finished and tid not in failed]
    done = len(finished | set(failed))
    remain_full = 40 - done - len(open_ids)
    remain_steps = sum(max(0, STEPS - steps_by[tid]) for tid in open_ids)
    remain_steps += max(0, remain_full) * STEPS
    print(f"mean_decode_s {mean:.2f} n={len(lats)}")
    print(f"remain_full_if_all_complete {remain_full}")
    print(f"remain_h_if_all_complete {remain_steps * mean / 3600:.1f}")
    # deaths so far are short; if the rest die in ~6 steps:
    print(
        f"remain_h_if_rest_die_in_6_steps {(6 * max(0, remain_full) + sum(max(0, 6 - steps_by[t]) for t in open_ids)) * mean / 3600:.2f}"
    )


if __name__ == "__main__":
    main()
