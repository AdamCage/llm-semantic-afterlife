"""Print S9 generate progress from events.jsonl. Read-only."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

RID = "s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6"
RUN = Path(r"c:\projects\llm-semantic-afterlife\runs\s9") / RID
N_TRAJ = 40
STEPS_PER = 48  # 49152 / 1024


def parse_ts(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def main() -> None:
    events_path = RUN / "events.jsonl"
    status = (RUN / "STATUS").read_text(encoding="utf-8").strip() if (RUN / "STATUS").is_file() else "?"
    steps: list[dict] = []
    finished: list[dict] = []
    fails: list[dict] = []
    gens: list[dict] = []
    for raw in events_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        event = json.loads(raw)
        name = event.get("event")
        if name == "generation.step.completed":
            steps.append(event)
        elif name == "generation.trajectory.finished":
            finished.append(event)
        elif name in {"generation.trajectory.failed", "run.failed"} or event.get("level") == "ERROR":
            fails.append(event)
        elif name == "local.generate.completed":
            gens.append(event)

    by_traj: dict[str, dict] = defaultdict(
        lambda: {
            "n": 0,
            "max_step": -1,
            "cache": 0,
            "live": 0,
            "lats": [],
            "fills": [],
            "think": 0,
            "rt_fail": 0,
            "stop": 0,
        }
    )
    for event in steps:
        tid = str(event.get("trajectory_id"))
        row = by_traj[tid]
        row["n"] += 1
        row["max_step"] = max(row["max_step"], int(event.get("step") or -1))
        if event.get("from_cache"):
            row["cache"] += 1
        else:
            row["live"] += 1
            if event.get("latency_s") is not None:
                row["lats"].append(float(event["latency_s"]))
        if event.get("block_fill_ratio") is not None:
            row["fills"].append(float(event["block_fill_ratio"]))
        row["think"] += int(event.get("reasoning_tokens") or 0)
        if event.get("tokenizer_roundtrip_ok") is False:
            row["rt_fail"] += 1
        if event.get("finish_reason") not in {None, "length"}:
            row["stop"] += 1

    live_lats = [lat for row in by_traj.values() for lat in row["lats"]]
    live_lats.sort()
    median = live_lats[len(live_lats) // 2] if live_lats else None
    mean = sum(live_lats) / len(live_lats) if live_lats else None
    completed_steps = sum(row["n"] for row in by_traj.values())
    remaining_steps = N_TRAJ * STEPS_PER - completed_steps
    eta_s = remaining_steps * median if median is not None else None

    last = steps[-1] if steps else {}
    first = steps[0] if steps else {}
    now = datetime.now(timezone.utc)
    started = parse_ts(first["ts"]) if first.get("ts") else None
    last_ts = parse_ts(last["ts"]) if last.get("ts") else None
    stall_s = (now - last_ts).total_seconds() if last_ts else None
    elapsed_s = (now - started).total_seconds() if started else None

    tok = [float(event["tok_s"]) for event in gens if event.get("tok_s") is not None]
    print(f"run_id={RID}")
    print(f"STATUS={status}")
    print(f"traj_seen={len(by_traj)} traj_finished={len(finished)} errors={len(fails)}")
    print(f"steps_done={completed_steps}/{N_TRAJ * STEPS_PER} remaining_steps={remaining_steps}")
    if last:
        print(
            "last",
            last.get("trajectory_id"),
            f"step={last.get('step')}",
            f"tok={last.get('generated_tokens')}",
            f"turnovers={last.get('turnovers')}",
            f"fill={last.get('block_fill_ratio')}",
            f"think={last.get('reasoning_tokens')}",
            f"rt={last.get('tokenizer_roundtrip_ok')}",
            f"cache={last.get('from_cache')}",
            f"lat={last.get('latency_s')}",
            f"ts={last.get('ts')}",
        )
    print(
        f"live_steps={len(live_lats)} mean_lat_s={None if mean is None else round(mean, 3)} "
        f"median_lat_s={None if median is None else round(median, 3)}"
    )
    if tok:
        print(f"tok_s_n={len(tok)} tok_s_mean={round(sum(tok) / len(tok), 3)} tok_s_last={tok[-1]}")
    if elapsed_s is not None:
        print(f"elapsed_h={round(elapsed_s / 3600, 3)} stall_s={None if stall_s is None else round(stall_s, 1)}")
    if eta_s is not None:
        print(
            f"eta_this_run_h={round(eta_s / 3600, 2)} "
            f"eta_finish_utc={datetime.fromtimestamp(now.timestamp() + eta_s, timezone.utc).isoformat()}"
        )
        # After this run: Base 40 + INT8 20. INT8 latency unknown; use same median as sketch.
        after = (40 + 20) * STEPS_PER * (median or 0)
        print(f"sketch_remaining_after_this_run_h={round(after / 3600, 2)} (Base+INT8 at same median)")
    print("per_traj:")
    for tid, row in by_traj.items():
        mean_lat = sum(row["lats"]) / len(row["lats"]) if row["lats"] else None
        print(
            f"  {tid} steps={row['n']} max={row['max_step']} "
            f"cache={row['cache']} live={row['live']} think={row['think']} "
            f"rt_fail={row['rt_fail']} stopish={row['stop']} "
            f"mean_live_lat={None if mean_lat is None else round(mean_lat, 2)}"
        )
    print("finished:")
    for event in finished:
        print(
            " ",
            event.get("trajectory_id"),
            "tokens",
            event.get("generated_tokens"),
            "n_steps",
            event.get("n_steps"),
            "stop",
            event.get("stop_events"),
        )
    if fails:
        print("FAILS:")
        for event in fails[-8]:
            print(" ", event.get("ts"), event.get("event"), event.get("level"), str(event.get("error") or event.get("message") or "")[:200])
    sys.exit(0)


if __name__ == "__main__":
    main()
