"""Paper B persistence estimands: G_t, prefix lock/escape, seed-cluster bootstrap.

Confirmatory hierarchy and horizon rules: ADR-0023 (F1/F4), ADR-0025.
Pure functions only — no I/O. Synthetic tests live in ``tests/test_persistence.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from ..errors import AnalysisError

LockState = Literal["unlocked", "locked", "escaped"]


class PersistenceParams(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    n_confirm: int = Field(default=3, ge=1, description="Frozen F1 confirmation window")
    n_boot: int = Field(default=2000, ge=50)
    alpha: float = Field(default=0.05, gt=0.0, lt=0.5)
    seed: int = Field(default=0)
    log_band_start: float = Field(
        default=1.0,
        gt=0.0,
        description="first turnover band edge; bands are log-spaced after this",
    )
    n_log_bands: int = Field(default=12, ge=2)
    max_turnover: float | None = Field(
        default=None,
        description="if set, band edges stop here; else derived from data",
    )
    late_jaccard_cap_chunks: int = Field(
        default=64,
        ge=8,
        description="L2-safe subsample size for late pairwise Jaccard",
    )


@dataclass(slots=True)
class LockEscapeResult:
    trajectory_id: str
    states: list[LockState]
    tau_lock: float | None
    tau_escape: float | None
    confirmed_lock: bool
    confirmed_escape: bool


def log_turnover_bands(
    max_turnover: float,
    *,
    start: float = 1.0,
    n_bands: int = 12,
) -> np.ndarray:
    """Inclusive edges of log-spaced turnover bands covering ``[start, max_turnover]``."""
    if max_turnover <= start:
        return np.asarray([start, max(max_turnover, start)], dtype=np.float64)
    return np.geomspace(start, max_turnover, n_bands + 1)


def prefix_lock_escape(
    degenerate_by_turnover: np.ndarray,
    turnovers: np.ndarray,
    *,
    n_confirm: int = 3,
    trajectory_id: str = "traj",
) -> LockEscapeResult:
    """unlocked → locked → escaped with an N_confirm window on both edges.

    ``degenerate_by_turnover[i]`` is the per-turnover degeneracy flag (same
    construct as L0). Exact-cycle hash is intentionally not an input.
    """
    if degenerate_by_turnover.shape != turnovers.shape:
        raise AnalysisError("degenerate flags and turnovers must align")
    if degenerate_by_turnover.size == 0:
        raise AnalysisError(f"no turnovers for {trajectory_id}")

    states: list[LockState] = []
    phase: LockState = "unlocked"
    run = 0
    tau_lock: float | None = None
    tau_escape: float | None = None
    prev = bool(degenerate_by_turnover[0])
    run = 1
    # recompute run-length carefully
    run = 0
    last_val: bool | None = None
    for deg, t in zip(degenerate_by_turnover.astype(bool), turnovers, strict=True):
        if last_val is None or deg != last_val:
            run = 1
            last_val = bool(deg)
        else:
            run += 1

        if phase == "unlocked":
            if deg and run >= n_confirm:
                phase = "locked"
                tau_lock = float(t)
        elif phase == "locked":
            if (not deg) and run >= n_confirm:
                phase = "escaped"
                tau_escape = float(t)
        states.append(phase)

    return LockEscapeResult(
        trajectory_id=trajectory_id,
        states=states,
        tau_lock=tau_lock,
        tau_escape=tau_escape,
        confirmed_lock=tau_lock is not None,
        confirmed_escape=tau_escape is not None,
    )


def _pairwise_mean_distance(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or b.size == 0:
        return float("nan")
    # cosine distance on L2-normalised rows
    a_n = a / np.clip(np.linalg.norm(a, axis=1, keepdims=True), 1e-12, None)
    b_n = b / np.clip(np.linalg.norm(b, axis=1, keepdims=True), 1e-12, None)
    sims = a_n @ b_n.T
    return float(1.0 - np.mean(sims))


@dataclass(slots=True)
class TrajectoryEmbed:
    trajectory_id: str
    seed_id: str
    embeddings: np.ndarray  # (n_chunks, d)
    turnovers: np.ndarray


def gap_vs_turnover(
    trajectories: list[TrajectoryEmbed],
    *,
    band_edges: np.ndarray,
) -> pd.DataFrame:
    """Compute G_t = d_between(t) - d_within(t) per turnover band.

    Hierarchy: pairs are formed across trajectories; uncertainty belongs in
    :func:`seed_cluster_bootstrap`, not in this point estimate.
    """
    if len(trajectories) < 2:
        raise AnalysisError("G_t needs at least two trajectories")
    rows: list[dict[str, float | str]] = []
    for left, right in zip(band_edges[:-1], band_edges[1:], strict=True):  # noqa: RUF007
        within: list[float] = []
        between: list[float] = []
        by_seed: dict[str, list[np.ndarray]] = {}
        for traj in trajectories:
            mask = (traj.turnovers >= left) & (traj.turnovers < right)
            if not np.any(mask):
                continue
            by_seed.setdefault(traj.seed_id, []).append(traj.embeddings[mask])
        seeds = list(by_seed)
        for _seed, mats in by_seed.items():
            if len(mats) < 2:
                continue
            for i in range(len(mats)):
                for j in range(i + 1, len(mats)):
                    within.append(_pairwise_mean_distance(mats[i], mats[j]))
        for i, s_i in enumerate(seeds):
            for s_j in seeds[i + 1 :]:
                for a in by_seed[s_i]:
                    for b in by_seed[s_j]:
                        between.append(_pairwise_mean_distance(a, b))
        d_within = float(np.mean(within)) if within else float("nan")
        d_between = float(np.mean(between)) if between else float("nan")
        rows.append(
            {
                "band_left": float(left),
                "band_right": float(right),
                "band_mid": float(np.sqrt(left * right)),
                "d_within": d_within,
                "d_between": d_between,
                "G": d_between - d_within,
                "n_within_pairs": float(len(within)),
                "n_between_pairs": float(len(between)),
            }
        )
    return pd.DataFrame(rows)


def seed_cluster_bootstrap(
    trajectories: list[TrajectoryEmbed],
    *,
    band_edges: np.ndarray,
    params: PersistenceParams,
) -> pd.DataFrame:
    """Resample seeds (with descendant multiplicity) to CI the band-wise G_t."""
    rng = np.random.default_rng(params.seed)
    seeds = sorted({t.seed_id for t in trajectories})
    if len(seeds) < 2:
        raise AnalysisError("seed-cluster bootstrap needs at least two seeds")
    by_seed: dict[str, list[TrajectoryEmbed]] = {s: [] for s in seeds}
    for traj in trajectories:
        by_seed[traj.seed_id].append(traj)

    point = gap_vs_turnover(trajectories, band_edges=band_edges)
    boot = np.zeros((params.n_boot, len(point)), dtype=np.float64)
    for b in range(params.n_boot):
        drawn = rng.choice(seeds, size=len(seeds), replace=True)
        sample: list[TrajectoryEmbed] = []
        for k, seed in enumerate(drawn):
            for traj in by_seed[seed]:
                sample.append(
                    TrajectoryEmbed(
                        trajectory_id=f"{traj.trajectory_id}__boot{b}_{k}",
                        seed_id=f"{seed}__{k}",
                        embeddings=traj.embeddings,
                        turnovers=traj.turnovers,
                    )
                )
        try:
            frame = gap_vs_turnover(sample, band_edges=band_edges)
            boot[b] = frame["G"].to_numpy(dtype=np.float64)
        except AnalysisError:
            boot[b] = np.nan
    lo = np.nanpercentile(boot, 100 * params.alpha / 2.0, axis=0)
    hi = np.nanpercentile(boot, 100 * (1.0 - params.alpha / 2.0), axis=0)
    out = point.copy()
    out["G_lo"] = lo
    out["G_hi"] = hi
    return out


def capped_late_jaccard(
    shingle_sets: list[set[tuple[str, ...]]],
    *,
    cap: int = 64,
    seed: int = 0,
) -> float:
    """Mean pairwise Jaccard on a capped subsample of late chunks (L2-safe)."""
    if len(shingle_sets) < 2:
        return float("nan")
    rng = np.random.default_rng(seed)
    idx = np.arange(len(shingle_sets))
    if len(idx) > cap:
        idx = np.sort(rng.choice(idx, size=cap, replace=False))
    vals: list[float] = []
    for i in range(len(idx)):
        for j in range(i + 1, len(idx)):
            a = shingle_sets[int(idx[i])]
            b = shingle_sets[int(idx[j])]
            union = a | b
            vals.append(len(a & b) / len(union) if union else 0.0)
    return float(np.mean(vals)) if vals else float("nan")
