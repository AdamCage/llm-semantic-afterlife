"""S12 cohort progress and remaining decode time. Read-only."""

from __future__ import annotations

import json
from pathlib import Path

TARGET = 4834  # 4950016 / 1024
ROOT = Path("runs/s12")


def main() -> None:
    rows = []
    lats = []
    for run in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        status = (
            (run / "STATUS").read_text(encoding="utf-8").strip()
            if (run / "STATUS").is_file()
            else "NOSTATUS"
        )
        steps = 0
        last = None
        events = run / "events.jsonl"
        if events.is_file():
            for line in events.read_text(encoding="utf-8", errors="replace").splitlines():
                if "generation.step.completed" not in line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if ev.get("event") != "generation.step.completed":
                    continue
                steps += 1
                last = ev
                lat = ev.get("latency_s")
                if isinstance(lat, (int, float)) and lat > 5:
                    lats.append(float(lat))
        tok = int(last.get("generated_tokens") or 0) if last else 0
        rows.append((run.name, status, steps, tok, last.get("ts") if last else ""))
        print(f"{status} steps={steps}/{TARGET} tok={tok} {run.name}")
    total_done = sum(r[2] for r in rows)
    total_left = sum(max(0, TARGET - r[2]) for r in rows)
    mean = sum(lats) / len(lats) if lats else 36.0
    print(f"cells={len(rows)} steps_done={total_done} steps_left={total_left}")
    print(f"mean_step_s {mean:.2f} n={len(lats)}")
    print(f"remain_h {total_left * mean / 3600:.1f}")
    if last_ts := max((r[4] for r in rows if r[4]), default=""):
        print(f"newest_step {last_ts}")


if __name__ == "__main__":
    main()
