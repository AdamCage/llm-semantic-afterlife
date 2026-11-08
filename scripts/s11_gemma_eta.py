"""Gemma-only step timing. Read-only."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

RUN = Path("runs/s11/s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981")


def main() -> None:
    events = [json.loads(r) for r in (RUN / "events.jsonl").read_text(encoding="utf-8").splitlines() if r.strip()]
    steps = [e for e in events if e.get("event") == "generation.step.completed"]
    lats = [float(e["latency_s"]) for e in steps if isinstance(e.get("latency_s"), (int, float))]
    reasons = Counter(e.get("finish_reason") for e in steps)
    fills = [e.get("block_fill_ratio") for e in steps if e.get("block_fill_ratio") is not None]
    failed = {e.get("trajectory_id") for e in events if e.get("event") == "generation.trajectory.failed"}
    print(f"steps {len(steps)} failed {len(failed)}")
    print(f"finish_reason {dict(reasons)}")
    if fills:
        print(f"fill min/mean/max {min(fills):.3f} {sum(fills)/len(fills):.3f} {max(fills):.3f}")
    if lats:
        mean = sum(lats) / len(lats)
        print(f"latency_s min/mean/max {min(lats):.2f} {mean:.2f} {max(lats):.2f}")
        print(f"h_per_full {mean * 48 / 3600:.3f}")
        remain_steps = 35 * 48 + (48 - int(steps[-1].get("step") or 0))
        # last step field may be 44
        last_step = steps[-1].get("step")
        print(f"last_step {last_step}")
        if isinstance(last_step, int):
            remain = (40 - 5) * 48 + (48 - last_step)
            print(f"remain_steps {remain}")
            print(f"remain_h {remain * mean / 3600:.1f}")


if __name__ == "__main__":
    main()
