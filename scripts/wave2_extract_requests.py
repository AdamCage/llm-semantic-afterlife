"""Pull local.* extras from the first request record."""

from __future__ import annotations

import json
import sys
from pathlib import Path

run = Path(sys.argv[1])
req_dir = run / "requests"
files = sorted(req_dir.glob("*.jsonl")) if req_dir.is_dir() else []
print("request_files", [p.name for p in files])
for path in files:
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        obj = json.loads(raw)
        body = obj.get("response") or obj.get("body") or obj
        local = None
        if isinstance(body, dict):
            raw_body = body.get("raw") or body
            if isinstance(raw_body, dict):
                local = raw_body.get("local")
            if local is None:
                local = body.get("local")
        print("keys", list(obj.keys())[:20])
        print("local", local)
        text = None
        if isinstance(body, dict):
            choices = body.get("choices") or (body.get("raw") or {}).get("choices")
            if choices:
                text = choices[0].get("text")
        if text:
            print("text80", text[:80].replace("\n", " "))
        break
