"""Geometry and diffusion of a semantic trajectory.

Every quantity here is defined in ``docs/methodology.md`` §3.1–3.3. Two
conventions are enforced rather than left to the caller, because getting them
wrong is the standard way this kind of analysis produces confident nonsense:

* **Euclidean geometry is computed on L2-normalised vectors**, where it is a
  monotone function of cosine distance. Mixing normalised and unnormalised
  vectors within one comparison is not permitted.
* **The replicate unit is the trajectory.** Aggregation across trajectories is a
  separate function, and bootstrap resampling happens over trajectories rather
  than over chunks — chunks are autocorrelated by construction, so resampling
  them would shrink every confidence interval in the paper (risks.md R9).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from ..embeddings.client import l2_normalise
from ..errors import AnalysisError


class GeometryParams(BaseModel):
    """Parameters for the single-trajectory geometry pass."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    burn_in_turnovers: float = Field(
        default=1.0,
        ge=0.0,
        description="discard chunks before this many window turnovers; 1.0 = the context horizon",
    )
    msd_max_lag_fraction: float = Field(
        default=0.25,
        gt=0.0,
        le=0.5,
        description="longest lag as a fraction of the series length, so each lag keeps enough "
        "independent pairs for the estimate to mean anything",
    )
    msd_fit_min_lag: int = Field(default=1, ge=1)
    recurrence_quantile: float = Field(
        default=0.05,
        gt=0.0,
        lt=1.0,
        description="epsilon as a quantile of the pairwise distance distribution",
    )
    recurrence_min_line: int = Field(default=2, ge=2, description="minimum diagonal line length")
    autocorr_max_lag: int = Field(default=64, ge=1)


@dataclass(slots=True)
class GeometryResult:
    """Per-trajectory geometry. ``per_chunk`` and ``msd`` are tidy frames."""

    trajectory_id: str
    per_chunk: pd.DataFrame
    msd: pd.DataFrame
    autocorrelation: pd.DataFrame
    scalars: dict[str, float]
    recurrence: np.ndarray | None = None


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


def cosine_distance_to(Z: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """``1 − cos(z_k, reference)`` for every row of ``Z``."""
    Zn = l2_normalise(np.asarray(Z, dtype=np.float64))
    ref = np.asarray(reference, dtype=np.float64).ravel()
    norm = np.linalg.norm(ref)
    if norm == 0:
        raise AnalysisError("reference vector has zero norm")
    return 1.0 - (Zn @ (ref / norm))


def step_displacement(Z: np.ndarray) -> np.ndarray:
    """Semantic velocity: ``1 − cos(z_k, z_{k+1})``, length ``n−1``."""
    Zn = l2_normalise(np.asarray(Z, dtype=np.float64))
    return 1.0 - np.einsum("ij,ij->i", Zn[:-1], Zn[1:])


def mean_squared_displacement(
    Z: np.ndarray, *, max_lag: int | None = None
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``MSD(τ) = E_t‖z_{t+τ} − z_t‖²`` on L2-normalised vectors.

    Returns ``(lags, msd, n_pairs)``. ``n_pairs`` is returned because the
    variance of the estimate at large ``τ`` is dominated by how few pairs remain,
    and any fit must weight by it rather than treating all lags equally.
    """
    Zn = l2_normalise(np.asarray(Z, dtype=np.float64))
    n = Zn.shape[0]
    if n < 4:
        raise AnalysisError(f"MSD needs at least 4 observations, got {n}")
    top = max_lag if max_lag is not None else max(1, n // 4)
    # A power-law fit needs at least three points, so never return fewer, even for
    # a short series -- the caller decides whether such a fit is worth reporting.
    top = min(max(top, 3), n - 1)
    lags = np.arange(1, top + 1, dtype=np.int64)
    msd = np.empty(top, dtype=np.float64)
    pairs = np.empty(top, dtype=np.int64)
    for index, lag in enumerate(lags):
        delta = Zn[lag:] - Zn[:-lag]
        msd[index] = float(np.mean(np.einsum("ij,ij->i", delta, delta)))
        pairs[index] = delta.shape[0]
    return lags, msd, pairs


def fit_msd_exponent(
    lags: np.ndarray,
    msd: np.ndarray,
    n_pairs: np.ndarray,
    *,
    min_lag: int = 1,
) -> dict[str, float]:
    """Weighted least squares of ``log MSD`` on ``log τ``.

    ``alpha < 1`` subdiffusion/confinement, ``≈ 1`` free diffusion, ``> 1``
    directed drift. Weights are ``n_pairs``, so short lags — where the estimate
    is actually well determined — dominate the fit.
    """
    mask = (lags >= min_lag) & (msd > 0)
    if mask.sum() < 3:
        raise AnalysisError("not enough positive MSD points to fit an exponent")
    x = np.log(lags[mask].astype(np.float64))
    y = np.log(msd[mask])
    w = n_pairs[mask].astype(np.float64)
    w = w / w.sum()

    x_mean = float(w @ x)
    y_mean = float(w @ y)
    sxx = float(w @ (x - x_mean) ** 2)
    if sxx <= 0:
        raise AnalysisError("degenerate lag range for the MSD fit")
    alpha = float(w @ ((x - x_mean) * (y - y_mean))) / sxx
    intercept = y_mean - alpha * x_mean
    residuals = y - (intercept + alpha * x)
    ss_res = float(w @ residuals**2)
    ss_tot = float(w @ (y - y_mean) ** 2)
    # Effective sample size for a weighted fit; using raw point count would
    # overstate the precision at long lags.
    n_eff = 1.0 / float(np.sum(w**2))
    se = float(np.sqrt(ss_res / max(n_eff - 2.0, 1.0) / sxx)) if sxx > 0 else float("nan")
    return {
        "alpha": alpha,
        "alpha_se": se,
        "intercept": intercept,
        "r_squared": 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan"),
        "n_lags": int(mask.sum()),
        "plateau_msd": float(msd[mask][-1]),
    }


def autocorrelation(series: np.ndarray, *, max_lag: int) -> tuple[np.ndarray, np.ndarray]:
    """Normalised autocorrelation of a 1-D series, lags ``0…max_lag``."""
    x = np.asarray(series, dtype=np.float64)
    x = x - x.mean()
    n = x.size
    if n < 3:
        raise AnalysisError("autocorrelation needs at least 3 points")
    top = min(max_lag, n - 2)
    denominator = float(x @ x)
    lags = np.arange(0, top + 1, dtype=np.int64)
    if denominator == 0:
        # A constant series (a fully degenerate trajectory) has undefined
        # autocorrelation; zeros are the honest answer, not ones.
        return lags, np.zeros(top + 1, dtype=np.float64)
    values = np.array([float(x[: n - lag] @ x[lag:]) / denominator for lag in lags])
    return lags, values


def integrated_autocorrelation_time(lags: np.ndarray, acf: np.ndarray) -> float:
    """``1 + 2Σ ρ(τ)``, truncated at the first non-positive value.

    Used to report an effective sample size next to any statistic computed over
    chunks, so the autocorrelation is visible rather than implicit.
    """
    total = 1.0
    for lag, value in zip(lags[1:], acf[1:], strict=True):
        if value <= 0:
            break
        total += 2.0 * float(value)
        del lag
    return total


def recurrence_matrix(Z: np.ndarray, *, quantile: float = 0.05) -> tuple[np.ndarray, float]:
    """Boolean recurrence matrix ``R_ij = 1[‖z_i − z_j‖ < ε]`` and the ``ε`` used.

    ``ε`` is a quantile of the observed pairwise distance distribution rather
    than an absolute number, so the diagnostic is comparable across embedding
    spaces with different scales. The quantile is reported and swept.
    """
    Zn = l2_normalise(np.asarray(Z, dtype=np.float64))
    sq = np.sum(Zn**2, axis=1)
    d2 = np.maximum(sq[:, None] + sq[None, :] - 2.0 * (Zn @ Zn.T), 0.0)
    distances = np.sqrt(d2)
    off_diagonal = distances[~np.eye(distances.shape[0], dtype=bool)]
    epsilon = float(np.quantile(off_diagonal, quantile))
    return distances < epsilon, epsilon


def recurrence_quantification(R: np.ndarray, *, min_line: int = 2) -> dict[str, float]:
    """Standard RQA measures from a recurrence matrix.

    ``recurrence_rate`` — density of recurrent pairs.
    ``determinism`` — share of recurrent points lying on diagonal lines, i.e. how
    much of the recurrence is deterministic revisiting rather than coincidence.
    ``mean_diagonal_line`` / ``max_diagonal_line`` — predictability timescale.
    ``trapping_time`` — mean vertical line length, the dwell-time proxy.
    """
    n = R.shape[0]
    if n < 3:
        raise AnalysisError("RQA needs at least a 3x3 recurrence matrix")
    mask = ~np.eye(n, dtype=bool)
    n_recurrent = int(R[mask].sum())
    recurrence_rate = n_recurrent / max(mask.sum(), 1)

    diagonal_lengths: list[int] = []
    for offset in range(1, n):
        diagonal = np.diagonal(R, offset=offset)
        diagonal_lengths.extend(_run_lengths(diagonal, min_line))
    on_diagonals = sum(diagonal_lengths)
    determinism = on_diagonals / max(n_recurrent / 2.0, 1.0)

    vertical_lengths: list[int] = []
    for column in range(n):
        vertical_lengths.extend(_run_lengths(R[:, column], min_line))

    return {
        "recurrence_rate": float(recurrence_rate),
        "determinism": float(min(determinism, 1.0)),
        "mean_diagonal_line": float(np.mean(diagonal_lengths)) if diagonal_lengths else 0.0,
        "max_diagonal_line": float(max(diagonal_lengths)) if diagonal_lengths else 0.0,
        "trapping_time": float(np.mean(vertical_lengths)) if vertical_lengths else 0.0,
        "n_diagonal_lines": float(len(diagonal_lengths)),
    }


def _run_lengths(vector: np.ndarray, min_line: int) -> list[int]:
    lengths: list[int] = []
    current = 0
    for value in vector:
        if value:
            current += 1
        else:
            if current >= min_line:
                lengths.append(current)
            current = 0
    if current >= min_line:
        lengths.append(current)
    return lengths


# ---------------------------------------------------------------------------
# Trajectory-level pass
# ---------------------------------------------------------------------------


def compute_geometry(
    Z: np.ndarray,
    *,
    trajectory_id: str,
    token_positions: np.ndarray,
    W: int,
    params: GeometryParams,
    token_starts: np.ndarray | None = None,
    seed_embedding: np.ndarray | None = None,
    with_recurrence: bool = True,
) -> GeometryResult:
    """Full geometry pass for one trajectory.

    ``token_positions`` gives each chunk's *end* position in generated tokens, so
    that every quantity can be reported against both absolute tokens and window
    turnovers ``t/W``.

    ``token_starts`` gives each chunk's *start*. A chunk counts as post-horizon
    only when it began after the seed had left the window: a chunk straddling
    ``t = W`` was generated while the seed was still partly visible, so including
    it would mix the forced and free regimes. Without ``token_starts`` the start
    is inferred from the previous chunk's end.
    """
    Z = np.asarray(Z, dtype=np.float64)
    if Z.ndim != 2:
        raise AnalysisError(f"expected a 2-D embedding matrix, got shape {Z.shape}")
    n = Z.shape[0]
    if n != token_positions.size:
        raise AnalysisError(
            f"{n} embeddings but {token_positions.size} token positions for {trajectory_id}"
        )
    if token_starts is None:
        token_starts = np.concatenate([[0], token_positions[:-1]])
    elif token_starts.size != n:
        raise AnalysisError(
            f"{n} embeddings but {token_starts.size} token starts for {trajectory_id}"
        )

    turnover = token_positions / float(W)
    turnover_start = token_starts / float(W)
    from_origin = cosine_distance_to(Z, Z[0])
    # Length-n columns. step_displacement is n-1; its first difference is n-2.
    # A one-chunk fragment (failed early) used to crash here: concat([nan, nan],
    # diff([])) has length 2. Dropping those fragments silently would hide that
    # they exist; they stay in the table with NaN dynamics.
    step_col = np.full(n, np.nan, dtype=np.float64)
    accel_col = np.full(n, np.nan, dtype=np.float64)
    if n >= 2:
        displacement = step_displacement(Z)
        step_col[1:] = displacement
        if n >= 3:
            accel_col[2:] = np.diff(displacement)

    per_chunk = pd.DataFrame(
        {
            "trajectory_id": trajectory_id,
            "chunk_index": np.arange(n, dtype=np.int64),
            "token_start": np.asarray(token_starts, dtype=np.int64),
            "token_end": token_positions.astype(np.int64),
            "turnover": turnover,
            "past_horizon": turnover_start >= 1.0,
            "distance_from_origin": from_origin,
            "step_displacement": step_col,
            "semantic_acceleration": accel_col,
        }
    )
    if seed_embedding is not None:
        per_chunk["distance_from_seed"] = cosine_distance_to(Z, seed_embedding)

    # Long-run quantities use only the post-horizon segment: before the horizon
    # the model can still see the seed, so those chunks belong to a different
    # (forced) process.
    keep = turnover_start >= params.burn_in_turnovers
    if keep.sum() < 8:
        # Too short for the long-run estimators; fall back to the whole series
        # and record that fact so no report can silently treat it as post-horizon.
        keep = np.ones(n, dtype=bool)
        burn_in_applied = False
    else:
        burn_in_applied = True
    Z_post = Z[keep]

    if n < 4:
        # MSD and ACF refuse n < 4 / n < 3. A failed-early trajectory is still
        # a row in the ensemble; its exponent is undefined, not zero.
        empty_msd = pd.DataFrame(
            {
                "trajectory_id": pd.Series(dtype=str),
                "lag_chunks": pd.Series(dtype=np.int64),
                "msd": pd.Series(dtype=np.float64),
                "n_pairs": pd.Series(dtype=np.int64),
            }
        )
        empty_acf = pd.DataFrame(
            {
                "trajectory_id": pd.Series(dtype=str),
                "lag_chunks": pd.Series(dtype=np.int64),
                "autocorrelation": pd.Series(dtype=np.float64),
            }
        )
        scalars = {
            "n_chunks": float(n),
            "n_chunks_post_horizon": float(int((turnover_start >= 1.0).sum())),
            "burn_in_applied": 0.0,
            "too_short_for_msd": 1.0,
            "mean_step_displacement": float("nan"),
            "std_step_displacement": float("nan"),
            "mean_distance_from_origin": float(np.mean(from_origin[keep])),
            "final_distance_from_origin": float(from_origin[-1]),
            "msd_alpha": float("nan"),
            "msd_alpha_se": float("nan"),
            "msd_r_squared": float("nan"),
            "msd_plateau": float("nan"),
            "integrated_autocorr_time": float("nan"),
        }
        if seed_embedding is not None:
            seed_distance = cosine_distance_to(Z, seed_embedding)
            scalars["mean_distance_from_seed"] = float(np.mean(seed_distance[keep]))
            scalars["final_distance_from_seed"] = float(seed_distance[-1])
        return GeometryResult(
            trajectory_id=trajectory_id,
            per_chunk=per_chunk,
            msd=empty_msd,
            autocorrelation=empty_acf,
            scalars=scalars,
            recurrence=None,
        )

    max_lag = max(1, int(Z_post.shape[0] * params.msd_max_lag_fraction))
    lags, msd_values, pairs = mean_squared_displacement(Z_post, max_lag=max_lag)
    msd = pd.DataFrame(
        {
            "trajectory_id": trajectory_id,
            "lag_chunks": lags,
            "msd": msd_values,
            "n_pairs": pairs,
        }
    )
    fit = fit_msd_exponent(lags, msd_values, pairs, min_lag=params.msd_fit_min_lag)

    displacement_post = step_displacement(Z_post)
    acf_lags, acf_values = autocorrelation(displacement_post, max_lag=params.autocorr_max_lag)
    autocorr = pd.DataFrame(
        {
            "trajectory_id": trajectory_id,
            "lag_chunks": acf_lags,
            "autocorrelation": acf_values,
        }
    )

    long_scalars: dict[str, float] = {
        "n_chunks": float(n),
        "n_chunks_post_horizon": float(int(keep.sum())),
        "burn_in_applied": float(burn_in_applied),
        "mean_step_displacement": float(np.nanmean(displacement_post)),
        "std_step_displacement": float(np.nanstd(displacement_post)),
        "mean_distance_from_origin": float(np.mean(from_origin[keep])),
        "final_distance_from_origin": float(from_origin[-1]),
        "msd_alpha": fit["alpha"],
        "msd_alpha_se": fit["alpha_se"],
        "msd_r_squared": fit["r_squared"],
        "msd_plateau": fit["plateau_msd"],
        "integrated_autocorr_time": integrated_autocorrelation_time(acf_lags, acf_values),
        "too_short_for_msd": 0.0,
    }
    if seed_embedding is not None:
        seed_distance = cosine_distance_to(Z, seed_embedding)
        long_scalars["mean_distance_from_seed"] = float(np.mean(seed_distance[keep]))
        long_scalars["final_distance_from_seed"] = float(seed_distance[-1])

    recurrence: np.ndarray | None = None
    if with_recurrence and Z_post.shape[0] >= 8:
        recurrence, epsilon = recurrence_matrix(Z_post, quantile=params.recurrence_quantile)
        long_scalars["recurrence_epsilon"] = epsilon
        long_scalars.update(
            recurrence_quantification(recurrence, min_line=params.recurrence_min_line)
        )

    return GeometryResult(
        trajectory_id=trajectory_id,
        per_chunk=per_chunk,
        msd=msd,
        autocorrelation=autocorr,
        scalars=long_scalars,
        recurrence=recurrence,
    )


def aggregate_msd(
    results: list[GeometryResult], *, n_boot: int = 2000, seed: int = 0
) -> pd.DataFrame:
    """Ensemble MSD with a bootstrap CI **over trajectories**.

    Resampling trajectories rather than chunks is the whole point: chunks within
    a trajectory are strongly autocorrelated, so a chunk-level bootstrap would
    report intervals several times too narrow.
    """
    if not results:
        raise AnalysisError("no geometry results to aggregate")
    frames = [r.msd.set_index("lag_chunks")["msd"] for r in results if not r.msd.empty]
    if not frames:
        raise AnalysisError("no trajectory was long enough to form an MSD")
    wide = pd.concat(frames, axis=1, join="inner")
    if wide.empty:
        raise AnalysisError("trajectories share no common lag range")
    matrix = wide.to_numpy(dtype=np.float64)  # (n_lags, n_trajectories)

    rng = np.random.default_rng(seed)
    n_traj = matrix.shape[1]
    draws = rng.integers(0, n_traj, size=(n_boot, n_traj))
    boot_means = np.stack([matrix[:, draw].mean(axis=1) for draw in draws], axis=1)

    return pd.DataFrame(
        {
            "lag_chunks": wide.index.to_numpy(dtype=np.int64),
            "msd_mean": matrix.mean(axis=1),
            "msd_median": np.median(matrix, axis=1),
            "msd_ci_low": np.quantile(boot_means, 0.025, axis=1),
            "msd_ci_high": np.quantile(boot_means, 0.975, axis=1),
            "n_trajectories": n_traj,
        }
    )


def bootstrap_mean_ci(
    values: np.ndarray, *, n_boot: int = 2000, seed: int = 0, alpha: float = 0.05
) -> dict[str, float]:
    """Percentile bootstrap CI for a mean over trajectories."""
    x = np.asarray(values, dtype=np.float64)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return {"mean": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "n": 0}
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, x.size, size=(n_boot, x.size))
    means = x[draws].mean(axis=1)
    return {
        "mean": float(x.mean()),
        "ci_low": float(np.quantile(means, alpha / 2)),
        "ci_high": float(np.quantile(means, 1 - alpha / 2)),
        "n": int(x.size),
    }
