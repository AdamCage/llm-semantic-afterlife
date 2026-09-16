"""Print CRASHED trajectory errors from a run events.jsonl. No secrets."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    run = Path(sys.argv[1])
    events = run / "events.jsonl"
    print("run", run)
    print("exists", events.is_file())
    if not events.is_file():
        return
    for raw in events.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        obj = json.loads(raw)
        name = obj.get("event", "")
        if (
            name.endswith("crashed")
            or name.endswith("failed")
            or obj.get("level") == "ERROR"
            or "error" in obj
        ):
            print("---", name, obj.get("error_type"))
            err = str(obj.get("error") or "")
            print(err[:2000])


if __name__ == "__main__":
    main()
