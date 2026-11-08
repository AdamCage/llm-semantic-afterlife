"""S11 generate health: errors, protocol, deaths. Read-only."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

RUN = Path("runs/s11/s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b")


def main() -> None:
    status = (RUN / "STATUS").read_text(encoding="utf-8").strip()
    print(f"STATUS {status}")
    events_path = RUN / "events.jsonl"
    events = []
    for raw in events_path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            events.append(json.loads(raw))
    print(f"events {len(events)}")
    counts = Counter(e.get("event") for e in events)
    for name, n in counts.most_common():
        print(f"  {n:4d} {name}")

    steps = [e for e in events if e.get("event") == "generation.step.completed"]
    finished = [e for e in events if e.get("event") == "generation.trajectory.finished"]
    failed = [e for e in events if e.get("event") == "generation.trajectory.failed"]
    errors = [
        e
        for e in events
        if str(e.get("level", "")).upper() in {"ERROR", "CRITICAL"}
        or "error" in str(e.get("event", "")).lower()
        or "fail" in str(e.get("event", "")).lower()
    ]
    print(f"finished_traj {len({e.get('trajectory_id') for e in finished})}")
    print(f"failed_traj {len({e.get('trajectory_id') for e in failed})}")
    print(f"errorish_events {len(errors)}")
    for e in errors[:8]:
        print("  ERR", e.get("event"), e.get("trajectory_id"), str(e)[:220])

    providers = Counter(e.get("served_provider") for e in steps)
    reasons = Counter(e.get("finish_reason") for e in steps)
    reasoning = Counter(e.get("reasoning_tokens") for e in steps)
    roundtrip = Counter(e.get("tokenizer_roundtrip_ok") for e in steps)
    fills = [e.get("block_fill_ratio") for e in steps if e.get("block_fill_ratio") is not None]
    lats = [float(e["latency_s"]) for e in steps if isinstance(e.get("latency_s"), (int, float))]
    print(f"served_provider {dict(providers)}")
    print(f"finish_reason {dict(reasons)}")
    print(f"reasoning_tokens {dict(reasoning)}")
    print(f"roundtrip_ok {dict(roundtrip)}")
    if fills:
        print(f"fill min/mean/max {min(fills):.3f} {sum(fills) / len(fills):.3f} {max(fills):.3f}")
    if lats:
        print(f"latency_s min/mean/max {min(lats):.2f} {sum(lats) / len(lats):.2f} {max(lats):.2f}")

    last = steps[-1] if steps else {}
    print(
        "last",
        last.get("ts"),
        last.get("trajectory_id"),
        "step",
        last.get("step"),
        "lat",
        last.get("latency_s"),
    )

    log = Path("/home/adam/s11/pb-ministral-8b-base.log")
    if log.is_file():
        text = log.read_text(encoding="utf-8", errors="replace")
        hits = []
        for needle in (
            "Traceback",
            "OutOfMemory",
            "CUDA",
            "REFUSE",
            "ERROR",
            "empty completion",
            "FAILED",
        ):
            if needle.lower() in text.lower():
                hits.append(needle)
        print("log_needles", hits or "none")


if __name__ == "__main__":
    main()
