from __future__ import annotations

import json
from pathlib import Path

p = Path(r"c:/projects/llm-semantic-afterlife/runs/s9/s9-paperb-qwen-instruct-int8-20260912T180435Z-e9c7d498/events.jsonl")
rows = []
bad = 0
for raw in p.read_text(encoding="utf-8").splitlines():
    if not raw.strip():
        continue
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        bad += 1
        continue
    if not isinstance(event, dict):
        bad += 1
        continue
    rows.append(event)
print("n", len(rows), "bad", bad)
for event in rows[-12]:
    print(
        event.get("ts"),
        event.get("event"),
        event.get("trajectory_id", ""),
        event.get("step", ""),
        event.get("generated_tokens", ""),
        event.get("peak_vram_mib", ""),
    )
