"""Hourly S9 health snapshot. Read-only. Exit 2 if stalled or dead."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"c:\projects\llm-semantic-afterlife\runs\s9")
# INT8 live step ~135s; NF4 ~38s. Stall beyond this is hung.
STALL_S = 480


def parse_ts(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def main() -> int:
    now = datetime.now(timezone.utc)
    worst = 0
    for run in sorted(ROOT.iterdir()):
        status_path = run / "STATUS"
        if not status_path.is_file():
            continue
        status = status_path.read_text(encoding="utf-8").strip()
        events = run / "events.jsonl"
        last_step = None
        last_any = None
        if events.is_file():
            for raw in events.read_text(encoding="utf-8").splitlines():
                if not raw.strip():
                    continue
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                last_any = event
                if event.get("event") == "generation.step.completed":
                    last_step = event
        stall = None
        heartbeat = last_any if last_any and last_any.get("ts") else last_step
        if heartbeat and heartbeat.get("ts"):
            stall = (now - parse_ts(heartbeat["ts"])).total_seconds()
        flag = ""
        if status == "RUNNING" and stall is not None and stall > STALL_S:
            flag = " STALE_OR_HUNG"
            worst = 2
        print(
            f"{status:10} stall={None if stall is None else round(stall, 1)} "
            f"{run.name}{flag}"
        )
        if last_step:
            print(
                f"           last {last_step.get('trajectory_id')} "
                f"step={last_step.get('step')} tok={last_step.get('generated_tokens')} "
                f"fill={last_step.get('block_fill_ratio')} lat={last_step.get('latency_s')}"
            )
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
