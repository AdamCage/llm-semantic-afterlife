"""Read-only snapshot of all S9 generate runs."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"c:\projects\llm-semantic-afterlife\runs\s9")
STEPS_PER = 48


def parse_ts(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def summarize(run: Path) -> None:
    status = (run / "STATUS").read_text(encoding="utf-8").strip()
    events_path = run / "events.jsonl"
    finished: list[dict] = []
    failed: list[dict] = []
    steps: list[dict] = []
    lats: list[float] = []
    for raw in events_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        event = json.loads(raw)
        name = event.get("event")
        if name == "generation.trajectory.finished":
            if event.get("status") == "FAILED" or "fail" in str(event.get("error") or "").lower():
                failed.append(event)
            else:
                finished.append(event)
        elif name == "generation.trajectory.failed":
            failed.append(event)
        elif name == "generation.step.completed":
            steps.append(event)
            if event.get("latency_s") is not None and not event.get("from_cache"):
                lats.append(float(event["latency_s"]))
    last = steps[-1] if steps else {}
    lats.sort()
    median = lats[len(lats) // 2] if lats else None
    print(f"== {run.name} STATUS={status}")
    print(f"   finished={len(finished)} failed_events={len(failed)} step_events={len(steps)}")
    if last:
        print(
            f"   last {last.get('trajectory_id')} step={last.get('step')} "
            f"tok={last.get('generated_tokens')} fill={last.get('block_fill_ratio')} "
            f"think={last.get('reasoning_tokens')} lat={last.get('latency_s')} ts={last.get('ts')}"
        )
        stall = (datetime.now(timezone.utc) - parse_ts(last["ts"])).total_seconds()
        print(f"   stall_s={round(stall, 1)} median_live_lat_s={None if median is None else round(median, 3)}")
    reasons = Counter()
    for event in failed:
        reasons[str(event.get("error") or event.get("message") or event.get("status"))[:120]] += 1
    if reasons:
        print("   fail_reasons:")
        for reason, n in reasons.items():
            print(f"     n={n} {reason}")
    # also STATUS=FAILED trajectories from finished list if runner records them there
    fail_ids = []
    ok_ids = []
    for event in finished:
        tid = event.get("trajectory_id")
        if event.get("n_steps") and event.get("generated_tokens", 0) >= 40000:
            ok_ids.append(tid)
        else:
            fail_ids.append((tid, event.get("generated_tokens"), event.get("n_steps"), event.get("error")))
    if fail_ids:
        print("   short_finished:")
        for row in fail_ids:
            print("    ", row)


def main() -> None:
    for run in sorted(ROOT.iterdir()):
        if (run / "STATUS").is_file():
            summarize(run)


if __name__ == "__main__":
    main()
