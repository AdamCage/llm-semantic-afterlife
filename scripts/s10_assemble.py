"""Assemble Stage 10 publication artifacts from completed runs.

Does not re-bootstrap G_t. Reads persistence / degeneracy / generate
outputs under runs/s10 and writes self-contained bundles under
artifacts/stage-10/. Do not pool with S9 Qwen.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from semantic_afterlife.analysis.rates import quarter_diagnostics
from semantic_afterlife.config import get_settings
from semantic_afterlife.reporting.tables import save_table
from semantic_afterlife.viz.export import FigureMeta, save_matplotlib_figure, write_index
from semantic_afterlife.viz.figures import persistence_gt_figure
from semantic_afterlife.viz.export import save_plotly_figure
from semantic_afterlife.viz.theme import PALETTE, ROLE_COLORS, apply_seaborn_theme

GENERATE = {
    "base-nf4": "s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3",
    "sft-nf4": "s10-paperb-olmo-sft-nf4-20260917T142201Z-2b7b5b6e",
    "dpo-nf4": "s10-paperb-olmo-dpo-nf4-20260918T000412Z-64ad9f9f",
    "rlvr-nf4": "s10-paperb-olmo-rlvr-nf4-20260918T022536Z-30b5b3fc",
    "base-int8": "s10-paperb-olmo-base-int8-20260918T050048Z-2b2cdfd8",
    "rlvr-int8": "s10-paperb-olmo-rlvr-int8-20260918T142301Z-7125ccca",
}

PLANNED = {
    "base-nf4": 40,
    "sft-nf4": 40,
    "dpo-nf4": 40,
    "rlvr-nf4": 40,
    "base-int8": 10,
    "rlvr-int8": 10,
}

NF4 = ("base-nf4", "sft-nf4", "dpo-nf4", "rlvr-nf4")
EDGES = (("base-nf4", "sft-nf4"), ("sft-nf4", "dpo-nf4"), ("dpo-nf4", "rlvr-nf4"))
F2_SEEDS = ("physics", "biology", "love", "programming", "surreal")


def _git_sha(root: Path) -> str:
    out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True)
    return out.strip()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_embed(persist_dir: Path) -> str:
    cfg = persist_dir / "config.resolved.yaml"
    if cfg.is_file():
        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
        src = data.get("source_run_id")
        if src:
            return str(src)
    man = _read_json(persist_dir / "manifest.json")
    return str(man.get("config_resolved", {}).get("source_run_id") or "")


def _parse_traj(trajectory_id: str) -> dict[str, str]:
    parts = trajectory_id.split("__")
    seed = parts[3] if len(parts) > 3 else ""
    sto = parts[4] if len(parts) > 4 else ""
    return {"seed_id": seed, "stochastic": sto, "model": parts[0]}


def _load_events(run_dir: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    path = run_dir / "events.jsonl"
    if not path.is_file():
        return events
    with path.open("rb") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            try:
                events.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
    return events


def _tail_text(path: Path, n_chars: int = 420) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = text.replace("\r\n", "\n").strip()
    if len(text) <= n_chars:
        return text
    return text[-n_chars:].lstrip()


def _space_from_embed(embed_dir: Path, man: dict[str, Any]) -> str:
    name = embed_dir.name
    cmd = str(man.get("command") or "")
    if "qwen-hosted" in name or "qwen3-embed" in name or "embed-qwen" in name:
        return "qwen3-embed-8b"
    if "embed-bge" in name or "embed-bge" in cmd:
        return "local-bge-m3"
    return "local-bge-m3"


def main() -> None:
    settings = get_settings()
    root = settings.paths.root
    runs = settings.paths.runs / "s10"
    artifacts = settings.paths.stage_artifacts("10")
    git_sha = _git_sha(root)
    for leftover in (
        artifacts / "persistence-local-bge-m3",
        artifacts / "persistence-qwen3-embed-8b",
    ):
        if leftover.is_dir():
            shutil.rmtree(leftover)

    status_rows: list[dict[str, Any]] = []
    for run_dir in sorted(p for p in runs.iterdir() if p.is_dir()):
        man_path = run_dir / "manifest.json"
        status_file = (
            (run_dir / "STATUS").read_text(encoding="utf-8").strip()
            if (run_dir / "STATUS").is_file()
            else ""
        )
        man_status = ""
        if man_path.is_file():
            man_status = str(_read_json(man_path).get("status") or "")
        status_rows.append(
            {
                "run_id": run_dir.name,
                "status_file": status_file,
                "manifest_status": man_status,
                "superseded": (run_dir / "SUPERSEDED").is_file(),
            }
        )
    status_frame = pd.DataFrame(status_rows)

    embed_to_cell: dict[str, str] = {}
    embed_to_generate: dict[str, str] = {}
    embed_to_space: dict[str, str] = {}
    for embed_dir in sorted(runs.glob("s10-embed-*")):
        if (embed_dir / "SUPERSEDED").is_file():
            continue
        man = _read_json(embed_dir / "manifest.json")
        cfg = man.get("config_resolved") or {}
        src = str(cfg.get("source_run_id") or "")
        gen_cell = next((k for k, v in GENERATE.items() if v == src), "")
        space = _space_from_embed(embed_dir, man)
        embed_to_cell[embed_dir.name] = gen_cell
        embed_to_generate[embed_dir.name] = src
        embed_to_space[embed_dir.name] = space

    persist_rows: list[dict[str, Any]] = []
    band_frames: list[pd.DataFrame] = []
    lock_frames: list[pd.DataFrame] = []
    loo_frames: list[pd.DataFrame] = []

    for persist_dir in sorted(runs.glob("s10-persistence-*")):
        if (persist_dir / "SUPERSEDED").is_file():
            continue
        src_embed = _source_embed(persist_dir)
        cell = embed_to_cell.get(src_embed, "")
        space = embed_to_space.get(src_embed, "")
        if "local-bge-m3" in persist_dir.name:
            space = "local-bge-m3"
        elif "qwen3-embed-8b" in persist_dir.name:
            space = "qwen3-embed-8b"
        generate_id = embed_to_generate.get(src_embed, "")
        gt_path = persist_dir / "data" / "persistence_gt.parquet"
        if not gt_path.is_file():
            continue
        gt = pd.read_parquet(gt_path)
        last = gt.iloc[-1]
        locks_path = persist_dir / "data" / "persistence_locks.parquet"
        loo_path = persist_dir / "data" / "persistence_loo.parquet"
        locks = pd.read_parquet(locks_path) if locks_path.is_file() else pd.DataFrame()
        loo = pd.read_parquet(loo_path) if loo_path.is_file() else pd.DataFrame()
        n_lock = int(locks["confirmed_lock"].sum()) if not locks.empty else 0
        n_esc = int(locks["confirmed_escape"].sum()) if not locks.empty else 0
        n_traj = int(len(locks)) if not locks.empty else 0
        last_g = float(last["G"])
        n_within = int(last["n_within_pairs"])
        n_between = int(last["n_between_pairs"])
        identified = n_between > 0 and math.isfinite(last_g)
        if identified:
            sign = "+" if last_g > 0 else ("-" if last_g < 0 else "0")
            ci_excludes_0 = bool(float(last["G_lo"]) > 0 or float(last["G_hi"]) < 0)
        else:
            sign = "unidentified"
            ci_excludes_0 = False
        persist_rows.append(
            {
                "cell": cell,
                "rung": cell.split("-")[0] if cell else "",
                "quant": cell.split("-")[1] if cell else "",
                "embedding": space,
                "last_band_G": last_g,
                "G_lo": float(last["G_lo"]),
                "G_hi": float(last["G_hi"]),
                "sign": sign,
                "identified": identified,
                "ci_excludes_0": ci_excludes_0,
                "n_within_pairs": n_within,
                "n_between_pairs": n_between,
                "n_traj_lock_table": n_traj,
                "n_confirmed_lock": n_lock,
                "n_confirmed_escape": n_esc,
                "lock_rate": (n_lock / n_traj) if n_traj else float("nan"),
                "generate_run_id": generate_id,
                "embed_run_id": src_embed,
                "persistence_run_id": persist_dir.name,
            }
        )
        labeled_gt = gt.copy()
        labeled_gt["cell"] = cell
        labeled_gt["embedding"] = space
        labeled_gt["generate_run_id"] = generate_id
        labeled_gt["embed_run_id"] = src_embed
        labeled_gt["persistence_run_id"] = persist_dir.name
        band_frames.append(labeled_gt)
        if not locks.empty:
            lk = locks.copy()
            lk["cell"] = cell
            lk["embedding"] = space
            lk["generate_run_id"] = generate_id
            lk["embed_run_id"] = src_embed
            lk["persistence_run_id"] = persist_dir.name
            lock_frames.append(lk)
        if not loo.empty:
            lf = loo.copy()
            lf["cell"] = cell
            lf["embedding"] = space
            lf["generate_run_id"] = generate_id
            lf["embed_run_id"] = src_embed
            lf["persistence_run_id"] = persist_dir.name
            loo_frames.append(lf)

        if not cell:
            continue
        cell_dir = artifacts / "persistence" / f"{cell}-{space}"
        if cell_dir.exists():
            shutil.rmtree(cell_dir)
        figure, tidy, meta = persistence_gt_figure(
            gt,
            W=4096,
            embedding=f"{space} / {cell}",
            run_ids=[generate_id, src_embed, persist_dir.name],
        )
        meta.git_sha = git_sha
        save_plotly_figure(figure, cell_dir, meta, data=tidy, static=False)
        save_table(
            gt,
            cell_dir,
            FigureMeta(
                name="persistence_gt_bands",
                caption=(
                    f"G_t = d_between − d_within per integer turnover band in {space}, "
                    f"cell {cell}. CI is seed-cluster bootstrap (ADR-0025), not "
                    "Greenwood on 40 iid traj."
                ),
                run_ids=[generate_id, src_embed, persist_dir.name],
                git_sha=git_sha,
                limitations=(
                    "Positive G_t is seed-conditioned persistence in this space, "
                    "not a semantic state and not an absorbing lock. OLMo only; "
                    "do not pool with S9 Qwen."
                ),
            ),
        )
        if not locks.empty:
            save_table(
                locks,
                cell_dir,
                FigureMeta(
                    name="persistence_locks",
                    caption=(
                        f"Prefix long-lived repetition lock (F1 + N_confirm=3) for {cell} "
                        f"in {space}. Language: confirmed lock / no confirmed escape "
                        "through T. Not an absorbing state."
                    ),
                    run_ids=[generate_id, src_embed, persist_dir.name],
                    git_sha=git_sha,
                    limitations="Hash is diagnostic only and is not in this table.",
                ),
            )
        if not loo.empty:
            save_table(
                loo,
                cell_dir,
                FigureMeta(
                    name="persistence_loo",
                    caption=f"Last-band G_t after dropping one semantic seed ({cell}, {space}).",
                    run_ids=[generate_id, src_embed, persist_dir.name],
                    git_sha=git_sha,
                    limitations="A single held-out seed can flip a marginal last-band sign.",
                ),
            )

    last_band = pd.DataFrame(persist_rows)
    if not last_band.empty:
        last_band = last_band.sort_values(
            ["embedding", "cell", "persistence_run_id"]
        ).drop_duplicates(["cell", "embedding"], keep="last")
        last_band = last_band.sort_values(["embedding", "cell"])
    bands = pd.concat(band_frames, ignore_index=True) if band_frames else pd.DataFrame()
    locks_all = pd.concat(lock_frames, ignore_index=True) if lock_frames else pd.DataFrame()
    loo_all = pd.concat(loo_frames, ignore_index=True) if loo_frames else pd.DataFrame()

    degen_frames: list[pd.DataFrame] = []
    for degen_dir in sorted(runs.glob("s10-degeneracy-*")):
        if (degen_dir / "SUPERSEDED").is_file():
            continue
        man = _read_json(degen_dir / "manifest.json")
        cfg = man.get("config_resolved") or {}
        src = str(cfg.get("source_run_id") or "")
        cell = next((k for k, v in GENERATE.items() if v == src), "")
        parquet = degen_dir / "data" / "degeneracy_verdicts.parquet"
        if not parquet.is_file():
            continue
        frame = pd.read_parquet(parquet)
        frame["cell"] = cell
        frame["generate_run_id"] = src
        frame["degeneracy_run_id"] = degen_dir.name
        degen_frames.append(frame)
    degeneracy = pd.concat(degen_frames, ignore_index=True) if degen_frames else pd.DataFrame()

    failed_rows: list[dict[str, Any]] = []
    proto_rows: list[pd.DataFrame] = []
    step_diag_rows: list[dict[str, Any]] = []
    for cell, run_id in GENERATE.items():
        run_dir = runs / run_id
        events = _load_events(run_dir)
        finished = [e for e in events if e.get("event") == "generation.trajectory.finished"]
        steps = [e for e in events if e.get("event") == "generation.step.completed"]
        last_status: dict[str, dict[str, Any]] = {}
        for ev in finished:
            last_status[str(ev.get("trajectory_id") or "")] = ev
        n_completed = sum(1 for ev in last_status.values() if ev.get("status") == "COMPLETED")
        n_failed = sum(1 for ev in last_status.values() if ev.get("status") != "COMPLETED")
        for ev in last_status.values():
            if ev.get("status") == "COMPLETED":
                continue
            tid = str(ev.get("trajectory_id") or "")
            parsed = _parse_traj(tid)
            failed_rows.append(
                {
                    "cell": cell,
                    "generate_run_id": run_id,
                    "trajectory_id": tid,
                    "seed_id": parsed["seed_id"],
                    "stochastic": parsed["stochastic"],
                    "status": ev.get("status"),
                    "error": str(ev.get("error") or ev.get("reason") or ev.get("detail") or "")[:400],
                    "generated_tokens": ev.get("generated_tokens"),
                }
            )
        if steps:
            step_frame = pd.DataFrame(steps)
            if "generator" not in step_frame.columns:
                step_frame["generator"] = cell
            needed = {"trajectory_id", "generated_tokens", "block_fill_ratio", "finish_reason"}
            if needed <= set(step_frame.columns):
                q = quarter_diagnostics(step_frame)
                q["cell"] = cell
                q["generate_run_id"] = run_id
                proto_rows.append(q)
            reasoning = int(sum(float(e.get("reasoning_tokens") or 0) for e in steps))
            rt_fail = int(sum(1 for e in steps if not e.get("tokenizer_roundtrip_ok", True)))
            providers = sorted({str(e.get("served_provider") or "") for e in steps})
            fills = [float(e["block_fill_ratio"]) for e in steps]
            stops = [e.get("finish_reason") != "length" for e in steps]
            step_diag_rows.append(
                {
                    "cell": cell,
                    "generate_run_id": run_id,
                    "n_planned": PLANNED[cell],
                    "n_unique_trajectories": len(last_status),
                    "n_finished_events": len(finished),
                    "n_completed": n_completed,
                    "n_failed": n_failed,
                    "n_steps": len(steps),
                    "block_fill_mean": float(pd.Series(fills).mean()) if fills else float("nan"),
                    "block_fill_min": float(min(fills)) if fills else float("nan"),
                    "stop_rate": float(sum(stops) / len(stops)) if stops else float("nan"),
                    "reasoning_tokens_sum": reasoning,
                    "roundtrip_failures": rt_fail,
                    "served_providers": ",".join(providers),
                }
            )

    failed = pd.DataFrame(failed_rows)
    protocol_traj = pd.concat(proto_rows, ignore_index=True) if proto_rows else pd.DataFrame()
    generate_status = pd.DataFrame(step_diag_rows)

    protocol_quarter = pd.DataFrame()
    if not protocol_traj.empty:
        protocol_quarter = (
            protocol_traj.groupby(["cell", "generate_run_id", "quarter"], sort=True)
            .agg(
                n_trajectories=("trajectory_id", "nunique"),
                n_steps=("n_steps", "sum"),
                block_fill_mean=("block_fill", "mean"),
                block_fill_min=("block_fill", "min"),
                stop_rate_mean=("stop_rate", "mean"),
            )
            .reset_index()
        )

    seed_lock_rows: list[dict[str, Any]] = []
    if not locks_all.empty:
        bge_locks = locks_all[locks_all["embedding"] == "local-bge-m3"]
        for cell, block in bge_locks.groupby("cell"):
            for seed, sblock in block.groupby("seed_id"):
                seed_lock_rows.append(
                    {
                        "cell": cell,
                        "seed_id": seed,
                        "n_traj": int(len(sblock)),
                        "n_lock": int(sblock["confirmed_lock"].sum()),
                        "n_escape": int(sblock["confirmed_escape"].sum()),
                        "has_lock": bool(sblock["confirmed_lock"].any()),
                    }
                )
    seed_locks = pd.DataFrame(seed_lock_rows)

    edge_rows: list[dict[str, Any]] = []
    if not last_band.empty:
        for space in sorted(set(last_band["embedding"])):
            sub = last_band[(last_band["embedding"] == space) & (last_band["cell"].isin(NF4))]
            by_cell = {str(r["cell"]): r for r in sub.to_dict(orient="records")}
            for left, right in EDGES:
                if left not in by_cell or right not in by_cell:
                    continue
                a = by_cell[left]
                b = by_cell[right]
                edge_rows.append(
                    {
                        "embedding": space,
                        "edge": f"{left}→{right}",
                        "left_cell": left,
                        "right_cell": right,
                        "left_G": a["last_band_G"],
                        "right_G": b["last_band_G"],
                        "left_sign": a["sign"],
                        "right_sign": b["sign"],
                        "sign_flip": bool(
                            a["sign"] in {"+", "-"}
                            and b["sign"] in {"+", "-"}
                            and a["sign"] != b["sign"]
                        ),
                        "left_lock_rate": a["lock_rate"],
                        "right_lock_rate": b["lock_rate"],
                        "left_n_lock": a["n_confirmed_lock"],
                        "right_n_lock": b["n_confirmed_lock"],
                        "left_n_traj": a["n_traj_lock_table"],
                        "right_n_traj": b["n_traj_lock_table"],
                    }
                )
    edges = pd.DataFrame(edge_rows)

    int8_rows: list[dict[str, Any]] = []
    if not last_band.empty:
        for rung in ("base", "rlvr"):
            for space in sorted(set(last_band["embedding"])):
                nf = last_band[
                    (last_band["cell"] == f"{rung}-nf4") & (last_band["embedding"] == space)
                ]
                i8 = last_band[
                    (last_band["cell"] == f"{rung}-int8") & (last_band["embedding"] == space)
                ]
                if nf.empty or i8.empty:
                    continue
                int8_rows.append(
                    {
                        "rung": rung,
                        "embedding": space,
                        "nf4_G": float(nf.iloc[0]["last_band_G"]),
                        "int8_G": float(i8.iloc[0]["last_band_G"]),
                        "nf4_sign": nf.iloc[0]["sign"],
                        "int8_sign": i8.iloc[0]["sign"],
                        "same_sign": nf.iloc[0]["sign"] == i8.iloc[0]["sign"],
                        "nf4_run": nf.iloc[0]["generate_run_id"],
                        "int8_run": i8.iloc[0]["generate_run_id"],
                    }
                )
    int8_vs = pd.DataFrame(int8_rows)

    sample_specs = [
        ("base-nf4", "physics", "s1"),
        ("sft-nf4", "love", "s2"),
        ("dpo-nf4", "finance", "s1"),
        ("rlvr-nf4", "noise", "s1"),
        ("base-int8", "surreal", "s1"),
    ]
    samples: list[dict[str, str]] = []
    for cell, seed, sto in sample_specs:
        run_id = GENERATE[cell]
        tdir = runs / run_id / "data" / "trajectories"
        matches = sorted(tdir.glob(f"*__{seed}__{sto}.text"))
        if not matches:
            matches = sorted(tdir.glob(f"*__{seed}__{sto}*.text"))
        if not matches:
            continue
        samples.append(
            {
                "cell": cell,
                "seed_id": seed,
                "stochastic": sto,
                "path": str(matches[0].relative_to(root)),
                "excerpt": _tail_text(matches[0]),
            }
        )

    all_run_ids = list(GENERATE.values())
    if not last_band.empty:
        all_run_ids.extend(last_band["embed_run_id"].tolist())
        all_run_ids.extend(last_band["persistence_run_id"].tolist())
    if not degeneracy.empty:
        all_run_ids.extend(sorted(set(degeneracy["degeneracy_run_id"])))

    def _meta(
        name: str,
        caption: str,
        limitations: str,
        extra_runs: list[str] | None = None,
    ) -> FigureMeta:
        ids = extra_runs if extra_runs is not None else all_run_ids
        return FigureMeta(
            name=name,
            caption=caption,
            run_ids=[r for r in ids if r],
            git_sha=git_sha,
            limitations=limitations,
        )

    save_table(
        last_band,
        artifacts / "gt_last_band",
        _meta(
            "gt_last_band",
            "Last-band G_t (integer turnover band covering 12W) for every S10 "
            "cell × embedding that produced a persistence run. CI is seed-cluster "
            "bootstrap (ADR-0025). Lock counts use F1 + N_confirm=3.",
            "A positive last-band G_t is seed-conditioned ensemble persistence in "
            "that representation, not semantic-domain memory and not an absorbing "
            "lock. E5 headline is NF4 only. INT8 is concordance (P7). Do not pool "
            "with S9 Qwen. Empty-completion FAILED trajectories are absent from G_t.",
        ),
    )
    if not bands.empty:
        save_table(
            bands,
            artifacts / "gt_bands_all",
            _meta(
                "gt_bands_all",
                "G_t versus integer turnover band for all S10 persistence runs.",
                "Do not pool OLMo with S9 Qwen. Do not read a 2-D projection from this table.",
            ),
        )
    if not locks_all.empty:
        save_table(
            locks_all,
            artifacts / "locks",
            _meta(
                "persistence_locks_all",
                "Per-trajectory prefix lock / escape for S10 cells and both embedding spaces. "
                "Language: long-lived repetition lock / no confirmed escape through T.",
                "The lock is not absorbing. Hash is diagnostic only. Lock uses F1, not a fingerprint.",
            ),
        )
    if not seed_locks.empty:
        save_table(
            seed_locks,
            artifacts / "locks_by_seed",
            _meta(
                "locks_by_seed",
                "Seed-level lock incidence (BGE-M3 lock table; F1 is surface-form).",
                "A seed with no completed descendant cannot lock. Failed empty completions "
                "are excluded here and listed separately.",
            ),
        )
    if not loo_all.empty:
        save_table(
            loo_all,
            artifacts / "loo",
            _meta(
                "persistence_loo_all",
                "Last-band G_t after dropping one semantic seed, all cells × spaces.",
                "A single held-out seed can flip a marginal last-band sign. Small-n rungs have wide CIs.",
            ),
        )
    if not edges.empty:
        save_table(
            edges,
            artifacts / "adjacent_edges",
            _meta(
                "adjacent_edges",
                "Adjacent-edge table on the OLMo NF4 ladder (Base–SFT, SFT–DPO, DPO–RLVR): "
                "last-band G_t sign and completer lock saturation. Not a monotone-ladder test.",
                "E5 headline is last-band sign / lock saturation among completers, not a "
                "pooled OLMo+Qwen contrast. DPO last-band G_t is unidentified "
                "(0 between-seed pairs); that is not a sign flip. DPO/RLVR have few "
                "completers; rates are not Bernoulli-on-40.",
            ),
        )
    if not int8_vs.empty:
        save_table(
            int8_vs,
            artifacts / "int8_vs_nf4",
            _meta(
                "int8_vs_nf4",
                "INT8 vs NF4 last-band G_t sign on Base and RLVR (F2 seeds). Limitations, not a third headline.",
                "RLVR INT8 has 0 completers, so a missing row is recorded attrition, not a silent drop.",
            ),
        )
    if not degeneracy.empty:
        save_table(
            degeneracy,
            artifacts / "degeneracy",
            _meta(
                "degeneracy_verdicts",
                "Per-trajectory F1 degeneracy diagnostics for all six S10 generate runs. "
                "A chunk loops when 3-gram repetition exceeds 0.083 (99th percentile of "
                "natural English at this chunk size).",
                "Degeneracy is a surface-form measure. This table is why G_t is not read "
                "as confinement without a lock label.",
                extra_runs=sorted(
                    set(degeneracy["generate_run_id"]) | set(degeneracy["degeneracy_run_id"])
                ),
            ),
        )
    save_table(
        generate_status,
        artifacts / "generate_status",
        _meta(
            "generate_status",
            "S10 generate completeness and run-level protocol scalars. n_completed is "
            "STATUS=COMPLETED at target_tokens=49152. n_failed are empty-completion "
            "cells kept in the sample (not dropped).",
            "A run-level mean hides drift; use protocol_by_quarter for fill and stop. "
            "Do not pool these rates with S9 Qwen.",
            extra_runs=list(GENERATE.values()),
        ),
    )
    if not failed.empty:
        save_table(
            failed,
            artifacts / "empty_completions",
            _meta(
                "empty_completions",
                "Generate cells that finished FAILED. Kept in the S10 sample; not silently dropped. "
                "This is the second estimand (completion), not unlocks.",
                "Absence from G_t is missing data, not a lock or an escape.",
                extra_runs=list(GENERATE.values()),
            ),
        )
    if not protocol_quarter.empty:
        save_table(
            protocol_quarter,
            artifacts / "protocol_by_quarter",
            _meta(
                "protocol_by_quarter",
                "Block fill and stop rate by trajectory-quarter (four even step bins per "
                "trajectory, then mean across trajectories in the cell). Not a run-level mean.",
                "Fill and stop are P1 order parameters. Quarters are within-trajectory.",
                extra_runs=list(GENERATE.values()),
            ),
        )
    save_table(
        status_frame,
        artifacts / "run_status",
        _meta(
            "run_status",
            "Every directory under runs/s10 and its STATUS / manifest status.",
            "A WARN on the mechanical gate for incomplete sibling runs must be named in REPORT. "
            "The hung RLVR INT8 BGE is SUPERSEDED.",
            extra_runs=status_frame["run_id"].tolist(),
        ),
    )

    if not last_band.empty:
        apply_seaborn_theme()
        import matplotlib.pyplot as plt

        plot = last_band[last_band["identified"]].copy()
        plot["label"] = (
            plot["cell"]
            + " / "
            + plot["embedding"].str.replace("local-", "").str.replace("qwen3-embed-8b", "qwen-embed")
        )
        fig, ax = plt.subplots(figsize=(10.5, 5.2))
        xs = range(len(plot))
        colors = [PALETTE[i % len(PALETTE)] for i in xs]
        yerr = [plot["last_band_G"] - plot["G_lo"], plot["G_hi"] - plot["last_band_G"]]
        ax.bar(list(xs), plot["last_band_G"], yerr=yerr, color=colors, ecolor="#4D4D4D", capsize=4)
        ax.axhline(0.0, color=ROLE_COLORS["baseline"], linestyle="--", linewidth=1.2)
        ax.set_xticks(list(xs), plot["label"].tolist(), rotation=35, ha="right")
        ax.set_ylabel("last-band G_t")
        ax.set_title("S10 last-band G_t, seed-cluster 95% CI (OLMo only)")
        fig.tight_layout()
        save_matplotlib_figure(
            fig,
            artifacts / "gt_last_band_figure",
            FigureMeta(
                name="gt_last_band_figure",
                caption=(
                    "Last-band G_t for S10 persistence cells. Error bars are "
                    "seed-cluster bootstrap 95% intervals (ADR-0025), not Greenwood. "
                    "OLMo ladder only; not pooled with S9 Qwen."
                ),
                run_ids=[r for r in all_run_ids if r],
                git_sha=git_sha,
                alt_text="Bar chart of last-band G_t with confidence intervals for S10 cells.",
                limitations=(
                    "This is not a UMAP cluster count. INT8 bars are concordance. "
                    "DPO last-band G_t is unidentified (0 between-seed pairs) and is "
                    "omitted here; that is missing identification, not a sign of 0. "
                    "RLVR CIs include 0 (small-n). Do not pool with S9 Qwen."
                ),
            ),
            data=last_band,
        )
        plt.close(fig)

        if not bands.empty:
            for space, fname in (
                ("local-bge-m3", "gt_overlay_bge"),
                ("qwen3-embed-8b", "gt_overlay_qwen"),
            ):
                sub = bands[bands["embedding"] == space]
                if sub.empty:
                    continue
                fig, ax = plt.subplots(figsize=(9.5, 5.0))
                for i, (cell, block) in enumerate(sub.groupby("cell")):
                    style = "-" if "nf4" in cell else "--"
                    ax.plot(
                        block["band_mid"],
                        block["G"],
                        style,
                        color=PALETTE[i % len(PALETTE)],
                        label=cell,
                        linewidth=2.0,
                    )
                    ax.fill_between(
                        block["band_mid"],
                        block["G_lo"],
                        block["G_hi"],
                        color=PALETTE[i % len(PALETTE)],
                        alpha=0.12,
                    )
                ax.axhline(0.0, color=ROLE_COLORS["baseline"], linestyle="--", linewidth=1.0)
                ax.axvline(1.0, color=ROLE_COLORS["horizon"], linewidth=1.4)
                ax.set_xlabel("window turnovers t/W")
                ax.set_ylabel("G_t = d_between − d_within")
                ax.set_title(f"G_t vs turnover — {space} (OLMo)")
                ax.legend(frameon=False)
                fig.tight_layout()
                save_matplotlib_figure(
                    fig,
                    artifacts / fname,
                    FigureMeta(
                        name=fname,
                        caption=(
                            f"G_t versus turnover in {space} for S10 cells. "
                            "Shaded bands are seed-cluster 95% CIs. Vertical line is t/W = 1. "
                            "Solid = NF4, dashed = INT8. OLMo only."
                        ),
                        run_ids=[r for r in all_run_ids if r],
                        git_sha=git_sha,
                        alt_text=f"G_t versus turnover overlay in {space}.",
                        limitations=(
                            "Illustration of gt_bands_all. Do not read cluster counts. "
                            "Do not pool with S9 Qwen."
                        ),
                    ),
                    data=sub,
                )
                plt.close(fig)

    write_index(artifacts, stage="10", title="Stage 10 artifacts")

    summary = {
        "git_sha": git_sha,
        "last_band": last_band.to_dict(orient="records") if not last_band.empty else [],
        "generate_status": generate_status.to_dict(orient="records"),
        "failed": failed.to_dict(orient="records") if not failed.empty else [],
        "protocol_quarter": protocol_quarter.to_dict(orient="records")
        if not protocol_quarter.empty
        else [],
        "seed_locks": seed_locks.to_dict(orient="records") if not seed_locks.empty else [],
        "edges": edges.to_dict(orient="records") if not edges.empty else [],
        "int8_vs_nf4": int8_vs.to_dict(orient="records") if not int8_vs.empty else [],
        "samples": samples,
        "incomplete_runs": status_frame.loc[
            (status_frame["manifest_status"] != "COMPLETED") & (~status_frame["superseded"]),
            "run_id",
        ].tolist(),
    }
    (artifacts / "_close_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "wrote": str(artifacts),
                "n_last_band": int(len(last_band)),
                "n_failed": int(len(failed)),
                "n_edges": int(len(edges)),
                "n_samples": len(samples),
            },
            indent=2,
        )
    )
    if not last_band.empty:
        print("--- LAST BAND ---")
        print(last_band.to_string(index=False))
    print("--- GENERATE ---")
    print(generate_status.to_string(index=False))
    if not edges.empty:
        print("--- EDGES ---")
        print(edges.to_string(index=False))


if __name__ == "__main__":
    main()
