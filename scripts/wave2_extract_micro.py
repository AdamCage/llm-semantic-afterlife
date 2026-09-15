"""Summarise a Wave 2 microbench run (multi-step). No secrets."""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path


def main() -> None:
    run = Path(sys.argv[1])
    events = []
    path = run / "events.jsonl"
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                events.append(json.loads(raw))
    print("run_id", run.name)
    print("status", (run / "STATUS").read_text(encoding="utf-8").strip() if (run / "STATUS").is_file() else "?")
    loaded = [e for e in events if e.get("event") == "local.model.loaded"]
    gens = [e for e in events if e.get("event") == "local.generate.completed"]
    steps = [e for e in events if e.get("event") == "generation.step.completed"]
    finished = [e for e in events if e.get("event") == "generation.trajectory.finished"]
    if loaded:
        e = loaded[0]
        print("architecture", e.get("architecture"))
        print("loader_class", e.get("loader_class"))
        print("hf_revision", e.get("hf_revision"))
        print("quant_config", e.get("quant_config"))
        print("load_s", e.get("load_s"))
        print("peak_vram_mib_load", e.get("peak_vram_mib"))
    tok_s = [float(e["tok_s"]) for e in gens if e.get("tok_s") is not None]
    vram = [float(e["peak_vram_mib"]) for e in gens if e.get("peak_vram_mib") is not None]
    fills = [float(e["block_fill_ratio"]) for e in steps if e.get("block_fill_ratio") is not None]
    stops = sum(1 for e in steps if e.get("finish_reason") != "length")
    think = sum(int(e.get("reasoning_tokens") or 0) for e in steps)
    rt_fail = sum(1 for e in steps if e.get("tokenizer_roundtrip_ok") is False)
    print("n_generate_events", len(gens))
    print("n_steps", len(steps))
    if tok_s:
        print("tok_s_mean", round(statistics.mean(tok_s), 3))
        print("tok_s_min", round(min(tok_s), 3))
        print("tok_s_max", round(max(tok_s), 3))
        print("tok_s_median", round(statistics.median(tok_s), 3))
    if vram:
        print("peak_vram_mib_gen_max", max(vram))
    if fills:
        print("block_fill_mean", round(statistics.mean(fills), 4))
        print("block_fill_min", round(min(fills), 4))
    print("stop_steps", stops)
    print("reasoning_tokens_sum", think)
    print("roundtrip_failures", rt_fail)
    if finished:
        print("traj_status", finished[0].get("status"))
        print("generated_tokens", finished[0].get("generated_tokens"))
        print("stop_events", finished[0].get("stop_events"))
        print("n_chunks", finished[0].get("n_chunks"))
    if steps:
        lats = [float(e["latency_s"]) for e in steps if e.get("latency_s") is not None]
        if lats:
            print("step_latency_s_mean", round(statistics.mean(lats), 3))
            print("step_latency_s_median", round(statistics.median(lats), 3))
            print("s9_hours_one_traj_48_steps", round(statistics.median(lats) * 48 / 3600.0, 3))


if __name__ == "__main__":
    main()
