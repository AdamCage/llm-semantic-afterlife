"""S11 generate progress + remaining-time sketch. Read-only."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

RUNS = Path("runs/s11")
PLANNED = {
    "ministral-base": 40,
    "ministral-instruct": 40,
    "gemma4-base": 40,
    "gemma4-it": 40,
}
STEPS_PER_FULL = 48


def cell_from_name(name: str) -> str:
    if "ministral-base" in name:
        return "ministral-base"
    if "ministral-instruct" in name:
        return "ministral-instruct"
    if "gemma4-base" in name or "gemma4-12b-base" in name:
        return "gemma4-base"
    if "gemma4-it" in name or "gemma4-12b-it" in name:
        return "gemma4-it"
    return name


def load_events(path: Path) -> list[dict]:
    out: list[dict] = []
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            out.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return out


def main() -> None:
    now = datetime.now(UTC)
    print(f"now_utc {now.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    if not RUNS.is_dir():
        print("no runs/s11")
        return
    latencies: list[float] = []
    for run_dir in sorted(RUNS.glob("s11-paperb-*")):
        if (run_dir / "SUPERSEDED").is_file():
            continue
        status = (
            (run_dir / "STATUS").read_text(encoding="utf-8").strip()
            if (run_dir / "STATUS").is_file()
            else "NOSTATUS"
        )
        events = load_events(run_dir / "events.jsonl")
        steps = [e for e in events if e.get("event") == "generation.step.completed"]
        finished = [e for e in events if e.get("event") == "generation.trajectory.finished"]
        failed = [e for e in events if e.get("event") == "generation.trajectory.failed"]
        started = [e for e in events if e.get("event") == "generation.trajectory.started"]
        uniq_started = {e.get("trajectory_id") for e in started}
        uniq_finished = {e.get("trajectory_id") for e in finished}
        uniq_failed = {e.get("trajectory_id") for e in failed}
        for e in steps:
            lat = e.get("latency_s")
            if isinstance(lat, (int, float)) and lat > 0:
                latencies.append(float(lat))
        last = steps[-1] if steps else None
        last_ts = last.get("ts") if last else ""
        last_traj = (last.get("trajectory_id") or "") if last else ""
        last_step = last.get("step") if last else ""
        last_lat = last.get("latency_s") if last else ""
        print(
            f"{status} {run_dir.name} steps={len(steps)} "
            f"started={len(uniq_started)} finished={len(uniq_finished)} "
            f"failed={len(uniq_failed)}"
        )
        if last:
            print(f"  last step={last_step} lat={last_lat}s traj={last_traj} ts={last_ts}")
    if latencies:
        mean = sum(latencies) / len(latencies)
        print(f"mean_step_s {mean:.3f} n={len(latencies)}")
        h_per_full = mean * STEPS_PER_FULL / 3600.0
        print(f"h_per_full_traj {h_per_full:.3f}")
        _remaining_full = 160  # worst case if we have only started counting later
        # Better: remaining = planned cells not done * 40, minus progress on current
        print("sketch_if_all_complete_fill1_hours", round(160 * h_per_full, 1))


if __name__ == "__main__":
    main()
