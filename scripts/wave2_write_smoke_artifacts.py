"""Write artifacts/stage-8/smoke/ tables from completed Wave 2 runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs" / "s8"
OUT = ROOT / "artifacts" / "stage-8" / "smoke"
GIT_SHA = "bc06b36"


def events(run: Path) -> list[dict]:
    path = run / "events.jsonl"
    rows = []
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                rows.append(json.loads(raw))
    return rows


def smoke_row(run_id: str, slug: str, notes: str) -> dict:
    run = RUNS / run_id
    ev = events(run)
    loaded = next((e for e in ev if e.get("event") == "local.model.loaded"), {})
    gen = next((e for e in ev if e.get("event") == "local.generate.completed"), {})
    step = next((e for e in ev if e.get("event") == "generation.step.completed"), {})
    fin = next((e for e in ev if e.get("event") == "generation.trajectory.finished"), {})
    status = (run / "STATUS").read_text(encoding="utf-8").strip() if (run / "STATUS").is_file() else "?"
    return {
        "slug": slug,
        "run_id": run_id,
        "status": status,
        "architecture": loaded.get("architecture"),
        "loader_class": loaded.get("loader_class"),
        "hf_revision": loaded.get("hf_revision"),
        "quant_config": loaded.get("quant_config"),
        "peak_vram_mib": loaded.get("peak_vram_mib") or gen.get("peak_vram_mib"),
        "load_s": loaded.get("load_s"),
        "tok_s": gen.get("tok_s"),
        "generated_tokens": fin.get("generated_tokens") or step.get("generated_tokens"),
        "n_steps": fin.get("n_steps") or (1 if step else 0),
        "block_fill": step.get("block_fill_ratio"),
        "stop_events": fin.get("stop_events"),
        "reasoning_tokens": step.get("reasoning_tokens"),
        "tokenizer_roundtrip_ok": step.get("tokenizer_roundtrip_ok"),
        "served_provider": step.get("served_provider"),
        "notes": notes,
    }


def micro_row(run_id: str, slug: str, notes: str, *, valid: bool) -> dict:
    run = RUNS / run_id
    ev = events(run)
    loaded = next((e for e in ev if e.get("event") == "local.model.loaded"), {})
    gens = [e for e in ev if e.get("event") == "local.generate.completed"]
    steps = [e for e in ev if e.get("event") == "generation.step.completed"]
    fin = next((e for e in ev if e.get("event") == "generation.trajectory.finished"), {})
    tok = [float(e["tok_s"]) for e in gens if e.get("tok_s") is not None]
    lats = [float(e["latency_s"]) for e in steps if e.get("latency_s") is not None]
    fills = [float(e["block_fill_ratio"]) for e in steps if e.get("block_fill_ratio") is not None]
    status = (run / "STATUS").read_text(encoding="utf-8").strip() if (run / "STATUS").is_file() else "?"
    think = sum(int(e.get("reasoning_tokens") or 0) for e in steps)
    rt_fail = sum(1 for e in steps if e.get("tokenizer_roundtrip_ok") is False)
    median_lat = sorted(lats)[len(lats) // 2] if lats else None
    return {
        "slug": slug,
        "run_id": run_id,
        "status": status,
        "valid_for_wallclock": valid,
        "architecture": loaded.get("architecture"),
        "loader_class": loaded.get("loader_class"),
        "hf_revision": loaded.get("hf_revision"),
        "quant_config": loaded.get("quant_config"),
        "peak_vram_mib": max((e.get("peak_vram_mib") or 0) for e in gens) if gens else loaded.get("peak_vram_mib"),
        "tok_s_mean": round(sum(tok) / len(tok), 3) if tok else None,
        "tok_s_median": sorted(tok)[len(tok) // 2] if tok else None,
        "block_fill_mean": round(sum(fills) / len(fills), 4) if fills else None,
        "stop_events": fin.get("stop_events"),
        "reasoning_tokens_sum": think,
        "roundtrip_failures": rt_fail,
        "generated_tokens": fin.get("generated_tokens"),
        "n_steps": len(steps),
        "step_latency_s_median": round(median_lat, 3) if median_lat is not None else None,
        "hours_per_12w_traj_48_steps": round(median_lat * 48 / 3600.0, 3) if median_lat else None,
        "notes": notes,
    }


def write_meta(name: str, caption: str, run_ids: list[str], path: Path) -> None:
    payload = {
        "name": name,
        "caption": caption,
        "alt_text": caption,
        "limitations": (
            "Smoke is T=32 / W=32, not a 12W scientific horizon. "
            "tok/s on smoke includes a tiny decode and is not the S9 operating point. "
            "UMAP is not used. No G_t or lock claim."
        ),
        "run_ids": run_ids,
        "git_sha": GIT_SHA,
        "units": {
            "peak_vram_mib": "MiB allocated peak as reported by torch",
            "tok_s": "new tokens / generate() wall seconds",
            "block_fill": "completion_tokens / requested max_tokens",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    smoke = [
        smoke_row(
            "s8-paperb-smoke-qwen3-8b-base-20260910T200925Z-28827fb7",
            "pb-qwen3-8b-base",
            "first completed smoke; earlier T200741/T200901 failed tokenizer",
        ),
        smoke_row(
            "s8-paperb-smoke-qwen3-8b-instruct-20260910T202114Z-c1a44453",
            "pb-qwen3-8b-instruct",
            "thinking=0 under enable_thinking=false",
        ),
        smoke_row(
            "s8-paperb-smoke-olmo3-7b-base-20260910T203216Z-a08dbea4",
            "pb-olmo3-7b-base",
            "",
        ),
        smoke_row(
            "s8-paperb-smoke-olmo3-7b-sft-20260910T204127Z-e446abc8",
            "pb-olmo3-7b-sft",
            "",
        ),
        smoke_row(
            "s8-paperb-smoke-olmo3-7b-dpo-20260910T205044Z-1d237e73",
            "pb-olmo3-7b-dpo",
            "",
        ),
        smoke_row(
            "s8-paperb-smoke-olmo3-7b-rlvr-20260910T205941Z-2fc2def8",
            "pb-olmo3-7b-rlvr",
            "",
        ),
        smoke_row(
            "s8-paperb-smoke-ministral-8b-base-20260910T215816Z-42f29e6e",
            "pb-ministral-8b-base",
            "retry after Mistral3ForConditionalGeneration loader; T210848 FAILED CausalLM",
        ),
        smoke_row(
            "s8-paperb-smoke-ministral-8b-instruct-20260910T220441Z-1c1fd482",
            "pb-ministral-8b-instruct",
            "retry after loader fix; T210903 FAILED CausalLM; sibling duplicate T220451",
        ),
        smoke_row(
            "s8-paperb-smoke-gemma4-12b-base-20260910T210919Z-2cf3ff6d",
            "pb-gemma4-12b-base",
            "loaded via AutoModelForCausalLM dispatching to Gemma4UnifiedForConditionalGeneration; repetitive Polyakov text",
        ),
        smoke_row(
            "s8-paperb-smoke-gemma4-12b-it-20260910T213805Z-58e90177",
            "pb-gemma4-12b-it",
            "named Gemma4UnifiedForConditionalGeneration; 3 steps; first_80 commas",
        ),
    ]
    smoke_df = pd.DataFrame(smoke)
    smoke_df.to_parquet(OUT / "smoke_10x32.parquet", index=False)
    write_meta(
        "smoke_10x32",
        "Wave 2 NF4 smoke: 32 new tokens × 10 Paper B checkpoints. "
        "Shows load class, Hub revision, peak VRAM, decode tok/s, fill, stop, thinking. "
        "Does not measure G_t, lock, or 12W occupancy.",
        [r["run_id"] for r in smoke],
        OUT / "smoke_10x32.meta.json",
    )

    micro = [
        micro_row(
            "s8-paperb-micro-qwen3-8b-instruct-20260910T221623Z-61c9ad74",
            "pb-qwen3-8b-instruct",
            "exclusive GPU; S9 family head",
            valid=True,
        ),
        micro_row(
            "s8-paperb-micro-ministral-8b-instruct-20260910T233421Z-e528749b",
            "pb-ministral-8b-instruct",
            "exclusive re-run (throwaway cache); T222222 coresident with OLMo, not used",
            valid=True,
        ),
        micro_row(
            "s8-paperb-micro-olmo3-7b-base-20260910T232755Z-e3cc4b7f",
            "pb-olmo3-7b-base",
            "exclusive re-run; T222217 hung after coresidency, killed, not used",
            valid=True,
        ),
        micro_row(
            "s8-paperb-micro-gemma4-12b-it-20260910T233125Z-f89a95a4",
            "pb-gemma4-12b-it",
            "FAILED: 5 consecutive empty completions at W=4096; smoke-only tok/s",
            valid=False,
        ),
    ]
    micro_df = pd.DataFrame(micro)
    micro_df.to_parquet(OUT / "microbench.parquet", index=False)
    write_meta(
        "microbench",
        "Wave 2 microbench: physics × s1 × W=4096 × T=8192 (2 turnovers) × 4 family heads. "
        "Shows exclusive-GPU decode tok/s and step latency for S9–S11 wall-clock. "
        "Does not start the 12W matrix. Gemma IT failed empty-completion and is not a tok/s source.",
        [r["run_id"] for r in micro],
        OUT / "microbench.meta.json",
    )
    print(smoke_df.to_string(index=False))
    print()
    print(micro_df.to_string(index=False))


if __name__ == "__main__":
    main()
