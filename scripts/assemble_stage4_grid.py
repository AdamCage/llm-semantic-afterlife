#!/usr/bin/env python3
"""Assemble the Stage 4 (W, T) grid from S2.2 raw + S4.1 + S4.2.

The CLI analysis passes write one run at a time and would overwrite the
S4.1 geometry/separation directories. This script joins the three sources
without regenerating anything, then writes the faceted order-parameter
figures the PLAN asks for.

α is reported only on trajectories with degenerate=false. A cell with
n_clean < 2 is marked undefined (F4). Separation is computed inside each
matched (W, T) cell so D_within never pools temperatures.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import orjson
import pandas as pd
from matplotlib.lines import Line2D

from semantic_afterlife.analysis.geometry import bootstrap_mean_ci
from semantic_afterlife.analysis.rates import (
    parse_trajectory_id,
    quarter_diagnostics,
    rate_ci,
)
from semantic_afterlife.analysis.separation import (
    SeparationParams,
    compute_separation,
    trajectories_from_frame,
)
from semantic_afterlife.config import get_settings
from semantic_afterlife.provenance import git_state
from semantic_afterlife.reporting.tables import save_table
from semantic_afterlife.viz.export import FigureMeta, save_matplotlib_figure, save_plotly_figure
from semantic_afterlife.viz.theme import (
    FIGSIZE_DOUBLE,
    PALETTE,
    ROLE_COLORS,
    apply_seaborn_theme,
    plotly_template,
)

S22_GEN = "s2-mechanism-20260901T071519Z-dfbb173a"
S22_EMBED = "s2-embed-mechanism-20260901T131051Z-55761049"
S41_GEN = "s4-w4096-new-temps-20260904T103121Z-589c8eb1"
S41_EMBED = "s4-embed-w4096-new-temps-20260904T120202Z-37e61e58"
S42_GEN = "s4-w8192-20260904T120057Z-ce82ce55"

RAW_PREFIX = "or-qwen3-8b__"
EMBEDDINGS = ("bge-m3", "qwen3-embed-8b")


def _git_sha(root: Path) -> str | None:
    return git_state(root).get("sha")


def _filter_raw(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["trajectory_id"].astype(str).str.startswith(RAW_PREFIX)].copy()


def _with_ids(frame: pd.DataFrame, *, source: str, gen_run: str) -> pd.DataFrame:
    parsed = pd.DataFrame(frame["trajectory_id"].map(parse_trajectory_id).tolist())
    out = frame.merge(parsed, on="trajectory_id", how="left", suffixes=("", "_parsed"))
    for column in ("W", "temperature", "semantic_seed", "stochastic_seed", "generator"):
        parsed_col = f"{column}_parsed"
        if column not in out.columns and parsed_col in out.columns:
            out[column] = out[parsed_col]
        elif parsed_col in out.columns and out[column].isna().any():
            out[column] = out[column].fillna(out[parsed_col])
    out["source"] = source
    out["generation_run_id"] = gen_run
    return out


def _load_verdicts(path: Path, *, source: str, gen_run: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "trajectory_id" not in frame.columns:
        raise SystemExit(f"{path} has no trajectory_id")
    return _with_ids(_filter_raw(frame), source=source, gen_run=gen_run)


def _load_geometry(path: Path, *, source: str, gen_run: str, embedding: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame = _filter_raw(frame)
    keep = [
        c
        for c in (
            "trajectory_id",
            "msd_alpha",
            "msd_alpha_se",
            "msd_r_squared",
            "degenerate",
            "looping_fraction",
            "unproductive_fraction",
            "at_fixed_point",
            "degeneracy_mode",
            "n_chunks_post_horizon",
            "mean_step_displacement",
        )
        if c in frame.columns
    ]
    out = _with_ids(frame[keep].copy(), source=source, gen_run=gen_run)
    out["embedding"] = embedding
    return out


def _load_steps(events_path: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    with events_path.open("rb") as handle:
        for raw in handle:
            if b"generation.step.completed" not in raw:
                continue
            payload = orjson.loads(raw)
            if payload.get("event") != "generation.step.completed":
                continue
            trajectory_id = str(payload["trajectory_id"])
            if not trajectory_id.startswith(RAW_PREFIX):
                continue
            rows.append(
                {
                    "trajectory_id": trajectory_id,
                    "generated_tokens": payload["generated_tokens"],
                    "block_fill_ratio": payload["block_fill_ratio"],
                    "finish_reason": payload.get("finish_reason"),
                }
            )
    if not rows:
        raise SystemExit(f"no raw generation.step.completed events in {events_path}")
    return pd.DataFrame(rows)


def looping_rates(verdicts: pd.DataFrame, *, seed: int = 0) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (window, temperature), block in verdicts.groupby(["W", "temperature"], sort=True):
        flags = block["degenerate"].to_numpy(dtype=np.float64)
        stats = rate_ci(flags, seed=seed)
        rows.append(
            {
                "W": int(window),
                "temperature": float(temperature),
                "n": int(stats["n"]),
                "n_degenerate": int(stats["n_positive"]),
                "rate": float(stats["rate"]),
                "ci_low": float(stats["ci_low"]),
                "ci_high": float(stats["ci_high"]),
                "n_clean": int(stats["n"] - stats["n_positive"]),
            }
        )
    return pd.DataFrame(rows)


def clean_alpha_cells(geometry: pd.DataFrame, *, seed: int = 0) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    grouped = geometry.groupby(["embedding", "W", "temperature"], sort=True)
    for (embedding, window, temperature), block in grouped:
        clean = block.loc[~block["degenerate"].astype(bool), "msd_alpha"].to_numpy(dtype=np.float64)
        defined = int(np.isfinite(clean).sum()) >= 2
        if defined:
            stats = bootstrap_mean_ci(clean, seed=seed)
            alpha, low, high = stats["mean"], stats["ci_low"], stats["ci_high"]
        else:
            alpha = low = high = float("nan")
        rows.append(
            {
                "embedding": embedding,
                "W": int(window),
                "temperature": float(temperature),
                "n_traj": int(len(block)),
                "n_clean": int(np.isfinite(clean).sum()),
                "alpha_defined": defined,
                "msd_alpha": alpha,
                "ci_low": low,
                "ci_high": high,
            }
        )
    return pd.DataFrame(rows)


def protocol_cells(steps: pd.DataFrame, *, seed: int = 0) -> pd.DataFrame:
    per = quarter_diagnostics(steps)
    # Map once per row. Merging a repeated parse table on trajectory_id
    # Cartesian-explodes the quarters (4 copies → n=16 for a 4-traj cell)
    # and shrinks the bootstrap CI without adding data.
    parsed = per["trajectory_id"].map(parse_trajectory_id)
    per = per.assign(
        W=parsed.map(lambda row: row["W"]),
        temperature=parsed.map(lambda row: row["temperature"]),
    )
    rows: list[dict[str, object]] = []
    for keys, block in per.groupby(["W", "temperature", "quarter"], sort=True):
        window, temperature, quarter = keys
        fill = bootstrap_mean_ci(block["block_fill"].to_numpy(), seed=seed + int(quarter))
        stop = bootstrap_mean_ci(block["stop_rate"].to_numpy(), seed=seed + 30 + int(quarter))
        rows.append(
            {
                "W": int(window),
                "temperature": float(temperature),
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


def separation_cells(
    settings: object,
    embed_runs: dict[str, str],
    *,
    params: SeparationParams | None = None,
) -> pd.DataFrame:
    params = params or SeparationParams()
    rows: list[dict[str, object]] = []
    for source, run_id in embed_runs.items():
        run = settings.paths.find_run(run_id)
        for slug in EMBEDDINGS:
            path = run.embeddings(slug)
            if not path.is_file():
                raise SystemExit(f"{run_id} missing {path.name}")
            frame = _filter_raw(pd.read_parquet(path))
            frame = _with_ids(frame, source=source, gen_run=run_id)
            for (window, temperature), block in frame.groupby(["W", "temperature"], sort=True):
                trajectories = trajectories_from_frame(block)
                result = compute_separation(trajectories, params=params)
                last = result.per_band.sort_values("band").iloc[-1]
                rows.append(
                    {
                        "source": source,
                        "embed_run_id": run_id,
                        "embedding": slug,
                        "W": int(window),
                        "temperature": float(temperature),
                        "n_trajectories": int(result.scalars["n_trajectories"]),
                        "last_band": float(last["band"]),
                        "d_within": float(last["d_within"]),
                        "d_between": float(last["d_between"]),
                        "gap": float(last["gap"]),
                        "gap_ci_low": float(last["gap_ci_low"]),
                        "gap_ci_high": float(last["gap_ci_high"]),
                        "separated": bool(last["separated"]),
                        "n_within_pairs": int(last["n_within_pairs"]),
                        "n_between_pairs": int(last["n_between_pairs"]),
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
    figure, axes = plt.subplots(1, 2, figsize=FIGSIZE_DOUBLE, sharey=True)
    for ax, (window, block) in zip(axes, rates.groupby("W", sort=True), strict=True):
        block = block.sort_values("temperature")
        _errorbar_panel(
            ax,
            block,
            x="temperature",
            y="rate",
            low="ci_low",
            high="ci_high",
            color=PALETTE[0],
        )
        ax.set_title(f"W = {int(window)}")
        ax.set_xlabel("temperature")
        ax.set_ylim(-0.05, 1.05)
        ax.set_xticks(sorted(block["temperature"].unique()))
    axes[0].set_ylabel("degenerate fraction")
    figure.suptitle(
        "Looping / fixed-point rate on or-qwen3-8b (P1 raw), n = 4 per cell",
        x=0.01,
        ha="left",
    )
    figure.tight_layout()
    meta = FigureMeta(
        name="looping_rate_vs_T",
        caption=(
            "Degenerate fraction per (W, T) cell on or-qwen3-8b under P1 raw_completion, "
            "with a 95% trajectory-bootstrap CI (n = 4). Degenerate = calibrated looping "
            "fraction ≥ 0.5 or late-phase shingle Jaccard at a fixed point (threshold 0.0122). "
            "W=4096 T∈{0.3,1.0} are the reused S2.2 raw eight; they were not regenerated."
        ),
        run_ids=run_ids,
        git_sha=git_sha,
        limitations=(
            "n = 4 makes every interval wide by construction; a cell whose CI includes 0.5 "
            "does not decide a direction. The flag is a surface-form verdict, not a semantic "
            "state. One S4.1 T=0.7 physics replicate is degenerate via the fixed-point arm "
            "at looping_fraction 0.0465 — below the 0.083 per-chunk loop threshold."
        ),
        units={"rate": "proportion of trajectories", "temperature": "sampling temperature"},
    )
    return figure, rates.copy(), meta


def clean_alpha_figure(
    cells: pd.DataFrame, *, run_ids: list[str], git_sha: str | None
) -> tuple[plt.Figure, pd.DataFrame, FigureMeta]:
    apply_seaborn_theme()
    embeddings = list(EMBEDDINGS)
    figure, axes = plt.subplots(1, 2, figsize=FIGSIZE_DOUBLE, sharey=True)
    windows = sorted(cells["W"].unique())
    window_colors = {windows[i]: PALETTE[i] for i in range(len(windows))}
    for ax, slug in zip(axes, embeddings, strict=True):
        for window in windows:
            block = cells[(cells["embedding"] == slug) & (cells["W"] == window)].sort_values(
                "temperature"
            )
            defined = block[block["alpha_defined"]]
            undefined = block[~block["alpha_defined"]]
            if not defined.empty:
                _errorbar_panel(
                    ax,
                    defined,
                    x="temperature",
                    y="msd_alpha",
                    low="ci_low",
                    high="ci_high",
                    color=window_colors[window],
                    label=f"W={int(window)}",
                )
            if not undefined.empty:
                ax.scatter(
                    undefined["temperature"],
                    np.full(len(undefined), -0.02),
                    marker="x",
                    s=60,
                    color=window_colors[window],
                    label=f"W={int(window)} undefined",
                )
        ax.axhline(1.0, color=ROLE_COLORS["baseline"], ls="--", lw=1.0)
        ax.set_title(slug)
        ax.set_xlabel("temperature")
        ax.set_xticks(sorted(cells["temperature"].unique()))
    axes[0].set_ylabel("clean-subset MSD α")
    axes[0].legend(frameon=False, loc="upper left")
    figure.suptitle(
        "MSD α on non-degenerate trajectories only; × = n_clean < 2 (undefined)",
        x=0.01,
        ha="left",
    )
    figure.tight_layout()
    meta = FigureMeta(
        name="clean_alpha_vs_T",
        caption=(
            "Mean fitted MSD exponent α on the non-degenerate subset of each (W, T) cell, "
            "separately in bge-m3 and qwen3-embed-8b, with a 95% trajectory-bootstrap CI. "
            "A cell with n_clean < 2 is marked undefined (×) and is not an α estimate. "
            "The dashed line is free diffusion (α = 1). Degenerate trajectories are excluded "
            "because their exponent measures repetition, not semantic motion."
        ),
        run_ids=run_ids,
        git_sha=git_sha,
        limitations=(
            "Exponents are fitted over a lag range bounded by the observed turnover count "
            "and cannot establish asymptotic behaviour. Cross-W comparison is at matched "
            "turnover, not matched token count. A one-space result is not a result."
        ),
        units={"msd_alpha": "MSD log-log slope", "temperature": "sampling temperature"},
    )
    return figure, cells.copy(), meta


def protocol_figure(
    cells: pd.DataFrame, *, run_ids: list[str], git_sha: str | None
) -> tuple[plt.Figure, pd.DataFrame, FigureMeta]:
    apply_seaborn_theme()
    temperatures = sorted(cells["temperature"].unique())
    temp_colors = {t: PALETTE[i % len(PALETTE)] for i, t in enumerate(temperatures)}
    figure, axes = plt.subplots(2, 2, figsize=(FIGSIZE_DOUBLE[0], FIGSIZE_DOUBLE[1] * 1.55))
    for col, (window, block_w) in enumerate(cells.groupby("W", sort=True)):
        for row, (metric, low, high, ylabel) in enumerate(
            (
                ("block_fill", "block_fill_ci_low", "block_fill_ci_high", "block fill"),
                ("stop_rate", "stop_rate_ci_low", "stop_rate_ci_high", "stop rate"),
            )
        ):
            ax = axes[row, col]
            for temperature, block in block_w.groupby("temperature", sort=True):
                piece = block.sort_values("quarter")
                renamed = piece.rename(columns={metric: "y", low: "lo", high: "hi"})
                _errorbar_panel(
                    ax,
                    renamed,
                    x="quarter",
                    y="y",
                    low="lo",
                    high="hi",
                    color=temp_colors[float(temperature)],
                    marker="o",
                    label=f"T={temperature:g}",
                )
            ax.set_title(f"W = {int(window)} · {ylabel}")
            ax.set_xlabel("quarter of the run")
            ax.set_ylim(-0.05, 1.05)
            ax.set_xticks([1, 2, 3, 4])
            if col == 0:
                ax.set_ylabel(ylabel)
            if row == 0 and col == 1:
                handles = [
                    Line2D([0], [0], color=temp_colors[t], marker="o", label=f"T={t:g}")
                    for t in temperatures
                ]
                ax.legend(handles=handles, frameon=False, loc="best")
    figure.suptitle(
        "Block fill and stop-token rate by quarter, faceted by W, coloured by T",
        x=0.01,
        ha="left",
    )
    figure.tight_layout()
    meta = FigureMeta(
        name="protocol_by_quarter_vs_T",
        caption=(
            "Block fill (completion tokens / 1024) and stop-token rate by quarter of each "
            "trajectory, then the mean across the four trajectories of a (W, T) cell with a "
            "95% trajectory-bootstrap CI. Quarters are even bins over steps, not tokens. "
            "W=4096 T∈{0.3,1.0} reuse S2.2 raw; the other cells are new S4 generation."
        ),
        run_ids=run_ids,
        git_sha=git_sha,
        limitations=(
            "A run-level mean is not shown and must not be read off the figure. Fill collapse "
            "at high T raises the step count and therefore input cost; it is a protocol "
            "finding, not a semantic measurement. Drift inside a quarter is hidden."
        ),
        units={
            "block_fill": "completion tokens / requested max_tokens",
            "stop_rate": "fraction of steps with finish_reason ≠ length",
            "quarter": "1–4, equal step counts",
        },
    )
    return figure, cells.copy(), meta


def _plotly_rate(rates: pd.DataFrame, *, run_ids: list[str], git_sha: str | None):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    figure = make_subplots(rows=1, cols=2, subplot_titles=[f"W = {int(w)}" for w in sorted(rates["W"].unique())], shared_yaxes=True)
    for col, (window, block) in enumerate(rates.groupby("W", sort=True), start=1):
        block = block.sort_values("temperature")
        figure.add_trace(
            go.Scatter(
                x=block["temperature"],
                y=block["rate"],
                mode="markers",
                error_y={
                    "type": "data",
                    "symmetric": False,
                    "array": block["ci_high"] - block["rate"],
                    "arrayminus": block["rate"] - block["ci_low"],
                },
                marker={"color": PALETTE[0], "size": 10},
                name=f"W={int(window)}",
                showlegend=False,
            ),
            row=1,
            col=col,
        )
    figure.update_yaxes(title_text="degenerate fraction", range=[-0.05, 1.05], row=1, col=1)
    figure.update_xaxes(title_text="temperature")
    figure.update_layout(
        template=plotly_template(),
        title="Looping / fixed-point rate on or-qwen3-8b (P1 raw), n = 4 per cell",
    )
    meta = FigureMeta(
        name="looping_rate_vs_T_interactive",
        caption=(
            "Interactive companion to looping_rate_vs_T. Same numbers: degenerate fraction "
            "per (W, T) with a 95% trajectory-bootstrap CI."
        ),
        run_ids=run_ids,
        git_sha=git_sha,
        limitations=(
            "Illustration of the same tidy frame as looping_rate_vs_T. Do not read a "
            "cluster count or a statistical claim from the interactive layout."
        ),
    )
    return figure, rates.copy(), meta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--s42-embed", required=True, help="S4.2 embed run_id")
    parser.add_argument(
        "--s42-degeneracy",
        default="artifacts/stage-4/degeneracy/degeneracy_verdicts.csv",
        help="S4.2 degeneracy CSV written by analyze degeneracy",
    )
    args = parser.parse_args()

    settings = get_settings()
    root = settings.paths.root
    git_sha = _git_sha(root)
    out_dir = settings.paths.stage_artifacts("s4") / "grid"
    out_dir.mkdir(parents=True, exist_ok=True)

    s41_deg = root / "artifacts/stage-4/s41/degeneracy/degeneracy_verdicts.csv"
    s22_deg = root / "artifacts/stage-2/mechanism/degeneracy/degeneracy_verdicts.csv"
    s42_deg = root / args.s42_degeneracy
    for path in (s22_deg, s41_deg, s42_deg):
        if not path.is_file():
            raise SystemExit(f"missing degeneracy table: {path}")

    verdicts = pd.concat(
        [
            _load_verdicts(s22_deg, source="s2.2", gen_run=S22_GEN),
            _load_verdicts(s41_deg, source="s4.1", gen_run=S41_GEN),
            _load_verdicts(s42_deg, source="s4.2", gen_run=S42_GEN),
        ],
        ignore_index=True,
    )
    if len(verdicts) != 32:
        raise SystemExit(f"expected 32 raw trajectories, got {len(verdicts)}")

    geom_frames = []
    geom_sources = (
        (
            "s2.2",
            S22_GEN,
            {
                "bge-m3": root / "artifacts/stage-2/mechanism/geometry-bge-m3/geometry_scalars.csv",
                "qwen3-embed-8b": root
                / "artifacts/stage-2/mechanism/geometry-qwen3-embed-8b/geometry_scalars.csv",
            },
        ),
        (
            "s4.1",
            S41_GEN,
            {
                "bge-m3": root / "artifacts/stage-4/s41/geometry-bge-m3/geometry_scalars.csv",
                "qwen3-embed-8b": root
                / "artifacts/stage-4/s41/geometry-qwen3-embed-8b/geometry_scalars.csv",
            },
        ),
        (
            "s4.2",
            S42_GEN,
            {
                "bge-m3": root / "artifacts/stage-4/geometry-bge-m3/geometry_scalars.csv",
                "qwen3-embed-8b": root
                / "artifacts/stage-4/geometry-qwen3-embed-8b/geometry_scalars.csv",
            },
        ),
    )
    for source, gen_run, paths in geom_sources:
        for slug, path in paths.items():
            if not path.is_file():
                raise SystemExit(f"missing geometry scalars: {path}")
            loaded = _load_geometry(path, source=source, gen_run=gen_run, embedding=slug)
            if source == "s4.2" and set(loaded["W"].unique()) != {8192}:
                raise SystemExit(
                    f"{path} is not the S4.2 (W=8192) table; snapshot S4.1 first "
                    "and run analyze geometry on the S4.2 embed run"
                )
            geom_frames.append(loaded)
    geometry = pd.concat(geom_frames, ignore_index=True)
    if geometry["trajectory_id"].nunique() != 32:
        raise SystemExit(
            f"expected 32 unique trajectories in geometry, got {geometry['trajectory_id'].nunique()}"
        )

    steps = pd.concat(
        [
            _load_steps(settings.paths.find_run(S22_GEN).events),
            _load_steps(settings.paths.find_run(S41_GEN).events),
            _load_steps(settings.paths.find_run(S42_GEN).events),
        ],
        ignore_index=True,
    )

    rates = looping_rates(verdicts)
    alpha = clean_alpha_cells(geometry)
    protocol = protocol_cells(steps)
    sep = separation_cells(
        settings,
        {"s2.2": S22_EMBED, "s4.1": S41_EMBED, "s4.2": args.s42_embed},
    )

    run_ids = [
        S22_GEN,
        S22_EMBED,
        S41_GEN,
        S41_EMBED,
        S42_GEN,
        args.s42_embed,
    ]

    save_table(
        verdicts.sort_values(["W", "temperature", "semantic_seed", "stochastic_seed"]),
        out_dir,
        FigureMeta(
            name="degeneracy_verdicts_grid",
            caption=(
                "Per-trajectory degeneracy verdicts for the 32-cell Stage 4 grid. "
                "S2.2 raw eight (W=4096, T∈{0.3,1.0}) are reused labels, not a new "
                "threshold and not a regenerated generate run."
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
            name="looping_rate_by_cell",
            caption=(
                "Degenerate fraction per (W, T) with a 95% trajectory-bootstrap CI. "
                "n = 4 in every cell."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations="n = 4; an interval that includes 0.5 does not decide a direction.",
        ),
    )
    save_table(
        alpha,
        out_dir,
        FigureMeta(
            name="clean_alpha_by_cell",
            caption=(
                "MSD α on the non-degenerate subset of each (W, T, embedding) cell. "
                "alpha_defined is false when n_clean < 2; those rows are not estimates."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=(
                "An α from a degenerate trajectory is excluded because it measures "
                "repetition. Finite-lag fits cannot establish asymptotic diffusion."
            ),
        ),
    )
    save_table(
        protocol,
        out_dir,
        FigureMeta(
            name="protocol_by_quarter_cell",
            caption=(
                "Block fill and stop rate per (W, T, quarter), mean over the four "
                "trajectories with a 95% trajectory-bootstrap CI."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations="Quarters are even step bins. A run-level mean is not computed.",
        ),
    )
    save_table(
        sep,
        out_dir,
        FigureMeta(
            name="separation_last_band_by_cell",
            caption=(
                "Seed-separation last-band gap per (W, T, embedding). Pairs are formed "
                "only inside a matched (W, T) cell; temperatures are never pooled into "
                "D_within."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=(
                "A positive gap shows the seed still shapes the trajectory; it does not "
                "say the information is recoverable. n = 4 trajectories per cell."
            ),
        ),
    )

    figure, tidy, meta = looping_figure(rates, run_ids=run_ids, git_sha=git_sha)
    save_matplotlib_figure(figure, out_dir, meta, data=tidy)
    plt.close(figure)

    figure, tidy, meta = clean_alpha_figure(alpha, run_ids=run_ids, git_sha=git_sha)
    save_matplotlib_figure(figure, out_dir, meta, data=tidy)
    plt.close(figure)

    figure, tidy, meta = protocol_figure(protocol, run_ids=run_ids, git_sha=git_sha)
    save_matplotlib_figure(figure, out_dir, meta, data=tidy)
    plt.close(figure)

    figure, tidy, meta = _plotly_rate(rates, run_ids=run_ids, git_sha=git_sha)
    save_plotly_figure(figure, out_dir, meta, data=tidy)

    print(f"wrote {out_dir}")
    print(rates.to_string(index=False))
    print(alpha.to_string(index=False))
    print(sep.to_string(index=False))


if __name__ == "__main__":
    main()
