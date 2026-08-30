"""Figure builders for the geometry pass.

Each function returns ``(figure, tidy_data, FigureMeta)`` and performs no I/O, so
that exporting, captioning and testing stay separate concerns. Every time-axis
figure marks the context horizon ``t = W`` and carries a secondary turnover axis,
because absolute token counts are not comparable across ``W``.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns
from plotly.subplots import make_subplots

from .export import FigureMeta
from .theme import (
    FIGSIZE_DOUBLE,
    PALETTE,
    ROLE_COLORS,
    apply_seaborn_theme,
    horizon_annotations,
    horizon_shapes,
    plotly_template,
    turnover_axis,
)


def _ensemble(frame: pd.DataFrame, x: str, y: str) -> pd.DataFrame:
    """Mean and 95% CI across trajectories at each x value.

    The CI is a normal-approximation interval over the *trajectory* mean, which
    is the replicate unit; a chunk-level interval would be far too narrow.
    """
    grouped = frame.groupby(x, dropna=True)[y]
    out = grouped.agg(["mean", "std", "count"]).reset_index()
    se = out["std"] / np.sqrt(out["count"].clip(lower=1))
    out["ci_low"] = out["mean"] - 1.96 * se
    out["ci_high"] = out["mean"] + 1.96 * se
    return out


def _time_axis_layout(
    figure: go.Figure, *, W: int, x_max: float, x_title: str, y_title: str, title: str
) -> None:
    figure.update_layout(
        template=plotly_template(),
        title=title,
        xaxis={"title": x_title, "range": [0, x_max]},
        yaxis={"title": y_title},
        xaxis2=turnover_axis(W, x_max),
        shapes=horizon_shapes(W, x_max=x_max),
        annotations=horizon_annotations(W, x_max=x_max),
    )
    # An invisible trace bound to the secondary axis is what makes plotly render it.
    figure.add_trace(
        go.Scatter(x=[0, x_max], y=[None, None], xaxis="x2", showlegend=False, hoverinfo="skip")
    )


def trajectory_series_figure(
    per_chunk: pd.DataFrame,
    *,
    value_column: str,
    W: int,
    title: str,
    y_title: str,
    caption: str,
    run_ids: list[str],
    name: str,
    limitations: str | None = None,
    group_column: str = "semantic_seed",
) -> tuple[go.Figure, pd.DataFrame, FigureMeta]:
    """Per-trajectory traces (thin) plus the ensemble mean and CI band (thick).

    Showing only the mean would hide exactly the thing this project is about —
    whether trajectories stay separated — so individual traces are always drawn.
    """
    data = per_chunk.dropna(subset=[value_column]).copy()
    x_max = float(data["token_end"].max())
    figure = go.Figure()

    groups = sorted(data[group_column].dropna().unique()) if group_column in data else []
    colours = {group: PALETTE[i % len(PALETTE)] for i, group in enumerate(groups)}

    for trajectory_id, block in data.groupby("trajectory_id", sort=True):
        group = block[group_column].iloc[0] if group_column in block else None
        figure.add_trace(
            go.Scatter(
                x=block["token_end"],
                y=block[value_column],
                mode="lines",
                name=str(group),
                legendgroup=str(group),
                showlegend=False,
                line={"width": 1.0, "color": colours.get(group, ROLE_COLORS["trajectory"])},
                opacity=0.45,
                hovertemplate=(
                    f"{trajectory_id}<br>t=%{{x:,}} tokens<br>{y_title}=%{{y:.4f}}<extra></extra>"
                ),
            )
        )

    for group in groups:
        block = data[data[group_column] == group]
        ensemble = _ensemble(block, "token_end", value_column)
        colour = colours[group]
        figure.add_trace(
            go.Scatter(
                x=np.concatenate([ensemble["token_end"], ensemble["token_end"][::-1]]),
                y=np.concatenate([ensemble["ci_high"], ensemble["ci_low"][::-1]]),
                fill="toself",
                fillcolor=_rgba(colour, 0.15),
                line={"width": 0},
                name=f"{group} 95% CI",
                legendgroup=str(group),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=ensemble["token_end"],
                y=ensemble["mean"],
                mode="lines",
                name=f"{group} (n={int(ensemble['count'].max())})",
                legendgroup=str(group),
                line={"width": 2.6, "color": colour},
                hovertemplate=f"{group}<br>t=%{{x:,}}<br>mean=%{{y:.4f}}<extra></extra>",
            )
        )

    _time_axis_layout(
        figure,
        W=W,
        x_max=x_max,
        x_title="generated tokens t",
        y_title=y_title,
        title=title,
    )
    meta = FigureMeta(
        name=name,
        caption=caption,
        run_ids=run_ids,
        alt_text=f"{y_title} against generated tokens, per trajectory and ensemble mean with CI.",
        limitations=limitations,
        units={"token_end": "generator tokens", value_column: "cosine distance"},
        extra={"W": W, "n_trajectories": int(data["trajectory_id"].nunique())},
    )
    return figure, data, meta


def msd_figure(
    per_trajectory_msd: pd.DataFrame,
    aggregate: pd.DataFrame,
    fits: pd.DataFrame,
    *,
    chunk_size: int,
    W: int,
    run_ids: list[str],
    name: str = "msd_loglog",
) -> tuple[go.Figure, pd.DataFrame, FigureMeta]:
    """Log–log MSD with the fitted exponent annotated.

    A slope of 1 (free diffusion) is drawn as a reference line so the reader can
    see the deviation rather than take the fitted number on trust.
    """
    figure = go.Figure()
    lag_tokens = aggregate["lag_chunks"] * chunk_size

    for trajectory_id, block in per_trajectory_msd.groupby("trajectory_id", sort=True):
        figure.add_trace(
            go.Scatter(
                x=block["lag_chunks"] * chunk_size,
                y=block["msd"],
                mode="lines",
                name=str(trajectory_id),
                showlegend=False,
                line={"width": 0.9, "color": ROLE_COLORS["trajectory"]},
                opacity=0.35,
                hovertemplate=f"{trajectory_id}<br>τ=%{{x:,}} tokens<br>MSD=%{{y:.4g}}<extra></extra>",
            )
        )

    figure.add_trace(
        go.Scatter(
            x=np.concatenate([lag_tokens, lag_tokens[::-1]]),
            y=np.concatenate([aggregate["msd_ci_high"], aggregate["msd_ci_low"][::-1]]),
            fill="toself",
            fillcolor=_rgba(ROLE_COLORS["ci"], 0.18),
            line={"width": 0},
            name="95% CI (bootstrap over trajectories)",
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=lag_tokens,
            y=aggregate["msd_mean"],
            mode="lines+markers",
            name=f"ensemble mean (n={int(aggregate['n_trajectories'].max())})",
            line={"width": 2.8, "color": ROLE_COLORS["ci"]},
            marker={"size": 6},
            hovertemplate="τ=%{x:,} tokens<br>MSD=%{y:.4g}<extra></extra>",
        )
    )

    anchor_x = float(lag_tokens.iloc[0])
    anchor_y = float(aggregate["msd_mean"].iloc[0])
    reference = anchor_y * (lag_tokens / anchor_x) ** 1.0
    figure.add_trace(
        go.Scatter(
            x=lag_tokens,
            y=reference,
            mode="lines",
            name="α = 1 (free diffusion)",
            line={"width": 1.4, "color": ROLE_COLORS["baseline"], "dash": "dash"},
            hoverinfo="skip",
        )
    )

    alpha_mean = float(fits["msd_alpha"].mean())
    alpha_sd = float(fits["msd_alpha"].std(ddof=1)) if len(fits) > 1 else float("nan")
    regime = (
        "subdiffusive / confined"
        if alpha_mean < 0.9
        else "≈ free diffusion"
        if alpha_mean <= 1.1
        else "superdiffusive / directed drift"
    )
    figure.update_layout(
        template=plotly_template(),
        title=(
            f"Mean squared displacement in representation space<br>"
            f"<sub>fitted α = {alpha_mean:.3f} ± {alpha_sd:.3f} (sd over {len(fits)} "
            f"trajectories) — {regime}</sub>"
        ),
        xaxis={"title": "lag τ (generator tokens)", "type": "log"},
        yaxis={"title": "MSD(τ)  [squared Euclidean, L2-normalised embeddings]", "type": "log"},
    )
    # W marks the one lag with intrinsic meaning: a full memory turnover.
    if float(lag_tokens.max()) >= W:
        figure.add_vline(
            x=W,
            line={"color": ROLE_COLORS["horizon"], "width": 1.6},
            annotation={"text": "τ = W", "font": {"color": ROLE_COLORS["horizon"], "size": 10}},
        )

    meta = FigureMeta(
        name=name,
        caption=(
            f"Mean squared displacement against lag, log–log, on L2-normalised chunk embeddings, "
            f"post-horizon segment only. Thin grey lines are individual trajectories; the blue "
            f"curve is the ensemble mean with a 95% bootstrap CI resampled over trajectories "
            f"(n={int(aggregate['n_trajectories'].max())}). The dashed line has slope 1, the "
            f"free-diffusion reference. Fitted exponent α = {alpha_mean:.3f} ± {alpha_sd:.3f}."
        ),
        run_ids=run_ids,
        alt_text="Log-log plot of mean squared displacement against lag with a slope-1 reference.",
        limitations=(
            "An exponent estimated over a finite trajectory cannot establish asymptotic "
            "behaviour; the accessible lag range is bounded by the observed turnover count."
        ),
        units={"lag_chunks": "chunks", "lag_tokens": "generator tokens", "msd": "squared distance"},
        extra={"alpha_mean": alpha_mean, "alpha_sd": alpha_sd, "chunk_size": chunk_size, "W": W},
    )
    tidy = aggregate.assign(lag_tokens=lag_tokens)
    return figure, tidy, meta


def recurrence_figure(
    matrix: np.ndarray,
    *,
    trajectory_id: str,
    chunk_size: int,
    W: int,
    epsilon: float,
    rqa: dict[str, float],
    run_ids: list[str],
    name: str | None = None,
) -> tuple[go.Figure, dict[str, np.ndarray], FigureMeta]:
    """Recurrence plot: does the trajectory return to regions it has already visited?"""
    positions = (np.arange(matrix.shape[0]) + 1) * chunk_size
    figure = go.Figure(
        go.Heatmap(
            z=matrix.astype(np.int8),
            x=positions,
            y=positions,
            colorscale=[[0.0, "#FFFFFF"], [1.0, "#0072B2"]],
            showscale=False,
            hovertemplate="t_i=%{y:,}<br>t_j=%{x:,}<br>recurrent=%{z}<extra></extra>",
        )
    )
    figure.update_layout(
        template=plotly_template(),
        title=(
            f"Recurrence plot — {trajectory_id}<br>"
            f"<sub>ε at the {epsilon:.4f} distance threshold; recurrence rate "
            f"{rqa.get('recurrence_rate', float('nan')):.3f}, determinism "
            f"{rqa.get('determinism', float('nan')):.3f}, trapping time "
            f"{rqa.get('trapping_time', float('nan')):.1f} chunks</sub>"
        ),
        xaxis={"title": "generated tokens t_j", "constrain": "domain"},
        yaxis={"title": "generated tokens t_i", "scaleanchor": "x", "autorange": "reversed"},
        width=760,
        height=720,
    )
    meta = FigureMeta(
        name=name or f"recurrence_{trajectory_id}",
        caption=(
            f"Recurrence plot for trajectory {trajectory_id} over the post-horizon segment. A dark "
            f"pixel at (t_i, t_j) means the two chunk embeddings are within ε={epsilon:.4f} of each "
            f"other. Diagonal structure indicates the trajectory retracing previously visited "
            f"semantic regions; block structure indicates extended residence in one region."
        ),
        run_ids=run_ids,
        alt_text="Square binary matrix showing which pairs of time points are close in embedding space.",
        limitations=(
            "ε is a quantile of this trajectory's own distance distribution, so recurrence rates "
            "are comparable across trajectories only at equal quantile, not in absolute distance."
        ),
        units={"axes": "generator tokens"},
        extra={"epsilon": epsilon, "W": W, "chunk_size": chunk_size, **rqa},
    )
    return figure, {"recurrence": matrix.astype(np.int8), "token_positions": positions}, meta


def geometry_summary_panel(
    per_chunk: pd.DataFrame,
    scalars: pd.DataFrame,
    *,
    W: int,
    run_ids: list[str],
    name: str = "geometry_summary_panel",
) -> tuple[plt.Figure, pd.DataFrame, FigureMeta]:
    """Print-quality seaborn panel: displacement, drift, exponent, autocorrelation time."""
    apply_seaborn_theme()
    figure, axes = plt.subplots(1, 4, figsize=(FIGSIZE_DOUBLE[0] * 1.35, FIGSIZE_DOUBLE[1]))

    sns.histplot(
        data=per_chunk.dropna(subset=["step_displacement"]),
        x="step_displacement",
        hue="semantic_seed" if "semantic_seed" in per_chunk else None,
        element="step",
        stat="density",
        common_norm=False,
        ax=axes[0],
        legend=False,
    )
    axes[0].set_title("(a) semantic velocity")
    axes[0].set_xlabel("1 − cos(z_k, z_{k+1})")

    drift = per_chunk.dropna(subset=["distance_from_origin"])
    sns.lineplot(
        data=drift,
        x="turnover",
        y="distance_from_origin",
        hue="semantic_seed" if "semantic_seed" in drift else None,
        errorbar=("ci", 95),
        ax=axes[1],
        legend=False,
    )
    axes[1].axvline(1.0, color=ROLE_COLORS["horizon"], lw=1.4)
    axes[1].set_title("(b) drift from trajectory origin")
    axes[1].set_xlabel("window turnovers t/W")
    axes[1].set_ylabel("1 − cos(z_k, z_0)")

    sns.stripplot(
        data=scalars,
        x="msd_alpha",
        y="semantic_seed" if "semantic_seed" in scalars else None,
        ax=axes[2],
        size=7,
        alpha=0.85,
    )
    axes[2].axvline(1.0, color=ROLE_COLORS["baseline"], ls="--", lw=1.2)
    axes[2].set_title("(c) MSD exponent α")
    axes[2].set_xlabel("α  (1 = free diffusion)")
    axes[2].set_ylabel("")

    sns.barplot(
        data=scalars,
        x="integrated_autocorr_time",
        y="semantic_seed" if "semantic_seed" in scalars else None,
        ax=axes[3],
        errorbar=("ci", 95),
    )
    axes[3].set_title("(d) integrated autocorrelation time")
    axes[3].set_xlabel("chunks")
    axes[3].set_ylabel("")

    figure.suptitle(
        f"Trajectory geometry — W = {W:,} generator tokens, post-horizon statistics",
        x=0.005,
        ha="left",
        fontsize=14,
        fontweight="semibold",
    )
    figure.tight_layout()

    meta = FigureMeta(
        name=name,
        caption=(
            f"Geometry summary at W={W:,}. (a) distribution of per-step cosine displacement; "
            "(b) drift away from each trajectory's own first chunk, with the context horizon "
            "marked; (c) fitted MSD exponent per trajectory against the free-diffusion reference "
            "α=1; (d) integrated autocorrelation time of the displacement series, i.e. the "
            "effective spacing between independent observations."
        ),
        run_ids=run_ids,
        alt_text="Four-panel statistical summary of trajectory geometry.",
        limitations=(
            "Descriptive only. None of these panels distinguishes metastability from a slowly "
            "mixing single state; that requires the Markov-state analysis."
        ),
        units={"turnover": "t/W", "integrated_autocorr_time": "chunks"},
        extra={"W": W},
    )
    return figure, scalars, meta


def projection_figure(
    Z: np.ndarray,
    labels: pd.DataFrame,
    *,
    W: int,
    chunk_size: int,
    run_ids: list[str],
    name: str = "pca_projection_illustration",
) -> tuple[go.Figure, pd.DataFrame, FigureMeta]:
    """2-D PCA projection of the trajectories. **Illustration only.**

    Deliberately PCA rather than UMAP: it is linear, deterministic, and its
    distortion is at least characterisable. Either way no claim may rest on it,
    and the caption says so.
    """
    Zc = np.asarray(Z, dtype=np.float64)
    Zc = Zc - Zc.mean(axis=0, keepdims=True)
    # SVD rather than an eigendecomposition of the covariance: better conditioned
    # when d >> n, which is the usual case here (4096-d embeddings, ~10^2-10^3 chunks).
    _, singular, components = np.linalg.svd(Zc, full_matrices=False)
    coords = Zc @ components[:2].T
    explained = (singular[:2] ** 2) / float((singular**2).sum())

    tidy = labels.copy()
    tidy["pc1"] = coords[:, 0]
    tidy["pc2"] = coords[:, 1]

    figure = go.Figure()
    groups = sorted(tidy["semantic_seed"].unique()) if "semantic_seed" in tidy else ["all"]
    for index, group in enumerate(groups):
        block = tidy[tidy["semantic_seed"] == group] if "semantic_seed" in tidy else tidy
        figure.add_trace(
            go.Scatter(
                x=block["pc1"],
                y=block["pc2"],
                mode="markers+lines",
                name=str(group),
                marker={
                    "size": 6,
                    "color": block.get("turnover"),
                    "colorscale": "Viridis",
                    "showscale": index == 0,
                    "colorbar": {"title": "t/W"} if index == 0 else None,
                    "line": {"width": 0.6, "color": PALETTE[index % len(PALETTE)]},
                },
                line={"width": 0.8, "color": PALETTE[index % len(PALETTE)]},
                opacity=0.8,
                customdata=block[["trajectory_id", "chunk_index"]].to_numpy()
                if "trajectory_id" in block
                else None,
                hovertemplate=(
                    "%{customdata[0]}<br>chunk %{customdata[1]}<br>"
                    "PC1=%{x:.3f} PC2=%{y:.3f}<extra></extra>"
                ),
            )
        )
    figure.update_layout(
        template=plotly_template(),
        title=(
            "Semantic trajectories, first two principal components<br>"
            "<sub>ILLUSTRATION ONLY — all statistics are computed in the full embedding space. "
            f"PC1 {explained[0]:.1%}, PC2 {explained[1]:.1%} of variance</sub>"
        ),
        xaxis={"title": f"PC1 ({explained[0]:.1%} var)"},
        yaxis={"title": f"PC2 ({explained[1]:.1%} var)", "scaleanchor": "x"},
    )
    meta = FigureMeta(
        name=name,
        caption=(
            "Chunk embeddings projected onto their first two principal components, coloured by "
            f"window turnover t/W and connected in generation order. W={W:,}, chunk={chunk_size} "
            "tokens. Illustration only: all statistics reported in this project are computed in "
            "the full high-dimensional space."
        ),
        run_ids=run_ids,
        alt_text="Scatter of chunk embeddings in two principal components, connected in time order.",
        limitations=(
            "A 2-D projection cannot establish the existence, number, or separation of clusters. "
            "Nothing in this figure may be used as evidence; see the Markov-state analysis."
        ),
        units={"pc1": "arbitrary", "pc2": "arbitrary", "turnover": "t/W"},
        extra={
            "explained_variance_pc1": float(explained[0]),
            "explained_variance_pc2": float(explained[1]),
            "W": W,
        },
    )
    return figure, tidy, meta


def cost_breakdown_figure(
    estimates: pd.DataFrame,
    *,
    run_ids: list[str],
    name: str = "cost_breakdown",
) -> tuple[go.Figure, pd.DataFrame, FigureMeta]:
    """Input vs. output token cost per cell — the cost law made visible."""
    figure = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("cost by cell (USD)", "input amplification (input tokens / output tokens)"),
        horizontal_spacing=0.14,
    )
    label = estimates["generator"] + " W=" + estimates["W"].astype(str)
    figure.add_trace(
        go.Bar(x=label, y=estimates["input_usd"], name="input", marker_color=PALETTE[0]),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Bar(x=label, y=estimates["output_usd"], name="output", marker_color=PALETTE[1]),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Bar(
            x=label,
            y=estimates["input_amplification"],
            name="W/S",
            marker_color=PALETTE[2],
            showlegend=False,
        ),
        row=1,
        col=2,
    )
    figure.update_layout(
        template=plotly_template(),
        barmode="stack",
        title=(
            "Forecast cost under protocol P1<br>"
            "<sub>the whole window is re-sent every S tokens, so input ≈ T·W/S dominates</sub>"
        ),
    )
    figure.update_yaxes(title_text="USD", row=1, col=1)
    figure.update_yaxes(title_text="ratio", row=1, col=2)

    meta = FigureMeta(
        name=name,
        caption=(
            "Forecast API cost per experiment cell, split into input and output tokens, with the "
            "input amplification factor W/S alongside. Under the re-prompt protocol the entire "
            "window is re-sent every S generated tokens, so input tokens — not output tokens — "
            "set the budget."
        ),
        run_ids=run_ids,
        alt_text="Stacked bar chart of forecast input and output cost per cell, plus amplification ratio.",
        limitations=(
            "A forecast, not a bill. Assumes every request returns the full block and uses the "
            "prices recorded in the config at forecast time."
        ),
        units={"input_usd": "USD", "output_usd": "USD", "input_amplification": "dimensionless"},
    )
    return figure, estimates, meta


def _rgba(hex_colour: str, alpha: float) -> str:
    hex_colour = hex_colour.lstrip("#")
    r, g, b = (int(hex_colour[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"
