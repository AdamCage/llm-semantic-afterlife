"""S11 generate health for all paperb runs. Read-only."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path("runs/s11")


def main() -> None:
    for run_dir in sorted(ROOT.glob("s11-paperb-*")):
        if (run_dir / "SUPERSEDED").is_file():
            continue
        status = (
            (run_dir / "STATUS").read_text(encoding="utf-8").strip()
            if (run_dir / "STATUS").is_file()
            else "NOSTATUS"
        )
        events = []
        path = run_dir / "events.jsonl"
        if path.is_file():
            for raw in path.read_text(encoding="utf-8").splitlines():
                if raw.strip():
                    events.append(json.loads(raw))
        steps = [e for e in events if e.get("event") == "generation.step.completed"]
        failed = {e.get("trajectory_id") for e in events if e.get("event") == "generation.trajectory.failed"}
        errors = [
            e
            for e in events
            if str(e.get("level", "")).upper() in {"ERROR", "CRITICAL"}
        ]
        providers = Counter(e.get("served_provider") for e in steps)
        reasons = Counter(e.get("finish_reason") for e in steps)
        reasoning = Counter(e.get("reasoning_tokens") for e in steps)
        roundtrip = Counter(e.get("tokenizer_roundtrip_ok") for e in steps)
        fills = [e.get("block_fill_ratio") for e in steps if e.get("block_fill_ratio") is not None]
        print(run_dir.name, status)
        print(
            f"  steps={len(steps)} failed={len(failed)} errors={len(errors)} "
            f"provider={dict(providers)} reason={dict(reasons)} "
            f"think={dict(reasoning)} roundtrip={dict(roundtrip)}"
        )
        if fills:
            print(f"  fill {min(fills):.3f}/{sum(fills)/len(fills):.3f}/{max(fills):.3f}")


if __name__ == "__main__":
    main()
