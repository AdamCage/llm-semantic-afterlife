"""One-shot S10 generate progress. No network."""

from __future__ import annotations

import json
from pathlib import Path

RUN = Path(
    "/mnt/c/projects/llm-semantic-afterlife/runs/s10/"
    "s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3"
)


def main() -> None:
    print("STATUS", (RUN / "STATUS").read_text(encoding="utf-8").strip())
    events = RUN / "events.jsonl"
    n = 0
    last: dict | None = None
    steps = 0
    if events.exists():
        for line in events.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            n += 1
            last = json.loads(line)
            if last.get("event", "").endswith("step.completed"):
                steps += 1
    print(f"events={n} step_completed={steps}")
    if last:
        keys = (
            "event",
            "trajectory_id",
            "step",
            "finish_reason",
            "completion_tokens",
            "prompt_tokens",
        )
        print("last", {k: last.get(k) for k in keys if k in last or True})
        print("last_event", last.get("event"), last.get("level"))
    req = list((RUN / "requests").glob("*.jsonl"))
    print("request_files", len(req))
    for p in req:
        print(p.name, "lines", sum(1 for _ in p.open(encoding="utf-8")))


if __name__ == "__main__":
    main()
