"""Extract Wave 2 fields for every s8 smoke/micro run."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("runs/s8")


def extract(run: Path) -> dict:
    rows = []
    events = run / "events.jsonl"
    if events.is_file():
        for raw in events.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                rows.append(json.loads(raw))
    loaded = next((e for e in rows if e.get("event") == "local.model.loaded"), {})
    gens = [e for e in rows if e.get("event") == "local.generate.completed"]
    steps = [e for e in rows if e.get("event") == "generation.step.completed"]
    finished = next((e for e in rows if e.get("event") == "generation.trajectory.finished"), {})
    crashed = next((e for e in rows if e.get("event") == "generation.trajectory.crashed"), {})
    status = (run / "STATUS").read_text(encoding="utf-8").strip() if (run / "STATUS").is_file() else "?"
    first80 = ""
    chunks = run / "data" / "chunks.parquet"
    if chunks.is_file():
        import pandas as pd

        frame = pd.read_parquet(chunks)
        if not frame.empty and "text" in frame.columns:
            first80 = str(frame.iloc[0]["text"])[:80].replace("\n", " ")
    tok_s = [e.get("tok_s") for e in gens if e.get("tok_s") is not None]
    fills = [e.get("block_fill_ratio") for e in steps if e.get("block_fill_ratio") is not None]
    stops = [e.get("finish_reason") for e in steps]
    reasoning = sum(int(e.get("reasoning_tokens") or 0) for e in steps)
    return {
        "run_id": run.name,
        "status": status,
        "traj": finished.get("status") or crashed.get("error_type"),
        "architecture": loaded.get("architecture"),
        "loader_class": loaded.get("loader_class"),
        "hf_revision": loaded.get("hf_revision"),
        "quant": loaded.get("quant_config"),
        "load_s": loaded.get("load_s"),
        "peak_vram_mib": loaded.get("peak_vram_mib") or (gens[0].get("peak_vram_mib") if gens else None),
        "tok_s_first": tok_s[0] if tok_s else None,
        "tok_s_median": sorted(tok_s)[len(tok_s) // 2] if tok_s else None,
        "n_gen_events": len(gens),
        "n_steps": len(steps),
        "fill_mean": round(sum(fills) / len(fills), 3) if fills else None,
        "stop_rate": round(sum(1 for s in stops if s and s != "length") / len(stops), 3) if stops else None,
        "reasoning_tokens": reasoning,
        "generated_tokens": finished.get("generated_tokens"),
        "first_80": first80,
        "error": (finished.get("error") or crashed.get("error") or "")[:200],
    }


def main() -> None:
    if not ROOT.is_dir():
        print("no runs/s8")
        return
    for run in sorted(ROOT.iterdir()):
        if not run.is_dir():
            continue
        rec = extract(run)
        print(json.dumps(rec, ensure_ascii=False))


if __name__ == "__main__":
    main()
