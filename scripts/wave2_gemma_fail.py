import json
from pathlib import Path

run = Path("runs/s8/s8-paperb-micro-gemma4-12b-it-20260910T233125Z-f89a95a4")
for raw in (run / "events.jsonl").read_text(encoding="utf-8").splitlines():
    obj = json.loads(raw)
    if obj.get("event") in {
        "generation.trajectory.failed",
        "generation.trajectory.finished",
        "generation.step.completed",
        "local.generate.completed",
    } or obj.get("level") == "ERROR":
        print("---", obj.get("event"), obj.get("error_type"))
        for key in (
            "error",
            "generated_tokens",
            "finish_reason",
            "tok_s",
            "n_output_ids",
            "peak_vram_mib",
            "block_fill_ratio",
            "reasoning_tokens",
        ):
            if key in obj:
                val = obj[key]
                print(key, str(val)[:400])
