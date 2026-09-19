"""Inventory one S10 generate run after an unclean stop."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

RUN = Path(
    "/mnt/c/projects/llm-semantic-afterlife/runs/s10/"
    "s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3"
)
TARGET = 49152


def _steps(path: Path) -> tuple[int, int, str]:
    n = 0
    tokens = 0
    last_reason = ""
    truncated = False
    with path.open("rb") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                truncated = True
                break
            n += 1
            tokens += int(rec.get("completion_tokens") or 0)
            last_reason = str(rec.get("finish_reason") or "")
    return n, tokens, ("TRUNCATED " if truncated else "") + last_reason


def main() -> None:
    print("STATUS", (RUN / "STATUS").read_text(encoding="utf-8").strip())
    manifest = json.loads((RUN / "manifest.json").read_text(encoding="utf-8"))
    print("manifest_status", manifest.get("status"))
    print("config_sha", (manifest.get("config_sha256") or "")[:8])
    print("finished_at", manifest.get("finished_at"))
    traj_dir = RUN / "data" / "trajectories"
    files = sorted(traj_dir.glob("*.steps.jsonl")) if traj_dir.is_dir() else []
    print("traj_files", len(files))
    done = 0
    inflight = 0
    reasons: Counter[str] = Counter()
    for path in files:
        n, tokens, reason = _steps(path)
        reasons[reason.split()[-1] if reason else ""] += 1
        flag = "DONE" if tokens >= TARGET else "INFLIGHT"
        if tokens >= TARGET:
            done += 1
        else:
            inflight += 1
        print(f"{flag}\t{path.stem}\tsteps={n}\ttokens={tokens}\t{reason}")
    print("done", done, "inflight", inflight, "reasons", dict(reasons))
    events = RUN / "events.jsonl"
    if events.is_file():
        last = None
        n_step = 0
        n_fail = 0
        for line in events.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            last = json.loads(line)
            ev = last.get("event", "")
            if ev.endswith("step.completed"):
                n_step += 1
            if "fail" in ev or last.get("level") == "ERROR":
                n_fail += 1
        print("events_step_completed", n_step, "errorish", n_fail)
        if last:
            print(
                "last_event",
                last.get("ts"),
                last.get("event"),
                last.get("trajectory_id"),
            )


if __name__ == "__main__":
    main()
