"""VAMP, non-reversible MSM, and the time-blind Leiden branch.

Every quantity here is defined in ``docs/methodology.md`` §3.5–3.6. Two
conventions are enforced rather than left to the caller:

* **PCA is a projection, not a whitening.** VAMP does its own covariance
  normalisation. Whitening before VAMP would double-count and invent
  isotropic noise as kinetic variance.
* **The replicate unit is the trajectory.** Count matrices, currents and
  agreement CIs are resampled over trajectories, never over chunks.

k-means cells are *microstates*. Only a PCCA+ / spectral coarse-graining
that survives implied-timescale flatness and a Chapman–Kolmogorov test
is a *macrostate*, and only those may be called semantic states.

A looping trajectory occupies one point in representation space. The
estimator will happily find one absorbing microstate. That is a
degeneracy result, not H1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.neighbors import NearestNeighbors

from ..embeddings.client import l2_normalise
from ..errors import AnalysisError


class DynamicsParams(BaseModel):
    """Knobs for the Stage 3 dynamics pass. Sourced from config, not literals."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    burn_in_turnovers: float = Field(default=1.0, ge=0.0)
    n_pca: int = Field(default=128, ge=2)
    n_vamp: int = Field(default=10, ge=1)
    n_microstates: int = Field(default=50, ge=2)
    n_macrostates: int = Field(default=3, ge=1)
    lags: tuple[int, ...] = Field(default=(1, 2, 4, 8))
    msm_lag: int = Field(default=1, ge=1)
    seed: int = Field(default=0)
    min_frames: int = Field(default=40, ge=8)
    min_trajectories: int = Field(default=2, ge=1)
    min_lag_pairs: int = Field(default=20, ge=4)
    n_pca_grid: tuple[int, ...] = Field(default=(64, 128))
    n_vamp_grid: tuple[int, ...] = Field(default=(5, 10, 15))
    k_grid: tuple[int, ...] = Field(default=(50, 100, 200, 400))
    k_max_fraction: float = Field(default=1.0 / 3.0, gt=0.0, le=0.5)
    n_macro_max: int = Field(default=4, ge=1)
    ck_ks: tuple[int, ...] = Field(default=(2, 3))
    ck_max_error: float = Field(default=0.15, gt=0.0)
    its_flat_rel: float = Field(default=0.5, gt=0.0)
    leiden_n_pca: int = Field(default=50, ge=2)
    leiden_k: int = Field(default=30, ge=2)
    leiden_resolution: float = Field(default=1.0, gt=0.0)
    kinetic_map: bool = True
    n_boot: int = Field(default=200, ge=20)
    min_chunks_per_trajectory: int = Field(default=40, ge=4)
    eligible_generators: tuple[str, ...] = Field(
        default=(
            "or-qwen3-8b",
            "or-qwen3-8b-prefill",
            "or-gpt-oss-120b",
            "or-muse-glimmer-30b",
        )
    )
    glimmer_temperature: float = 0.3
    glimmer_semantic_seed: str = "physics"
    spectral_gap_ratio: float = Field(default=2.0, gt=1.0)

    @classmethod
    def from_yaml(cls, path: Path | str | None) -> DynamicsParams:
        """Load knobs from ``configs/analysis/dynamics.yaml``. Extra keys stripped."""
        if path is None:
            return cls()
        target = Path(path)
        if not target.is_file():
            return cls()
        raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            raise AnalysisError(f"dynamics config {target} must be a mapping")
        raw.pop("analysis", None)
        return cls.model_validate(raw)


@dataclass(slots=True)
class TrajectorySeries:
    """One trajectory's post-horizon embeddings plus the labels MSM groups on."""

    trajectory_id: str
    embeddings: np.ndarray
    turnovers: np.ndarray
    token_ends: np.ndarray
    W: int
    generator: str
    temperature: float
    semantic_seed: str
    stochastic_seed: int
    embedding: str
    degenerate: bool = False


@dataclass(slots=True)
class DynamicsResult:
    """One (generator, embedding) group's MSM + Leiden fit."""

    group: str
    generator: str
    embedding: str
    scalars: dict[str, float]
    its: pd.DataFrame
    ck: pd.DataFrame
    currents: pd.DataFrame
    occupancy: pd.DataFrame
    vamp_scores: pd.DataFrame
    agreement: pd.DataFrame
    transition: np.ndarray
    notes: list[str] = field(default_factory=list)


def _as_matrix(Z: np.ndarray) -> np.ndarray:
    array = np.asarray(Z, dtype=np.float64)
    if array.ndim != 2 or array.shape[0] < 2:
        raise AnalysisError(f"expected a (n, d) embedding matrix with n>=2, got {array.shape}")
    return array


def _invsqrt(cov: np.ndarray, *, eps: float = 1e-6) -> np.ndarray:
    """Symmetric inverse square root, regularised.

    Used by VAMP to whiten both ends of the lagged pair. The epsilon is a
    numerical floor, not a scientific knob: without it a rank-deficient
    covariance (more coordinates than frames) produces NaNs that look like
    a kinetic result.
    """
    symmetric = 0.5 * (cov + cov.T)
    symmetric = symmetric + eps * np.eye(symmetric.shape[0])
    eigenvalues, eigenvectors = np.linalg.eigh(symmetric)
    eigenvalues = np.clip(eigenvalues, eps, None)
    return (eigenvectors * (1.0 / np.sqrt(eigenvalues))) @ eigenvectors.T


def lagged_pairs(series: list[np.ndarray], lag: int) -> tuple[np.ndarray, np.ndarray]:
    """Stack (X_t, X_{t+lag}) pairs from every trajectory.

    Trajectories are not concatenated in time: a pair never crosses a
    trajectory boundary. That would invent a transition the process did
    not make.
    """
    if lag < 1:
        raise AnalysisError("lag must be >= 1")
    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    for block in series:
        matrix = _as_matrix(block)
        if matrix.shape[0] <= lag:
            continue
        xs.append(matrix[:-lag])
        ys.append(matrix[lag:])
    if not xs:
        raise AnalysisError(f"no lagged pairs at τ={lag}")
    return np.vstack(xs), np.vstack(ys)


def pca_project(blocks: list[np.ndarray], *, n_pca: int, seed: int) -> list[np.ndarray]:
    """Project L2-normalised embeddings. No whitening."""
    stacked = np.vstack([l2_normalise(_as_matrix(block)) for block in blocks])
    n_components = int(min(n_pca, stacked.shape[0] - 1, stacked.shape[1]))
    if n_components < 2:
        raise AnalysisError(
            f"PCA needs at least 2 components; n_frames={stacked.shape[0]} d={stacked.shape[1]}"
        )
    model = PCA(n_components=n_components, svd_solver="full", random_state=seed)
    model.fit(stacked)
    return [model.transform(l2_normalise(_as_matrix(block))) for block in blocks]


def vamp_fit(
    blocks: list[np.ndarray],
    *,
    lag: int,
    n_vamp: int,
    kinetic_map: bool = True,
) -> tuple[np.ndarray, list[np.ndarray], float]:
    """VAMP at one lag. Returns singular values, per-trajectory coordinates, VAMP-2.

    VAMP rather than tICA because generation has an arrow of time:
    ``A → B`` need not equal ``B → A``. The VAMP-2 score is
    ``‖K‖_F² = Σ s_i²`` and is used for model selection only — a
    singular value is not a relaxation timescale.
    """
    x, y = lagged_pairs(blocks, lag)
    x = x - x.mean(axis=0, keepdims=True)
    y = y - y.mean(axis=0, keepdims=True)
    n = x.shape[0]
    cov_00 = (x.T @ x) / max(n - 1, 1)
    cov_0t = (x.T @ y) / max(n - 1, 1)
    cov_tt = (y.T @ y) / max(n - 1, 1)
    left = _invsqrt(cov_00)
    right = _invsqrt(cov_tt)
    koopman = left @ cov_0t @ right
    u_left, singular, _vt = np.linalg.svd(koopman, full_matrices=False)
    n_keep = int(min(n_vamp, singular.size, x.shape[1]))
    if n_keep < 1:
        raise AnalysisError("VAMP produced no coordinates")
    weights = singular[:n_keep] if kinetic_map else np.ones(n_keep)
    projector = left.T @ u_left[:, :n_keep] * weights
    # Map every frame, not just the lagged pairs, so k-means sees the
    # whole post-horizon series.
    coords = [((block - x.mean(axis=0)) @ projector) for block in blocks]
    vamp2 = float(np.sum(singular[:n_keep] ** 2))
    return singular[:n_keep], coords, vamp2


def tica_fit(
    blocks: list[np.ndarray],
    *,
    lag: int,
    n_tica: int,
) -> tuple[np.ndarray, list[np.ndarray]]:
    """Reversible tICA ablation. The VAMP/tICA gap is a measure of irreversibility."""
    x, y = lagged_pairs(blocks, lag)
    x = x - x.mean(axis=0, keepdims=True)
    y = y - y.mean(axis=0, keepdims=True)
    n = x.shape[0]
    cov_00 = (x.T @ x) / max(n - 1, 1)
    cov_0t = 0.5 * ((x.T @ y) + (y.T @ x)) / max(n - 1, 1)
    cov_00 = cov_00 + 1e-6 * np.eye(cov_00.shape[0])
    eigenvalues, eigenvectors = np.linalg.eig(np.linalg.solve(cov_00, cov_0t))
    order = np.argsort(-np.real(eigenvalues))
    eigenvalues = np.real(eigenvalues[order])
    eigenvectors = np.real(eigenvectors[:, order])
    n_keep = int(min(n_tica, eigenvalues.size))
    projector = eigenvectors[:, :n_keep]
    coords = [(block - x.mean(axis=0)) @ projector for block in blocks]
    return eigenvalues[:n_keep], coords


def subspace_gap(a: np.ndarray, b: np.ndarray) -> float:
    """Mean principal angle (radians) between two column-spaces.

    Zero means VAMP and tICA found the same subspace; a large angle is
    the irreversibility the methodology asked us to report.
    """
    left, _ = np.linalg.qr(a, mode="reduced")
    right, _ = np.linalg.qr(b, mode="reduced")
    n_keep = min(left.shape[1], right.shape[1])
    if n_keep == 0:
        return float("nan")
    singular = np.linalg.svd(left[:, :n_keep].T @ right[:, :n_keep], compute_uv=False)
    singular = np.clip(singular, 0.0, 1.0)
    return float(np.mean(np.arccos(singular)))


def assign_microstates(coords: list[np.ndarray], *, k: int, seed: int) -> list[np.ndarray]:
    stacked = np.vstack(coords)
    k_use = int(min(k, stacked.shape[0]))
    if k_use < 2:
        raise AnalysisError("k-means needs at least 2 frames and 2 centres")
    model = KMeans(n_clusters=k_use, n_init=10, random_state=seed)
    labels = model.fit_predict(stacked)
    out: list[np.ndarray] = []
    cursor = 0
    for block in coords:
        n = block.shape[0]
        out.append(labels[cursor : cursor + n].astype(np.int64))
        cursor += n
    return out


def count_matrix(assignments: list[np.ndarray], *, lag: int, n_states: int) -> np.ndarray:
    counts = np.zeros((n_states, n_states), dtype=np.float64)
    for series in assignments:
        if series.size <= lag:
            continue
        src = series[:-lag]
        dst = series[lag:]
        for i, j in zip(src, dst, strict=True):
            counts[int(i), int(j)] += 1.0
    return counts


def transition_matrix(counts: np.ndarray) -> np.ndarray:
    """Row-normalised ``T`` without detailed balance.

    Reversibility is a hypothesis to test, not a constraint to assume.
    An unvisited state is given a self-loop so ``T`` stays stochastic.
    """
    totals = counts.sum(axis=1, keepdims=True)
    transition = np.zeros_like(counts, dtype=np.float64)
    for i, total in enumerate(totals.ravel()):
        if total <= 0:
            transition[i, i] = 1.0
        else:
            transition[i] = counts[i] / total
    return transition


def stationary_distribution(transition: np.ndarray) -> np.ndarray:
    """Left eigenvector of ``T`` at λ=1, solved as a linear system.

    Taking ``eig`` and clipping the real part to be positive silently
    destroyed a valid all-negative eigenvector (a common sign convention)
    and reported a degenerate stationary distribution on any circulating
    chain. The constraint ``π T = π``, ``Σ π = 1`` does not have that
    failure mode.
    """
    n = transition.shape[0]
    system = transition.T - np.eye(n)
    system[-1] = 1.0
    rhs = np.zeros(n)
    rhs[-1] = 1.0
    try:
        pi = np.linalg.solve(system, rhs)
    except np.linalg.LinAlgError:
        pi = np.linalg.lstsq(system, rhs, rcond=None)[0]
    pi = np.real(pi)
    if float(pi.sum()) < 0:
        pi = -pi
    pi = np.maximum(pi, 0.0)
    total = float(pi.sum())
    if total <= 0:
        raise AnalysisError("stationary distribution is degenerate")
    return pi / total


def probability_currents(pi: np.ndarray, transition: np.ndarray) -> np.ndarray:
    """``J_ij = π_i T_ij − π_j T_ji``. Non-zero ⇒ circulation."""
    flux = pi[:, None] * transition
    return flux - flux.T


def implied_timescales(transition: np.ndarray, *, lag: int) -> tuple[np.ndarray, np.ndarray]:
    """``t_i = −τ / ln|λ_i|`` from the MSM, not from VAMP singular values."""
    eigenvalues = np.linalg.eigvals(transition)
    order = np.argsort(-np.abs(eigenvalues))
    eigenvalues = eigenvalues[order]
    timescales: list[float] = []
    for value in eigenvalues[1:]:
        magnitude = float(np.abs(value))
        if magnitude >= 1.0 - 1e-12 or magnitude <= 1e-15:
            timescales.append(float("inf") if magnitude >= 1.0 - 1e-12 else 0.0)
        else:
            timescales.append(float(-lag / np.log(magnitude)))
    return np.asarray(timescales, dtype=np.float64), eigenvalues


def choose_n_macro(timescales: np.ndarray, *, max_n: int, gap_ratio: float) -> int:
    """Number of macrostates from a spectral gap, or 1 if none.

    A fixed-point process has no gap. Returning 1 is the honest reading
    of H1 on that sample, not a failure of the estimator.
    """
    finite = [float(t) for t in timescales if np.isfinite(t) and t > 0]
    if len(finite) < 2:
        return 1
    for i in range(len(finite) - 1):
        if finite[i] / max(finite[i + 1], 1e-12) >= gap_ratio:
            return int(min(i + 2, max_n))
    return 1


def pcca_assign(
    transition: np.ndarray, assignments: list[np.ndarray], *, n_macro: int, seed: int
) -> list[np.ndarray]:
    """Spectral coarse-graining of microstates.

    k-means on the leading right eigenvectors of ``T`` (the PCCA+ /
    spectral-coarse-graining step in methodology §3.5). Not a geometric
    clustering of embeddings — that is the Leiden branch.
    """
    if n_macro <= 1:
        return [np.zeros(series.size, dtype=np.int64) for series in assignments]
    eigenvalues, eigenvectors = np.linalg.eig(transition)
    order = np.argsort(-np.abs(eigenvalues))
    features = np.real(eigenvectors[:, order[:n_macro]])
    # The first column is the stationary mode (constant up to scaling).
    # Clustering on it alone would put every microstate in one cell.
    if features.shape[1] >= 2:
        features = features[:, 1:]
    model = KMeans(n_clusters=int(min(n_macro, features.shape[0])), n_init=10, random_state=seed)
    micro_to_macro = model.fit_predict(features).astype(np.int64)
    return [micro_to_macro[series] for series in assignments]


def entropy_rate(pi: np.ndarray, transition: np.ndarray) -> float:
    safe = np.clip(transition, 1e-15, 1.0)
    return float(-np.sum(pi[:, None] * transition * np.log(safe)))


def mean_dwell(transition: np.ndarray, *, lag: int) -> np.ndarray:
    stay = np.clip(1.0 - np.diag(transition), 1e-15, 1.0)
    return lag / stay


def chapman_kolmogorov(
    assignments: list[np.ndarray],
    *,
    lag: int,
    ks: tuple[int, ...],
    n_states: int,
    object_name: str = "micro",
) -> pd.DataFrame:
    """``T(kτ) ≈ T(τ)^k``. Applied to a labelled assignment, not to VAMP.

    ``object_name`` records *which* assignment was tested. The pre-registered
    Stage 3 bar (F6) is the k-means micro-MSM. A coarse-grained assignment is
    a different object and must not inherit that bar's interpretation.
    """
    base = transition_matrix(count_matrix(assignments, lag=lag, n_states=n_states))
    rows: list[dict[str, float | str]] = []
    for k in ks:
        power = np.linalg.matrix_power(base, int(k))
        direct = transition_matrix(count_matrix(assignments, lag=lag * int(k), n_states=n_states))
        error = float(np.max(np.abs(direct - power)))
        rows.append(
            {
                "lag": float(lag),
                "k": float(k),
                "lag_k": float(lag * k),
                "max_abs_error": error,
                "object": object_name,
                "n_states": float(n_states),
            }
        )
    return pd.DataFrame(rows)


def leiden_partition(
    blocks: list[np.ndarray], *, n_pca: int, k: int, resolution: float, seed: int
) -> list[np.ndarray]:
    """Time-blind Leiden on a mutual-kNN graph of PCA(embeddings).

    Deliberately not run in VAMP coordinates, so this branch shares no
    temporal projection with the MSM.
    """
    import igraph as ig
    import leidenalg

    projected = pca_project(blocks, n_pca=n_pca, seed=seed)
    stacked = np.vstack(projected)
    n = stacked.shape[0]
    k_use = int(min(k, max(n // 2, 2)))
    neighbors = NearestNeighbors(n_neighbors=k_use + 1, metric="cosine")
    neighbors.fit(stacked)
    indices = neighbors.kneighbors(stacked, return_distance=False)[:, 1:]
    membership = [set(row.tolist()) for row in indices]
    edges: list[tuple[int, int]] = []
    for i, nbrs in enumerate(indices):
        for j in nbrs:
            j_int = int(j)
            if i < j_int and i in membership[j_int]:
                edges.append((i, j_int))
    graph = ig.Graph(n=n, edges=edges, directed=False)
    graph.simplify()
    partition = leidenalg.find_partition(
        graph,
        leidenalg.RBConfigurationVertexPartition,
        resolution_parameter=float(resolution),
        seed=int(seed),
    )
    labels = np.asarray(partition.membership, dtype=np.int64)
    out: list[np.ndarray] = []
    cursor = 0
    for block in projected:
        n_block = block.shape[0]
        out.append(labels[cursor : cursor + n_block])
        cursor += n_block
    return out


def _bootstrap_current_norm(
    assignments: list[np.ndarray],
    *,
    lag: int,
    n_states: int,
    n_boot: int,
    seed: int,
) -> dict[str, float]:
    """Bootstrap the Frobenius norm of ``J`` over trajectories."""
    rng = np.random.default_rng(seed)
    n = len(assignments)
    if n == 0:
        return {
            "j_norm": float("nan"),
            "j_norm_ci_low": float("nan"),
            "j_norm_ci_high": float("nan"),
        }
    observed = probability_currents(
        stationary_distribution(
            transition_matrix(count_matrix(assignments, lag=lag, n_states=n_states))
        ),
        transition_matrix(count_matrix(assignments, lag=lag, n_states=n_states)),
    )
    norms = np.empty(n_boot, dtype=np.float64)
    for b in range(n_boot):
        draw = [assignments[i] for i in rng.integers(0, n, size=n)]
        counts = count_matrix(draw, lag=lag, n_states=n_states)
        if counts.sum() == 0:
            norms[b] = 0.0
            continue
        transition = transition_matrix(counts)
        currents = probability_currents(stationary_distribution(transition), transition)
        norms[b] = float(np.linalg.norm(currents))
    return {
        "j_norm": float(np.linalg.norm(observed)),
        "j_norm_ci_low": float(np.quantile(norms, 0.025)),
        "j_norm_ci_high": float(np.quantile(norms, 0.975)),
    }


def _bootstrap_ari(
    a: list[np.ndarray],
    b: list[np.ndarray],
    *,
    n_boot: int,
    seed: int,
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    n = len(a)
    point = float(adjusted_rand_score(np.concatenate(a), np.concatenate(b)))
    nmi = float(normalized_mutual_info_score(np.concatenate(a), np.concatenate(b)))
    if n < 2:
        return {
            "ari": point,
            "ari_ci_low": float("nan"),
            "ari_ci_high": float("nan"),
            "nmi": nmi,
        }
    draws = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        draws[i] = adjusted_rand_score(
            np.concatenate([a[j] for j in idx]),
            np.concatenate([b[j] for j in idx]),
        )
    return {
        "ari": point,
        "ari_ci_low": float(np.quantile(draws, 0.025)),
        "ari_ci_high": float(np.quantile(draws, 0.975)),
        "nmi": nmi,
    }


def valid_k_grid(n_frames: int, params: DynamicsParams) -> tuple[int, ...]:
    cap = max(int(n_frames * params.k_max_fraction), 2)
    return tuple(k for k in params.k_grid if 2 <= k <= cap)


def its_is_flat(its: pd.DataFrame, *, rel: float) -> bool:
    """Slowest finite timescale changes by less than ``rel`` across adjacent τ."""
    if its.empty:
        return False
    slow = (
        its.replace([np.inf, -np.inf], np.nan)
        .dropna(subset=["timescale_chunks"])
        .groupby("lag", sort=True)["timescale_chunks"]
        .max()
    )
    if slow.size < 2:
        return False
    values = slow.to_numpy(dtype=np.float64)
    for left, right in pairwise(values):
        denom = max(abs(left), abs(right), 1e-12)
        if abs(right - left) / denom >= rel:
            return False
    return True


def filter_eligible(frame: pd.DataFrame, params: DynamicsParams) -> pd.DataFrame:
    """Drop arms the plan forbade and trajectories shorter than the bar."""
    lengths = frame.groupby("trajectory_id").size()
    keep_ids = set(lengths[lengths >= params.min_chunks_per_trajectory].index.astype(str))
    out = frame[frame["trajectory_id"].astype(str).isin(keep_ids)].copy()
    if params.eligible_generators:
        out = out[out["generator"].isin(params.eligible_generators)]
    glimmer = out["generator"].astype(str).str.contains("glimmer", case=False)
    if glimmer.any():
        keep_glimmer = glimmer & (out["temperature"] == params.glimmer_temperature)
        if "semantic_seed" in out.columns:
            keep_glimmer = keep_glimmer & (out["semantic_seed"] == params.glimmer_semantic_seed)
        out = out[~glimmer | keep_glimmer]
    return out


def series_from_frame(
    frame: pd.DataFrame,
    *,
    embedding: str,
    params: DynamicsParams,
    degenerate: dict[str, bool] | None = None,
) -> list[TrajectorySeries]:
    embedding_columns = [c for c in frame.columns if c.startswith("e") and c[1:].isdigit()]
    if not embedding_columns:
        raise AnalysisError("embedding frame has no e0… columns")
    out: list[TrajectorySeries] = []
    for trajectory_id, block in frame.groupby("trajectory_id", sort=True):
        block = block.sort_values("chunk_index")
        W = int(block["W"].iloc[0])
        turnovers = block["turnover"].to_numpy(dtype=np.float64)
        keep = turnovers >= params.burn_in_turnovers
        if int(keep.sum()) < 4:
            continue
        out.append(
            TrajectorySeries(
                trajectory_id=str(trajectory_id),
                embeddings=block.loc[keep, embedding_columns].to_numpy(dtype=np.float64),
                turnovers=turnovers[keep],
                token_ends=block.loc[keep, "token_end"].to_numpy(dtype=np.float64),
                W=W,
                generator=str(block["generator"].iloc[0]),
                temperature=float(block["temperature"].iloc[0]),
                semantic_seed=str(block["semantic_seed"].iloc[0]),
                stochastic_seed=int(block["stochastic_seed"].iloc[0]),
                embedding=embedding,
                degenerate=bool((degenerate or {}).get(str(trajectory_id), False)),
            )
        )
    return out


def compute_dynamics(
    trajectories: list[TrajectorySeries],
    *,
    params: DynamicsParams,
    group: str,
) -> DynamicsResult:
    """Fit VAMP → k-means → non-reversible MSM → Leiden for one process."""
    notes: list[str] = []
    if len(trajectories) < params.min_trajectories:
        raise AnalysisError(
            f"{group}: {len(trajectories)} trajectories < min {params.min_trajectories}"
        )
    blocks = [item.embeddings for item in trajectories]
    n_frames = int(sum(block.shape[0] for block in blocks))
    if n_frames < params.min_frames:
        raise AnalysisError(f"{group}: {n_frames} frames < min {params.min_frames}")

    n_pca = int(min(params.n_pca, n_frames - 2, blocks[0].shape[1]))
    projected = pca_project(blocks, n_pca=n_pca, seed=params.seed)
    n_vamp = int(min(params.n_vamp, n_pca))
    singular, vamp_coords, vamp2 = vamp_fit(
        projected, lag=params.msm_lag, n_vamp=n_vamp, kinetic_map=params.kinetic_map
    )
    tica_vals, tica_coords = tica_fit(projected, lag=params.msm_lag, n_tica=n_vamp)
    gap = subspace_gap(np.vstack(vamp_coords), np.vstack(tica_coords))

    k_choices = valid_k_grid(n_frames, params)
    if not k_choices:
        k_choices = (max(2, min(params.n_microstates, n_frames // 3)),)
        notes.append(f"K grid empty at n_frames={n_frames}; using {k_choices[0]}")
    k = int(min(params.n_microstates, k_choices[-1] if k_choices else n_frames // 3))
    if k not in k_choices:
        k = k_choices[0]
    # VAMP-2 is used for selection among valid K when we can afford a
    # two-trajectory holdout. With two trajectories the holdout is a
    # coin flip; we still record the in-sample score.
    vamp_rows = [{"n_pca": n_pca, "n_vamp": n_vamp, "K": k, "vamp2": vamp2, "split": "full"}]
    assignments = assign_microstates(vamp_coords, k=k, seed=params.seed)
    n_states = int(max(int(np.max(np.concatenate(assignments))) + 1, 2))

    its_rows: list[dict[str, float]] = []
    for lag in params.lags:
        n_pairs = sum(max(block.shape[0] - int(lag), 0) for block in projected)
        if n_pairs < params.min_lag_pairs:
            notes.append(f"skipped τ={lag}: {n_pairs} pairs")
            continue
        try:
            lagged_pairs(projected, int(lag))
        except AnalysisError:
            continue
        transition = transition_matrix(count_matrix(assignments, lag=int(lag), n_states=n_states))
        times, eigs = implied_timescales(transition, lag=int(lag))
        for index, (timescale, value) in enumerate(zip(times, eigs[1:], strict=False)):
            its_rows.append(
                {
                    "lag": float(lag),
                    "timescale_index": float(index + 1),
                    "timescale_chunks": float(timescale) if np.isfinite(timescale) else np.nan,
                    "abs_eigenvalue": float(np.abs(value)),
                    "imag_eigenvalue": float(np.imag(value)),
                    "n_pairs": float(n_pairs),
                }
            )
    its = pd.DataFrame(its_rows)
    flat = its_is_flat(its, rel=params.its_flat_rel)

    try:
        ck_micro = chapman_kolmogorov(
            assignments,
            lag=params.msm_lag,
            ks=params.ck_ks,
            n_states=n_states,
            object_name="micro",
        )
    except AnalysisError as exc:
        ck_micro = pd.DataFrame(
            columns=["lag", "k", "lag_k", "max_abs_error", "object", "n_states"]
        )
        notes.append(f"CK skipped: {exc}")
    ck_pass = bool(len(ck_micro) and float(ck_micro["max_abs_error"].max()) < params.ck_max_error)

    counts = count_matrix(assignments, lag=params.msm_lag, n_states=n_states)
    primary = transition_matrix(counts)
    pi = stationary_distribution(primary)
    currents = probability_currents(pi, primary)
    current_ci = _bootstrap_current_norm(
        assignments,
        lag=params.msm_lag,
        n_states=n_states,
        n_boot=params.n_boot,
        seed=params.seed,
    )
    times_primary, _ = implied_timescales(primary, lag=params.msm_lag)
    n_macro = choose_n_macro(
        times_primary, max_n=params.n_macro_max, gap_ratio=params.spectral_gap_ratio
    )
    if n_macro <= 1:
        notes.append("no spectral gap; n_macro=1 — H1 is unsupported on this cell")
    macros = pcca_assign(primary, assignments, n_macro=n_macro, seed=params.seed)
    n_macro_states = int(max((int(np.max(lab)) + 1) for lab in macros)) if macros else 1
    try:
        ck_macro = (
            chapman_kolmogorov(
                macros,
                lag=params.msm_lag,
                ks=params.ck_ks,
                n_states=max(n_macro_states, 1),
                object_name="macro",
            )
            if n_macro >= 2
            else pd.DataFrame(columns=["lag", "k", "lag_k", "max_abs_error", "object", "n_states"])
        )
    except AnalysisError as exc:
        ck_macro = pd.DataFrame(
            columns=["lag", "k", "lag_k", "max_abs_error", "object", "n_states"]
        )
        notes.append(f"macro CK skipped: {exc}")
    ck = pd.concat([ck_micro, ck_macro], ignore_index=True)
    ck_macro_max = float(ck_macro["max_abs_error"].max()) if len(ck_macro) else float("nan")
    ck_macro_pass = bool(len(ck_macro) and ck_macro_max < params.ck_max_error)

    try:
        leiden = leiden_partition(
            blocks,
            n_pca=min(params.leiden_n_pca, n_frames - 2),
            k=params.leiden_k,
            resolution=params.leiden_resolution,
            seed=params.seed,
        )
        agreement_stats = _bootstrap_ari(macros, leiden, n_boot=params.n_boot, seed=params.seed)
    except (ImportError, AnalysisError, ValueError, RuntimeError) as exc:
        notes.append(f"Leiden skipped: {exc}")
        leiden = [np.zeros(series.size, dtype=np.int64) for series in assignments]
        agreement_stats = {
            "ari": float("nan"),
            "ari_ci_low": float("nan"),
            "ari_ci_high": float("nan"),
            "nmi": float("nan"),
        }

    occupancy_rows: list[dict[str, object]] = []
    for item, micro, macro, community in zip(
        trajectories, assignments, macros, leiden, strict=True
    ):
        for index, (turnover, token_end, s_micro, s_macro, s_leiden) in enumerate(
            zip(item.turnovers, item.token_ends, micro, macro, community, strict=True)
        ):
            occupancy_rows.append(
                {
                    "trajectory_id": item.trajectory_id,
                    "generator": item.generator,
                    "embedding": item.embedding,
                    "temperature": item.temperature,
                    "semantic_seed": item.semantic_seed,
                    "chunk_index_post": index,
                    "turnover": float(turnover),
                    "token_end": float(token_end),
                    "microstate": int(s_micro),
                    "macrostate": int(s_macro),
                    "leiden": int(s_leiden),
                    "degenerate": bool(item.degenerate),
                }
            )
    occupancy = pd.DataFrame(occupancy_rows)

    current_rows = [
        {
            "i": i,
            "j": j,
            "J": float(currents[i, j]),
            "pi_i": float(pi[i]),
            "T_ij": float(primary[i, j]),
        }
        for i in range(n_states)
        for j in range(n_states)
        if i < j and abs(currents[i, j]) > 1e-12
    ]
    current_frame = pd.DataFrame(current_rows)

    n_degenerate = sum(1 for item in trajectories if item.degenerate)
    validated = bool(flat and ck_pass and n_macro >= 2 and n_degenerate < len(trajectories))
    if n_degenerate:
        notes.append(
            f"{n_degenerate}/{len(trajectories)} trajectories degenerate; "
            "timescales on those frames measure the loop"
        )

    visited = counts.sum(axis=1) > 0
    dwells = mean_dwell(primary, lag=params.msm_lag)
    mean_dwell_visited = float(np.mean(dwells[visited])) if bool(visited.any()) else float("nan")

    scalars = {
        "n_trajectories": float(len(trajectories)),
        "n_frames": float(n_frames),
        "n_pca": float(n_pca),
        "n_vamp": float(n_vamp),
        "K": float(n_states),
        "n_macro": float(n_macro),
        "vamp2": float(vamp2),
        "vamp_tica_angle": float(gap),
        "leading_singular": float(singular[0]) if singular.size else float("nan"),
        "leading_tica": float(tica_vals[0]) if tica_vals.size else float("nan"),
        "entropy_rate": entropy_rate(pi, primary),
        "mean_dwell_chunks": mean_dwell_visited,
        "its_flat": float(flat),
        "ck_pass": float(ck_pass),
        "ck_max_error": float(ck_micro["max_abs_error"].max()) if len(ck_micro) else float("nan"),
        "ck_macro_max_error": ck_macro_max,
        "ck_macro_pass": float(ck_macro_pass),
        "validated_macrostates": float(validated),
        "n_degenerate": float(n_degenerate),
        "underpowered": float(n_frames < 120 or len(trajectories) < 4),
        **current_ci,
        **{f"agreement_{key}": value for key, value in agreement_stats.items()},
    }

    agreement = pd.DataFrame(
        [
            {
                "generator": trajectories[0].generator,
                "embedding": trajectories[0].embedding,
                **agreement_stats,
                "n_macro": n_macro,
                "n_leiden": int(max((int(np.max(lab)) + 1) for lab in leiden)),
                "validated": validated,
            }
        ]
    )

    return DynamicsResult(
        group=group,
        generator=trajectories[0].generator,
        embedding=trajectories[0].embedding,
        scalars=scalars,
        its=its.assign(generator=trajectories[0].generator, embedding=trajectories[0].embedding),
        ck=ck.assign(generator=trajectories[0].generator, embedding=trajectories[0].embedding),
        currents=current_frame.assign(
            generator=trajectories[0].generator, embedding=trajectories[0].embedding
        ),
        occupancy=occupancy,
        vamp_scores=pd.DataFrame(vamp_rows).assign(
            generator=trajectories[0].generator, embedding=trajectories[0].embedding
        ),
        agreement=agreement,
        transition=primary,
        notes=notes,
    )


def compute_k_stability(
    trajectories: list[TrajectorySeries],
    *,
    params: DynamicsParams,
    group: str,
) -> pd.DataFrame:
    """Refit the MSM at every K that the plan's one-third cap allows.

    F7 is this table, not a single-K ``n_macro``. Each row is a full
    ``compute_dynamics`` so ``afterlife reproduce`` of the dynamics run
    regenerates it.
    """
    n_frames = int(sum(item.embeddings.shape[0] for item in trajectories))
    ks = list(valid_k_grid(n_frames, params))
    if params.n_microstates not in ks:
        fallback = int(min(params.n_microstates, max(n_frames // 3, 2)))
        if fallback >= 2 and fallback not in ks:
            ks.append(fallback)
    rows: list[dict[str, float | str]] = []
    for k in sorted(ks):
        varied = params.model_copy(update={"n_microstates": int(k)})
        result = compute_dynamics(trajectories, params=varied, group=group)
        rows.append(
            {
                "group": group,
                "generator": result.generator,
                "embedding": result.embedding,
                "K": result.scalars["K"],
                "n_macro": result.scalars["n_macro"],
                "its_flat": result.scalars["its_flat"],
                "ck_pass": result.scalars["ck_pass"],
                "ck_max_error": result.scalars["ck_max_error"],
                "ck_macro_max_error": result.scalars["ck_macro_max_error"],
                "validated": result.scalars["validated_macrostates"],
                "n_frames": result.scalars["n_frames"],
                "n_trajectories": result.scalars["n_trajectories"],
            }
        )
    return pd.DataFrame(rows)
