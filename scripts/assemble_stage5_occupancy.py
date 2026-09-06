#!/usr/bin/env python3
"""Assemble Stage 5 lock occupancy from S5.1 + reused S2.2 T=0.3 four.

The CLI ``analyze separation`` on the S5.1 embed frame alone is the wrong
F4 number: it would pool the two twin pairs into ``D_between`` and omit
physics/surreal. This script joins the two embed runs, splits domain vs
twin, then writes the occupancy artifacts.

Geometry ``α`` is diagnostic and labelled degenerate. A lock is not a
semantic basin.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import orjson
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D

from semantic_afterlife.analysis.geometry import bootstrap_mean_ci
from semantic_afterlife.analysis.occupancy import (
    DOMAIN_SEED_ORDER,
    TWIN_PAIRS,
    TWIN_SEED_ORDER,
    filter_raw_lock,
    is_raw_lock_trajectory,
    last_band_seed_matrix,
    last_chunk_2d_illustration,
    lock_rate_by_seed,
    require_occupancy_grid,
    split_domain_twin,
)
from semantic_afterlife.analysis.rates import parse_trajectory_id, quarter_diagnostics
from semantic_afterlife.analysis.separation import (
    SeparationParams,
    compute_separation,
    trajectories_from_frame,
)
from semantic_afterlife.analysis.twins import TwinParams, compute_twin_contrast
from semantic_afterlife.config import get_settings
from semantic_afterlife.errors import AnalysisError
from semantic_afterlife.provenance import git_state
from semantic_afterlife.reporting.tables import save_table
from semantic_afterlife.viz.export import FigureMeta, save_matplotlib_figure, save_plotly_figure
from semantic_afterlife.viz.theme import (
    FIGSIZE_DOUBLE,
    FIGSIZE_SQUARE,
    PALETTE,
    ROLE_COLORS,
    SEQUENTIAL,
    apply_seaborn_theme,
    plotly_template,
)

S22_GEN = "s2-mechanism-20260901T071519Z-dfbb173a"
S22_EMBED = "s2-embed-mechanism-20260901T131051Z-55761049"
S51_GEN = "s5-lock-occupancy-20260905T164327Z-6780902f"
S51_EMBED = "s5-embed-lock-occupancy-20260906T030125Z-eab6e484"
S51_DEGENERACY = "s5-degeneracy-20260906T030145Z-deb4c3bd"

EMBEDDINGS = ("bge-m3", "qwen3-embed-8b")
RAW_PREFIX = "or-qwen3-8b__"
# S5.1 generated the eight remaining domains plus both twin pairs.
S51_SEEDS = frozenset((*DOMAIN_SEED_ORDER[2:], *TWIN_SEED_ORDER))


def _git_sha(root: Path) -> str | None:
    return git_state(root).get("sha")


def _require_completed(run_id: str, settings: object) -> Path:
    run = settings.paths.find_run(run_id)
    status = (run.root / "STATUS").read_text(encoding="utf-8").strip()
    if status != "COMPLETED":
        raise SystemExit(f"{run_id} STATUS={status}; refuse to assemble an unfinished run")
    return run


def _load_steps(events_path: Path, *, seeds: set[str] | None = None) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    with events_path.open("rb") as handle:
        for raw in handle:
            if b"generation.step.completed" not in raw:
                continue
            payload = orjson.loads(raw)
            if payload.get("event") != "generation.step.completed":
                continue
            trajectory_id = str(payload["trajectory_id"])
            if not is_raw_lock_trajectory(trajectory_id):
                continue
            parsed = parse_trajectory_id(trajectory_id)
            if seeds is not None and str(parsed["semantic_seed"]) not in seeds:
                continue
            rows.append(
                {
                    "trajectory_id": trajectory_id,
                    "generated_tokens": payload["generated_tokens"],
                    "block_fill_ratio": payload["block_fill_ratio"],
                    "finish_reason": payload.get("finish_reason"),
                    "semantic_seed": parsed["semantic_seed"],
                }
            )
    if not rows:
        raise SystemExit(f"no raw generation.step.completed events in {events_path}")
    return pd.DataFrame(rows)


def _load_verdicts(path: Path, *, source: str, gen_run: str) -> pd.DataFrame:
    frame = filter_raw_lock(pd.read_csv(path))
    parsed = pd.DataFrame(frame["trajectory_id"].map(parse_trajectory_id).tolist())
    out = frame.merge(parsed, on="trajectory_id", how="left", suffixes=("", "_parsed"))
    out["source"] = source
    out["generation_run_id"] = gen_run
    return out


def _load_embed(settings: object, run_id: str, slug: str) -> pd.DataFrame:
    path = settings.paths.find_run(run_id).embeddings(slug)
    if not path.is_file():
        raise SystemExit(f"{run_id} missing {path.name}")
    return filter_raw_lock(pd.read_parquet(path))


def protocol_by_quarter(steps: pd.DataFrame, *, seed: int = 0) -> pd.DataFrame:
    per = quarter_diagnostics(steps)
    parsed = per["trajectory_id"].map(parse_trajectory_id)
    per = per.assign(semantic_seed=parsed.map(lambda row: row["semantic_seed"]))
    rows: list[dict[str, object]] = []
    for scope, block_scope in (
        ("s5_scientific_28", per),
        ("s5_1_new_24", per[per["semantic_seed"].isin(S51_SEEDS)]),
        ("domain_20", per[per["semantic_seed"].isin(DOMAIN_SEED_ORDER)]),
    ):
        for quarter, block in block_scope.groupby("quarter", sort=True):
            fill = bootstrap_mean_ci(block["block_fill"].to_numpy(), seed=seed + int(quarter))
            stop = bootstrap_mean_ci(block["stop_rate"].to_numpy(), seed=seed + 30 + int(quarter))
            rows.append(
                {
                    "scope": scope,
                    "quarter": int(quarter),
                    "n_trajectories": int(fill["n"]),
                    "block_fill": fill["mean"],
                    "block_fill_ci_low": fill["ci_low"],
                    "block_fill_ci_high": fill["ci_high"],
                    "stop_rate": stop["mean"],
                    "stop_rate_ci_low": stop["ci_low"],
                    "stop_rate_ci_high": stop["ci_high"],
                }
            )
    return pd.DataFrame(rows)


def protocol_by_seed_quarter(steps: pd.DataFrame, *, seed: int = 0) -> pd.DataFrame:
    per = quarter_diagnostics(steps)
    parsed = per["trajectory_id"].map(parse_trajectory_id)
    per = per.assign(semantic_seed=parsed.map(lambda row: row["semantic_seed"]))
    rows: list[dict[str, object]] = []
    for (seed_name, quarter), block in per.groupby(["semantic_seed", "quarter"], sort=True):
        fill = bootstrap_mean_ci(block["block_fill"].to_numpy(), seed=seed + 100 + int(quarter))
        stop = bootstrap_mean_ci(block["stop_rate"].to_numpy(), seed=seed + 200 + int(quarter))
        rows.append(
            {
                "semantic_seed": str(seed_name),
                "quarter": int(quarter),
                "n_trajectories": int(fill["n"]),
                "block_fill": fill["mean"],
                "block_fill_ci_low": fill["ci_low"],
                "block_fill_ci_high": fill["ci_high"],
                "stop_rate": stop["mean"],
                "stop_rate_ci_low": stop["ci_low"],
                "stop_rate_ci_high": stop["ci_high"],
            }
        )
    return pd.DataFrame(rows)


def _errorbar_panel(
    ax: plt.Axes,
    block: pd.DataFrame,
    *,
    x: str,
    y: str,
    low: str,
    high: str,
    color: str,
    marker: str = "o",
    label: str | None = None,
) -> None:
    xs = block[x].to_numpy()
    ys = block[y].to_numpy()
    yerr = np.vstack([ys - block[low].to_numpy(), block[high].to_numpy() - ys])
    finite = np.isfinite(ys)
    ax.errorbar(
        xs[finite],
        ys[finite],
        yerr=yerr[:, finite],
        fmt=marker,
        color=color,
        capsize=4,
        markersize=7,
        linewidth=1.4,
        label=label,
    )


def looping_figure(
    rates: pd.DataFrame, *, run_ids: list[str], git_sha: str | None
) -> tuple[plt.Figure, pd.DataFrame, FigureMeta]:
    apply_seaborn_theme()
    per_seed = rates[rates["role"].isin(("domain", "twin"))].copy()
    order = [
        s for s in (*DOMAIN_SEED_ORDER, *TWIN_SEED_ORDER) if s in set(per_seed["semantic_seed"])
    ]
    per_seed["semantic_seed"] = pd.Categorical(per_seed["semantic_seed"], order, ordered=True)
    per_seed = per_seed.sort_values("semantic_seed")
    colors = [PALETTE[0] if role == "domain" else PALETTE[1] for role in per_seed["role"]]
    figure, ax = plt.subplots(figsize=(FIGSIZE_DOUBLE[0], 4.6))
    ax.bar(
        np.arange(len(per_seed)),
        per_seed["fraction"].to_numpy(),
        color=colors,
        width=0.7,
    )
    ax.set_xticks(np.arange(len(per_seed)))
    ax.set_xticklabels(list(per_seed["semantic_seed"].astype(str)), rotation=40, ha="right")
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("degenerate fraction (k/n)")
    for index, row in enumerate(per_seed.itertuples(index=False)):
        ax.text(
            index, float(row.fraction) + 0.04, row.k_over_n, ha="center", va="bottom", fontsize=9
        )
    ax.legend(
        handles=[
            Line2D([0], [0], color=PALETTE[0], lw=8, label="domain seed"),
            Line2D([0], [0], color=PALETTE[1], lw=8, label="twin member"),
        ],
        frameon=False,
        loc="upper right",
    )
    figure.suptitle(
        "Lock occupancy per seed on or-qwen3-8b (P1 raw), W=4096 T=0.3, n=2",
        x=0.01,
        ha="left",
    )
    figure.tight_layout()
    meta = FigureMeta(
        name="looping_rate_per_seed",
        caption=(
            "Degenerate fraction per semantic seed at the S5 lock (or-qwen3-8b, P1 "
            "raw_completion, W=4096, T=0.3). Labels are k/n with n=2 stochastic "
            "replicates. Domain seeds are blue; twin members are vermillion. "
            "Degenerate = looping fraction ≥ 0.5 of post-horizon chunks at the "
            "0.083 3-gram bar, or late-phase shingle Jaccard at the 0.0122 "
            "fixed-point arm. Physics/surreal are reused S2.2 raw cells."
        ),
        run_ids=run_ids,
        git_sha=git_sha,
        limitations=(
            "n=2 is a count, not an uncertainty interval. A 2/2 bar is not CI "
            "[1, 1]. The flag is a surface-form verdict; a lock is not a semantic "
            "basin and not an MSM macrostate. love s1 can sit under the bar and "
            "still remain in the occupancy table."
        ),
        units={"fraction": "degenerate trajectories / 2", "semantic_seed": "seed id"},
    )
    return figure, per_seed.reset_index(drop=True), meta


def matrix_figure(
    tidy: pd.DataFrame,
    *,
    embedding: str,
    run_ids: list[str],
    git_sha: str | None,
) -> tuple[plt.Figure, pd.DataFrame, FigureMeta]:
    apply_seaborn_theme()
    seeds = [s for s in DOMAIN_SEED_ORDER if s in set(tidy["seed_row"])]
    pivot = tidy.pivot_table(
        index="seed_row", columns="seed_col", values="distance", aggfunc="mean"
    ).reindex(index=seeds, columns=seeds)
    figure, ax = plt.subplots(figsize=(FIGSIZE_SQUARE[0] + 2.4, FIGSIZE_SQUARE[1] + 1.2))
    sns.heatmap(
        pivot,
        ax=ax,
        cmap=SEQUENTIAL,
        vmin=0.0,
        vmax=max(0.4, float(np.nanmax(pivot.to_numpy()))),
        square=True,
        cbar_kws={"label": "last-band cosine distance"},
    )
    ax.set_xlabel("semantic seed")
    ax.set_ylabel("semantic seed")
    ax.set_title(f"{embedding} last-band occupancy map")
    figure.tight_layout()
    meta = FigureMeta(
        name=f"last_band_distance_matrix_{embedding.replace('-', '_')}",
        caption=(
            f"Last-band mean cosine-distance matrix among the ten domain seeds in "
            f"{embedding}. Diagonal cells are D_within (same seed, two stochastic "
            f"replicates). Off-diagonal cells are mean last-band between-seed "
            f"distance. Computed in the original embedding space; this is an "
            f"occupancy map, not a cluster count."
        ),
        run_ids=run_ids,
        git_sha=git_sha,
        limitations=(
            "A large off-diagonal distance means two locked trajectories sit apart "
            "in this representation. It does not recover the seed, name a semantic "
            "state, or transfer to another embedding. Twin pairs are excluded so "
            "they cannot shrink D_between."
        ),
        units={"distance": "1 − cosine similarity", "last_band": "turnover band start"},
    )
    return figure, tidy.copy(), meta


def separation_figure(
    per_band: pd.DataFrame, *, run_ids: list[str], git_sha: str | None
) -> tuple[plt.Figure, pd.DataFrame, FigureMeta]:
    apply_seaborn_theme()
    figure, axes = plt.subplots(1, 2, figsize=FIGSIZE_DOUBLE, sharey=True)
    for ax, (slug, block) in zip(axes, per_band.groupby("embedding", sort=True), strict=True):
        block = block.sort_values("band")
        _errorbar_panel(
            ax,
            block,
            x="band",
            y="gap",
            low="gap_ci_low",
            high="gap_ci_high",
            color=PALETTE[0],
            label="gap",
        )
        ax.axhline(0.0, color=ROLE_COLORS["baseline"], ls="--", lw=1.0)
        ax.set_title(str(slug))
        ax.set_xlabel("turnover band start (t/W)")
    axes[0].set_ylabel("D_between − D_within")
    figure.suptitle(
        "Ten-domain seed gap vs turnover on or-qwen3-8b (P1 raw), W=4096 T=0.3",
        x=0.01,
        ha="left",
    )
    figure.tight_layout()
    meta = FigureMeta(
        name="domain_separation_vs_turnover",
        caption=(
            "Domain last-band occupancy contrast: D_between − D_within among the "
            "ten domain seeds of seed_bank_v1, in both embedding spaces, with a "
            "95% trajectory-bootstrap CI. Twin pairs are excluded from this "
            "figure. Physics/surreal are the reused S2.2 raw T=0.3 four."
        ),
        run_ids=run_ids,
        git_sha=git_sha,
        limitations=(
            "A gap whose CI excludes 0 means the seed still shapes the locked "
            "trajectory. It is not recovery of the prompt and not a semantic "
            "basin. Degenerate rows are kept: the lock is the sample."
        ),
        units={"gap": "cosine-distance contrast", "band": "turnover bin start"},
    )
    return figure, per_band.copy(), meta


def twins_figure(
    per_band: pd.DataFrame, *, run_ids: list[str], git_sha: str | None
) -> tuple[plt.Figure, pd.DataFrame, FigureMeta]:
    apply_seaborn_theme()
    families = ["all", "reactor-stable+reactor-unstable", "waterloo-lost+waterloo-won"]
    present = [f for f in families if f in set(per_band["scope"])]
    embeddings = list(EMBEDDINGS)
    figure, axes = plt.subplots(
        len(present), 2, figsize=(FIGSIZE_DOUBLE[0], 3.2 * len(present)), sharex=True, sharey=True
    )
    if len(present) == 1:
        axes = np.array([axes])
    for row, family in enumerate(present):
        for col, slug in enumerate(embeddings):
            ax = axes[row, col]
            block = per_band[
                (per_band["scope"] == family) & (per_band["embedding"] == slug)
            ].sort_values("band")
            if block.empty:
                ax.set_axis_off()
                continue
            _errorbar_panel(
                ax,
                block,
                x="band",
                y="delta",
                low="delta_ci_low",
                high="delta_ci_high",
                color=PALETTE[1],
            )
            ax.axhline(0.0, color=ROLE_COLORS["baseline"], ls="--", lw=1.0)
            if row == 0:
                ax.set_title(slug)
            if col == 0:
                ax.set_ylabel(f"Δ ({family})")
            if row == len(present) - 1:
                ax.set_xlabel("turnover band start (t/W)")
    figure.suptitle(
        "Twin Δ = D_twin_matched − D_control vs turnover, W=4096 T=0.3",
        x=0.01,
        ha="left",
    )
    figure.tight_layout()
    meta = FigureMeta(
        name="twin_delta_vs_turnover",
        caption=(
            "Twin-seed contrast Δ = D_twin_matched − D_control per turnover band, "
            "for the pooled twins and for each family, in both embedding spaces, "
            "with a 95% trajectory-bootstrap CI. Divergent iff the last-band CI "
            "excludes 0 from above; otherwise collapsed. Not a metastable-state "
            "label."
        ),
        run_ids=run_ids,
        git_sha=git_sha,
        limitations=(
            "Each family has n=4 trajectories. A CI that includes 0 is a collapse "
            "verdict, including a negative Δ. Crossed twin pairs (different "
            "stochastic seeds) are excluded from both sides of Δ."
        ),
        units={"delta": "cosine-distance contrast", "band": "turnover bin start"},
    )
    return figure, per_band.copy(), meta


def pca_figure(
    coords: pd.DataFrame,
    *,
    embedding: str,
    run_ids: list[str],
    git_sha: str | None,
) -> tuple[plt.Figure, pd.DataFrame, FigureMeta]:
    apply_seaborn_theme()
    figure, ax = plt.subplots(figsize=FIGSIZE_SQUARE)
    domain = coords[coords["semantic_seed"].isin(DOMAIN_SEED_ORDER)]
    for index, seed in enumerate(DOMAIN_SEED_ORDER):
        block = domain[domain["semantic_seed"] == seed]
        if block.empty:
            continue
        ax.scatter(
            block["pc1"],
            block["pc2"],
            color=PALETTE[index % len(PALETTE)],
            s=42,
            label=seed,
        )
    ax.set_xlabel("PCA component 1 of last-chunk embedding (illustration)")
    ax.set_ylabel("PCA component 2 of last-chunk embedding (illustration)")
    ax.legend(frameon=False, fontsize=8, loc="best")
    figure.suptitle(f"{embedding} last-chunk PCA — illustration only", x=0.01, ha="left")
    figure.tight_layout()
    meta = FigureMeta(
        name=f"last_chunk_pca_illustration_{embedding.replace('-', '_')}",
        caption=(
            f"Two-dimensional PCA of last-chunk embeddings for the ten domain "
            f"seeds in {embedding}. Illustration only. Statistical claims, "
            f"including the last-band gap, are taken from the original "
            f"high-dimensional space."
        ),
        run_ids=run_ids,
        git_sha=git_sha,
        limitations=(
            "A 2-D projection is not a cluster count and is not evidence of a "
            "semantic basin. Distances in this plane are not the cosine "
            "distances used for F4."
        ),
        units={"pc1": "illustration axis", "pc2": "illustration axis"},
    )
    return figure, coords.copy(), meta


def _plotly_matrix(tidy: pd.DataFrame, *, embedding: str, run_ids: list[str], git_sha: str | None):
    import plotly.graph_objects as go

    seeds = [s for s in DOMAIN_SEED_ORDER if s in set(tidy["seed_row"])]
    pivot = tidy.pivot_table(
        index="seed_row", columns="seed_col", values="distance", aggfunc="mean"
    ).reindex(index=seeds, columns=seeds)
    figure = go.Figure(
        data=go.Heatmap(
            z=pivot.to_numpy(),
            x=list(pivot.columns),
            y=list(pivot.index),
            colorscale=SEQUENTIAL,
            colorbar={"title": "cosine distance"},
        )
    )
    figure.update_layout(
        template=plotly_template(),
        title=f"{embedding} last-band occupancy map (interactive companion)",
        xaxis_title="semantic seed",
        yaxis_title="semantic seed",
        yaxis_autorange="reversed",
    )
    meta = FigureMeta(
        name=f"last_band_distance_matrix_{embedding.replace('-', '_')}_interactive",
        caption=(
            f"Interactive companion to the {embedding} last-band domain occupancy "
            "matrix. Same tidy source as the print heatmap."
        ),
        run_ids=run_ids,
        git_sha=git_sha,
        limitations=(
            "Illustration of the same numbers as the print matrix. Do not read a "
            "cluster count from the interactive layout."
        ),
    )
    return figure, tidy.copy(), meta


def late_quotes(chunks: pd.DataFrame, trajectory_ids: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for trajectory_id in trajectory_ids:
        block = chunks[chunks["trajectory_id"] == trajectory_id].sort_values("chunk_index")
        if block.empty:
            continue
        last = block.iloc[-1]
        text = str(last["text"])
        rows.append(
            {
                "trajectory_id": trajectory_id,
                "semantic_seed": parse_trajectory_id(trajectory_id)["semantic_seed"],
                "chunk_index": int(last["chunk_index"]),
                "turnover": float(last["turnover"]),
                "n_chars": len(text),
                "text_head": text[:1600],
            }
        )
    if not rows:
        raise AnalysisError("no late chunks found for the requested quotes")
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--s51-embed", default=S51_EMBED)
    parser.add_argument("--s51-gen", default=S51_GEN)
    parser.add_argument("--s22-embed", default=S22_EMBED)
    parser.add_argument("--s22-gen", default=S22_GEN)
    parser.add_argument(
        "--s51-degeneracy",
        default="artifacts/stage-5/degeneracy/degeneracy_verdicts.csv",
    )
    parser.add_argument(
        "--s22-degeneracy",
        default="artifacts/stage-2/mechanism/degeneracy/degeneracy_verdicts.csv",
    )
    args = parser.parse_args()

    settings = get_settings()
    root = settings.paths.root
    git_sha = _git_sha(root)
    out_dir = settings.paths.stage_artifacts("s5") / "occupancy"
    out_dir.mkdir(parents=True, exist_ok=True)

    _require_completed(args.s51_gen, settings)
    _require_completed(args.s51_embed, settings)
    _require_completed(args.s22_gen, settings)
    _require_completed(args.s22_embed, settings)

    s51_deg = _load_verdicts(root / args.s51_degeneracy, source="s5.1", gen_run=args.s51_gen)
    s22_deg = _load_verdicts(root / args.s22_degeneracy, source="s2.2", gen_run=args.s22_gen)
    s22_deg = s22_deg[s22_deg["semantic_seed"].isin(("physics", "surreal"))].copy()
    verdicts = pd.concat([s51_deg, s22_deg], ignore_index=True)
    domain_v, twin_v = split_domain_twin(verdicts)
    require_occupancy_grid(domain_v, twin_v)
    rates = lock_rate_by_seed(verdicts)

    sep_rows: list[pd.DataFrame] = []
    twin_rows: list[pd.DataFrame] = []
    domain_last_rows: list[pd.DataFrame] = []
    twin_last_rows: list[pd.DataFrame] = []
    matrix_rows: list[pd.DataFrame] = []
    for slug in EMBEDDINGS:
        s51 = _load_embed(settings, args.s51_embed, slug)
        s22 = _load_embed(settings, args.s22_embed, slug)
        s22 = s22[s22["semantic_seed"].isin(("physics", "surreal"))].copy()
        joined = pd.concat([s51, s22], ignore_index=True)
        domain, twin = split_domain_twin(joined)
        require_occupancy_grid(domain, twin)

        domain_traj = trajectories_from_frame(domain)
        twin_traj = trajectories_from_frame(twin)
        sep = compute_separation(domain_traj, params=SeparationParams())
        twins = compute_twin_contrast(twin_traj, twin_pairs=list(TWIN_PAIRS), params=TwinParams())
        matrix = last_band_seed_matrix(domain_traj).assign(embedding=slug)

        sep.per_band = sep.per_band.assign(embedding=slug)
        twins.per_band = twins.per_band.assign(embedding=slug)
        last = sep.per_band.sort_values("band").iloc[-1]
        domain_last_rows.append(
            pd.DataFrame(
                [
                    {
                        "embedding": slug,
                        "scope": "domain_10",
                        "n_trajectories": int(sep.scalars["n_trajectories"]),
                        "last_band": float(last["band"]),
                        "d_within": float(last["d_within"]),
                        "d_between": float(last["d_between"]),
                        "gap": float(last["gap"]),
                        "gap_ci_low": float(last["gap_ci_low"]),
                        "gap_ci_high": float(last["gap_ci_high"]),
                        "separated": bool(last["separated"]),
                    }
                ]
            )
        )
        last_scopes = twins.per_band.loc[twins.per_band.groupby("scope")["band"].idxmax()]
        last_scopes = last_scopes[
            last_scopes["scope"].eq("all")
            | last_scopes["scope"].astype(str).str.contains("+", regex=False)
        ]
        twin_last_rows.append(last_scopes.assign(embedding=slug))
        sep_rows.append(sep.per_band)
        twin_rows.append(twins.per_band)
        matrix_rows.append(matrix)
        pca = last_chunk_2d_illustration(domain).assign(embedding=slug)

        figure, tidy, meta = matrix_figure(
            matrix, embedding=slug, run_ids=[args.s51_embed, args.s22_embed], git_sha=git_sha
        )
        save_matplotlib_figure(figure, out_dir, meta, data=tidy)
        plt.close(figure)
        figure, tidy, meta = _plotly_matrix(
            matrix, embedding=slug, run_ids=[args.s51_embed, args.s22_embed], git_sha=git_sha
        )
        save_plotly_figure(figure, out_dir, meta, data=tidy)
        figure, tidy, meta = pca_figure(
            pca,
            embedding=slug,
            run_ids=[args.s51_embed, args.s22_embed],
            git_sha=git_sha,
        )
        save_matplotlib_figure(figure, out_dir, meta, data=tidy)
        plt.close(figure)

    sep_all = pd.concat(sep_rows, ignore_index=True)
    twin_all = pd.concat(twin_rows, ignore_index=True)
    last_band = pd.concat(domain_last_rows, ignore_index=True)
    twin_last_all = pd.concat(twin_last_rows, ignore_index=True)
    matrix_tidy = pd.concat(matrix_rows, ignore_index=True)

    s51_steps = _load_steps(settings.paths.find_run(args.s51_gen).events)
    s22_steps = _load_steps(
        settings.paths.find_run(args.s22_gen).events, seeds={"physics", "surreal"}
    )
    steps = pd.concat([s51_steps, s22_steps], ignore_index=True)
    protocol = protocol_by_quarter(steps)
    protocol_seed = protocol_by_seed_quarter(steps)

    quote_ids = [
        "or-qwen3-8b__W4096__T0p3__finance__s1",
        "or-qwen3-8b__W4096__T0p3__philosophy__s1",
        "or-qwen3-8b__W4096__T0p3__noise__s1",
        "or-qwen3-8b__W4096__T0p3__love__s1",
        "or-qwen3-8b__W4096__T0p3__waterloo-lost__s1",
        "or-qwen3-8b__W4096__T0p3__physics__s1",
    ]
    s51_chunks = pd.read_parquet(settings.paths.find_run(args.s51_gen).chunks())
    s22_chunks = pd.read_parquet(settings.paths.find_run(args.s22_gen).chunks())
    chunks = pd.concat([s51_chunks, s22_chunks], ignore_index=True)
    quotes = late_quotes(chunks, quote_ids)

    run_ids = [
        args.s51_gen,
        args.s51_embed,
        S51_DEGENERACY,
        args.s22_gen,
        args.s22_embed,
    ]

    save_table(
        verdicts.sort_values(["source", "semantic_seed", "stochastic_seed"]),
        out_dir,
        FigureMeta(
            name="degeneracy_verdicts_occupancy",
            caption=(
                "Per-trajectory degeneracy verdicts for the 28-cell Stage 5 occupancy "
                "grid (24 new S5.1 + 4 reused S2.2 raw T=0.3 physics/surreal). "
                "Degenerate rows are kept in occupancy and twin tables."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=(
                "Degeneracy is a surface-form measure. A trajectory can be lexically "
                "varied and still semantically static."
            ),
        ),
    )
    save_table(
        rates,
        out_dir,
        FigureMeta(
            name="lock_rate_by_seed",
            caption=(
                "Degenerate count per seed as k/n. Domain overall is 20 trajectories; "
                "domain seed-hit is how many of the ten domain seeds have at least "
                "one degenerate replicate. n=2 CIs are not reported as if they were "
                "uncertainty."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations="n=2 per seed. A 2/2 cell is a count, not CI [1, 1].",
        ),
    )
    save_table(
        sep_all,
        out_dir,
        FigureMeta(
            name="domain_separation_per_band",
            caption=(
                "Ten-domain D_between − D_within per turnover band, both embedding "
                "spaces. Twin pairs are excluded."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations="The lock is the sample; degenerate rows are kept.",
        ),
    )
    save_table(
        last_band,
        out_dir,
        FigureMeta(
            name="domain_separation_last_band",
            caption=(
                "F4 last-band gap on the ten domain seeds, both spaces, with a 95% "
                "trajectory-bootstrap CI. Separated iff the CI excludes 0 from above."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=(
                "A positive gap is distinguishable locks, not a recovered semantic "
                "state. One-space agreement is not a result."
            ),
        ),
    )
    save_table(
        twin_all,
        out_dir,
        FigureMeta(
            name="twin_per_band",
            caption=(
                "F6 twin contrast per turnover band. scope=all is the pooled twins; "
                "family scopes are waterloo and reactor. Δ = D_twin_matched − D_control."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations="Divergent iff last-band CI excludes 0 from above; else collapsed.",
        ),
    )
    save_table(
        twin_last_all,
        out_dir,
        FigureMeta(
            name="twin_last_band",
            caption=(
                "F6 last-band twin Δ per family and pooled, both embedding spaces. "
                "divergent is the F6 verdict."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations="n=4 trajectories per family. Not an MSM macrostate.",
        ),
    )
    save_table(
        matrix_tidy,
        out_dir,
        FigureMeta(
            name="last_band_distance_matrix",
            caption=(
                "Tidy last-band 10×10 cosine-distance matrix among domain seeds, "
                "both spaces. Diagonal = D_within."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations="Occupancy map in the original space. Not a cluster count.",
        ),
    )
    save_table(
        protocol,
        out_dir,
        FigureMeta(
            name="protocol_by_quarter",
            caption=(
                "Block fill and stop rate by quarter for the S5 lock. Scopes: "
                "s5_scientific_28 (10 domains + 2 twin pairs), s5_1_new_24 "
                "(generated this stage), domain_20 (F4 sample). Quarters are even "
                "step bins."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations="A run-level mean is not the Q7 object; use quarter 4.",
        ),
    )
    save_table(
        protocol_seed,
        out_dir,
        FigureMeta(
            name="protocol_by_seed_quarter",
            caption=(
                "Block fill and stop rate by seed and quarter at W=4096 T=0.3. "
                "n=2 per seed. Fill is seed-heterogeneous on this lock."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations="n=2. Do not retune sampling because a twin filled poorly.",
        ),
    )
    geom_frames: list[pd.DataFrame] = []
    for slug in EMBEDDINGS:
        s51_geom = root / f"artifacts/stage-5/geometry-{slug}/geometry_scalars.csv"
        s22_geom = root / f"artifacts/stage-2/mechanism/geometry-{slug}/geometry_scalars.csv"
        if s51_geom.is_file():
            geom_frames.append(
                filter_raw_lock(pd.read_csv(s51_geom)).assign(source="s5.1", embedding=slug)
            )
        if s22_geom.is_file():
            reused = filter_raw_lock(pd.read_csv(s22_geom))
            reused = reused[reused["semantic_seed"].isin(("physics", "surreal"))].copy()
            geom_frames.append(reused.assign(source="s2.2", embedding=slug))
    if geom_frames:
        geometry = pd.concat(geom_frames, ignore_index=True)
        save_table(
            geometry.sort_values(["embedding", "source", "semantic_seed", "stochastic_seed"]),
            out_dir,
            FigureMeta(
                name="geometry_scalars_occupancy",
                caption=(
                    "Diagnostic geometry on the 28-cell occupancy grid, both spaces. "
                    "α on a degenerate row measures repetition, not diffusion. "
                    "Physics/surreal scalars are the reused S2.2 raw T=0.3 four."
                ),
                run_ids=run_ids,
                git_sha=git_sha,
                limitations=(
                    "A lock is not a semantic basin. Do not headline α or n_macro. "
                    "Every row carries its degeneracy verdict."
                ),
            ),
        )

    save_table(
        quotes,
        out_dir,
        FigureMeta(
            name="late_chunk_quotes",
            caption=(
                "Last-chunk text heads from three domain seeds, the non-degenerate "
                "love s1 row, one twin member, and reused physics s1. Used for Q8 "
                "register scoring."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations="Heads are truncated to 1600 characters. Read the raw chunk for the rest.",
        ),
    )

    figure, tidy, meta = looping_figure(rates, run_ids=run_ids, git_sha=git_sha)
    save_matplotlib_figure(figure, out_dir, meta, data=tidy)
    plt.close(figure)

    figure, tidy, meta = separation_figure(sep_all, run_ids=run_ids, git_sha=git_sha)
    save_matplotlib_figure(figure, out_dir, meta, data=tidy)
    plt.close(figure)

    figure, tidy, meta = twins_figure(twin_all, run_ids=run_ids, git_sha=git_sha)
    save_matplotlib_figure(figure, out_dir, meta, data=tidy)
    plt.close(figure)

    print(f"wrote {out_dir}")
    print(rates.to_string(index=False))
    print(last_band.to_string(index=False))
    print(twin_last_all.to_string(index=False))
    q4 = protocol[protocol["quarter"] == 4]
    print(q4.to_string(index=False))


if __name__ == "__main__":
    main()
