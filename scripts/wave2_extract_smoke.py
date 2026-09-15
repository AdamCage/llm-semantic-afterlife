"""Extract Wave 2 smoke/microbench fields from a run directory."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    run = Path(sys.argv[1])
    events_path = run / "events.jsonl"
    rows: list[dict] = []
    if events_path.is_file():
        for raw in events_path.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                rows.append(json.loads(raw))
    loaded = [e for e in rows if e.get("event") == "local.model.loaded"]
    unloaded = [e for e in rows if e.get("event") == "local.model.unloaded"]
    steps = [e for e in rows if e.get("event") == "generation.step.completed"]
    finished = [e for e in rows if e.get("event") == "generation.trajectory.finished"]
    crashed = [e for e in rows if e.get("event") == "generation.trajectory.crashed"]
    print("run_id", run.name)
    print("status_file", (run / "STATUS").read_text(encoding="utf-8").strip() if (run / "STATUS").is_file() else "?")
    if loaded:
        e = loaded[0]
        print("architecture", e.get("architecture"))
        print("loader_class", e.get("loader_class"))
        print("hf_revision", e.get("hf_revision"))
        print("quant_config", e.get("quant_config"))
        print("load_s", e.get("load_s"))
        print("peak_vram_mib_load", e.get("peak_vram_mib"))
    if steps:
        e = steps[0]
        print("generated_tokens", e.get("generated_tokens"))
        print("finish_reason", e.get("finish_reason"))
        print("block_fill_ratio", e.get("block_fill_ratio"))
        print("latency_s", e.get("latency_s"))
        print("reasoning_tokens", e.get("reasoning_tokens"))
        print("tokenizer_roundtrip_ok", e.get("tokenizer_roundtrip_ok"))
        print("served_provider", e.get("served_provider"))
        n = e.get("completion_tokens") or 0
        lat = e.get("latency_s") or 0
        print("tok_s_from_step", round(n / lat, 3) if lat else None)
    if finished:
        print("traj_status", finished[0].get("status"))
        print("stop_events", finished[0].get("stop_events"))
    if crashed:
        print("crash", crashed[0].get("error_type"), str(crashed[0].get("error") or "")[:500])
    gens = [e for e in rows if e.get("event") == "local.generate.completed"]
    if gens:
        e = gens[0]
        print("tok_s", e.get("tok_s"))
        print("decode_s", e.get("decode_s"))
        print("peak_vram_mib_gen", e.get("peak_vram_mib"))
        print("n_output_ids", e.get("n_output_ids"))
    if unloaded:
        print("peak_vram_mib_unload", unloaded[0].get("peak_vram_mib"))
    chunks = run / "data" / "chunks.parquet"
    if chunks.is_file():
        import pandas as pd

        frame = pd.read_parquet(chunks)
        if not frame.empty and "text" in frame.columns:
            text = str(frame.iloc[0]["text"])
            print("first_80", text[:80].replace("\n", " "))


if __name__ == "__main__":
    main()
