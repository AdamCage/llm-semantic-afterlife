from __future__ import annotations

import json
from pathlib import Path

path = Path(
    "runs/s8/s8-paperb-smoke-qwen3-8b-base-20260910T200925Z-28827fb7/"
    "requests/pb-qwen3-8b-base__W32__T0p3__physics__s1.jsonl"
)
obj = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
resp = obj["response"]
print("response_keys", sorted(resp.keys()))
raw = resp.get("raw")
if isinstance(raw, dict):
    print("raw_keys", sorted(raw.keys()))
    print("raw.local", raw.get("local"))
print("usage", resp.get("usage"))
print("finish", resp.get("finish_reason"))
print("text80", (resp.get("text") or "")[:80])
